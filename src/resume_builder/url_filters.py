"""Jinja2 filters used by the resume templates."""

from __future__ import annotations

import re
from re import Match

URL_PATTERN = re.compile(r"https?://\S+")
TRAILING_PUNCT = ".,;)!?'\"]"


def linkify(text: str) -> str:
    r"""Wrap every http(s) URL in text with \href{url}{\underline{url}}.

    Greedy match for ``https?://\S+`` is post-processed: any trailing sentence
    punctuation that was captured by ``\S`` (``.,;)!?'"]``) is stripped from
    the URL and re-emitted outside the ``\href{...}{...}`` so the rendered
    text preserves it.

    Known limitation: URLs containing literal ``)`` (e.g. Wikipedia
    disambiguation links) lose their trailing ``)``. The render-ready
    fixtures do not exercise this case.
    """
    if not text:
        return text

    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        url = raw.rstrip(TRAILING_PUNCT)
        trailing = raw[len(url) :]
        return "\\href{" + url + "}{\\underline{" + url + "}}" + trailing

    return URL_PATTERN.sub(replace, text)


def latex_escape(text: str) -> str:
    r"""Escape LaTeX-significant characters in a plain string.

    Used for free-form text fields whose source value may contain ``& % $ # _ { } ~ ^ \``.
    Hyperlinks (detected by ``linkify``) must be escaped *before* linkify runs;
    this filter is the second line of defence for fields that aren't URL text.

    Implementation note: a sequential ``str.replace`` chain is unsafe here,
    because the replacement for one char (``\``) would re-escape the backslash
    introduced by another (``\``, ``\&``, ``\%``, ...). Instead we walk the
    string once with a single regex that maps each special character to its
    LaTeX command, leaving everything else untouched.
    """
    if text is None:
        return ""
    return _LATEX_ESCAPE_RE.sub(_latex_repl, text)


_LATEX_ESCAPE_RE = re.compile(r"[\\&%$#_{}~^]")
_LATEX_REPL = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _latex_repl(match: Match[str]) -> str:
    return _LATEX_REPL[match.group(0)]


__all__ = ["linkify", "latex_escape"]
