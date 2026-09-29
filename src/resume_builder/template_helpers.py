"""Helpers used by the Jinja2 templates, registered as filters and globals."""

from __future__ import annotations

from .url_filters import latex_escape

__all__ = ["render_achievement_item"]


def render_achievement_item(item: dict) -> str:
    """Render a single achievements item to its full LaTeX body.

    Behaviour matches the hand-written ``../Resume/src/achievements.tex``:
    if a link's display text already appears at the end of ``item.text`` (the
    fixture encodes both the plain-text occurrence and the link annotation),
    the plain-text occurrence is stripped and the link is re-emitted with
    styling so the rendered text reads once with the link treatment applied.

    Links with a non-null ``url`` become ``\\href{url}{\\underline{text}}``;
    links with ``url == null`` become ``\\underline{text}`` only.
    """
    text = item.get("text", "") or ""
    out = text
    for link in item.get("links") or []:
        link_text = link.get("text", "") or ""
        link_url = link.get("url")
        if not link_text:
            continue
        stripped = out.rstrip()
        if stripped.endswith(link_text.rstrip()):
            out = stripped[: -len(link_text.rstrip())].rstrip()
        if link_url:
            out += f" \\href{{{link_url}}}{{\\underline{{{latex_escape(link_text)}}}}}"
        else:
            out += f" \\underline{{{latex_escape(link_text)}}}"
    return out
