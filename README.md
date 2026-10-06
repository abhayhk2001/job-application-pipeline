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
                         rendered resume JSON  ◄── contract: docs/render-contract.md
                                        │          schema:   schemas/rendered_resume.schema.json
                                        ▼
                          validate  ──► exit 3 + path: message
                                        │          (the LLM's feedback loop)
                                        ▼
                       renderer (Python + Jinja2)  ◄── template: docs/templates.md
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
| `docs/render-contract.md` | **The page to paste into a tailoring prompt.** The exact JSON an LLM must emit. |
| `docs/templates.md` | How templates work: picking one, editing one, writing one. |
| `schemas/rendered_resume.schema.json` | Machine-readable version of that contract; what `--validate-only` checks. |
| `tests/fixtures/test_resume.json` | A rendered resume in render-ready form — the renderer's **input contract**. |
| `tests/fixtures/resume.pdf` | The base resume's compiled PDF, used for format-parity assertions. |
| `tests/golden/resume.tex` | Expected render of the fixture. Generated, never hand-edited. |
| `src/resume_builder/` | The Python package: `api.py`, `validation.py`, `renderer.py`, `pdf_compiler.py`, `cli.py`. |
| `src/resume_builder/templates/<name>/` | One directory per template (`classic`, `serif`): its `resume.tex.j2` and any partial it overrides. |
| `src/resume_builder/templates/_shared/` | The section partials every template inherits unless it overrides one. |
| `templates/` (repo root) | Your own templates. Shadow a built-in by using its name. Optional; absent by default. |

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

One function does the work. Everything else is a shell over it.

```python
import json
from pathlib import Path
from resume_builder.api import build_resume

resume = json.loads(Path("custom_resume.json").read_text())
result = build_resume(resume, Path("build"))
print(result.tex_path, result.pdf_path)
```

`build_resume` validates first and raises `ValidationError` carrying every problem, so malformed
JSON can never reach LaTeX. Pass `tex_only=True` to skip Tectonic entirely — that path is pure
Python.

From the CLI:

```bash
resume-render --list-templates                               # the available templates
resume-render -i custom_resume.json --validate-only --json   # check, write nothing
resume-render -i custom_resume.json -o build/resume.pdf      # validate, render, compile
resume-render -i custom_resume.json -o build/resume.tex      # TeX only, no Tectonic
resume-render -i custom_resume.json -o build/resume.pdf -t serif   # pick a template
```

Exit codes: `0` success, `1` render/compile failure, `2` missing or unparseable input or an unknown
`--template`, `3` invalid resume JSON. On `3`, each problem prints as `path: message` with `path` a JSON Pointer — that is the
feedback an LLM iterates against. See `docs/render-contract.md`.

The renderer is deterministic: same JSON → same `.tex` → same PDF. `tests/golden/resume.tex` pins
that, and `tests/test_renderer.py` asserts the compiled PDF reads identically to the hand-written
`../Resume/resume.pdf` apart from a short, explicit list of defects in the base that we decline to
reproduce.

## Templates

A template is a directory, not a file, and the LaTeX format is no longer hardcoded:

```bash
resume-render --list-templates
  classic  Dense single-column Latin Modern, small-caps rule-underlined section headings.
  serif    The classic layout set in Times; same geometry and spacing, traditional type.
```

Choose one with `--template serif`, or carry the choice in the resume JSON as a top-level
`"template": "serif"` — the flag wins if both are given. **That string is the entire surface an
LLM needs**; it never writes LaTeX, so it cannot produce a document that fails to compile.

Add your own by copying one into `templates/` at the repo root and editing it:

```bash
cp -r src/resume_builder/templates/classic templates/mine
resume-render -i custom_resume.json -o build/resume.pdf -t mine
```

A template owns the preamble (`resume.tex.j2`) and inherits the six section partials from
`templates/_shared/`, so a variant that only changes fonts or margins is one file. The full
contract — the three macros a preamble must define, the variables it receives, and which font
packages actually take effect under Tectonic — is in **`docs/templates.md`**.

## Serving it (not built yet)

If the tailoring LLM is remote rather than a local agent, wrap `build_resume` rather than
reimplementing it:

- **A plain `POST /render` fits serverless better than MCP.** MCP is the right shape for *LLM calls a
  tool* and gives typed schemas across clients, but a tool result is content blocks — a PDF has to be
  base64 or a resource link, and 25 KB of PDF is ~34 KB of base64, roughly 8.5k tokens of bytes the
  model cannot read. Return a reference, not the artefact, whatever the transport. MCP's
  streamable-HTTP transport also carries session state, which is friction on a stateless function.
  Build the REST route first; an MCP tool is then a ~40-line adapter over the same function.
- **The deployment risk is Tectonic, not the protocol.** The binary is 19 MB and its package cache
  after rendering this resume is 57 MB, fetched from the network on first run. Ship a **container
  image**, not a zip: Lambda zip caps at 250 MB unzipped with a 512 MB `/tmp`, and a cold start that
  downloads a TeX bundle will time out. Lambda container or Cloud Run are both comfortable at a
  ~250-350 MB image. Pre-bake the cache and point `TECTONIC_CACHE_DIR` at it so no invocation
  reaches the network; verify by building with networking disabled.
- **Output location stays at the edge.** `BuildResult.pdf_path` is a local path today. When object
  storage arrives, one function at the edge maps it to a URL — no renderer or template change.

## Installing

```bash
brew install tectonic             # one-time; the only external dep beyond Python
pip install -e ".[dev]"           # editable install with pytest + ruff + pypdf
```

The LaTeX target lives in the sibling `../Resume/` project — its static `.tex` sources served as
the reference port into Jinja2 templates here, but the renderer does not read them at runtime; the
templates are self-contained under `src/resume_builder/templates/`, one directory per template.

## Checks

```bash
pytest                            # linkify, latex_escape, per-section, templates, full pipeline
ruff check src tests              # lint
python3 -m json.tool data/master_resume.json > /dev/null && echo OK
python3 -m json.tool tests/fixtures/test_resume.json > /dev/null && echo OK
```

`docs/master-resume.md` carries the check that `data/NEEDS_INPUT.md` is still in sync with
`metadata.needs_input`.
