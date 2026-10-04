"""Validate a render-ready resume JSON before any TeX is produced.

This is the gate that makes an LLM loop workable: the model emits JSON, this
module reports every problem with a JSON Pointer path, and the model fixes
them. The renderer refuses to run until validation is clean, so a malformed
document can never reach Tectonic.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from . import DATA_DIR, RENDERED_SCHEMA

__all__ = ["Problem", "validate", "load_schema", "confidential_terms"]

EMPTY_MD_LINK = re.compile(r"\[[^\]\n]*\]\(\s*\)")
CONFIDENTIAL_TERMS_FILE = DATA_DIR / "confidential_terms.txt"


@dataclass(frozen=True)
class Problem:
    """One validation failure, addressed by JSON Pointer."""

    path: str
    message: str
    value: Any = field(default=None, repr=False)

    def __str__(self) -> str:
        return f"{self.path or '/'}: {self.message}"


_schema_cache: dict[Path, dict] = {}


def load_schema(path: Path | None = None) -> dict:
    path = Path(path or RENDERED_SCHEMA)
    if path not in _schema_cache:
        _schema_cache[path] = json.loads(path.read_text())
    return _schema_cache[path]


def confidential_terms() -> list[str]:
    """Terms that must never appear in a rendered resume.

    ``data/master_resume.json`` deliberately no longer records the withheld
    Intel customer identities, so the denylist cannot live there. It is read
    from ``data/confidential_terms.txt`` (one term per line, ``#`` comments
    allowed), which is gitignored precisely so the names stay out of version
    control. ``RESUME_CONFIDENTIAL_TERMS`` overrides the path.

    An absent file yields an empty list, and the check simply does not fire.
    """
    override = os.environ.get("RESUME_CONFIDENTIAL_TERMS")
    path = Path(override) if override else CONFIDENTIAL_TERMS_FILE
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _pointer(parts) -> str:
    out = ""
    for p in parts:
        token = str(p).replace("~", "~0").replace("/", "~1")
        out += "/" + token
    return out


def _iter_prose(resume: dict):
    """Yield ``(pointer, text)`` for every free-form string the renderer emits."""
    for s_idx, section in enumerate(resume.get("sections") or []):
        if not isinstance(section, dict):
            continue
        base = ["sections", s_idx]
        for e_idx, entry in enumerate(section.get("entries") or []):
            if not isinstance(entry, dict):
                continue
            for b_idx, bullet in enumerate(entry.get("bullets") or []):
                if isinstance(bullet, str):
                    yield _pointer([*base, "entries", e_idx, "bullets", b_idx]), bullet
        for i_idx, item in enumerate(section.get("items") or []):
            if isinstance(item, str):
                yield _pointer([*base, "items", i_idx]), item


SECTION_TYPES = ("education", "experience", "projects", "skills", "achievements")


def _explain_section(error) -> list[Problem]:
    """Turn an unreadable ``oneOf`` failure into problems a caller can act on.

    A section is matched by its ``type``, so only one ``oneOf`` branch is ever
    relevant. Reporting the raw failure lists all five branches' complaints --
    including nonsense like a projects section needing ``groups``. We pick the
    branch whose ``type`` const matched and report only its errors.

    Note that a context error's ``absolute_path`` already runs from the
    document root (jsonschema walks the parent chain), so it is used as-is.
    """
    section_type = error.instance.get("type")
    if section_type not in SECTION_TYPES:
        return [
            Problem(
                _pointer(error.absolute_path),
                f"unknown section type {section_type!r}; expected one of "
                f"{', '.join(SECTION_TYPES)}",
                error.instance,
            )
        ]

    by_branch: dict[Any, list] = {}
    for sub in error.context or []:
        branch = sub.schema_path[0] if sub.schema_path else None
        by_branch.setdefault(branch, []).append(sub)

    def failed_on_type(errors) -> bool:
        return any(list(e.absolute_path)[-1:] == ["type"] for e in errors)

    matching = [errs for errs in by_branch.values() if not failed_on_type(errs)]
    if not matching:
        return [
            Problem(
                _pointer(error.absolute_path),
                f"invalid {section_type} section: {error.message}",
                error.instance,
            )
        ]

    return [
        Problem(
            _pointer(sub.absolute_path),
            f"invalid {section_type} section: {sub.message}",
            sub.instance,
        )
        for errs in matching
        for sub in errs
    ]


def validate(resume: Any, *, schema: dict | None = None) -> list[Problem]:
    """Return every problem found in ``resume``; an empty list means valid.

    Schema failures are reported first, then the semantic checks a schema
    cannot express. Schema errors are sorted by path so output is stable.
    """
    problems: list[Problem] = []

    if not isinstance(resume, dict):
        return [Problem("", f"top level must be a JSON object, got {type(resume).__name__}")]

    validator = Draft202012Validator(schema or load_schema())
    for error in sorted(validator.iter_errors(resume), key=lambda e: list(e.absolute_path)):
        if error.validator == "oneOf" and isinstance(error.instance, dict):
            problems.extend(_explain_section(error))
            continue
        problems.append(Problem(_pointer(error.absolute_path), error.message, error.instance))

    denylist = confidential_terms()
    for pointer, text in _iter_prose(resume):
        if EMPTY_MD_LINK.search(text):
            problems.append(
                Problem(pointer, "markdown link has an empty URL; give it a target or drop it", text)
            )
        lowered = text.lower()
        for term in denylist:
            if term.lower() in lowered:
                problems.append(
                    Problem(
                        pointer,
                        f"contains the withheld term {term!r}; use the agreed abstraction instead",
                        text,
                    )
                )

    return problems
