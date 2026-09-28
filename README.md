# resume-builder

An end-to-end job-application pipeline. A single role-neutral record of everything Abhay has done is
kept as structured data; a job description is matched against it; and a tailored resume is rendered
to LaTeX and compiled.

```
                data/master_resume.json          job description
                   (the data lake)                     │
                          │                            │
                          └────────────┬───────────────┘
                                       ▼
                              tailoring (LLM)
                                       │
                                       ▼
                        rendered resume JSON  ◄── contract shown by
                                       │          tests/fixtures/test_resume.json
                                       ▼
                              renderer (Python)
                                       │
                                       ▼
                                    .tex ──► pdflatex ──► .pdf
```

## Layout

| Path | What it is |
|---|---|
| `data/master_resume.json` | The career data lake. Atomic facts, never bullet prose, never tuned to a role. |
| `data/NEEDS_INPUT.md` | Living worksheet mirroring `metadata.needs_input`. One question open. |
| `docs/master-resume.md` | The schema contract: what each section holds and the rules a generator must obey. |
| `docs/schema-rationale.md` | Why the data lake is structured JSON rather than vector retrieval. |
| `tests/fixtures/test_resume.json` | A rendered resume in render-ready form — the renderer's **input contract**. |
| `tests/fixtures/resume.pdf` | The PDF that fixture was captured from, verbatim, typos included. |
| `src/resume_builder/` | The Python package. Currently resolves paths only. |

## The two JSON shapes

They are deliberately different and must not be conflated.

**`data/master_resume.json`** is the *input* to tailoring. Every engagement is decomposed into
`situation`, `constraints`, `actions[]`, `technologies_used[]`, `metrics[]` and `outcomes[]`. There is
no `bullets` field anywhere, and ordering carries no emphasis.

**A rendered resume** — shaped like `tests/fixtures/test_resume.json` — is the *output*. Ordered
`sections`, each entry carrying finished bullet strings plus a `source_ref` back to the master id it
was drawn from. This is what the TeX renderer consumes.

Two metadata blocks in the master bind the renderer:
`metadata.presentation_preferences` (omit project dates, order projects by relevance, achievements
section drops first, never print work authorization) and `metadata.confidentiality` (client
identities stay abstracted).

## Building the renderer

Put the JSON-to-TeX conversion in `src/resume_builder/`. `__init__.py` already resolves the project
paths, so a module can do:

```python
from resume_builder import TEST_RESUME, MASTER_RESUME
```

Add a CLI entry point under `[project.scripts]` in `pyproject.toml` when there is one. Install for
development with:

```bash
pip install -e .
```

The LaTeX target lives in the sibling `../Resume/` project — `resume.tex` includes
`src/{heading,education,experience,projects,skills,achievements}.tex` and `custom-commands.tex`
defines `\resumeSubheading`, `\resumeItem` and friends. Note that those `.tex` sources are stale:
`data/master_resume.json` supersedes them, and `metadata.pending_resume_corrections` says how.

## Checks

```bash
python3 -m json.tool data/master_resume.json > /dev/null && echo OK
python3 -m json.tool tests/fixtures/test_resume.json > /dev/null && echo OK
```

`docs/master-resume.md` carries the check that `data/NEEDS_INPUT.md` is still in sync with
`metadata.needs_input`.
