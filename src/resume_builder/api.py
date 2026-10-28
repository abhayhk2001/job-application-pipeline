"""The one function that knows how to turn resume JSON into artefacts.

Everything else is a shell over this: the CLI today, and -- if the service in
``README.md`` gets built -- a REST route or an MCP tool tomorrow. Nothing here
imports a web framework, and nothing here decides where the artefacts should
ultimately live; callers at the edge do that.
"""

from __future__ import annotations

import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from . import TEMPLATES_DIR, templates_registry
from .exceptions import ValidationError
from .pdf_compiler import DEFAULT_COMPILE_TIMEOUT_SECONDS, check_timeout, compile_pdf
from .renderer import render_to_file
from .validation import Problem, validate

__all__ = ["BuildResult", "WARMUP_TIMEOUT_SECONDS", "build_resume", "warmup"]

#: The per-compile limit ``warmup`` uses. Longer than a normal build's, because
#: this is the run that downloads Tectonic's TeX packages.
WARMUP_TIMEOUT_SECONDS = 300


@dataclass(frozen=True)
class BuildResult:
    """What a build produced.

    ``pdf_path`` is ``None`` for a TeX-only build. When object storage is
    added, the edge adapter maps ``pdf_path`` to a URL; the renderer stays
    unaware of it.

    ``template`` is the name actually used, after the resume's own ``template``
    key and any override have been reconciled -- worth reporting back, because
    a caller that set neither has no other way to know.
    """

    tex_path: Path
    pdf_path: Path | None
    template: str = ""
    warnings: tuple[str, ...] = ()


def build_resume(
    resume: Mapping,
    out_dir: Path,
    *,
    tex_only: bool = False,
    stem: str = "resume",
    template: str | None = None,
    templates_dir: Path | str | None = None,
    compile_timeout_seconds: float = DEFAULT_COMPILE_TIMEOUT_SECONDS,
) -> BuildResult:
    """Validate ``resume``, render it, and compile it unless ``tex_only``.

    Raises ``ValidationError`` with every problem if the JSON is malformed,
    ``TemplateNotFound`` if no template answers to the requested name,
    ``TectonicNotFound`` if the engine is missing, ``CompileTimeoutError`` if
    Tectonic outlasts ``compile_timeout_seconds``, ``CompileError`` if LaTeX
    fails. ``tex_only=True`` needs no Tectonic at all, which is what makes a
    deployment degradable; it also ignores the timeout.

    ``template`` overrides the resume's own ``template`` key; omit both and the
    default is used. ``templates_dir`` prepends a directory to the template
    search path.
    """
    problems: list[Problem] = validate(resume)
    if problems:
        raise ValidationError(problems)

    name = templates_registry.choose(resume, template)
    # Resolve before writing anything: an unknown name should fail the build,
    # not leave a half-built directory behind.
    templates_registry.find(name, templates_dir)
    if not tex_only:
        check_timeout(compile_timeout_seconds)

    out_dir = Path(out_dir)
    tex_path = render_to_file(
        resume,
        out_dir / f"{stem}.tex",
        template=name,
        templates_dir=templates_dir,
        check=False,
    )
    if tex_only:
        return BuildResult(tex_path=tex_path, pdf_path=None, template=name)

    pdf_path = compile_pdf(tex_path, out_dir, timeout_seconds=compile_timeout_seconds)
    return BuildResult(tex_path=tex_path, pdf_path=pdf_path, template=name)


# A tiny but complete resume: one of every section type, plus a link and a bold
# span, so compiling it asks Tectonic for every package and font face the
# built-in templates use (bold, italic, underline, hyperref).
_WARMUP_RESUME = {
    "basics": {
        "name": "Warm Up",
        "contacts": [
            {"type": "email", "label": "warm@example.com", "url": "mailto:warm@example.com"},
            {"type": "phone", "label": "+1 555 0100", "url": None},
        ],
    },
    "sections": [
        {
            "type": "education",
            "heading": "Education",
            "entries": [
                {
                    "institution": "Example University",
                    "location": "Example City",
                    "qualification": "Bachelor of Science",
                    "date": "August 2019 - May 2023",
                }
            ],
        },
        {
            "type": "experience",
            "heading": "Work Experience",
            "entries": [
                {
                    "organization": "Example Corp",
                    "location": "Example City",
                    "title": "Engineer",
                    "dateRange": "January 2023 - July 2026",
                    "bullets": ["Built a **fast** thing with [a link](https://example.com/a_b)"],
                }
            ],
        },
        {
            "type": "projects",
            "heading": "Projects",
            "entries": [{"name": "Example Project", "bullets": ["Shipped it"]}],
        },
        {
            "type": "skills",
            "heading": "Skills",
            "groups": [{"label": "Languages", "items": ["Python", "C/C++"]}],
        },
        {
            "type": "achievements",
            "heading": "Publications",
            "items": ["A. **Author**, Title, 2024. [Paper](https://example.com/paper)"],
        },
    ],
}


def warmup(*, timeout_seconds: float = WARMUP_TIMEOUT_SECONDS) -> list[str]:
    """Compile a tiny resume with every built-in template; return their names.

    Tectonic downloads its TeX packages the first time it needs them, which can
    take longer than a normal build's timeout. Run this once on a new machine
    (``resume-render --warmup``) so a later timeout means a slow build, not a
    cold cache. ``timeout_seconds`` applies to each template's compile.

    Only the templates shipped with the package are warmed: ``templates_dir`` is
    pinned to them, so a project template that shadows a built-in name cannot
    stand in for it. Nothing is kept; the output lives in a temporary directory.
    """
    names = [info.name for info in templates_registry.list_templates(TEMPLATES_DIR)]
    with tempfile.TemporaryDirectory(prefix="resume-builder-warmup-") as tmp:
        for name in names:
            build_resume(
                _WARMUP_RESUME,
                Path(tmp) / name,
                template=name,
                templates_dir=TEMPLATES_DIR,
                compile_timeout_seconds=timeout_seconds,
            )
    return names
