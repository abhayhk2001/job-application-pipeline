"""Per-section template render tests.

These tests render each section partial against the render-ready fixture and
diff against golden strings captured by hand from
``../Resume/src/*.tex``. They catch macro typos, missing fields, wrong joiners
and incorrect whitespace control.
"""

from __future__ import annotations

from resume_builder import TEMPLATES_DIR
from resume_builder.jinja_env import build_environment


def _env():
    return build_environment(TEMPLATES_DIR)


def _render(template: str, **ctx) -> str:
    return _env().get_template(template).render(**ctx)


def test_heading_renders_name_and_contacts(fixture_resume):
    tex = _render("heading.tex.j2", basics=fixture_resume["basics"])
    assert "\\textbf{\\Huge \\scshape Abhay Harish Kashyap}" in tex
    assert "\\href{https://www.linkedin.com/in/abhay-h-kashyap/}" in tex
    assert "\\href{https://github.com/abhayhk2001}" in tex
    assert "\\href{tel:+12173051018}" in tex
    assert "\\href{mailto:abhayhk2001@gmail.com}" in tex
    assert tex.count(" \\quad") == 3  # three separators between four contacts
    assert tex.rstrip().endswith("\\end{center}")


def test_education_renders_subheading_macro(fixture_resume):
    edu = next(s for s in fixture_resume["sections"] if s["type"] == "education")
    tex = _render("education.tex.j2", section=edu)
    assert "\\section{Education}" in tex
    assert "\\resumeSubheading" in tex
    assert "{RV College of Engineering}" in tex
    assert "{Bengaluru, India}" in tex
    assert "{Bachelor in Computer Science and Engineering (GPA: 9.22)}" in tex
    assert "{August 2023}" in tex
    assert "{University of Illinois Urbana-Champaign}" in tex
    assert "{August 2026}" in tex
    assert tex.count("\\resumeSubheading") == 2
    assert "\\resumeSubHeadingListStart" in tex
    assert "\\resumeSubHeadingListEnd" in tex


def test_experience_renders_subheading_and_bullets(fixture_resume):
    exp = next(s for s in fixture_resume["sections"] if s["type"] == "experience")
    tex = _render("experience.tex.j2", section=exp)
    assert "\\section{Work Experience}" in tex
    assert "{Qualcomm India Private Limited}" in tex
    assert "{Software Engineer}" in tex
    assert "{January 2023" in tex
    assert "July 2026}" in tex
    assert "{Epsilon Pvt Ltd}" in tex
    assert "{Software Engineering Intern}" in tex
    # 4 Qualcomm bullets + 3 Epsilon bullets = 7 total.
    assert tex.count("\\resumeItem{") == 7


def test_experience_bullets_are_latex_escaped(fixture_resume):
    """A bullet containing `%` must be escaped so it doesn't start a comment."""
    # Inject a synthetic entry with a literal percent sign.
    exp = next(s for s in fixture_resume["sections"] if s["type"] == "experience")
    exp = {
        **exp,
        "entries": [
            *exp["entries"],
            {
                "organization": "Test Co",
                "location": "Test City",
                "title": "Tester",
                "dateRange": "Test Date",
                "bullets": ["Improved throughput by 24% in 1 day"],
            },
        ],
    }
    tex = _render("experience.tex.j2", section=exp)
    assert "24\\%" in tex
    # Make sure the unescaped `%` is NOT in the output (it would start a comment).
    assert "24% in 1 day" not in tex


def test_experience_bullets_get_urls_linkified(fixture_resume):
    exp = next(s for s in fixture_resume["sections"] if s["type"] == "experience")
    exp = {
        **exp,
        "entries": [
            {
                "organization": "Test Co",
                "location": "Test City",
                "title": "Tester",
                "dateRange": "Test Date",
                "bullets": ["See https://example.com for details"],
            },
        ],
    }
    tex = _render("experience.tex.j2", section=exp)
    assert "\\href{https://example.com}{\\underline{https://example.com}}" in tex


def test_projects_renders_project_heading_and_bullets(fixture_resume):
    proj = next(s for s in fixture_resume["sections"] if s["type"] == "projects")
    tex = _render("projects.tex.j2", section=proj)
    assert "\\section{Project Experience}" in tex
    assert "\\resumeProjectHeading" in tex
    assert "Novel Biomarker Prediction for Lung Cancer Using Random Forest Classifier" in tex
    # Three projects, each with two bullets.
    assert tex.count("\\resumeProjectHeading") == 3
    assert tex.count("\\resumeItem{") == 6
    # The published URLs in bullets should be wrapped as hrefs.
    assert "\\href{https://journals.sagepub.com/doi/10.1177/11769351231167992}" in tex
    assert "\\href{http://www.jait.us/shw-229-1347-1.html}" in tex


def test_skills_renders_single_block_with_groups(fixture_resume):
    skills = next(s for s in fixture_resume["sections"] if s["type"] == "skills")
    tex = _render("skills.tex.j2", section=skills)
    assert "\\section{Skills}" in tex
    # Four groups, each as \\textbf{Label}: items
    assert tex.count("\\textbf{") == 4
    assert "Programming Languages" in tex
    assert "Frameworks" in tex
    assert "Tools" in tex
    assert "Machine Learning" in tex
    # Items are comma-joined within each group.
    assert "Python, Java, C/C++, SQL, Dart, R, Rust" in tex
    # Groups are joined by \\.
    assert tex.count(" \\\\") == 3


def test_achievements_renders_underline_link_with_no_url(fixture_resume):
    achievements = next(s for s in fixture_resume["sections"] if s["type"] == "achievements")
    tex = _render("achievements.tex.j2", section=achievements)
    assert "\\section{Achievements}" in tex
    # The first item has a link with no URL; it should be rendered as
    # \\underline{Certificates} without \\href, and the plain-text "Certificates"
    # should NOT be duplicated.
    assert "\\underline{Certificates}" in tex
    # Specifically, the rendered bullet should be: "Won two hackathons with
    # Blockchain News DAap - \\underline{Certificates}"
    # (the duplicate plain-text "Certificates" must be stripped).
    assert "Won two hackathons with Blockchain News DAap - \\underline{Certificates}" in tex
    # Items 2 and 3 have no links; they should be plain text.
    assert "RVCE" in tex
    assert "Samsung, LexisNexis, Epsilon, and SCII" in tex


def test_achievements_keeps_inline_link_when_url_provided(fixture_resume):
    """When a link's URL is non-null, it should appear as \\href even if its
    text overlaps with the end of item.text."""
    achievements = {
        "type": "achievements",
        "heading": "Achievements",
        "items": [
            {
                "text": "Project home - homepage",
                "links": [{"text": "homepage", "url": "https://example.com"}],
            }
        ],
    }
    tex = _render("achievements.tex.j2", section=achievements)
    assert "\\href{https://example.com}{\\underline{homepage}}" in tex
    # The plain "homepage" should have been stripped from the body and re-emitted
    # only inside the \\href.
    assert tex.count("homepage") == 1


def test_full_resume_renders_all_sections(fixture_resume):
    """Smoke test: render the whole resume from the fixture."""
    from resume_builder.renderer import render

    tex = render(fixture_resume)
    assert "\\begin{document}" in tex
    assert "\\end{document}" in tex
    # Each section heading should appear in the assembled output.
    for heading in ("Education", "Work Experience", "Project Experience", "Skills", "Achievements"):
        assert f"\\section{{{heading}" in tex, f"missing section {heading!r}"
