"""Compile a rendered .tex file to PDF using Tectonic.

Tectonic is the modernised, self-contained TeX/LaTeX engine derived from
XeTeX. It auto-downloads required packages on first run, so we don't need a
locally maintained TeX Live install.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .exceptions import CompileError, TectonicNotFound

__all__ = ["compile_pdf", "is_tectonic_available"]


def is_tectonic_available() -> bool:
    return shutil.which("tectonic") is not None


def compile_pdf(tex_path: Path, out_dir: Path, *, keep_logs: bool = False) -> Path:
    """Compile ``tex_path`` to a PDF in ``out_dir`` using Tectonic.

    Returns the path to the produced PDF. Raises ``TectonicNotFound`` if the
    binary is missing, ``CompileError`` if Tectonic exits non-zero.
    """
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
    if not keep_logs:
        cmd.insert(1, "--keep-logs")

    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise CompileError(
            f"tectonic failed (exit {proc.returncode}) for {tex_path}\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )

    pdf_path = out_dir / (tex_path.stem + ".pdf")
    if not pdf_path.exists():
        raise CompileError(
            f"tectonic reported success but {pdf_path} was not produced.\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    return pdf_path
