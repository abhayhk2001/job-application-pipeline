"""Job-application pipeline.

Layout:
    data/            the career data lake and its open-questions worksheet
    docs/            the schema contract and its rationale
    tests/fixtures/  a captured resume in render-ready form, plus the PDF it came from
    src/resume_builder/
        renderer.py      JSON -> TeX
        pdf_compiler.py  TeX -> PDF via tectonic
        cli.py           resume-render entry point
        templates/       Jinja2 templates (heading, education, ...)

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

MASTER_RESUME = DATA_DIR / "master_resume.json"
NEEDS_INPUT = DATA_DIR / "NEEDS_INPUT.md"
TEST_RESUME = FIXTURES_DIR / "test_resume.json"
REFERENCE_PDF = FIXTURES_DIR / "resume.pdf"

__all__ = [
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
    "DATA_DIR",
    "DOCS_DIR",
    "FIXTURES_DIR",
    "TEMPLATES_DIR",
    "MASTER_RESUME",
    "NEEDS_INPUT",
    "TEST_RESUME",
    "REFERENCE_PDF",
]
