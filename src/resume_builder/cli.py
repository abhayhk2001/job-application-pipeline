"""Command-line entry points: ``resume-render`` and ``resume-builder``.

Exit codes are the feedback signal for an automated caller:

====  ==========================================================
0     success
1     render or Tectonic compilation failed (including a compile timeout)
2     bad invocation: file missing, not parseable as JSON, or an
      unknown --template (stderr then names the valid ones)
3     the resume JSON is invalid (one line per problem on stderr)
====  ==========================================================

Two commands share that contract:

``resume-render``
    The general one. It renders to whatever ``--out`` says -- a ``.tex``
    suffix stops at the TeX source, anything else goes on to Tectonic --
    or validates and writes nothing with ``--validate-only``. ``--warmup``
    compiles a tiny resume with every built-in template so Tectonic fetches
    its TeX packages up front.

``resume-builder``
    The one-shot one. It takes an input and nothing else, and writes the
    PDF next to the input under the input's own name: ``r.json`` becomes
    ``r.pdf`` in the same directory. The intermediate ``.tex`` and the
    LaTeX log go to a temporary directory that is removed afterwards, so
    the PDF is the only file left behind.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from . import templates_registry
from .api import WARMUP_TIMEOUT_SECONDS, BuildResult, build_resume, warmup
from .exceptions import TemplateNotFound, ValidationError
from .pdf_compiler import DEFAULT_COMPILE_TIMEOUT_SECONDS
from .validation import validate

__all__ = [
    "main",
    "main_builder",
    "build_parser",
    "build_builder_parser",
]

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BAD_INPUT = 2
EXIT_INVALID = 3


class _InputError(Exception):
    """Something is wrong with the caller's input file: exit code 2."""


def _positive_seconds(value: str) -> float:
    """argparse type for ``--compile-timeout``; a bad value is a usage error (exit 2)."""
    try:
        seconds = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {value!r}") from None
    if not seconds > 0 or seconds == float("inf"):
        raise argparse.ArgumentTypeError(f"must be a positive number of seconds, got {value!r}")
    return seconds


def _add_compile_timeout(parser: argparse.ArgumentParser, *, extra: str = "") -> None:
    parser.add_argument(
        "--compile-timeout",
        type=_positive_seconds,
        default=None,
        metavar="SECONDS",
        help="Kill Tectonic and fail if one compile runs longer than this "
        f"(default: {DEFAULT_COMPILE_TIMEOUT_SECONDS}). The first run on a machine "
        "downloads TeX packages and may need more; see --warmup." + extra,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-render",
        description="Render a render-ready resume JSON to TeX/PDF via Jinja2 + Tectonic.",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Path to the render-ready resume JSON file. "
        "Required unless --list-templates is given.",
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        help="Output path. A .tex suffix produces only the TeX source; any other "
        "suffix (typically .pdf) triggers Tectonic compilation. "
        "Not required with --validate-only.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Where intermediate files live (default: a sibling of --out).",
    )
    parser.add_argument(
        "--template",
        "-t",
        help="Name of the template to render with. Overrides the resume JSON's "
        "own 'template' key. See --list-templates.",
    )
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=None,
        help="An extra directory of templates, searched before the project's "
        "templates/ and the built-in ones.",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List the available templates and exit. Writes nothing; needs no --input.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Check the JSON against schemas/rendered_resume.schema.json and exit. "
        "Writes nothing.",
    )
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="Compile a tiny resume with every built-in template so Tectonic downloads "
        "its TeX packages now, then exit. Writes nothing; needs no --input. With "
        f"--compile-timeout, that limit applies to each compile (default: "
        f"{WARMUP_TIMEOUT_SECONDS}).",
    )
    _add_compile_timeout(parser)
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable lines.",
    )
    return parser


def build_builder_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-builder",
        description="Render a render-ready resume JSON to a PDF beside it: the "
        "output is <input dir>/<input name>.pdf. The input is the only thing "
        "you have to give.",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to the render-ready resume JSON file. The PDF is written "
        "next to it, under the same name with a .pdf suffix.",
    )
    parser.add_argument(
        "--template",
        "-t",
        help="Name of the template to render with. Overrides the resume JSON's "
        "own 'template' key. See 'resume-render --list-templates'.",
    )
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=None,
        help="An extra directory of templates, searched before the project's "
        "templates/ and the built-in ones.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Where the intermediate .tex and the LaTeX log live. Default: a "
        "temporary directory, removed afterwards, leaving only the PDF.",
    )
    _add_compile_timeout(parser)
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable lines.",
    )
    return parser


def _report(problems, as_json: bool) -> None:
    if as_json:
        payload = {
            "ok": False,
            "problems": [{"path": p.path, "message": p.message} for p in problems],
        }
        print(json.dumps(payload, indent=2))
        return
    print(f"{len(problems)} validation problem(s):", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)


def _list_templates(templates_dir, as_json: bool) -> int:
    """Print the template menu. This is the list an agent chooses a name from."""
    infos = templates_registry.list_templates(templates_dir)
    if as_json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "default": templates_registry.DEFAULT_TEMPLATE,
                    "templates": [i.as_dict() for i in infos],
                },
                indent=2,
            )
        )
    else:
        print(templates_registry.describe(infos))
        print(f"\ndefault: {templates_registry.DEFAULT_TEMPLATE}")
    return EXIT_OK


def _read_input(path: Path) -> Path:
    """Normalise the input path and check that it is a readable file."""
    resolved = Path(os.path.abspath(path.expanduser()))
    if not resolved.exists():
        raise _InputError(f"input file not found: {path}")
    if not resolved.is_file():
        raise _InputError(f"input is not a file: {path}")
    return resolved


def _load_resume(path: Path) -> dict:
    """Read and parse the resume JSON."""
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise _InputError(f"input is not valid JSON: {e}") from e


def _output_path(input_path: Path) -> Path:
    """The PDF path for an input: same directory, same name, .pdf suffix.

    ``r.json`` -> ``r.pdf`` beside it; ``my.resume.json`` -> ``my.resume.pdf``.
    """
    out = input_path.with_suffix(".pdf")
    if out == input_path:
        raise _InputError(f"input and output would be the same file: {input_path}")
    return out


def _build(
    resume,
    workdir: Path,
    *,
    tex_only: bool,
    template: str | None,
    templates_dir: Path | None,
    as_json: bool,
    compile_timeout: float | None = None,
    stem: str = "resume",
) -> tuple[BuildResult | None, int]:
    """Run the build, mapping every failure onto the exit-code contract."""
    try:
        result = build_resume(
            resume,
            workdir,
            tex_only=tex_only,
            stem=stem,
            template=template,
            templates_dir=templates_dir,
            compile_timeout_seconds=(
                DEFAULT_COMPILE_TIMEOUT_SECONDS if compile_timeout is None else compile_timeout
            ),
        )
    except ValidationError as e:
        _report(e.problems, as_json)
        return None, EXIT_INVALID
    except TemplateNotFound as e:
        print(f"error: {e}", file=sys.stderr)
        return None, EXIT_BAD_INPUT
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return None, EXIT_FAILED
    return result, EXIT_OK


def _warmup(compile_timeout: float | None, as_json: bool) -> int:
    """Run ``--warmup``: compile a tiny resume per built-in template."""
    timeout = WARMUP_TIMEOUT_SECONDS if compile_timeout is None else compile_timeout
    try:
        names = warmup(timeout_seconds=timeout)
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return EXIT_FAILED
    if as_json:
        print(json.dumps({"ok": True, "warmed": names}, indent=2))
    else:
        print(f"tectonic is warm (templates: {', '.join(names)})")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_templates:
        return _list_templates(args.templates_dir, args.as_json)

    if args.warmup:
        return _warmup(args.compile_timeout, args.as_json)

    if args.input is None:
        parser.error("--input is required unless --list-templates or --warmup is given")

    try:
        resume = _load_resume(_read_input(args.input))
    except _InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_BAD_INPUT

    if args.validate_only:
        problems = validate(resume)
        if problems:
            _report(problems, args.as_json)
            return EXIT_INVALID
        print(json.dumps({"ok": True, "problems": []}, indent=2) if args.as_json else "ok")
        return EXIT_OK

    if args.out is None:
        parser.error("--out is required unless --validate-only is given")

    out: Path = args.out
    tex_only = out.suffix == ".tex"
    workdir = args.workdir or out.parent

    result, code = _build(
        resume,
        workdir,
        tex_only=tex_only,
        template=args.template,
        templates_dir=args.templates_dir,
        as_json=args.as_json,
        compile_timeout=args.compile_timeout,
    )
    if result is None:
        return code

    produced = result.tex_path if tex_only else result.pdf_path
    if produced is not None and produced != out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(produced.read_bytes())

    if args.as_json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "tex_path": str(result.tex_path),
                    "pdf_path": str(result.pdf_path) if result.pdf_path else None,
                    "out": str(out),
                    "template": result.template,
                    "warnings": list(result.warnings),
                },
                indent=2,
            )
        )
    else:
        print(f"wrote {out} (template: {result.template})")
    return EXIT_OK


def main_builder(argv: list[str] | None = None) -> int:
    """``resume-builder``: the input is all you give, the PDF lands beside it."""
    parser = build_builder_parser()
    args = parser.parse_args(argv)

    try:
        input_path = _read_input(args.input)
        resume = _load_resume(input_path)
        out = _output_path(input_path)
    except _InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_BAD_INPUT

    # The .tex and the LaTeX log are build noise: they go to a temporary
    # directory unless the caller asks for them explicitly, so the input's
    # directory ends up holding the PDF and nothing else.
    with tempfile.TemporaryDirectory(prefix="resume-builder-") as tmp:
        workdir = args.workdir or Path(tmp)
        result, code = _build(
            resume,
            workdir,
            tex_only=False,
            template=args.template,
            templates_dir=args.templates_dir,
            as_json=args.as_json,
            compile_timeout=args.compile_timeout,
            stem=input_path.stem,
        )
        if result is None:
            return code
        pdf = result.pdf_path
        if pdf is None:
            print("error: no PDF was produced", file=sys.stderr)
            return EXIT_FAILED
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf.read_bytes())

    if args.as_json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "pdf_path": str(out),
                    "out": str(out),
                    "template": result.template,
                    "warnings": list(result.warnings),
                },
                indent=2,
            )
        )
    else:
        print(f"wrote {out} (template: {result.template})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
