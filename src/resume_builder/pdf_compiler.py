"""Compile a rendered .tex file to PDF using Tectonic.

Tectonic is the modernised, self-contained TeX/LaTeX engine derived from
XeTeX. It auto-downloads required packages on first run, so we don't need a
locally maintained TeX Live install.
"""

from __future__ import annotations

import math
import os
import shutil
import signal
import subprocess
from pathlib import Path

from .exceptions import CompileError, CompileTimeoutError, TectonicNotFound

__all__ = [
    "DEFAULT_COMPILE_TIMEOUT_SECONDS",
    "check_timeout",
    "compile_pdf",
    "is_tectonic_available",
]

#: Enough for a warm cache. The first run on a machine downloads TeX packages
#: and can exceed it; see ``api.warmup``.
DEFAULT_COMPILE_TIMEOUT_SECONDS = 60

#: How long to wait for a killed process to hand over its output before giving
#: up on it. The kill is SIGKILL, so this only matters if something escaped the
#: process group while holding the pipes open.
_REAP_GRACE_SECONDS = 5


def is_tectonic_available() -> bool:
    return shutil.which("tectonic") is not None


def check_timeout(timeout_seconds: float) -> None:
    """Raise ``ValueError`` unless ``timeout_seconds`` is a positive, finite number."""
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise ValueError(f"timeout_seconds must be a positive number, got {timeout_seconds!r}")


def _kill_and_collect(proc: subprocess.Popen) -> tuple[str, str]:
    """SIGKILL ``proc`` and everything it started, reap it, return what it printed.

    ``proc`` leads its own session (see ``compile_pdf``), so signalling the
    process group also reaches any helper it spawned. Killing only the direct
    child would leave those running and holding our pipes open.
    """
    try:
        if hasattr(os, "killpg"):
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except ProcessLookupError:
        pass  # it exited on its own between the timeout and the kill
    try:
        stdout, stderr = proc.communicate(timeout=_REAP_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        proc.wait()
        return "", ""
    return stdout or "", stderr or ""


def compile_pdf(
    tex_path: Path,
    out_dir: Path,
    *,
    keep_logs: bool = False,
    timeout_seconds: float = DEFAULT_COMPILE_TIMEOUT_SECONDS,
) -> Path:
    """Compile ``tex_path`` to a PDF in ``out_dir`` using Tectonic.

    Returns the path to the produced PDF. Raises ``TectonicNotFound`` if the
    binary is missing, ``CompileTimeoutError`` if Tectonic runs longer than
    ``timeout_seconds`` (it and its children are killed first), and
    ``CompileError`` if it exits non-zero or produces no PDF. ``keep_logs``
    leaves Tectonic's ``.log`` file next to the PDF.
    """
    check_timeout(timeout_seconds)
    tex_path = Path(tex_path).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not is_tectonic_available():
        raise TectonicNotFound(
            "tectonic was not found on PATH. Install with `brew install tectonic`."
        )

    cmd = [
        "tectonic",
        "--outdir",
        str(out_dir),
        str(tex_path),
    ]
    if keep_logs:
        cmd.insert(1, "--keep-logs")

    # Own session, so a timeout can take the whole process group down.
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        stdout, stderr = _kill_and_collect(proc)
        raise CompileTimeoutError(
            f"tectonic timed out after {timeout_seconds:g}s for {tex_path}. The first run on a "
            "machine downloads TeX packages: run `resume-render --warmup` once, or raise the "
            "limit.\n"
            f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}",
            timeout_seconds=timeout_seconds,
        ) from None
    except BaseException:
        # Ctrl-C or similar: never leave a compiler running behind us.
        _kill_and_collect(proc)
        raise

    if proc.returncode != 0:
        raise CompileError(
            f"tectonic failed (exit {proc.returncode}) for {tex_path}\n"
            f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}"
        )

    pdf_path = out_dir / (tex_path.stem + ".pdf")
    if not pdf_path.exists():
        raise CompileError(
            f"tectonic reported success but {pdf_path} was not produced.\n"
            f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}"
        )
    return pdf_path
