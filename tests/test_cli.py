"""CLI tests: the exit-code contract, and where the files land.

``resume-render`` keeps its behaviour; ``resume-builder`` is the one-shot
command that writes the PDF beside the input and leaves nothing else there.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import resume_builder.cli as cli
from resume_builder import TEST_RESUME
from resume_builder.api import BuildResult
from resume_builder.cli import (
    EXIT_BAD_INPUT,
    EXIT_FAILED,
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


# --------------------------------------------------------------------------- #
# --compile-timeout and --warmup
# --------------------------------------------------------------------------- #


@pytest.fixture
def seen_timeout(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replace the CLI's ``build_resume`` with one that records its timeout."""
    seen: dict = {}

    def fake_build(resume, workdir, **kwargs):
        seen.update(kwargs)
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        tex = workdir / f"{kwargs['stem']}.tex"
        pdf = workdir / f"{kwargs['stem']}.pdf"
        tex.write_text("x")
        pdf.write_bytes(b"%PDF-1.4\n")
        return BuildResult(tex_path=tex, pdf_path=pdf, template="classic")

    monkeypatch.setattr(cli, "build_resume", fake_build)
    return seen


def test_render_uses_the_default_timeout(resume_copy: Path, tmp_path: Path, seen_timeout):
    assert main(["-i", str(resume_copy), "-o", str(tmp_path / "o.pdf")]) == EXIT_OK
    assert seen_timeout["compile_timeout_seconds"] == 60


def test_render_forwards_compile_timeout(resume_copy: Path, tmp_path: Path, seen_timeout):
    argv = ["-i", str(resume_copy), "-o", str(tmp_path / "o.pdf"), "--compile-timeout", "7.5"]
    assert main(argv) == EXIT_OK
    assert seen_timeout["compile_timeout_seconds"] == 7.5


def test_builder_forwards_compile_timeout(resume_copy: Path, seen_timeout):
    assert main_builder(["-i", str(resume_copy), "--compile-timeout", "120"]) == EXIT_OK
    assert seen_timeout["compile_timeout_seconds"] == 120


@pytest.mark.parametrize("bad", ["0", "-5", "nan", "inf", "soon"])
@pytest.mark.parametrize("command", [main, main_builder])
def test_bad_compile_timeout_is_a_usage_error(resume_copy: Path, command, bad, capsys):
    with pytest.raises(SystemExit) as exit_info:
        command(["-i", str(resume_copy), "--compile-timeout", bad])
    assert exit_info.value.code == EXIT_BAD_INPUT
    assert "--compile-timeout" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["render", "builder"])
def test_a_compile_timeout_exits_1_and_says_so(
    command, resume_copy: Path, tmp_path: Path, fake_tectonic, capsys
):
    fake_tectonic.mode("hang")
    if command == "render":
        argv = ["-i", str(resume_copy), "-o", str(tmp_path / "o.pdf"), "--compile-timeout", "0.5"]
        code = main(argv)
    else:
        code = main_builder(["-i", str(resume_copy), "--compile-timeout", "0.5"])

    assert code == EXIT_FAILED
    err = capsys.readouterr().err
    assert "timed out after 0.5s" in err
    assert "--warmup" in err
    assert not (tmp_path / "o.pdf").exists()
    assert not (tmp_path / "resume.pdf").exists()
    assert fake_tectonic.child_is_gone()


def test_warmup_compiles_every_builtin_template_and_needs_no_input(
    tmp_path: Path, fake_tectonic, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)

    assert main(["--warmup"]) == EXIT_OK

    assert "classic" in capsys.readouterr().out
    assert len(fake_tectonic.calls()) == 2  # classic and serif
    assert sorted(p.name for p in tmp_path.iterdir() if p.name != "fake-tectonic") == []


def test_warmup_json(fake_tectonic, capsys):
    assert main(["--warmup", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out) == {"ok": True, "warmed": ["classic", "serif"]}


def test_warmup_uses_a_longer_default_timeout_and_honours_the_flag(monkeypatch):
    seen = []
    monkeypatch.setattr(
        cli, "warmup", lambda *, timeout_seconds: seen.append(timeout_seconds) or []
    )

    assert main(["--warmup"]) == EXIT_OK
    assert main(["--warmup", "--compile-timeout", "900"]) == EXIT_OK

    assert seen == [300, 900]


def test_warmup_timeout_exits_1(fake_tectonic, capsys):
    fake_tectonic.mode("hang")
    assert main(["--warmup", "--compile-timeout", "0.5"]) == EXIT_FAILED
    assert "timed out after 0.5s" in capsys.readouterr().err
    assert fake_tectonic.child_is_gone()


def test_warmup_without_tectonic_exits_1(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert main(["--warmup"]) == EXIT_FAILED
    assert "tectonic was not found" in capsys.readouterr().err


def test_input_is_still_required_without_warmup(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code == EXIT_BAD_INPUT
    assert "--warmup" in capsys.readouterr().err
