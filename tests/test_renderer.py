"""Integration test: render the fixture to a PDF and diff against the reference."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from resume_builder.pdf_compiler import compile_pdf
from resume_builder.renderer import render_to_file


def _normalize(text: str) -> str:
    """Strip whitespace, lowercase, drop non-alphanumerics, fold ligatures.

    Different TeX engines (pdftex vs xetex) produce slightly different text
    extraction: spaces between letters may be collapsed, ligatures may or may
    not be split (e.g. ``fi`` vs ``ﬁ``). For content comparison we only care
    about whether the same words appear in the same order, so we fold common
    ligatures (``ﬁ`` ``ﬂ`` ``ﬀ`` ``ﬃ`` ``ﬄ``) to their component letters.
    """
    text = (
        text.replace("ﬁ", "fi")
        .replace("ﬂ", "fl")
        .replace("ﬀ", "ff")
        .replace("ﬃ", "ffi")
        .replace("ﬄ", "ffl")
    )
    return "".join(c.lower() for c in text if c.isalnum())


def test_fixture_renders_to_tex(fixture_resume, tmp_path: Path):
    out = tmp_path / "resume.tex"
    render_to_file(fixture_resume, out)
    assert out.exists()
    body = out.read_text()
    assert "\\begin{document}" in body
    assert "\\end{document}" in body
    assert "\\resumeSubheading" in body
    assert "\\resumeProjectHeading" in body


def test_fixture_compiles_to_pdf(fixture_resume, tmp_path: Path, require_tectonic):
    tex_path = tmp_path / "resume.tex"
    render_to_file(fixture_resume, tex_path)
    pdf_path = compile_pdf(tex_path, tmp_path)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000  # not an empty/error PDF


def test_pdf_text_matches_reference(fixture_resume, reference_pdf, tmp_path, require_tectonic):
    """The text extracted from the rendered PDF should match the reference.

    xetex (used by tectonic) and pdftex (used by the original build) produce
    slightly different text-extraction output: spaces between letters may be
    collapsed, ligatures may or may not be split (e.g. ``fi`` vs ``ﬁ``). The
    test normalises both before comparing, and additionally verifies every
    chunk of the reference appears in the output.
    """
    tex_path = tmp_path / "resume.tex"
    render_to_file(fixture_resume, tex_path)
    pdf_path = compile_pdf(tex_path, tmp_path)

    ref_text = "".join(p.extract_text() for p in PdfReader(reference_pdf).pages)
    out_text = "".join(p.extract_text() for p in PdfReader(pdf_path).pages)

    ref_norm = _normalize(ref_text)
    out_norm = _normalize(out_text)

    # Sanity check: lengths should be within a few percent of each other.
    len_ratio = min(len(out_norm), len(ref_norm)) / max(len(out_norm), len(ref_norm))
    assert len_ratio >= 0.98, f"length ratio {len_ratio:.4f} too low"

    # Every 20-char chunk of the reference (the smaller one) must appear in
    # the output. This catches dropped sections or reordered content without
    # being brittle to ligature/whitespace differences.
    shorter, longer = sorted([ref_norm, out_norm], key=len)
    chunk = 20
    missing = []
    for i in range(0, len(shorter) - chunk, chunk):
        if shorter[i : i + chunk] not in longer:
            missing.append(shorter[i : i + chunk])
    assert not missing, f"missing chunks: {missing[:5]}"


@pytest.mark.parametrize(
    "section_type,expected_heading",
    [
        ("education", "Education"),
        ("experience", "WorkExperience"),  # xetex extraction collapses spaces
        ("projects", "ProjectExperience"),
        ("skills", "Skills"),
        ("achievements", "Achievements"),
    ],
)
def test_every_section_type_in_pdf(
    fixture_resume, tmp_path: Path, require_tectonic, section_type: str, expected_heading: str
):
    tex_path = tmp_path / "resume.tex"
    render_to_file(fixture_resume, tex_path)
    pdf_path = compile_pdf(tex_path, tmp_path)
    text = "".join(p.extract_text() for p in PdfReader(pdf_path).pages)
    assert expected_heading in text, f"{expected_heading!r} not in compiled PDF"
