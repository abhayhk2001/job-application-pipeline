"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from resume_builder import TEST_RESUME
from resume_builder.pdf_compiler import is_tectonic_available


@pytest.fixture(scope="session")
def fixture_resume() -> dict:
    """The render-ready fixture JSON loaded as a dict."""
    return json.loads(TEST_RESUME.read_text())


@pytest.fixture(scope="session")
def reference_pdf() -> Path:
    """Path to the reference PDF shipped with the test fixtures."""
    from resume_builder import REFERENCE_PDF

    return REFERENCE_PDF


@pytest.fixture
def require_tectonic() -> None:
    """Skip the test if tectonic is not on PATH."""
    if not is_tectonic_available():
        pytest.skip("tectonic is not installed; install with `brew install tectonic`")


@pytest.fixture
def cleanup_build() -> None:
    """Ensure the build directory is removed before/after tests that use it."""
    build = Path.cwd() / "build"
    if build.exists():
        shutil.rmtree(build)
    yield
    if build.exists():
        shutil.rmtree(build)
