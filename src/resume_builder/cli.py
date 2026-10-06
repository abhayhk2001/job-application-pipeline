"""Command-line entry point: ``resume-render``.

Exit codes are the feedback signal for an automated caller:

====  ==========================================================
0     success
1     render or Tectonic compilation failed
2     bad invocation: file missing, not parseable as JSON, or an
      unknown --template (stderr then names the valid ones)
3     the resume JSON is invalid (one line per problem on stderr)
====  ==========================================================
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import templates_registry
from .api import build_resume
from .exceptions import TemplateNotFound, ValidationError
from .validation import validate

__all__ = ["main", "build_parser"]

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BAD_INPUT = 2
EXIT_INVALID = 3


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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_templates:
        return _list_templates(args.templates_dir, args.as_json)

    if args.input is None:
        parser.error("--input is required unless --list-templates is given")

    if not args.input.exists():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return EXIT_BAD_INPUT

    try:
        resume = json.loads(args.input.read_text())
    except json.JSONDecodeError as e:
        print(f"error: input is not valid JSON: {e}", file=sys.stderr)
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

    try:
        result = build_resume(
            resume,
            workdir,
            tex_only=tex_only,
            template=args.template,
            templates_dir=args.templates_dir,
        )
    except ValidationError as e:
        _report(e.problems, args.as_json)
        return EXIT_INVALID
    except TemplateNotFound as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_BAD_INPUT
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return EXIT_FAILED

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


if __name__ == "__main__":
    sys.exit(main())
