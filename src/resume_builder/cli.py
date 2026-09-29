"""Command-line entry point: ``resume-render``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pdf_compiler import compile_pdf
from .renderer import render_to_file

__all__ = ["main", "build_parser"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-render",
        description="Render a render-ready resume JSON to TeX/PDF via Jinja2 + Tectonic.",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to the render-ready resume JSON file.",
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        required=True,
        help="Output path. A .tex suffix produces only the TeX source; "
        "any other suffix (typically .pdf) triggers Tectonic compilation.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Where intermediate files live (default: a sibling of --out).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        resume = json.loads(args.input.read_text())
    except json.JSONDecodeError as e:
        print(f"error: input is not valid JSON: {e}", file=sys.stderr)
        return 2

    out = args.out
    workdir = args.workdir or out.parent
    tex_path = out if out.suffix == ".tex" else workdir / "resume.tex"

    try:
        render_to_file(resume, tex_path)
    except Exception as e:  # noqa: BLE001
        print(f"error: rendering failed: {e}", file=sys.stderr)
        return 1

    if out.suffix == ".tex":
        print(f"wrote {tex_path}")
        return 0

    try:
        pdf_path = compile_pdf(tex_path, workdir)
    except Exception as e:  # noqa: BLE001
        print(f"error: compilation failed: {e}", file=sys.stderr)
        return 1

    if out != pdf_path:
        # User asked for an output path distinct from workdir/resume.pdf
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_path.read_bytes())

    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
