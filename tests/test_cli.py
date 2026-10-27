"""CLI tests: the exit-code contract, and where the files land.

``resume-render`` keeps its behaviour; ``resume-builder`` is the one-shot
command that writes the PDF beside the input and leaves nothing else there.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from resume_builder import TEST_RESUME
from resume_builder.cli import (
    EXIT_BAD_INPUT,
    EXIT_INVALID,
    EXIT_OK,
    _output_path,
    main,
    main_builder,
)


@pytest.fixture
def resume_copy(tmp_path: Path) -> Path:
    """The render-ready fixture, copied into a temp directory."""
    target = tmp_path / "resume.json"
    shutil.copy(TEST_RESUME, target)
    return target


@pytest.mark.parametrize(
    "name,expected",
    [
        ("resume.json", "resume.pdf"),
        ("my.resume.json", "my.resume.pdf"),
        ("resume", "resume.pdf"),
        ("2026-08-01_resume.json", "2026-08-01_resume.pdf"),
    ],
)
def test_output_path_keeps_the_directory_and_the_name(tmp_path: Path, name, expected):
    """The PDF is the input's name with a .pdf suffix, in the input's directory."""
    out = _output_path(tmp_path / name)
    assert out == tmp_path / expected
    assert out.parent == tmp_path


def test_builder_writes_only_the_pdf_next_to_the_input(
    resume_copy: Path, tmp_path: Path, require_tectonic
):
    """The .tex and the LaTeX log are build noise: they must not land here."""
    assert main_builder(["-i", str(resume_copy)]) == EXIT_OK

    pdf = tmp_path / "resume.pdf"
    assert pdf.exists()
    assert pdf.stat().st_size > 1000
    assert sorted(p.name for p in tmp_path.iterdir()) == ["resume.json", "resume.pdf"]


def test_builder_output_name_follows_the_input_name(
    resume_copy: Path, tmp_path: Path, require_tectonic
):
    renamed = tmp_path / "my.resume.json"
    shutil.move(str(resume_copy), renamed)

    assert main_builder(["-i", str(renamed)]) == EXIT_OK
    assert (tmp_path / "my.resume.pdf").exists()
    assert not (tmp_path / "my.resume.tex").exists()


def test_builder_json_output_names_the_pdf(
    resume_copy: Path, tmp_path: Path, require_tectonic, capsys
):
    assert main_builder(["-i", str(resume_copy), "--json"]) == EXIT_OK

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert Path(payload["pdf_path"]) == tmp_path / "resume.pdf"
    assert payload["out"] == str(tmp_path / "resume.pdf")
    assert payload["template"] == "classic"


def test_builder_missing_input_exits_2(tmp_path: Path, capsys):
    assert main_builder(["-i", str(tmp_path / "nope.json")]) == EXIT_BAD_INPUT
    assert "not found" in capsys.readouterr().err


def test_builder_unparseable_json_exits_2(tmp_path: Path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")

    assert main_builder(["-i", str(bad)]) == EXIT_BAD_INPUT
    assert "not valid JSON" in capsys.readouterr().err
    assert not (tmp_path / "bad.pdf").exists()


def test_builder_invalid_resume_exits_3(tmp_path: Path, capsys):
    """Parses as JSON, fails the schema: nothing is written."""
    bad = tmp_path / "invalid.json"
    bad.write_text(
        json.dumps({"basics": {"name": "X", "contacts": [{"label": "e"}]}, "sections": []})
    )

    assert main_builder(["-i", str(bad)]) == EXIT_INVALID
    assert "validation problem" in capsys.readouterr().err
    assert not (tmp_path / "invalid.pdf").exists()


def test_builder_unknown_template_exits_2(resume_copy: Path, capsys):
    assert main_builder(["-i", str(resume_copy), "-t", "nope"]) == EXIT_BAD_INPUT
    assert "nope" in capsys.readouterr().err


def test_builder_workdir_keeps_the_intermediates(
    resume_copy: Path, tmp_path: Path, require_tectonic
):
    """--workdir is the opt-out from the temp directory."""
    work = tmp_path / "work"
    work.mkdir()

    assert main_builder(["-i", str(resume_copy), "--workdir", str(work)]) == EXIT_OK
    assert (work / "resume.tex").exists()
    assert (work / "resume.pdf").exists()
    assert (tmp_path / "resume.pdf").exists()


def test_render_still_writes_to_out(resume_copy: Path, tmp_path: Path, require_tectonic):
    """The refactor must not have moved resume-render's output."""
    out = tmp_path / "out.pdf"
    assert main(["-i", str(resume_copy), "-o", str(out)]) == EXIT_OK
    assert out.exists()


def test_render_validate_only_still_reports_exit_3(tmp_path: Path, capsys):
    bad = tmp_path / "invalid.json"
    bad.write_text(
        json.dumps({"basics": {"name": "X", "contacts": [{"label": "e"}]}, "sections": []})
    )

    assert main(["-i", str(bad), "--validate-only"]) == EXIT_INVALID
    assert "validation problem" in capsys.readouterr().err


def test_module_dispatch_reaches_both_commands(resume_copy: Path, tmp_path: Path, require_tectonic):
    """``python -m resume_builder build`` is the same command as the script."""
    from resume_builder.__main__ import main as module_main

    assert module_main(["build", "-i", str(resume_copy)]) == EXIT_OK
    assert (tmp_path / "resume.pdf").exists()

    out = tmp_path / "rendered.pdf"
    assert module_main(["render", "-i", str(resume_copy), "-o", str(out)]) == EXIT_OK
    assert out.exists()
