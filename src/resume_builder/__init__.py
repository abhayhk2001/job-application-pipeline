"""Job-application pipeline.

Layout:
    data/            the career data lake and its open-questions worksheet
    docs/            the schema contract and its rationale
    tests/fixtures/  a captured resume in render-ready form, plus the PDF it came from

This module resolves paths only. Loading, tailoring and TeX rendering live in
sibling modules.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"

MASTER_RESUME = DATA_DIR / "master_resume.json"
NEEDS_INPUT = DATA_DIR / "NEEDS_INPUT.md"
TEST_RESUME = FIXTURES_DIR / "test_resume.json"
REFERENCE_PDF = FIXTURES_DIR / "resume.pdf"

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "DOCS_DIR",
    "FIXTURES_DIR",
    "MASTER_RESUME",
    "NEEDS_INPUT",
    "TEST_RESUME",
    "REFERENCE_PDF",
]
