"""Tests for ``compile_pdf`` and ``build_resume``'s compile plumbing.

Most of these run against ``fake_tectonic`` -- a scripted stand-in for the
binary -- so timeouts, failures and process cleanup are exercised without a
LaTeX engine. The ``--keep-logs`` regression also runs once against real
Tectonic when it is installed.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

import resume_builder.api as api
from resume_builder.api import build_resume
from resume_builder.exceptions import (
    CompileError,
    CompileTimeoutError,
    TectonicNotFound,
    ValidationError,
)
from resume_builder.pdf_compiler import (
    DEFAULT_COMPILE_TIMEOUT_SECONDS,
    check_timeout,
    compile_pdf,
)


@pytest.fixture
def tex(tmp_path: Path) -> Path:
    path = tmp_path / "src" / "doc.tex"
    path.parent.mkdir()
    path.write_text("\\documentclass{article}\\begin{document}hi\\end{document}\n")
    return path


class TestCompilePdf:
    def test_success_returns_the_pdf(self, tex: Path, tmp_path: Path, fake_tectonic):
        out = tmp_path / "out"
        pdf = compile_pdf(tex, out)
        assert pdf == (out / "doc.pdf").resolve()
        assert pdf.read_bytes().startswith(b"%PDF")

    def test_default_timeout_is_sixty_seconds(self):
        assert DEFAULT_COMPILE_TIMEOUT_SECONDS == 60

    def test_nonzero_exit_is_a_compile_error_not_a_timeout(
        self, tex: Path, tmp_path: Path, fake_tectonic
    ):
        fake_tectonic.mode("fail")
        with pytest.raises(CompileError) as caught:
            compile_pdf(tex, tmp_path / "out")
        assert not isinstance(caught.value, CompileTimeoutError)
        message = str(caught.value)
        assert "exit 3" in message
        assert "boom on stdout" in message and "boom on stderr" in message

    def test_success_without_a_pdf_is_a_compile_error(
        self, tex: Path, tmp_path: Path, fake_tectonic
    ):
        fake_tectonic.mode("no-pdf")
        with pytest.raises(CompileError, match="was not produced") as caught:
            compile_pdf(tex, tmp_path / "out")
        assert not isinstance(caught.value, CompileTimeoutError)

    def test_missing_engine_is_tectonic_not_found(
        self, tex: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        empty = tmp_path / "empty-bin"
        empty.mkdir()
        monkeypatch.setenv("PATH", str(empty))
        with pytest.raises(TectonicNotFound):
            compile_pdf(tex, tmp_path / "out")


class TestTimeout:
    def test_hung_compile_raises_compile_timeout_error(
        self, tex: Path, tmp_path: Path, fake_tectonic
    ):
        fake_tectonic.mode("hang")
        started = time.monotonic()
        with pytest.raises(CompileTimeoutError) as caught:
            compile_pdf(tex, tmp_path / "out", timeout_seconds=0.5)

        assert time.monotonic() - started < 10
        error = caught.value
        assert isinstance(error, CompileError)
        assert error.timeout_seconds == 0.5
        assert "timed out after 0.5s" in str(error)
        assert "--warmup" in str(error)
        assert "started" in str(error)  # what the compiler printed before it was killed

    def test_timeout_kills_the_compilers_children_too(
        self, tex: Path, tmp_path: Path, fake_tectonic
    ):
        fake_tectonic.mode("hang")
        with pytest.raises(CompileTimeoutError):
            compile_pdf(tex, tmp_path / "out", timeout_seconds=0.5)
        assert fake_tectonic.child_is_gone()

    def test_a_timed_out_compile_leaves_no_pdf(self, tex: Path, tmp_path: Path, fake_tectonic):
        fake_tectonic.mode("hang")
        out = tmp_path / "out"
        with pytest.raises(CompileTimeoutError):
            compile_pdf(tex, out, timeout_seconds=0.5)
        assert not list(out.glob("*.pdf"))

    def test_a_fast_compile_is_not_cut_short(self, tex: Path, tmp_path: Path, fake_tectonic):
        assert compile_pdf(tex, tmp_path / "out", timeout_seconds=30).exists()

    @pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf"), "60", None, True])
    def test_invalid_timeouts_are_rejected_before_any_work(
        self, tex: Path, tmp_path: Path, fake_tectonic, bad
    ):
        with pytest.raises(ValueError, match="timeout_seconds"):
            compile_pdf(tex, tmp_path / "out", timeout_seconds=bad)
        assert fake_tectonic.calls() == []
        assert not (tmp_path / "out").exists()

    def test_timeout_is_keyword_only(self, tex: Path, tmp_path: Path, fake_tectonic):
        with pytest.raises(TypeError):
            compile_pdf(tex, tmp_path / "out", False, 5)  # type: ignore[misc]

    def test_check_timeout_accepts_ints_and_floats(self):
        check_timeout(1)
        check_timeout(0.25)


class TestKeepLogs:
    """Regression: the condition was inverted, so logs were kept only by default."""

    def test_logs_are_not_requested_by_default(self, tex: Path, tmp_path: Path, fake_tectonic):
        compile_pdf(tex, tmp_path / "out")
        assert "--keep-logs" not in fake_tectonic.calls()[0]

    def test_logs_are_requested_when_asked_for(self, tex: Path, tmp_path: Path, fake_tectonic):
        compile_pdf(tex, tmp_path / "out", keep_logs=True)
        assert "--keep-logs" in fake_tectonic.calls()[0]

    def test_real_tectonic_leaves_a_log_only_when_asked(
        self, tex: Path, tmp_path: Path, require_tectonic
    ):
        compile_pdf(tex, tmp_path / "quiet")
        assert not list((tmp_path / "quiet").glob("*.log"))

        compile_pdf(tex, tmp_path / "logged", keep_logs=True)
        assert (tmp_path / "logged" / "doc.log").exists()


class TestBuildResume:
    def test_default_timeout_is_forwarded(self, fixture_resume, tmp_path, monkeypatch):
        seen = {}

        def fake_compile(tex_path, out_dir, **kwargs):
            seen.update(kwargs)
            return Path(out_dir) / "resume.pdf"

        monkeypatch.setattr(api, "compile_pdf", fake_compile)
        build_resume(fixture_resume, tmp_path)
        assert seen == {"timeout_seconds": 60}

    def test_custom_timeout_is_forwarded(self, fixture_resume, tmp_path, monkeypatch):
        seen = {}

        def fake_compile(tex_path, out_dir, **kwargs):
            seen.update(kwargs)
            return Path(out_dir) / "resume.pdf"

        monkeypatch.setattr(api, "compile_pdf", fake_compile)
        build_resume(fixture_resume, tmp_path, compile_timeout_seconds=7.5)
        assert seen == {"timeout_seconds": 7.5}

    def test_timeout_is_keyword_only(self, fixture_resume, tmp_path):
        with pytest.raises(TypeError):
            build_resume(fixture_resume, tmp_path, False, "resume", None, None, 5)  # type: ignore[misc]

    def test_hung_compile_surfaces_as_compile_timeout_and_keeps_the_tex(
        self, fixture_resume, tmp_path, fake_tectonic
    ):
        fake_tectonic.mode("hang")
        with pytest.raises(CompileTimeoutError):
            build_resume(fixture_resume, tmp_path, compile_timeout_seconds=0.5)
        assert (tmp_path / "resume.tex").exists()
        assert not (tmp_path / "resume.pdf").exists()
        assert fake_tectonic.child_is_gone()

    def test_invalid_timeout_fails_before_anything_is_written(
        self, fixture_resume, tmp_path, fake_tectonic
    ):
        out = tmp_path / "out"
        with pytest.raises(ValueError, match="timeout_seconds"):
            build_resume(fixture_resume, out, compile_timeout_seconds=0)
        assert not out.exists()
        assert fake_tectonic.calls() == []

    def test_tex_only_ignores_the_timeout_and_needs_no_engine(
        self, fixture_resume, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("PATH", str(tmp_path))  # no tectonic anywhere
        result = build_resume(fixture_resume, tmp_path, tex_only=True, compile_timeout_seconds=-1)
        assert result.pdf_path is None
        assert result.tex_path.exists()

    def test_existing_call_shape_still_works(self, fixture_resume, tmp_path, fake_tectonic):
        result = build_resume(fixture_resume, tmp_path, stem="r", template="serif")
        assert result.pdf_path == (tmp_path / "r.pdf").resolve()
        assert result.template == "serif"

    def test_validation_still_comes_first(self, tmp_path, fake_tectonic):
        with pytest.raises(ValidationError):
            build_resume({"sections": []}, tmp_path, compile_timeout_seconds=0)
        assert fake_tectonic.calls() == []
