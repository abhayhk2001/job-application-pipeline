# resume-builder

An end-to-end job-application pipeline. A single role-neutral record of everything Abhay has done is
kept as structured data; a job description is matched against it; and a tailored resume is rendered
to LaTeX and compiled with Tectonic.

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
                       renderer (Python + Jinja2)
                                        │
                                        ▼
                                     .tex ──► tectonic ──► .pdf
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
| `src/resume_builder/` | The Python package: `renderer.py`, `pdf_compiler.py`, `cli.py`, Jinja2 templates. |
| `src/resume_builder/templates/*.tex.j2` | One Jinja2 template per section, plus `resume.tex.j2`. |

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

## Using the renderer

```python
import json
from pathlib import Path
from resume_builder.renderer import render_to_file
from resume_builder.pdf_compiler import compile_pdf

resume = json.loads(Path("rendered.json").read_text())
tex_path = render_to_file(resume, Path("build/resume.tex"))
pdf_path = compile_pdf(tex_path, Path("build"))
```

Or from the CLI:

```bash
resume-render --input tests/fixtures/test_resume.json --out build/resume.pdf
resume-render --input rendered.json               --out build/resume.tex   # TeX only
```

The renderer is deterministic: same JSON → same .tex → same PDF.

## Installing

```bash
brew install tectonic             # one-time; the only external dep beyond Python
pip install -e ".[dev]"           # editable install with pytest + ruff + pypdf
```

The LaTeX target lives in the sibling `../Resume/` project — its static `.tex` sources served as
the reference port into Jinja2 templates here, but the renderer does not read them at runtime; the
templates are self-contained under `src/resume_builder/templates/`.

## Checks

```bash
pytest                            # 38 tests: linkify, latex_escape, per-section, full pipeline
ruff check src tests              # lint
python3 -m json.tool data/master_resume.json > /dev/null && echo OK
python3 -m json.tool tests/fixtures/test_resume.json > /dev/null && echo OK
```

`docs/master-resume.md` carries the check that `data/NEEDS_INPUT.md` is still in sync with
`metadata.needs_input`.
