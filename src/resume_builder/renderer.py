"""Render a render-ready resume JSON dict into a .tex file.

The renderer is the deterministic post-tailoring step: it consumes the
output-shape JSON (see ``tests/fixtures/test_resume.json``) and emits the
``.tex`` that Tectonic compiles to a PDF. It does not know about tailoring
or about ``data/master_resume.json``; those are upstream concerns.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from jinja2 import Environment

from . import TEMPLATES_DIR
from .exceptions import ValidationError
from .jinja_env import build_environment
from .validation import validate

__all__ = ["render", "render_to_file"]


HEADING_TEMPLATE = "heading.tex.j2"
SECTION_TEMPLATE_NAMES = {
    "education": "education.tex.j2",
    "experience": "experience.tex.j2",
    "projects": "projects.tex.j2",
    "skills": "skills.tex.j2",
    "achievements": "achievements.tex.j2",
}
MAIN_TEMPLATE = "resume.tex.j2"


def render(resume: Mapping, *, env: Environment | None = None, check: bool = True) -> str:
    """Return the rendered LaTeX source as a string.

    Validates against ``schemas/rendered_resume.schema.json`` first and raises
    ``ValidationError`` listing every problem, so malformed JSON can never
    produce TeX. Pass ``check=False`` only when the caller has already
    validated.
    """
    if check:
        problems = validate(resume)
        if problems:
            raise ValidationError(problems)
    env = env or build_environment(TEMPLATES_DIR)

    heading_tex = env.get_template(HEADING_TEMPLATE).render(basics=resume["basics"])

    sections_tex = []
    for section in resume["sections"]:
        section_type = section.get("type")
        template_name = SECTION_TEMPLATE_NAMES.get(section_type)
        if template_name is None:
            raise ValueError(f"unknown section type: {section_type!r}")
        sections_tex.append(env.get_template(template_name).render(section=section))

    return env.get_template(MAIN_TEMPLATE).render(
        basics=resume["basics"],
        heading_tex=heading_tex,
        sections_tex=sections_tex,
    )


def render_to_file(
    resume: Mapping, out_path: Path, *, env: Environment | None = None, check: bool = True
) -> Path:
    """Render ``resume`` to ``out_path`` and return ``out_path``."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(resume, env=env, check=check))
    return out_path
