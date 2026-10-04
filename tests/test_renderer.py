"""Integration tests: fixture -> TeX -> PDF, and parity with the base resume."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from resume_builder.api import build_resume
from resume_builder.pdf_compiler import compile_pdf
from resume_builder.renderer import render_to_file

# Differences we deliberately do NOT reproduce from ../Resume/resume.tex, as
# normalised text. Each pair is (what the base says, what we emit). The parity
# test applies these to the base and then demands an exact match, so a new
# divergence cannot slip through unnoticed.
KNOWN_BASE_DEFECTS = [
    # the base dropped the country code
    ("2173051018", "12173051018"),
    # doubled degree phrase, and "Decemeber" misspelt
    (
        "masterofcomputerscienceincomputerscienceandengineeringaugust2026decemeber2027",
        "masterofcomputerscienceaugust2026december2027",
    ),
    # the published paper title is plural
    ("randomforestclassifier", "randomforestclassifiers"),
]


def _normalize(text: str) -> str:
    """Fold to comparable form: ligatures split, alphanumerics only, lowercased.

    pdftex and xetex extract text differently -- inter-letter spacing and
    ligature handling both vary -- so only the sequence of alphanumerics is
    meaningfully comparable.
    """
    for lig, plain in (("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl")):
        text = text.replace(lig, plain)
    return "".join(c.lower() for c in text if c.isalnum())


def _pdf_text(path: Path) -> str:
    return "".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def test_fixture_renders_to_tex(fixture_resume, tmp_path: Path):
    out = render_to_file(fixture_resume, tmp_path / "resume.tex")
    body = out.read_text()
    assert "\\begin{document}" in body
    assert "\\end{document}" in body
    assert "\\documentclass[letterpaper,10pt]{article}" in body
    assert "\\usepackage[left=0.75in, right=0.75in, top=0.5in, bottom=0.5in]{geometry}" in body
    assert "\\newcommand{\\resumesub}{\\small}" in body
    # The pdfTeX-only ATS hook must stay guarded or tectonic/xetex will fail.
    assert "\\ifdefined\\pdfgentounicode" in body


def test_build_resume_tex_only_needs_no_tectonic(fixture_resume, tmp_path: Path):
    result = build_resume(fixture_resume, tmp_path, tex_only=True)
    assert result.tex_path.exists()
    assert result.pdf_path is None


def test_build_resume_produces_a_single_page_pdf(fixture_resume, tmp_path: Path, require_tectonic):
    result = build_resume(fixture_resume, tmp_path)
    assert result.pdf_path is not None and result.pdf_path.exists()
    assert result.pdf_path.stat().st_size > 1000
    assert len(PdfReader(str(result.pdf_path)).pages) == 1, "the resume must stay on one page"


def test_pdf_matches_the_base_resume_except_for_known_defects(
    fixture_resume, reference_pdf, tmp_path: Path, require_tectonic
):
    """Format parity: our PDF must read identically to the hand-built base.

    This is the test that catches ../Resume/resume.tex drifting away from the
    templates again. If it fails, either the base changed and the templates
    need porting, or a template regressed.
    """
    result = build_resume(fixture_resume, tmp_path)
    ours = _normalize(_pdf_text(result.pdf_path))
    base = _normalize(_pdf_text(reference_pdf))

    for base_text, our_text in KNOWN_BASE_DEFECTS:
        assert base_text in base, f"base no longer contains {base_text!r}; update KNOWN_BASE_DEFECTS"
        assert our_text in ours, f"our output no longer contains {our_text!r}"
        base = base.replace(base_text, our_text)

    assert ours == base


def test_pdf_fonts_match_the_base_resume(fixture_resume, reference_pdf, tmp_path, require_tectonic):
    """Same embedded font set as the base, so the visual result is the same."""

    def fonts(path):
        found = set()
        for page in PdfReader(str(path)).pages:
            resources = page.get("/Resources") or {}
            for font in (resources.get("/Font") or {}).values():
                base_font = font.get_object().get("/BaseFont")
                if base_font:
                    found.add(str(base_font))
        return found

    result = build_resume(fixture_resume, tmp_path)
    assert fonts(result.pdf_path) == fonts(reference_pdf)


@pytest.mark.parametrize("heading", ["Education", "WorkExperience", "ProjectExperience", "Skills"])
def test_every_section_heading_reaches_the_pdf(
    fixture_resume, tmp_path: Path, require_tectonic, heading: str
):
    tex_path = render_to_file(fixture_resume, tmp_path / "resume.tex")
    pdf_path = compile_pdf(tex_path, tmp_path)
    # xetex extraction collapses inter-letter spacing, hence the squashed headings.
    assert heading in _pdf_text(pdf_path).replace(" ", "")
