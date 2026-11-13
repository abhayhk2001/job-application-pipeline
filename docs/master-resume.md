# Master Resume — `data/master_resume.json`

The career record for the job-application pipeline. It is the **single source of truth** about
the candidate's professional history, and it is injected wholesale into the context of the
agent that writes each job-specific resume.

It is a biography, not a pitch.

## The two rules that shape the file

**1. Facts, not bullets.** Nothing in this file is a resume line. Each engagement is decomposed into
`situation`, `constraints`, `actions[]`, `technologies_used[]`, `metrics[]` and `outcomes[]`. The
downstream generator recombines those atoms into bullets sized and angled for the target job. There
is deliberately no `highlights` or `bullets` field anywhere.

**2. Role-neutral.** No section is ordered by importance and no directive says "emphasize X for ML
roles." Tailoring happens at generation time against a specific job description, not here.

## Structure

| Key | What it holds |
|---|---|
| `schema` | Version, purpose, and the hard rules above |
| `basics` | Identity, contacts, three length-variant summaries, stated interests |
| `education` | Two institutions, with coursework, standing and MOOC record |
| `work` | Three employers, each with `positions[]` (title history) and nested `projects[]` |
| `projects` | Six non-employment engagements: lung-cancer research, document extraction, RCoT, Samsung instant apps, a misinformation-detection hackathon project, and the Unifrost Drona startup platform (with optional `technical_details`) |
| `publications` | Three papers with full titles, author lists and DOIs, cross-linked via `project_ref` |
| `awards` | Four entries, cross-linked via `project_ref` |
| `affiliations` | Club and division leadership |
| `collaborating_organizations` | Named partner organizations |
| `skills` | Eleven categories containing 145 skills, each with a name and optional factual note |
| `metadata` | Generation directives, confidentiality rules, maintenance instructions, presentation preferences, and deliberate exclusions |

Every object with an `id` can be cross-referenced. `project_ref`, `publication_ref` and `award_ref`
point at those ids; a rendered resume can retain a `source_ref` back to its source record.

The `abhay-master-resume/v3` extension (version `3.0.0`) stores the following text lists as arrays
of strings:

- `work[].projects[].actions[]` and `projects[].actions[]`
- `work[].working_practices[]`
- `basics.stated_interests.items[]`

For example, use `"actions": ["Implemented the upgrade solution."]`. Keep these lists as strings
when adding entries.

Project `outcomes[]` entries containing only outcome text are also strings. Keep an outcome object
when it carries additional metadata, such as `award_ref` or a note. Coursework retains its existing
object structure, including course names and notes.

### UIUC coursework

The UIUC entry (`id: edu.uiuc`) in [the master record](../data/master_resume.json) contains five
course names supplied by the candidate. Titles are recorded as provided, without inferred
course codes, dates, grades or completion status.

### RVCE coursework

The RVCE entry (`id: edu.rvce`) in [the master record](../data/master_resume.json) contains
28 selected course names from RVCE's Consolidated Grade Card for Bachelor of Engineering
(`Transcript.pdf`). The selection omits all first- and second-semester courses and the additional
courses excluded by the candidate. Entries retain official course titles and existing factual
notes; course codes, semesters, credits and grades are not stored. The separate NPTEL courses
remain under `mooc`.

### How coursework reaches a resume

Each course is `{name, display?, note?}`. `name` is the recorded title and the source of the
course's stable ID (`<education id>.<slug of name>`), so renaming a course changes its ID.
`display` is an optional shorter or clearer title written by the candidate (for example
`"Computer Security"` for `"Computer Security 1"`); when set it is the only text printed.
`note` is private context and is never printed.

For each tailored job, `resume_generator` asks the LLM whether a "Relevant Coursework" line helps,
which 2–5 courses to list, and whether the line is worth more than a project's second bullet when
the page is full. The LLM chooses IDs only; the printed titles come from this file.

## Authoritative facts and skills

The file is self-contained and holds only candidate-confirmed facts. Add confirmed information
directly; resolve questions with the candidate before recording new facts. Unavailable or
intentionally omitted details may remain `null`. Never infer a date, measurement or named entity
to fill an empty field. An unquantified outcome can still be described qualitatively.

Each skills category is an array of objects with a required `name` and an optional factual `note`:

```json
{
  "name": "Shell scripting",
  "note": "Self-taught; no project use is recorded."
}
```

Every listed skill is confirmed and may appear in a relevant skills section. General competency
does not establish use in a particular engagement. Experience and project bullets must draw from
that engagement's recorded technologies and activities, with explicit shared facts applied only
within their stated scope. Factual notes retain limits such as self-taught skills and AWS usage
where only Amazon S3 is named.

Both UIUC graduation alternatives remain valid: December 2027 and May 2028. The existing instruction
selects the date based on the role. Summaries describe current enrollment in the Master of Computer
Science program. The AIMLBIO 2022 Best Presentation award belongs to the team; GAN/VAE exploration
is separate from the published Random Forest results; the RCoT metric is 50% faster than ProbSpace.

## Rules for the generating agent

Spelled out in `metadata.generation_directives`. In short: synthesize, never copy verbatim; never
invent values to fill a `null`; keep skill use scoped to its engagement; never present `stated_interests` as
accomplishments; and obey `metadata.confidentiality`, which keeps withheld client and customer names abstracted.

## `tests/fixtures/test_resume.json` — the output-shape fixture

`data/master_resume.json` is the input to generation; `tests/fixtures/test_resume.json` is a worked example of the
**output**: ordered `sections`, each entry carrying finished bullet prose and a `source_ref` back to
the master id it was drawn from. It is the one place in this project where bullet strings are allowed.

Its content follows the hand-written base resume (`tests/fixtures/resume.pdf`) so that the
format-parity test in `tests/test_renderer.py` is meaningful. Unambiguous typographic defects in the base are corrected
there (`_meta.fixed_from_base`); substantive content errors are reproduced and logged
(`_meta.deviations_from_master`). It is **not** a correct resume and must not be used as the expected
output of a generator reading the corrected master.

The render-ready shape itself is specified by `schemas/rendered_resume.schema.json` and explained for
an LLM in `docs/render-contract.md`.

## Extending it

Add a new engagement as an object under `work[].projects[]` (if it happened at an employer) or under
`projects[]` (if it did not), reusing the same field shape. Give it a stable `id`, record its
`technologies_used`, and add relevant general skills as objects with a name and optional factual note.

The invariant: **every stated metric, date and named entity is candidate-confirmed.** Unavailable
details may be omitted or left `null`; nothing is inferred.

## Two metadata blocks the generator must honour

`metadata.presentation_preferences` — layout rules the candidate set: order projects by relevance and
never chronologically, omit project dates, collapse the main employer entry to one line when space is
tight, drop the achievements section first, never print work authorization, and treat a future
portfolio link as a replacement for GitHub rather than an addition.

`metadata.deliberate_exclusions` — content that must never be reintroduced: a fourth publication
(IEEE Access, 2025) that exists on ORCID but is excluded by choice, and a removed project.

## Compatibility and validation

The sibling `resume_generator` reads the v3 contract (migrated 2026-11-05). The
[migration handoff](master-resume-migration.md) describes the completed changes and preserves all
eight legacy LaTeX/PDF correction notes.
Those historical corrections do not belong in the career record.

Validate after any edit:

```bash
python3 -m json.tool data/master_resume.json > /dev/null && echo OK
pytest tests/test_master_resume.py
```
