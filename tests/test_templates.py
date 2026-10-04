"""Per-section template render tests.

Each test renders one section partial against the render-ready fixture and
asserts the LaTeX idiom used by the current base resume (``../Resume/resume.tex``):
inline ``tabular*`` blocks sized to ``\\linewidth``, item text wrapped in
``\\resumesub{...}``, and no ``\\resumeSubheading``-style custom commands, which
that base deleted.
"""

from __future__ import annotations

import pytest

from resume_builder import TEMPLATES_DIR
from resume_builder.jinja_env import build_environment

ENTRY_TABULAR = "\\begin{tabular*}{\\linewidth}[t]{@{\\extracolsep{\\fill}}lr}"


def _render(template: str, **ctx) -> str:
    return build_environment(TEMPLATES_DIR).get_template(template).render(**ctx)


def _section(fixture_resume, section_type):
    return next(s for s in fixture_resume["sections"] if s["type"] == section_type)


def test_no_template_uses_the_deleted_custom_commands():
    """The base dropped these macros; emitting them would not compile."""
    for name in (
        "heading.tex.j2",
        "education.tex.j2",
        "experience.tex.j2",
        "projects.tex.j2",
        "skills.tex.j2",
        "achievements.tex.j2",
        "resume.tex.j2",
    ):
        body = (TEMPLATES_DIR / name).read_text()
        for macro in (
            "\\resumeSubheading",
            "\\resumeItem{",
            "\\resumeProjectHeading",
            "\\resumeSubHeadingListStart",
            "\\resumeItemListStart",
        ):
            assert macro not in body, f"{name} still uses {macro}"


def test_heading_renders_name_and_labelled_contacts(fixture_resume):
    tex = _render("heading.tex.j2", basics=fixture_resume["basics"])
    assert "\\textbf{\\resumename Abhay Harish Kashyap}" in tex
    # Contacts render as labels, not raw URLs.
    assert "\\href{https://www.linkedin.com/in/abhay-h-kashyap/}{\\underline{Linkedin}}" in tex
    assert "\\href{https://github.com/abhayhk2001}{\\underline{Github}}" in tex
    assert "\\href{mailto:abhayhk2001@gmail.com}{\\underline{abhayhk2001@gmail.com}}" in tex
    assert "https://github.com/abhayhk2001}{\\underline{https" not in tex
    # A null url renders as plain text.
    assert "+1 217 305 1018" in tex
    assert "\\href{tel:" not in tex
    # Three separators between four contacts, and none trailing.
    assert tex.count(" \\quad") == 3
    assert tex.rstrip().endswith("\\end{center}")


def test_education_uses_inline_tabular(fixture_resume):
    tex = _render("education.tex.j2", section=_section(fixture_resume, "education"))
    assert "\\section{Education}" in tex
    assert tex.count(ENTRY_TABULAR) == 2
    assert "\\textbf{University of Illinois Urbana-Champaign} & Champaign, USA \\\\" in tex
    assert "\\textit{\\resumesub Master of Computer Science}" in tex
    assert "\\textit{\\resumesub August 2026 - December 2027}" in tex
    assert "\\textbf{RV College of Engineering} & Bengaluru, India \\\\" in tex
    assert "(GPA: 9.22/10.0)" in tex
    # UIUC before RVCE: reverse chronological, as the base has it.
    assert tex.index("University of Illinois") < tex.index("RV College")
    # No nested bullet list in education.
    assert "\\item \\resumesub{" not in tex


def test_experience_renders_tabular_and_resumesub_bullets(fixture_resume):
    tex = _render("experience.tex.j2", section=_section(fixture_resume, "experience"))
    assert "\\section{Work Experience}" in tex
    assert tex.count(ENTRY_TABULAR) == 2
    assert "\\textbf{Qualcomm India Private Limited} & Bengaluru, India \\\\" in tex
    assert "\\textit{\\resumesub Software Engineer}" in tex
    assert "\\textit{\\resumesub January 2023 - July 2026}" in tex
    # 4 Qualcomm + 3 Epsilon bullets.
    assert tex.count("\\item \\resumesub{") == 7
    assert tex.count("\\end{itemize}\\vspace{-5pt}") == 2


def test_projects_render_bold_name_without_tabular(fixture_resume):
    tex = _render("projects.tex.j2", section=_section(fixture_resume, "projects"))
    assert "\\section{Project Experience}" in tex
    assert ENTRY_TABULAR not in tex
    assert tex.count("\\item\\noindent\\resumesub\\textbf{") == 3
    # Three projects, two bullets each.
    assert tex.count("\\item \\resumesub{") == 6
    # Markdown links become labelled hrefs, not bare URLs.
    assert "\\href{https://rdcu.be/wZSePwoXqLVa}{\\underline{Paper Link}}" in tex
    assert "\\href{https://journals.sagepub.com/doi/10.1177/11769351231167992}{\\underline{Paper Link}}" in tex
    assert "\\href{http://www.jait.us/shw-229-1347-1.html}{\\underline{Paper Link}}" in tex
    assert "{\\underline{https://" not in tex
    # Business Documents first, matching the base ordering.
    assert tex.index("Business Documents") < tex.index("Novel Biomarker")


def test_skills_uses_resumesub_block(fixture_resume):
    tex = _render("skills.tex.j2", section=_section(fixture_resume, "skills"))
    assert "\\section{Skills}" in tex
    assert "\\resumesub{\\item{" in tex
    assert "\\small{\\item{" not in tex
    assert tex.count("\\textbf{") == 4
    assert "Python, Java, C/C++, SQL, Dart, R, Rust" in tex
    assert tex.count(" \\\\") == 3  # three joiners between four groups


def test_achievements_render_as_plain_strings():
    """Achievement items are plain strings now, with the same markdown-link rule."""
    section = {
        "type": "achievements",
        "heading": "Achievements",
        "items": [
            "Led the data-driven astronomy research division in RVCE's astrophysics club, Dhruva",
            "Won two hackathons. [Certificates](https://example.com/certs)",
        ],
    }
    tex = _render("achievements.tex.j2", section=section)
    assert "\\section{Achievements}" in tex
    assert tex.count("\\item \\resumesub{") == 2
    assert "\\href{https://example.com/certs}{\\underline{Certificates}}" in tex
    assert tex.count("Certificates") == 1


@pytest.mark.parametrize(
    "bullet,expected,forbidden",
    [
        ("Improved throughput by 24% in 1 day", "24\\%", "24% in 1 day"),
        ("Cut cost by $5 & time by 30%", "\\$5 \\& time by 30\\%", None),
        ("Used C_style naming", "C\\_style", None),
        ("See https://example.com for details", "\\href{https://example.com}", None),
    ],
)
def test_bullets_are_escaped_and_linkified(fixture_resume, bullet, expected, forbidden):
    section = {
        **_section(fixture_resume, "experience"),
        "entries": [
            {
                "organization": "Test Co",
                "location": "Test City",
                "title": "Tester",
                "dateRange": "Test Date",
                "bullets": [bullet],
            }
        ],
    }
    tex = _render("experience.tex.j2", section=section)
    assert expected in tex
    if forbidden:
        assert forbidden not in tex


def test_full_resume_renders_every_section_present_in_the_fixture(fixture_resume):
    from resume_builder.renderer import render

    tex = render(fixture_resume)
    assert "\\begin{document}" in tex
    assert "\\end{document}" in tex
    for section in fixture_resume["sections"]:
        assert f"\\section{{{section['heading']}" in tex
