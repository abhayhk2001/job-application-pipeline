"""Unit tests for the linkify and latex_escape filters."""

from __future__ import annotations

from resume_builder.url_filters import latex_escape, linkify


class TestLinkify:
    def test_simple_url_at_end_of_string(self):
        assert linkify("See https://example.com") == (
            "See \\href{https://example.com}{\\underline{https://example.com}}"
        )

    def test_url_in_middle_of_string(self):
        assert linkify("Visit https://example.com today") == (
            "Visit \\href{https://example.com}{\\underline{https://example.com}} today"
        )

    def test_url_followed_by_period(self):
        out = linkify("See https://example.com.")
        assert out == (
            "See \\href{https://example.com}{\\underline{https://example.com}}."
        )

    def test_url_followed_by_comma(self):
        out = linkify("Tags: https://example.com, https://other.com")
        assert out == (
            "Tags: \\href{https://example.com}{\\underline{https://example.com}}, "
            "\\href{https://other.com}{\\underline{https://other.com}}"
        )

    def test_url_followed_by_closing_paren(self):
        # The trailing ")" must remain outside the \href{...}.
        out = linkify("(see https://example.com)")
        assert out == (
            "(see \\href{https://example.com}{\\underline{https://example.com}})"
        )

    def test_url_with_path_and_query(self):
        url = "https://journals.sagepub.com/doi/10.1177/11769351231167992"
        out = linkify(f"Published. {url}")
        assert out == (
            f"Published. \\href{{{url}}}{{\\underline{{{url}}}}}"
        )

    def test_no_url_passthrough(self):
        assert linkify("Plain text with no URLs") == "Plain text with no URLs"

    def test_empty_string(self):
        assert linkify("") == ""

    def test_none_passthrough(self):
        assert linkify(None) is None

    def test_http_and_https_both_caught(self):
        out = linkify("http://x.io and https://y.io")
        assert "\\href{http://x.io}" in out
        assert "\\href{https://y.io}" in out


class TestLatexEscape:
    def test_ampersand(self):
        assert latex_escape("AT&T") == r"AT\&T"

    def test_percent(self):
        # % is a LaTeX comment; must be escaped or it eats the rest of the line.
        assert latex_escape("24%") == r"24\%"

    def test_dollar(self):
        assert latex_escape("$100") == r"\$100"

    def test_hash(self):
        assert latex_escape("#1") == r"\#1"

    def test_underscore(self):
        assert latex_escape("foo_bar") == r"foo\_bar"

    def test_braces(self):
        assert latex_escape("{x}") == r"\{x\}"

    def test_tilde(self):
        assert latex_escape("~") == r"\textasciitilde{}"

    def test_caret(self):
        assert latex_escape("^") == r"\textasciicircum{}"

    def test_backslash_must_be_first(self):
        # Backslash must be escaped first, otherwise later replacements would
        # double-escape the backslash they themselves introduce.
        assert latex_escape(r"a\b") == r"a\textbackslash{}b"

    def test_combined(self):
        assert latex_escape("Hello & 50% world_") == r"Hello \& 50\% world\_"
