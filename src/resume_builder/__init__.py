"""Renderer for render-ready resume JSON.

Layout:
    data/            the authoritative career record
    docs/            the schema contract and its rationale
    tests/fixtures/  a captured resume in render-ready form, plus the PDF it came from
    schemas/         JSON Schema for the render-ready resume shape
    src/resume_builder/
        api.py           build_resume (validate, render, compile) and warmup
        validation.py    render-ready JSON -> list[Problem]
        renderer.py      JSON -> TeX
        jinja_env.py     the Jinja environment and its filters
        url_filters.py   LaTeX escaping and Markdown-ish rich text
        pdf_compiler.py  TeX -> PDF via tectonic
        cli.py           resume-render and resume-builder entry points
        exceptions.py    the errors callers can catch
        templates_registry.py  which template a render uses
        templates/       one directory per template, plus _shared/ partials
    templates/       optional, not shipped: your own templates; shadow the built-ins by name

This module resolves paths only. Loading, rendering and TeX compilation live in
sibling modules.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DATA_DIR = PROJECT_ROOT / "data"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
TEMPLATES_DIR = PACKAGE_ROOT / "templates"
SHARED_TEMPLATES_DIR = TEMPLATES_DIR / "_shared"
PROJECT_TEMPLATES_DIR = PROJECT_ROOT / "templates"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"

MASTER_RESUME = DATA_DIR / "master_resume.json"
TEST_RESUME = FIXTURES_DIR / "test_resume.json"
REFERENCE_PDF = FIXTURES_DIR / "resume.pdf"
GOLDEN_TEX = PROJECT_ROOT / "tests" / "golden" / "resume.tex"
RENDERED_SCHEMA = SCHEMAS_DIR / "rendered_resume.schema.json"

__all__ = [
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
    "DATA_DIR",
    "FIXTURES_DIR",
    "TEMPLATES_DIR",
    "SHARED_TEMPLATES_DIR",
    "PROJECT_TEMPLATES_DIR",
    "SCHEMAS_DIR",
    "MASTER_RESUME",
    "TEST_RESUME",
    "REFERENCE_PDF",
    "GOLDEN_TEX",
    "RENDERED_SCHEMA",
]
