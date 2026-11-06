# Master resume v3 migration handoff

The authoritative career record is now `data/master_resume.json`, using
`abhay-master-resume/v3`, version `3.0.0`. The sibling `resume_generator` has
since been migrated (see "Generator migration status" below); the record now
also holds the Unifrost Drona project (`proj.unifrost-lms`) and 129 skills.

## Generator migration status (2026-11-05)

Done. `resume_generator` reads v3 (`--audit-data-lake`: 20 units, 129 skills,
zero warnings). Departures from the plan below, and later additions:

- A skill links to a unit when the unit's `technologies_used` (including
  `technical_details[].technologies_used`) share an alias with it, or the unit's
  own actions, constraints, outcomes or metric names name one of its aliases.
  Unlinked skills stay `listed_only`: listable, never in experience prose.
- The Git shared fact applies to every unit (note fingerprint re-pinned).
- `dup.best-presentation` is gone. The NSCLC outcome that restates the award now
  carries `award_ref`, and any outcome with an `award_ref` is represented by the
  award claim alone.
- Unifrost's people/institution metrics use `unit: "count"` with inline
  qualifiers (`about`, a `"7-8"` value) so their claim slots read naturally.
- `proj.unifrost-lms` holds 6 canonical bullets (`canonical_bullet_counts` in the
  normalization rules); a resume shows the ones that name the most JD terms.

The counts below (80 skills, 19 units) describe the state at migration time.

## Completed in resume_builder

- Removed skill `evidence_refs`, `status` (`evidenced` / `listed_only`), and `skills.legend`.
  All 80 skills remain in their original 10 categories. Entries retain `name` and optional
  factual `note`; Shell scripting remains a self-taught skill without recorded project use.
- Removed `confidence: "needs_input"` markers, `metadata.needs_input`, the worksheet pointer,
  `data/NEEDS_INPUT.md`, and the public `resume_builder.NEEDS_INPUT` constant/export.
  Intentional nulls remain; no dates, customer names or measurements were invented.
- Confirmed the Best Presentation **team** award at the International Conference on
  Artificial Intelligence and Machine Learning in Applied Biotechnology (AIMLBIO 2022).
  Recorded `date: "2022"` and updated both the award and project outcome.
- Kept both UIUC graduation dates (`2027-12` and `2028-05`) and the existing role-based
  selection instruction. Updated summaries to current Master of Computer Science student wording.
- Kept RCoT's single 50% speed advantage over ProbSpace. Removed the stale reference to a
  deleted runtime-reduction metric. Do not rewrite 50% faster as 50% less runtime.
- Retained GAN/VAE as candidate-confirmed exploratory work, separately from the Random
  Forest AUC and accuracy. No experimental results were invented for GAN/VAE.
- Corrected the lung-cancer publication to April 2023 and authors Lavanya C / Pooja S;
  fixed the JAIT publisher URL and ICAIC's "Conference on" name.
- Removed historical source/reconciliation notes and relative-priority wording from career
  facts. Preserved the small embedded-ML contribution and non-production Phoenix benchmark scope.
- Moved all eight `metadata.pending_resume_corrections` entries below, verbatim. The old
  worksheet's resolved history remains available in Git; it is not a second career record.
- Updated the master documentation and README. The rendering fixture, golden TeX,
  templates, rendered-resume schema, stable IDs, paper links, confidentiality rules,
  deliberate exclusions, and presentation preferences remain unchanged.

Bibliographic corrections use the [SAGE article](https://journals.sagepub.com/doi/10.1177/11769351231167992),
[JAIT article](https://www.jait.us/show-229-1347-1.html), and
[Springer chapter](https://link.springer.com/chapter/10.1007/978-981-95-7238-0_36).
Candidate-confirmed experimental work may extend beyond the published paper.

## Input contract changes

Before (v2):

```json
{
  "schema": { "extension": "abhay-master-resume/v2", "version": "2.0.0" },
  "skills": {
    "legend": { "evidenced": "...", "listed_only": "..." },
    "tooling": [{ "name": "Shell scripting", "status": "listed_only", "evidence_refs": [] }]
  },
  "metadata": { "needs_input": [], "needs_input_worksheet": "...", "pending_resume_corrections": [] }
}
```

After (v3; abbreviated, not a complete input):

```json
{
  "schema": { "extension": "abhay-master-resume/v3", "version": "3.0.0" },
  "skills": {
    "tooling": [{ "name": "Shell scripting", "note": "Self-taught; no project use is recorded." }]
  },
  "metadata": {
    "generation_directives": ["..."],
    "confidentiality": [],
    "maintenance": { "how_to_extend": "...", "invariant": "..." },
    "presentation_preferences": {},
    "deliberate_exclusions": []
  }
}
```

Skill notes are optional strings. The remaining record shapes are unchanged:
`actions`, employer `working_practices`, and stated-interest items are string arrays;
text-only outcomes are strings, while outcomes with metadata can remain objects.
`project_ref`, `publication_ref`, `award_ref` and rendered `source_ref` remain valid.
General skills confirm competency; they do not place a technology in a particular project.

## Required changes in resume_generator

1. **Reader and validation.** Update `preflight.py`'s `SOURCE_EXTENSION`, shape validation,
   and `rules/normalization_rules.json`'s `source_extension` to v3. Accept skill objects with
   `name` and optional `note` without requiring `evidence_refs` or `metadata.needs_input`.
   Remove the retired question-suppression pass and associated warnings. Keep strict JSON,
   source-ID, snapshot, record-link, null, confidentiality, aspiration and exclusion checks.
   The planning audit found 19 normalized units, 80 skills and zero warnings on v2;
   removing the bookkeeping in memory while retaining the v2 header caused 81 shape errors
   (80 missing skill reference arrays and the missing question list).
2. **Skills and project scope.** Adapt `normalize_skills`, `NormalizedSkill` and their callers
   without restoring manual evidence mappings in the master. All v3 skills are confirmed and
   eligible for the skills section. Derive project-use associations from each engagement's
   `technologies_used` through the existing alias helpers. Apply explicitly recorded shared
   facts, such as Git/GitHub use across all engagements, only within their stated scope.
   Update or replace the shared Git rule's pinned note fingerprint because its wording changed.
   Do not assign every skill to every project. If internal `evidenced` / `listed_only` labels
   are retained, they describe recorded project-use linkage, not whether a skill is confirmed;
   a skill without such linkage must still be usable in the skills section.
3. **Downstream consumers.** Update `jd_compressor.py`, `scorer.py`, `skills.py` and `linter.py`
   where they consume skill statuses or evidence references. Use normalized project-use
   associations for unit relevance and technology authorization; general skills alone cannot
   authorize experience prose. Keep domains/practices as nontechnical context. Preserve
   employer-versus-project boundaries, Epsilon virtual-unit remapping/deduplication, typed
   claim/source references and the distinction between aspirations and accomplishments.
4. **Confirmed award.** Remove the obsolete `dup.best-presentation` suppression rule. It
   currently suppresses the award and its duplicate outcome unconditionally and pins the old
   outcome text; updating that text can fail preflight even after removing the question marker.
   Keep the confirmed team award eligible and represent its outcome once, retaining the
   award/project relationship. Accept a year-only award date; do not infer a month or day.
5. **Other changed source content.** Reconcile normalization anchors and source fingerprints
   against the v3 diff, especially exploratory GAN/VAE work, Random Forest metric notes,
   summary wording, citation notes, the Git note, publication metadata and award text.
   Rebuild from recorded facts rather than weakening stale-anchor checks. Keep RCoT's speed
   comparison, the document models' separate mAP bindings, and the Phoenix test-query caveat.
   Preserve both UIUC graduation alternatives and existing routing behavior.
6. **Versioning, caches and documentation.** Bump the normalization rules version. Bump any
   normalized schema or synthesis-contract version whose shape or semantics changes, and
   refresh corresponding prompt/specification contracts. Revalidate or regenerate affected
   bullet-bank revisions and archetype basis assets using the v3 source fingerprints; do not
   relabel old hashes to force cache hits. Historical render fixtures need not become
   expected output of the corrected generator.

### Acceptance checks for the generator migration

- Real v3 master loads read-only with stable source IDs, 19 normalized units and 80 skills;
  update intentional suppression expectations for the newly eligible team award.
- Skills without recorded project use remain available for skills sections, while arbitrary
  project claims using them are rejected. Explicit Git shared use still works. Alias splitting
  and Epsilon virtual-unit deduplication remain deterministic.
- The AIMLBIO team award appears at most once when selected, with its confirmed year and no
  stale suppression-mapping errors. Random Forest results cannot be assigned to GAN/VAE.
- Both UIUC graduation routes, null omission, confidentiality, deliberate exclusions,
  qualitative outcomes, model/metric bindings and the benchmark-only caveat still pass.
- Update retired v2-specific tests in preflight, models, claims, JD analysis, scoring, skills,
  linting, prompts and cache assets. Run the generator suite and representative generation
  checks before using v3 to produce applications; confirm source bytes remain unchanged.

## Legacy LaTeX/PDF correction log

These eight entries were moved verbatim from `metadata.pending_resume_corrections`.
They describe the old resume; their fixes and the font investigation were **not** performed
or reverified during this migration. They are not facts for generating experience prose.

### Correction 1

```json
{
  "target": "../Resume/resume.tex",
  "issue": "Education reads 'August 2026 - Decemeber 2027'.",
  "correction": "'December'."
}
```

### Correction 2

```json
{
  "target": "../Resume/resume.tex",
  "issue": "The UIUC degree reads 'Master of Computer Science in Computer Science and Engineering' - the field of study is stated twice.",
  "correction": "'Master of Computer Science'."
}
```

### Correction 3

```json
{
  "target": "../Resume/resume.tex",
  "issue": "Heading separators are uneven: no \\quad between the email and the phone, and a trailing \\quad after Github.",
  "correction": "One \\quad between each pair of contacts and none after the last."
}
```

### Correction 4

```json
{
  "target": "../Resume/resume.tex",
  "issue": "The phone number is rendered as '2173051018', without the country code.",
  "correction": "'+1 217 305 1018'."
}
```

### Correction 5

```json
{
  "target": "../Resume/resume.tex",
  "issue": "An Epsilon bullet reads 'primary//secondary indexing' with a doubled slash.",
  "correction": "'primary/secondary indexing'."
}
```

### Correction 6

```json
{
  "target": "../Resume/resume.tex",
  "issue": "A project is titled 'Novel Biomarker Prediction for Lung Cancer Using Random Forest Classifier'.",
  "correction": "The published title is plural: 'Random Forest Classifiers'."
}
```

### Correction 7

```json
{
  "target": "../Resume/resume.tex",
  "issue": "The Aug 2022 - Jan 2023 entry is labelled Epsilon Pvt Ltd but carries Epsilon's content, and the Intel internship is absent entirely.",
  "correction": "Epsilon ran 2022-01 to 2022-06; Intel ran 2022-08 to 2023-01. Both belong on the resume."
}
```

### Correction 8

```json
{
  "target": "../Resume/resume.tex",
  "issue": "The font table declares Helvetica (\\resumefam = phv) but the switch has no effect under Tectonic: the compiled PDF embeds Latin Modern Roman, a serif. Verified by compiling \\usepackage{helvet} with \\renewcommand{\\familydefault}{phv}, and \\usepackage{tgheros} with qhv, under Tectonic 0.17 - both produce LMRoman; \\usepackage{fontspec} fails to build. ../Resume/resume.pdf has the same LMRoman font set, so the resume is serif today.",
  "correction": "Unresolved. Either compile with pdflatex, where helvet works, or find a sans family Tectonic will honour."
}
```
