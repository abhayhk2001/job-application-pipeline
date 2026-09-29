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
from .jinja_env import build_environment

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


def _validate(resume: Mapping) -> None:
    """Top-level shape check; per-section validation is delegated to templates."""
    if "basics" not in resume:
        raise ValueError("resume JSON is missing 'basics'")
    if "sections" not in resume:
        raise ValueError("resume JSON is missing 'sections'")
    if not isinstance(resume["basics"].get("name"), str):
        raise ValueError("resume.basics.name is required and must be a string")
    if not isinstance(resume["sections"], list):
        raise ValueError("resume.sections must be a list")


def render(resume: Mapping, *, env: Environment | None = None) -> str:
    """Return the rendered LaTeX source as a string."""
    _validate(resume)
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


def render_to_file(resume: Mapping, out_path: Path, *, env: Environment | None = None) -> Path:
    """Render ``resume`` to ``out_path`` and return ``out_path``."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(resume, env=env))
    return out_path
