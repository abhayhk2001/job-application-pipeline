"""The authoritative career record keeps facts and stable links without review bookkeeping."""

from __future__ import annotations

import json

import pytest

from resume_builder import MASTER_RESUME


def _objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


@pytest.fixture(scope="module")
def master():
    return json.loads(MASTER_RESUME.read_text(encoding="utf-8"))


def test_master_contract_and_record_links(master):
    assert master["schema"]["extension"] == "abhay-master-resume/v3"
    assert master["schema"]["version"] == "3.0.0"
    objects = list(_objects(master))
    ids = [obj["id"] for obj in objects if "id" in obj]
    assert len(ids) == len(set(ids))
    for obj in objects:
        assert not {"bullets", "highlights", "pending_resume_corrections"} & obj.keys()
        for key, value in obj.items():
            if key.endswith("_ref"):
                assert value in ids, (key, value)
    text = json.dumps(master).lower()
    for retired in ("needs_input", "evidence_refs", "listed_only"):
        assert retired not in text


def test_master_lists_keep_their_fact_shapes(master):
    projects = [p for work in master["work"] for p in work["projects"]] + master["projects"]
    for project in projects:
        for key in ("actions", "constraints", "technologies_used"):
            assert all(isinstance(item, str) for item in project[key])
        for outcome in project["outcomes"]:
            assert isinstance(outcome, str) or isinstance(outcome["text"], str)
    for work in master["work"]:
        assert all(isinstance(item, str) for item in work.get("working_practices", []))
    assert all(isinstance(item, str) for item in master["basics"]["stated_interests"]["items"])
    for entries in master["skills"].values():
        assert isinstance(entries, list)
        for skill in entries:
            assert skill["name"]
            assert skill.keys() <= {"name", "note"}


def test_current_education_and_confirmed_team_award(master):
    uiuc = next(edu for edu in master["education"] if edu["id"] == "edu.uiuc")
    assert (uiuc["endDate"], uiuc["alternateEndDate"]) == ("2027-12", "2028-05")
    assert uiuc["status"] == "Enrolled"
    assert "incoming" not in json.dumps(master["basics"]["summaries"]).lower()
    award = next(a for a in master["awards"] if a["id"] == "award.best-presentation")
    assert award["date"] == "2022"
    assert "AIMLBIO" in award["awarder"]
    assert "team" in award["context"]
    assert award["project_ref"] == "proj.nsclc-biomarkers"


def test_research_measurements_keep_their_scope(master):
    projects = {p["id"]: p for p in master["projects"]}
    rcot = projects["proj.rcot-hpcc"]["metrics"]
    assert len(rcot) == 1
    assert (rcot[0]["name"], rcot[0]["value"]) == ("Speed advantage over ProbSpace", 50)
    assert "50% faster" in rcot[0]["note"]
    nsclc = projects["proj.nsclc-biomarkers"]
    assert {"GAN", "VAE"} <= set(nsclc["technologies_used"])
    assert "exploratory" in nsclc["note"].lower()
    for metric in nsclc["metrics"]:
        if metric["name"] in ("AUC", "Accuracy"):
            assert "Random Forest" in metric["note"]
    publication = next(p for p in master["publications"] if p["id"] == "pub.cancer-informatics")
    assert publication["releaseDate"] == "2023-04"
    assert publication["authors"][:2] == ["Lavanya C", "Pooja S"]
