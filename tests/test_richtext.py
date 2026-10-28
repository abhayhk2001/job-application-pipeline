"""Tests for the richtext filter: markdown links, bare URLs, and escaping.

The important property here is that prose and URLs are escaped by different
rules in a single pass. Escaping first and linkifying second -- the obvious
composition -- corrupts any URL containing ``_``, ``&``, ``#`` or ``%``.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

from resume_builder.api import build_resume
from resume_builder.url_filters import (
    TRAILING_PUNCT,
    _escape_url,
    _href,
    latex_escape,
    richtext,
)


class TestMarkdownLinks:
    def test_basic_link(self):
        assert richtext("See [Paper Link](https://x.io/a)") == (
            "See \\href{https://x.io/a}{\\underline{Paper Link}}"
        )

    def test_link_in_the_middle(self):
        assert richtext("a [b](https://x.io) c") == (
            "a \\href{https://x.io}{\\underline{b}} c"
        )

    def test_two_links(self):
        out = richtext("[one](https://a.io) and [two](https://b.io)")
        assert out.count("\\href{") == 2
        assert "\\underline{one}" in out and "\\underline{two}" in out

    def test_empty_url_degrades_to_underline(self):
        assert richtext("[Certificates]()") == "\\underline{Certificates}"

    def test_label_is_latex_escaped(self):
        assert richtext("[100% sure](https://x.io)") == (
            "\\href{https://x.io}{\\underline{100\\% sure}}"
        )


class TestUrlEscaping:
    @pytest.mark.parametrize("char", ["_", "&", "~", "$"])
    def test_url_safe_characters_are_left_verbatim(self, char):
        """These are LaTeX-special in prose but must survive inside \\href."""
        url = f"https://x.io/a{char}b"
        assert f"\\href{{{url}}}" in richtext(f"[L]({url})")

    def test_percent_and_hash_are_escaped_in_urls(self):
        out = richtext("[L](https://x.io/a%20b#frag)")
        assert "\\href{https://x.io/a\\%20b\\#frag}" in out

    def test_prose_still_escapes_those_same_characters(self):
        assert richtext("100% of a_b & c") == "100\\% of a\\_b \\& c"

    def test_bare_url_with_underscore_is_not_corrupted(self):
        """Regression: the old escape-then-linkify chain produced \\_ in the href."""
        out = richtext("See https://x.io/a_b_c for detail")
        assert "\\href{https://x.io/a_b_c}" in out
        assert "a\\_b" not in out


class TestBareUrls:
    def test_bare_url_is_wrapped(self):
        out = richtext("See https://x.io")
        assert out == "See \\href{https://x.io}{\\underline{https://x.io}}"

    def test_trailing_sentence_period_stays_outside(self):
        out = richtext("See https://x.io.")
        assert out.endswith("}.")
        assert "io.}" not in out


class TestEdgeCases:
    def test_none_becomes_empty_string(self):
        assert richtext(None) == ""

    def test_empty_string(self):
        assert richtext("") == ""

    def test_plain_prose_is_just_escaped(self):
        assert richtext("No links here") == "No links here"

    def test_latex_escape_rejects_nothing_silently(self):
        assert latex_escape("a\\b") == "a\\textbackslash{}b"


class TestBold:
    def test_bold_span(self):
        assert richtext("a **b** c") == "a \\textbf{b} c"

    def test_two_spans(self):
        assert richtext("**a** and **b**") == "\\textbf{a} and \\textbf{b}"

    def test_bold_content_is_latex_escaped(self):
        assert richtext("**R&D 100%** a_b") == "\\textbf{R\\&D 100\\%} a\\_b"

    def test_author_name_alongside_a_markdown_link(self):
        """The publication-item shape the generator emits."""
        item = (
            "C, L., S, P., **Kashyap, A.H.** et al. "
            '"Novel Biomarker Prediction..." Cancer Informatics, 2023. '
            "[Paper](https://doi.org/10.1177/11769351231167992)"
        )
        assert richtext(item) == (
            "C, L., S, P., \\textbf{Kashyap, A.H.} et al. "
            '"Novel Biomarker Prediction..." Cancer Informatics, 2023. '
            "\\href{https://doi.org/10.1177/11769351231167992}{\\underline{Paper}}"
        )

    def test_bold_may_wrap_a_link(self):
        assert richtext("**[Paper](https://x.io/a_b)**") == (
            "\\textbf{\\href{https://x.io/a_b}{\\underline{Paper}}}"
        )

    def test_bold_may_wrap_a_bare_url(self):
        out = richtext("**see https://x.io/a_b.**")
        assert out == ("\\textbf{see \\href{https://x.io/a_b}{\\underline{https://x.io/a_b}}.}")

    def test_link_label_may_be_bold(self):
        assert richtext("[**Paper**](https://x.io/a_b)") == (
            "\\href{https://x.io/a_b}{\\underline{\\textbf{Paper}}}"
        )

    def test_partly_bold_link_label(self):
        assert richtext("[see **this** 100%](https://x.io)") == (
            "\\href{https://x.io}{\\underline{see \\textbf{this} 100\\%}}"
        )

    def test_url_underscore_survives_next_to_bold(self):
        out = richtext("**bold** https://x.io/a_b_c")
        assert "\\href{https://x.io/a_b_c}" in out
        assert "a\\_b" not in out

    @pytest.mark.parametrize("text", ["unmatched ** here", "2 ** 3", "a ****", "**\n**"])
    def test_unclosed_or_empty_markers_stay_literal(self, text):
        assert "\\textbf" not in richtext(text)

    def test_markers_never_leak_into_latex(self):
        assert "**" not in richtext("**a** [**b**](https://x.io) **[c](https://y.io)**")


def _legacy_richtext(text: str | None) -> str:
    """``richtext`` exactly as it was before bold support, as the oracle."""
    pattern = re.compile(
        r"\[(?P<label>[^\]\n]*)\]\((?P<url>[^)\s]*)\)" + "|" + r"(?P<bare>https?://[^\s]+)"
    )
    if not text:
        return "" if text is None else text
    out: list[str] = []
    pos = 0
    for match in pattern.finditer(text):
        out.append(latex_escape(text[pos : match.start()]))
        bare = match.group("bare")
        if bare is not None:
            url = bare.rstrip(TRAILING_PUNCT)
            out.append(_href(url, _escape_url(url)))
            out.append(latex_escape(bare[len(url) :]))
        else:
            label = latex_escape(match.group("label"))
            url = match.group("url")
            out.append(_href(url, label) if url else "\\underline{" + label + "}")
        pos = match.end()
    out.append(latex_escape(text[pos:]))
    return "".join(out)


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)


TRICKY = [
    "",
    "100% of a_b & c # $ ~ ^ { } \\",
    "star * alone and 5 * 3 and a*b*c",
    "[label](https://x.io/a%20b#frag) and https://x.io/a_b_c.",
    "[Certificates]() then [L](https://x.io)",
    "(see https://x.io/a_b), done.",
]


def test_text_without_bold_markers_renders_exactly_as_before(fixture_resume):
    """The fixture feeds the golden file; no string in it may change."""
    corpus = [*_strings(fixture_resume), *TRICKY]
    assert all("**" not in text for text in corpus)
    assert len(corpus) > 50
    for text in corpus:
        assert richtext(text) == _legacy_richtext(text), text


@pytest.mark.parametrize("template", ["classic", "serif"])
def test_bold_publication_item_compiles_in_every_builtin_template(
    fixture_resume, tmp_path: Path, template: str, require_tectonic
):
    from pypdf import PdfReader

    resume = copy.deepcopy(fixture_resume)
    resume["sections"].append(
        {
            "type": "achievements",
            "heading": "Publications",
            "items": [
                "C, L., S, P., **Kashyap, A.H.** et al. Cancer Informatics, 2023. "
                "[Paper](https://doi.org/10.1177/11769351231167992)"
            ],
        }
    )

    result = build_resume(resume, tmp_path, template=template)

    assert "\\textbf{Kashyap, A.H.}" in result.tex_path.read_text()
    reader = PdfReader(result.pdf_path)
    assert len(reader.pages) == 1
    text = "".join(page.extract_text() for page in reader.pages)
    assert "Kashyap, A.H." in text
    assert "**" not in text
