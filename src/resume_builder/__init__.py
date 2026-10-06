"""Job-application pipeline.

Layout:
    data/            the career data lake and its open-questions worksheet
    docs/            the schema contract and its rationale
    tests/fixtures/  a captured resume in render-ready form, plus the PDF it came from
    schemas/         JSON Schema for the render-ready resume shape
    src/resume_builder/
        validation.py    render-ready JSON -> list[Problem]
        renderer.py      JSON -> TeX
        pdf_compiler.py  TeX -> PDF via tectonic
        cli.py           resume-render entry point
        templates_registry.py  which template a render uses
        templates/       one directory per template, plus _shared/ partials
    templates/       your own templates; shadow the built-ins by name

This module resolves paths only. Loading, rendering and TeX compilation live in
sibling modules.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
TEMPLATES_DIR = PACKAGE_ROOT / "templates"
SHARED_TEMPLATES_DIR = TEMPLATES_DIR / "_shared"
PROJECT_TEMPLATES_DIR = PROJECT_ROOT / "templates"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"

MASTER_RESUME = DATA_DIR / "master_resume.json"
NEEDS_INPUT = DATA_DIR / "NEEDS_INPUT.md"
TEST_RESUME = FIXTURES_DIR / "test_resume.json"
REFERENCE_PDF = FIXTURES_DIR / "resume.pdf"
GOLDEN_TEX = PROJECT_ROOT / "tests" / "golden" / "resume.tex"
RENDERED_SCHEMA = SCHEMAS_DIR / "rendered_resume.schema.json"

__all__ = [
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
    "DATA_DIR",
    "DOCS_DIR",
    "FIXTURES_DIR",
    "TEMPLATES_DIR",
    "SHARED_TEMPLATES_DIR",
    "PROJECT_TEMPLATES_DIR",
    "SCHEMAS_DIR",
    "MASTER_RESUME",
    "NEEDS_INPUT",
    "TEST_RESUME",
    "REFERENCE_PDF",
    "GOLDEN_TEX",
    "RENDERED_SCHEMA",
]
