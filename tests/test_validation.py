"""Validation tests: the gate an LLM's output has to pass before rendering."""

from __future__ import annotations

import copy

import pytest

from resume_builder.exceptions import ValidationError
from resume_builder.renderer import render
from resume_builder.validation import validate


def paths(problems):
    return [p.path for p in problems]


def messages(problems):
    return " | ".join(p.message for p in problems)


def test_the_fixture_is_valid(fixture_resume):
    assert validate(fixture_resume) == []


def test_top_level_must_be_an_object():
    problems = validate([1, 2, 3])
    assert len(problems) == 1
    assert "must be a JSON object" in problems[0].message


def test_missing_basics_and_sections():
    problems = validate({})
    assert messages(problems).count("is a required property") == 2


def test_unknown_section_type_is_named(fixture_resume):
    resume = copy.deepcopy(fixture_resume)
    resume["sections"].append({"type": "publications", "heading": "Papers", "entries": []})
    problems = validate(resume)
    assert any("unknown section type 'publications'" in p.message for p in problems)
    # The reported path points at the offending section, not the whole document.
    assert any(p.path == "/sections/4" for p in problems)


def test_wrong_branch_is_not_reported(fixture_resume):
    """A projects section must never be told it needs 'groups'.

    jsonschema's raw oneOf output complains about all five branches at once;
    validation picks the branch whose ``type`` matched.
    """
    resume = copy.deepcopy(fixture_resume)
    projects = next(s for s in resume["sections"] if s["type"] == "projects")
    projects["entries"][0]["bullets"] = []
    problems = validate(resume)
    assert problems, "empty bullets should be rejected"
    assert "groups" not in messages(problems)
    assert any("non-empty" in p.message for p in problems)
    assert any(p.path.endswith("/bullets") for p in problems)


def test_hallucinated_field_is_rejected(fixture_resume):
    resume = copy.deepcopy(fixture_resume)
    experience = next(s for s in resume["sections"] if s["type"] == "experience")
    experience["entries"][0]["summary"] = "a field the renderer would silently drop"
    problems = validate(resume)
    assert any("'summary' was unexpected" in p.message for p in problems)


def test_contact_requires_a_label(fixture_resume):
    resume = copy.deepcopy(fixture_resume)
    resume["basics"]["contacts"][0] = {"type": "email", "url": "mailto:a@b.com"}
    problems = validate(resume)
    assert any(p.path == "/basics/contacts/0" for p in problems)
    assert "'label' is a required property" in messages(problems)


def test_empty_markdown_link_is_flagged(fixture_resume):
    resume = copy.deepcopy(fixture_resume)
    projects = next(s for s in resume["sections"] if s["type"] == "projects")
    projects["entries"][0]["bullets"][0] = "Shipped it. [Paper Link]()"
    problems = validate(resume)
    assert any("empty URL" in p.message for p in problems)
    assert any(p.path == "/sections/2/entries/0/bullets/0" for p in problems)


def test_confidential_term_is_flagged(fixture_resume, tmp_path, monkeypatch):
    terms = tmp_path / "terms.txt"
    terms.write_text("# withheld\nAcme Motors\n")
    monkeypatch.setenv("RESUME_CONFIDENTIAL_TERMS", str(terms))

    resume = copy.deepcopy(fixture_resume)
    experience = next(s for s in resume["sections"] if s["type"] == "experience")
    experience["entries"][0]["bullets"][0] = "Processed telemetry for Acme Motors"
    problems = validate(resume)
    assert any("withheld term 'Acme Motors'" in p.message for p in problems)


def test_confidential_check_is_inert_without_a_denylist(fixture_resume, tmp_path, monkeypatch):
    monkeypatch.setenv("RESUME_CONFIDENTIAL_TERMS", str(tmp_path / "does-not-exist.txt"))
    assert validate(fixture_resume) == []


def test_renderer_refuses_invalid_input(fixture_resume):
    resume = copy.deepcopy(fixture_resume)
    del resume["basics"]["name"]
    with pytest.raises(ValidationError) as excinfo:
        render(resume)
    assert excinfo.value.problems
    assert "name" in str(excinfo.value)


def test_renderer_can_skip_validation_when_already_checked(fixture_resume):
    # check=False is the path build_resume uses after validating once.
    assert "\\begin{document}" in render(fixture_resume, check=False)
