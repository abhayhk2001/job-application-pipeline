"""``python -m resume_builder`` -- the CLI without the console scripts.

    python -m resume_builder render -i resume.json -o out.pdf   # == resume-render
    python -m resume_builder build  -i resume.json              # == resume-builder

Without a leading subcommand the render CLI runs, so the module invocation is
a drop-in for ``resume-render``. The package has to be importable, which an
editable install (``pip install -e .``) makes true from any directory.
"""

from __future__ import annotations

import sys

from .cli import main as render_main
from .cli import main_builder as build_main

__all__ = ["main", "COMMANDS"]

COMMANDS = {"render": render_main, "build": build_main}


def main(argv: list[str] | None = None) -> int:
    """Dispatch to a command, defaulting to ``render``."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in COMMANDS:
        command, rest = args[0], args[1:]
    else:
        command, rest = "render", args
    return COMMANDS[command](rest)


if __name__ == "__main__":
    sys.exit(main())
