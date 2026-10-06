"""Jinja2 environment configured for resume rendering."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .url_filters import latex_escape, linkify, richtext

__all__ = ["build_environment"]


def build_environment(templates_dir) -> Environment:
    """Return a Jinja2 Environment loading from ``templates_dir``.

    ``templates_dir`` is one directory, or a sequence of them searched in
    order. The sequence form is how a template inherits: given
    ``[<template>, templates/_shared]``, a partial the template does not
    define is picked up from the shared set, and one it does define wins.

    Uses ``StrictUndefined`` so a typo in a template variable name fails the
    render rather than silently emitting empty text. Autoescape is disabled
    because we are emitting LaTeX, not HTML.

    Filters: ``richtext`` for prose that may contain links, ``latex_escape``
    for plain fields, ``linkify`` for the bare-URL case alone.
    """
    if isinstance(templates_dir, (str, Path)):
        search_path = [str(templates_dir)]
    else:
        search_path = [str(d) for d in templates_dir]

    env = Environment(
        loader=FileSystemLoader(search_path),
        undefined=StrictUndefined,
        autoescape=select_autoescape(disabled_extensions=("tex.j2",), default=False),
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )
    env.filters["richtext"] = richtext
    env.filters["latex_escape"] = latex_escape
    env.filters["linkify"] = linkify
    return env
