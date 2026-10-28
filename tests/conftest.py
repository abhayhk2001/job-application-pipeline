"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import json
import os
import shutil
import time
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


# A stand-in for the tectonic binary. It is a /bin/sh script because the
# checkout's path may contain spaces, which a custom interpreter in a shebang
# cannot survive. It records every invocation and then behaves as FAKE_TECTONIC_MODE
# says, so timeout, failure and cleanup paths run without a real LaTeX engine.
_FAKE_TECTONIC = """#!/bin/sh
echo "$*" >> "$FAKE_TECTONIC_LOG"
outdir=.
tex=
while [ $# -gt 0 ]; do
  case "$1" in
    --outdir) outdir=$2; shift 2 ;;
    --*) shift ;;
    *) tex=$1; shift ;;
  esac
done
case "$FAKE_TECTONIC_MODE" in
  ok) stem=$(basename "$tex" .tex); printf '%%PDF-1.4\\n' > "$outdir/$stem.pdf" ;;
  fail) echo "boom on stdout"; echo "boom on stderr" >&2; exit 3 ;;
  no-pdf) exit 0 ;;
  hang) sleep 60 & echo $! > "$FAKE_TECTONIC_CHILD_PID"; echo started; wait ;;
esac
"""


class FakeTectonic:
    """Handle on the scripted ``tectonic`` that ``fake_tectonic`` puts on PATH."""

    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.log = root / "calls.log"
        self.child_pid_file = root / "child.pid"
        self._monkeypatch = monkeypatch
        self.mode("ok")

    def mode(self, mode: str) -> None:
        """One of ``ok``, ``fail``, ``no-pdf``, ``hang``."""
        self._monkeypatch.setenv("FAKE_TECTONIC_MODE", mode)

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [line.split() for line in self.log.read_text().splitlines()]

    def child_pid(self) -> int:
        return int(self.child_pid_file.read_text())

    def child_is_gone(self, within: float = 5.0) -> bool:
        """Whether the process ``hang`` mode started has died (it is reparented, so poll)."""
        pid = self.child_pid()
        deadline = time.monotonic() + within
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.05)
        return False


@pytest.fixture
def fake_tectonic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeTectonic:
    """Put a scripted ``tectonic`` first on PATH; default mode is ``ok``."""
    root = tmp_path / "fake-tectonic"
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True)
    script = bin_dir / "tectonic"
    script.write_text(_FAKE_TECTONIC)
    script.chmod(0o755)
    fake = FakeTectonic(root, monkeypatch)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_TECTONIC_LOG", str(fake.log))
    monkeypatch.setenv("FAKE_TECTONIC_CHILD_PID", str(fake.child_pid_file))
    return fake
