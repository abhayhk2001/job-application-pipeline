"""Tests for the richtext filter: markdown links, bare URLs, and escaping.

The important property here is that prose and URLs are escaped by different
rules in a single pass. Escaping first and linkifying second -- the obvious
composition -- corrupts any URL containing ``_``, ``&``, ``#`` or ``%``.
"""

from __future__ import annotations

import pytest

from resume_builder.url_filters import latex_escape, richtext


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
