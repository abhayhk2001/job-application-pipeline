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
    """

    tex_path: Path
    pdf_path: Path | None
    warnings: tuple[str, ...] = ()


def build_resume(
    resume: Mapping,
    out_dir: Path,
    *,
    tex_only: bool = False,
    stem: str = "resume",
) -> BuildResult:
    """Validate ``resume``, render it, and compile it unless ``tex_only``.

    Raises ``ValidationError`` with every problem if the JSON is malformed,
    ``TectonicNotFound`` if the engine is missing, ``CompileError`` if LaTeX
    fails. ``tex_only=True`` needs no Tectonic at all, which is what makes a
    deployment degradable.
    """
    problems: list[Problem] = validate(resume)
    if problems:
        raise ValidationError(problems)

    out_dir = Path(out_dir)
    tex_path = render_to_file(resume, out_dir / f"{stem}.tex", check=False)
    if tex_only:
        return BuildResult(tex_path=tex_path, pdf_path=None)

    pdf_path = compile_pdf(tex_path, out_dir)
    return BuildResult(tex_path=tex_path, pdf_path=pdf_path)
