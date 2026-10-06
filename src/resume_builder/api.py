"""The one function that knows how to turn resume JSON into artefacts.

Everything else is a shell over this: the CLI today, and -- if the service in
``README.md`` gets built -- a REST route or an MCP tool tomorrow. Nothing here
imports a web framework, and nothing here decides where the artefacts should
ultimately live; callers at the edge do that.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from . import templates_registry
from .exceptions import ValidationError
from .pdf_compiler import compile_pdf
from .renderer import render_to_file
from .validation import Problem, validate

__all__ = ["BuildResult", "build_resume"]


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
) -> BuildResult:
    """Validate ``resume``, render it, and compile it unless ``tex_only``.

    Raises ``ValidationError`` with every problem if the JSON is malformed,
    ``TemplateNotFound`` if no template answers to the requested name,
    ``TectonicNotFound`` if the engine is missing, ``CompileError`` if LaTeX
    fails. ``tex_only=True`` needs no Tectonic at all, which is what makes a
    deployment degradable.

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

    pdf_path = compile_pdf(tex_path, out_dir)
    return BuildResult(tex_path=tex_path, pdf_path=pdf_path, template=name)
