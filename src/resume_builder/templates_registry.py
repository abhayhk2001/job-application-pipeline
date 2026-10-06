"""Find the template a render should use.

A template is a *directory*, not a file: it holds ``resume.tex.j2`` (the
preamble and document skeleton) and, optionally, overrides for any of the
section partials it would otherwise inherit from ``templates/_shared/``. That
is the whole mechanism -- Jinja's ``FileSystemLoader`` takes a list of
directories and searches them in order, so ``[<template>, _shared]`` gives
inheritance for free. A template that only wants a different font is one file.

Directories are searched in this order, first match winning, so a template of
your own can shadow a built-in of the same name:

1. an explicit ``templates_dir`` (the ``--templates-dir`` flag)
2. ``<project root>/templates/``   -- yours, edit freely
3. ``src/resume_builder/templates/`` -- shipped with the package

Names starting with ``_`` or ``.`` are not templates, which is what keeps
``_shared`` out of the menu.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from . import PROJECT_TEMPLATES_DIR, SHARED_TEMPLATES_DIR, TEMPLATES_DIR
from .exceptions import TemplateNotFound

__all__ = [
    "DEFAULT_TEMPLATE",
    "MANIFEST_NAME",
    "TemplateInfo",
    "choose",
    "describe",
    "find",
    "list_templates",
    "resolve",
    "search_path",
]

DEFAULT_TEMPLATE = "classic"
MANIFEST_NAME = "template.json"
ROOT_TEMPLATE = "resume.tex.j2"

#: A template name must be a plain directory name. Rejecting anything else is
#: what stops an LLM-supplied ``"../../etc"`` from ever reaching the filesystem.
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class TemplateInfo:
    """One available template, as ``--list-templates`` reports it."""

    name: str
    description: str
    best_for: str
    path: Path
    source: str  # "explicit" | "project" | "builtin"

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "best_for": self.best_for,
            "path": str(self.path),
            "source": self.source,
        }


def search_path(templates_dir: Path | str | None = None) -> list[tuple[Path, str]]:
    """Return the ``(directory, source)`` pairs to search, highest priority first."""
    candidates: list[tuple[Path, str]] = []
    if templates_dir is not None:
        candidates.append((Path(templates_dir), "explicit"))
    candidates.append((PROJECT_TEMPLATES_DIR, "project"))
    candidates.append((TEMPLATES_DIR, "builtin"))
    return [(d, source) for d, source in candidates if d.is_dir()]


def _read_manifest(directory: Path) -> dict:
    """Read ``template.json`` if present. It is optional by design.

    A template with no manifest still works -- copying a directory and editing
    it should not require writing JSON -- so an absent or unreadable manifest
    degrades to an empty description rather than an error.
    """
    manifest = directory / MANIFEST_NAME
    if not manifest.is_file():
        return {}
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _is_template_dir(directory: Path) -> bool:
    return (
        directory.is_dir()
        and not directory.name.startswith(("_", "."))
        and (directory / ROOT_TEMPLATE).is_file()
    )


def list_templates(templates_dir: Path | str | None = None) -> list[TemplateInfo]:
    """Every available template, sorted by name, shadowed duplicates dropped."""
    found: dict[str, TemplateInfo] = {}
    for directory, source in search_path(templates_dir):
        for child in sorted(directory.iterdir()):
            if not _is_template_dir(child) or child.name in found:
                continue
            manifest = _read_manifest(child)
            found[child.name] = TemplateInfo(
                name=child.name,
                description=str(manifest.get("description", "")),
                best_for=str(manifest.get("best_for", "")),
                path=child,
                source=source,
            )
    return [found[name] for name in sorted(found)]


def find(name: str, templates_dir: Path | str | None = None) -> TemplateInfo:
    """Return the ``TemplateInfo`` for ``name``, or raise ``TemplateNotFound``.

    The name is checked against ``NAME_RE`` before anything is looked up, and
    it is only ever compared against discovered directory names -- it is never
    joined onto a path, so no name can escape the search directories.
    """
    valid = isinstance(name, str) and bool(NAME_RE.match(name))
    available = list_templates(templates_dir)
    if valid:
        for info in available:
            if info.name == name:
                return info
    raise TemplateNotFound(name, [t.name for t in available])


def resolve(name: str, templates_dir: Path | str | None = None) -> list[Path]:
    """Return the Jinja loader search path for ``name``.

    ``[<the template's directory>, templates/_shared]`` -- so a file the
    template does not define is inherited from the shared partials.
    """
    return [find(name, templates_dir).path, SHARED_TEMPLATES_DIR]


def choose(resume: Mapping | None = None, override: str | None = None) -> str:
    """Decide which template to use. The one place this precedence is written.

    An explicit argument (``--template``) beats the resume's own ``template``
    key, which beats the default. Keeping it here is what stops the CLI and
    ``api.build_resume`` from disagreeing.
    """
    if override:
        return override
    if isinstance(resume, Mapping):
        from_json = resume.get("template")
        if isinstance(from_json, str) and from_json:
            return from_json
    return DEFAULT_TEMPLATE


def describe(infos: Sequence[TemplateInfo]) -> str:
    """Human-readable listing, one template per line."""
    if not infos:
        return "no templates found"
    width = max(len(i.name) for i in infos)
    lines = []
    for info in infos:
        suffix = f" [{info.source}]" if info.source != "builtin" else ""
        lines.append(f"  {info.name.ljust(width)}  {info.description}{suffix}".rstrip())
    return "\n".join(lines)
