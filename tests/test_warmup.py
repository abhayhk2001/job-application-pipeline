"""``api.warmup``: prime Tectonic's package cache with a tiny resume per template."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from resume_builder import TEMPLATES_DIR, templates_registry
from resume_builder.api import _WARMUP_RESUME, warmup
from resume_builder.exceptions import CompileTimeoutError
from resume_builder.validation import validate


def test_the_warmup_resume_is_schema_valid():
    assert validate(_WARMUP_RESUME) == []


def test_warmup_resume_exercises_every_section_type_and_bold():
    types = {section["type"] for section in _WARMUP_RESUME["sections"]}
    assert types == {"education", "experience", "projects", "skills", "achievements"}
    assert "**" in str(_WARMUP_RESUME)


def test_warmup_compiles_each_builtin_template_once(fake_tectonic):
    assert warmup() == ["classic", "serif"]
    assert len(fake_tectonic.calls()) == 2


def test_warmup_covers_whatever_templates_ship_with_the_package(fake_tectonic):
    shipped = [i.name for i in templates_registry.list_templates(TEMPLATES_DIR)]
    assert warmup() == shipped


def test_warmup_leaves_nothing_behind(fake_tectonic, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    monkeypatch.setattr(tempfile, "tempdir", None)  # re-read TMPDIR

    warmup()

    assert list((tmp_path / "tmp").iterdir()) == []


def test_warmup_timeout_applies_to_the_compile(fake_tectonic):
    fake_tectonic.mode("hang")
    with pytest.raises(CompileTimeoutError):
        warmup(timeout_seconds=0.5)
    assert fake_tectonic.child_is_gone()


def test_a_project_template_cannot_stand_in_for_a_builtin(
    fake_tectonic, tmp_path: Path, monkeypatch
):
    """Warming a broken same-named override would prime nothing."""
    project = tmp_path / "templates"
    (project / "classic").mkdir(parents=True)
    (project / "classic" / "resume.tex.j2").write_text("{{ no_such_function() }}")
    monkeypatch.setattr(templates_registry, "PROJECT_TEMPLATES_DIR", project)

    assert warmup() == ["classic", "serif"]


def test_warmup_with_real_tectonic(require_tectonic):
    assert warmup() == ["classic", "serif"]
