# Master Resume — `master_resume.json`

The career data lake for the job-application pipeline. It is the **single source of truth** about
Abhay Harish Kashyap's professional history, and it is injected wholesale into the context of the
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
| `education` | RVCE and UIUC, with coursework, standing and MOOC record |
| `work` | Three employers, each with `positions[]` (title history) and nested `projects[]` |
| `projects` | Seven non-employment engagements: research, industry collaborations, hackathon, volunteering, coursework |
| `publications` | Three papers with full titles, author lists and DOIs, cross-linked via `project_ref` |
| `awards` | Six entries, cross-linked via `project_ref` |
| `affiliations` | Club and division leadership |
| `collaborating_organizations` | Named partner organizations |
| `skills` | Competency matrix, every skill carrying `evidence_refs` |
| `metadata` | Directives, confidentiality rules, presentation preferences, deliberate exclusions, gaps, pending resume corrections |

Every object with an `id` can be cross-referenced. `evidence_refs`, `project_ref`, `publication_ref`
and `award_ref` all point at those ids.

## Confidence and evidence

The file is self-contained — it no longer references the recommendation letters, statement of purpose
or prior resumes it was built from. What remains is the candidate-confirmed record.

A field carries `confidence: "needs_input"` when its value is `null` or incomplete; a matching
question sits in `metadata.needs_input`. Anything without that marker is confirmed.

All figures have been reconciled with the candidate, so there are no competing variants left in the
file. Where reconciliation changed a number that the live LaTeX/PDF resume still shows,
`metadata.pending_resume_corrections` records what that resume needs fixed.

Skills use a separate axis: `evidenced` (demonstrated by a specific engagement, see `evidence_refs`)
versus `listed_only` (claimed on the prior resume, but nothing recorded here demonstrates it).
`listed_only` skills may appear in a skills section but must never generate an experience bullet.

## Rules for the generating agent

Spelled out in `metadata.generation_directives`. In short: synthesize, never copy verbatim; never
state a `null` or use a `needs_input` metric unchecked; never present `stated_interests` as
accomplishments; and obey `metadata.confidentiality` — Qualcomm client names stay abstracted as
"two major clients", and Intel customer names need the candidate's clearance before appearing
publicly.

## Extending it

Add a new engagement as an object under `work[].projects[]` (if it happened at an employer) or under
`projects[]` (if it did not), reusing the same field shape. Give it a stable `id` and reference it
from any relevant `skills[].evidence_refs`.

The invariant: **every metric, date and named entity is either candidate-confirmed, or it is `null`
with a matching `metadata.needs_input` entry.** Nothing is inferred.

## Open questions

`metadata.needs_input` holds **one** remaining question: the conference where the NSCLC paper won its
Best Presentation award. `NEEDS_INPUT.md` carries the filled-in worksheet as the record of the other
21 answers.

`metadata.pending_resume_corrections` lists three things the live resume in `../Resume/` gets wrong
and that this file now supersedes.

## Two metadata blocks the generator must honour

`metadata.presentation_preferences` — layout rules the candidate set: order projects by relevance and
never chronologically, omit project dates, collapse the Qualcomm entry to one line when space is
tight, drop the achievements section first, never print work authorization, and treat a future
portfolio link as a replacement for GitHub rather than an addition.

`metadata.deliberate_exclusions` — content that must never be reintroduced: a fourth publication
(IEEE Access, 2025) that exists on ORCID but is excluded by choice, and a removed project.

Validate after any edit:

```bash
python3 -m json.tool master_resume.json > /dev/null && echo OK
```
