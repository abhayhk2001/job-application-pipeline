"""Jinja2 filters used by the resume templates.

``richtext`` is the filter templates should use for any free-form prose
(bullets, achievement items). ``latex_escape`` is for plain fields that can
never contain a link (institution, location, job title, skill-group label).
"""

from __future__ import annotations

import re
from re import Match

__all__ = ["richtext", "linkify", "latex_escape"]

URL_PATTERN = re.compile(r"https?://\S+")
TRAILING_PUNCT = ".,;)!?'\"]"


# --------------------------------------------------------------------------- #
# LaTeX escaping
# --------------------------------------------------------------------------- #

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


def latex_escape(text: str | None) -> str:
    r"""Escape LaTeX-significant characters in a plain string.

    Never apply this to a URL: ``\_`` and friends are not valid inside
    ``\href{...}``. Use :func:`richtext` for anything that may contain a link.

    Implementation note: a sequential ``str.replace`` chain is unsafe here,
    because the replacement for one char would re-escape the backslash
    introduced by another. We walk the string once with a single regex.
    """
    if text is None:
        return ""
    return _LATEX_ESCAPE_RE.sub(_latex_repl, text)


# --------------------------------------------------------------------------- #
# URLs
# --------------------------------------------------------------------------- #


def _escape_url(url: str) -> str:
    r"""Make a URL safe to sit inside ``\href{...}``.

    Only three characters actually break there: ``%`` starts a comment, ``#``
    is a macro parameter, and a literal backslash is not a URL character at
    all. Everything else -- ``_ & ~ ^ $`` -- must be left **verbatim**, since
    hyperref reads the argument with URL catcodes and escaping them would
    change the address.

    The backslash is percent-encoded first so the ``%`` it introduces gets
    escaped by the step that follows.
    """
    url = url.replace("\\", "%5C")
    return url.replace("%", r"\%").replace("#", r"\#")


def _href(url: str, label_tex: str) -> str:
    return "\\href{" + _escape_url(url) + "}{\\underline{" + label_tex + "}}"


def linkify(text: str) -> str:
    r"""Wrap every bare http(s) URL in ``text`` with ``\href{url}{\underline{url}}``.

    Retained for the bare-URL case and for direct use; :func:`richtext` calls
    the same logic. Trailing sentence punctuation swallowed by ``\S`` is
    stripped from the URL and re-emitted outside the ``\href``.

    Known limitation: a URL containing a literal ``)`` loses the trailing
    ``)``.
    """
    if not text:
        return text

    def replace(match: Match[str]) -> str:
        raw = match.group(0)
        url = raw.rstrip(TRAILING_PUNCT)
        trailing = raw[len(url) :]
        return _href(url, url) + trailing

    return URL_PATTERN.sub(replace, text)


# --------------------------------------------------------------------------- #
# richtext
# --------------------------------------------------------------------------- #

_MD_LINK = r"\[(?P<label>[^\]\n]*)\]\((?P<url>[^)\s]*)\)"
_BARE_URL = r"(?P<bare>https?://[^\s]+)"
_RICHTEXT_RE = re.compile(_MD_LINK + "|" + _BARE_URL)


def richtext(text: str | None) -> str:
    r"""Render prose that may contain links into LaTeX, in a single pass.

    Handles two link forms:

    * markdown -- ``[Paper Link](https://example.com/x)``
    * bare -- ``https://example.com/x``

    Both become ``\href{url}{\underline{label}}``.

    The single pass matters. Escaping first and linkifying second (the obvious
    composition, and what this package used to do) corrupts any URL containing
    ``_``, ``&``, ``#`` or ``%``, because the escape runs over the address as
    though it were prose. Here prose and link *labels* are escaped with
    :func:`latex_escape` while URLs go through :func:`_escape_url`, which
    touches only what ``\href`` cannot swallow.

    A markdown link with an empty URL renders as plain underlined text; the
    validator flags it separately so the LLM gets told rather than silently
    shipping a dead link.
    """
    if not text:
        return "" if text is None else text

    out: list[str] = []
    pos = 0
    for match in _RICHTEXT_RE.finditer(text):
        out.append(latex_escape(text[pos : match.start()]))
        bare = match.group("bare")
        if bare is not None:
            url = bare.rstrip(TRAILING_PUNCT)
            trailing = bare[len(url) :]
            out.append(_href(url, _escape_url(url)))
            out.append(latex_escape(trailing))
        else:
            label = latex_escape(match.group("label"))
            url = match.group("url")
            out.append(_href(url, label) if url else "\\underline{" + label + "}")
        pos = match.end()
    out.append(latex_escape(text[pos:]))
    return "".join(out)
