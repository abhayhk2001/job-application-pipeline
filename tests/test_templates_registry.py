"""Template discovery, selection, and the contract every template must meet.

The point of these tests is that adding a template is cheap and safe: the
parametrised cases below pick up any template on the search path, so a new one
is checked for the macro contract, for rendering, and (with tectonic
installed) for compiling, without anyone extending this file.
"""

from __future__ import annotations

import json

import pytest

from resume_builder import SHARED_TEMPLATES_DIR
from resume_builder.api import build_resume
from resume_builder.exceptions import TemplateNotFound
from resume_builder.renderer import render
from resume_builder.templates_registry import (
    DEFAULT_TEMPLATE,
    choose,
    describe,
    find,
    list_templates,
    resolve,
)

# Resolved once at collection time so each template becomes its own test case.
ALL_TEMPLATES = [info.name for info in list_templates()]

# A template's own resume.tex.j2 owns the preamble, so it must define the three
# macros the shared partials use. This is the whole inheritance contract.
CONTRACT_MACROS = ("\\resumename", "\\resumesec", "\\resumesub")

# Markers that identify which preamble was used. Both preambles *mention* the
# other font's package in their font-table comment, so the test has to match
# the real directive -- hence the leading newline -- not a bare substring.
SERIF_FONT = "\n\\usepackage{newtxtext}\n"
CLASSIC_FONT = "\n\\usepackage{helvet}\n"


def _write_template(directory, name, body):
    """Create a minimal template on disk and return its parent directory."""
    pack = directory / name
    pack.mkdir(parents=True)
    (pack / "resume.tex.j2").write_text(body)
    return directory


MINIMAL_ROOT = (
    "\\newcommand{\\resumename}{\\Large}\n"
    "\\newcommand{\\resumesec}{\\Large}\n"
    "\\newcommand{\\resumesub}{\\small}\n"
    "\\documentclass[letterpaper,10pt]{article}\n"
    "\\usepackage{enumitem}\n"
    "\\usepackage[hidelinks]{hyperref}\n"
    "% MARKER-FROM-TEST\n"
    "\\begin{document}\n"
    "{{ heading_tex }}\n"
    "{% for section_tex in sections_tex %}\n{{ section_tex }}\n{%- endfor %}\n"
    "\\end{document}\n"
)


# --- discovery -------------------------------------------------------------


def test_the_shipped_templates_are_discovered():
    names = {info.name for info in list_templates()}
    assert {"classic", "serif"} <= names


def test_shared_partials_are_not_a_template():
    """_shared holds the inherited partials; it is not something to choose."""
    assert SHARED_TEMPLATES_DIR.is_dir()
    assert "_shared" not in {info.name for info in list_templates()}


def test_listing_carries_descriptions_and_source():
    classic = find("classic")
    assert classic.source == "builtin"
    assert classic.description
    assert classic.best_for
    assert "classic" in describe(list_templates())


def test_a_template_without_a_manifest_still_works(tmp_path, fixture_resume):
    """Copying a directory and editing it must not require writing JSON."""
    _write_template(tmp_path, "nomanifest", MINIMAL_ROOT)
    info = find("nomanifest", tmp_path)
    assert info.description == ""
    assert info.source == "explicit"
    tex = render(fixture_resume, template="nomanifest", templates_dir=tmp_path)
    assert "MARKER-FROM-TEST" in tex
    # The section partials came from _shared, not from the new directory.
    assert "\\section{Education}" in tex


def test_a_directory_without_a_root_template_is_not_a_template(tmp_path):
    (tmp_path / "empty").mkdir()
    (tmp_path / "empty" / "experience.tex.j2").write_text("nope")
    assert "empty" not in {info.name for info in list_templates(tmp_path)}


def test_an_explicit_dir_shadows_a_builtin_of_the_same_name(tmp_path, fixture_resume):
    _write_template(tmp_path, "classic", MINIMAL_ROOT)
    assert find("classic", tmp_path).source == "explicit"
    tex = render(fixture_resume, template="classic", templates_dir=tmp_path)
    assert "MARKER-FROM-TEST" in tex
    # And the built-in is untouched when no override directory is given.
    assert "MARKER-FROM-TEST" not in render(fixture_resume)


# --- selection -------------------------------------------------------------


def test_choose_precedence():
    assert choose({}, None) == DEFAULT_TEMPLATE
    assert choose({"template": "serif"}, None) == "serif"
    assert choose({"template": "serif"}, "classic") == "classic", "the flag must win"
    assert choose(None, None) == DEFAULT_TEMPLATE
    # An empty or non-string key falls back rather than resolving to nothing.
    assert choose({"template": ""}, None) == DEFAULT_TEMPLATE
    assert choose({"template": 7}, None) == DEFAULT_TEMPLATE


def test_the_json_template_key_selects_the_template(fixture_resume):
    chosen = {**fixture_resume, "template": "serif"}
    assert SERIF_FONT in render(chosen)
    assert SERIF_FONT not in render(fixture_resume)


def test_the_argument_overrides_the_json_key(fixture_resume):
    chosen = {**fixture_resume, "template": "serif"}
    assert SERIF_FONT not in render(chosen, template="classic")


def test_unknown_template_names_the_available_ones():
    with pytest.raises(TemplateNotFound) as excinfo:
        find("no-such-template")
    message = str(excinfo.value)
    assert "no-such-template" in message
    for name in ALL_TEMPLATES:
        assert name in message
    assert excinfo.value.available == ALL_TEMPLATES


@pytest.mark.parametrize(
    "name",
    ["../evil", "../../etc/passwd", "/abs/path", ".", "..", "", "a/b", "_shared", "sub\\dir"],
)
def test_unsafe_names_are_refused(name):
    """A name is a plain directory name; it is never joined onto a path."""
    with pytest.raises(TemplateNotFound):
        find(name)


def test_build_resume_reports_the_template_used(fixture_resume, tmp_path):
    result = build_resume(fixture_resume, tmp_path, tex_only=True, template="serif")
    assert result.template == "serif"
    assert SERIF_FONT in result.tex_path.read_text()


def test_build_resume_rejects_an_unknown_template_before_writing(fixture_resume, tmp_path):
    out = tmp_path / "out"
    with pytest.raises(TemplateNotFound):
        build_resume(fixture_resume, out, tex_only=True, template="nope")
    assert not (out / "resume.tex").exists()


# --- the contract every template must meet ---------------------------------


@pytest.mark.parametrize("name", ALL_TEMPLATES)
def test_every_template_meets_the_macro_contract(name):
    body = (find(name).path / "resume.tex.j2").read_text()
    for macro in CONTRACT_MACROS:
        assert f"\\newcommand{{{macro}}}" in body, f"{name} does not define {macro}"
    assert "{{ heading_tex }}" in body, f"{name} never emits the heading"
    assert "sections_tex" in body, f"{name} never emits the sections"
    assert "\\begin{document}" in body and "\\end{document}" in body


@pytest.mark.parametrize("name", ALL_TEMPLATES)
def test_every_template_renders_the_fixture(name, fixture_resume):
    tex = render(fixture_resume, template=name)
    assert "\\begin{document}" in tex
    assert "\\end{document}" in tex
    for section in fixture_resume["sections"]:
        assert f"\\section{{{section['heading']}" in tex


@pytest.mark.parametrize("name", ALL_TEMPLATES)
def test_every_template_resolves_to_itself_then_the_shared_partials(name):
    search_path = resolve(name)
    assert search_path[0] == find(name).path
    assert search_path[-1] == SHARED_TEMPLATES_DIR


def test_serif_differs_from_classic_only_in_the_preamble(fixture_resume):
    classic = render(fixture_resume, template="classic")
    serif = render(fixture_resume, template="serif")
    assert classic != serif
    assert SERIF_FONT in serif and CLASSIC_FONT not in serif
    assert CLASSIC_FONT in classic and SERIF_FONT not in classic
    # Same bodies: everything from \begin{document} on is the shared partials.
    assert classic.split("\\begin{document}")[1] == serif.split("\\begin{document}")[1]


def _embedded_fonts(path) -> set[str]:
    from pypdf import PdfReader

    found = set()
    for page in PdfReader(str(path)).pages:
        for font in ((page.get("/Resources") or {}).get("/Font") or {}).values():
            base_font = font.get_object().get("/BaseFont")
            if base_font:
                found.add(str(base_font).split("+")[-1])
    return found


@pytest.mark.parametrize("name", ALL_TEMPLATES)
def test_every_template_compiles_to_a_single_page(name, fixture_resume, tmp_path, require_tectonic):
    from pypdf import PdfReader

    result = build_resume(fixture_resume, tmp_path / name, template=name)
    assert result.pdf_path is not None
    assert len(PdfReader(str(result.pdf_path)).pages) == 1, f"{name} overflowed one page"


def test_serif_actually_changes_the_embedded_font(fixture_resume, tmp_path, require_tectonic):
    r"""A font switch that compiles is not a font switch that happened.

    Tectonic is XeTeX, and it silently falls back to Latin Modern for the old
    Type1 NFSS families -- ``\renewcommand{\familydefault}{ptm}`` compiles
    cleanly and changes nothing. Only the embedded font set proves it took, so
    that is what this asserts.
    """
    classic = build_resume(fixture_resume, tmp_path / "c", template="classic")
    serif = build_resume(fixture_resume, tmp_path / "s", template="serif")

    classic_fonts = _embedded_fonts(classic.pdf_path)
    serif_fonts = _embedded_fonts(serif.pdf_path)
    assert any("Termes" in f for f in serif_fonts), serif_fonts
    assert not any("Termes" in f for f in classic_fonts), classic_fonts
    assert classic_fonts != serif_fonts


@pytest.mark.parametrize("name", ["classic", "serif"])
def test_shipped_manifests_are_valid_json_naming_themselves(name):
    manifest = find(name).path / "template.json"
    data = json.loads(manifest.read_text())
    assert data["name"] == name
    assert data["description"] and data["best_for"]
