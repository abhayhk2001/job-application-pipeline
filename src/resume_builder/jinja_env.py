"""Jinja2 environment configured for resume rendering."""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .template_helpers import render_achievement_item
from .url_filters import latex_escape, linkify

__all__ = ["build_environment"]


def build_environment(templates_dir) -> Environment:
    """Return a Jinja2 Environment loading from ``templates_dir``.

    Uses ``StrictUndefined`` so a typo in a template variable name fails the
    render rather than silently emitting empty text. Autoescape is disabled
    because we are emitting LaTeX, not HTML.
    """
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(disabled_extensions=("tex.j2",), default=False),
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )
    env.filters["linkify"] = linkify
    env.filters["latex_escape"] = latex_escape
    env.globals["render_achievement_item"] = render_achievement_item
    return env
