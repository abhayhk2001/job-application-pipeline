# resume-builder

Validates a render-ready resume JSON against a schema and renders it to LaTeX and PDF using Jinja2 and [Tectonic](https://tectonic-typesetting.github.io/). It is the rendering step of a job-application pipeline; [`resume_generator`](../resume_generator/) calls it in-process, and this repository also holds the career data that the generator reads.

```
rendered resume JSON  (contract: docs/render-contract.md, schema: schemas/rendered_resume.schema.json)
        │
        ▼
validate  ──► exit 3 + path: message
        │
        ▼
renderer (Python + Jinja2)  (templates: docs/templates.md)
        │
        ▼
      .tex ──► tectonic ──► .pdf
```

## Install

Requires Python 3.10+ and Tectonic (`brew install tectonic`, or see its install docs).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
resume-render --warmup      # once per machine: lets Tectonic download its TeX packages
```

Install it editable: the schema lives at the repository root, outside the package, so a non-editable install cannot validate.

## Usage

These assume the virtual environment is active. To try them, copy the fixture: `cp tests/fixtures/test_resume.json custom_resume.json`.

```bash
resume-render --list-templates                               # the available templates
resume-render -i custom_resume.json --validate-only --json   # check, write nothing
resume-render -i custom_resume.json -o build/resume.pdf      # validate, render, compile
resume-render -i custom_resume.json -o build/resume.tex      # TeX only, no Tectonic
resume-render -i custom_resume.json -o build/resume.pdf -t serif   # pick a template
```

`resume-builder` is the one-shot command: `custom_resume.json` becomes `custom_resume.pdf` in the same directory. The intermediate `.tex` goes to a temporary directory unless you pass `--workdir`.

```bash
resume-builder -i custom_resume.json            # -> custom_resume.pdf, next to the input
resume-builder -i custom_resume.json --json     # machine-readable
resume-builder -i custom_resume.json -t serif   # pick a template
resume-builder -i custom_resume.json --workdir build/   # keep the intermediate .tex
```

`python -m resume_builder render ...` and `python -m resume_builder build ...` run the same two commands, and `render` is the default.

From Python:

```python
import json
from pathlib import Path
from resume_builder.api import build_resume

resume = json.loads(Path("custom_resume.json").read_text())
result = build_resume(resume, Path("build"))
print(result.tex_path, result.pdf_path)
```

`build_resume` validates first and raises `ValidationError` carrying every problem. Pass `tex_only=True` to skip Tectonic.

Each compile is killed after 60 seconds and reported as `CompileTimeoutError` with exit code `1`. Change that with `--compile-timeout SECONDS`, or `build_resume(..., compile_timeout_seconds=...)` from Python.

Exit codes: `0` success, `1` render or compile failure, `2` missing or unparseable input or an unknown `--template`, `3` invalid resume JSON. On `3`, each problem prints as `path: message`, with `path` a JSON Pointer. See `docs/render-contract.md`.

The same JSON always renders to the same `.tex`; `tests/golden/resume.tex` pins that, and `tests/test_renderer.py` checks the compiled PDF against `tests/fixtures/resume.pdf` apart from a short list of known defects in that base.

## Templates

A template is a directory holding a `resume.tex.j2` preamble and any section partial it overrides; the rest are inherited from `templates/_shared/`. The built-ins are `classic` and `serif`.

Choose one with `--template serif`, or set a top-level `"template": "serif"` in the resume JSON. The flag wins if both are given.

Add your own by copying one into `templates/` at the repository root, or point `--templates-dir` at another directory:

```bash
mkdir -p templates
cp -r src/resume_builder/templates/classic templates/mine
resume-render -i custom_resume.json -o build/resume.pdf -t mine
```

The full contract is in `docs/templates.md`.

## Configuration

| Setting | Effect |
| :--- | :--- |
| `data/confidential_terms.txt` (gitignored, one term per line, `#` comments) | Validation rejects bullets and items containing these terms. If the file is absent, the check does not run. |
| `RESUME_CONFIDENTIAL_TERMS` | Path that replaces the file above. |

## Layout

| Path | What it is |
| :--- | :--- |
| `data/master_resume.json` | The career data lake: the author's real, role-neutral record, read by `resume_generator`. |
| `data/NEEDS_INPUT.md` | Worksheet mirroring `metadata.needs_input`. |
| `docs/` | The data lake contract (`master-resume.md`, `schema-rationale.md`), the JSON an LLM must emit (`render-contract.md`) and how templates work (`templates.md`). |
| `schemas/rendered_resume.schema.json` | The machine-readable contract `--validate-only` checks. |
| `src/resume_builder/` | `api.py` (`build_resume`), `validation.py`, `renderer.py`, `jinja_env.py`, `url_filters.py`, `templates_registry.py`, `pdf_compiler.py`, `cli.py`, `exceptions.py`. |
| `src/resume_builder/templates/` | One directory per built-in template, plus the shared partials in `_shared/`. |
| `tests/fixtures/test_resume.json` | A rendered resume in render-ready form. |
| `tests/golden/resume.tex` | Expected render of that fixture. Generated, never hand-edited. |

The master file and the rendered resume are different shapes. `data/master_resume.json` decomposes each engagement into situation, actions, metrics and outcomes and has no bullets. A rendered resume has ordered `sections` of finished bullets, each with a `source_ref` back to its master id.

## Development

```bash
pytest
ruff check .
ruff format --check .
```

`docs/master-resume.md` has a check that `data/NEEDS_INPUT.md` is in sync with `metadata.needs_input`.

`resume_generator` hashes `jinja_env.py`, `url_filters.py` and every `.j2` file into its render profile, so any byte change to them, even a comment, gives a different profile.

## Limitations

- The tracked data lake and test fixtures hold the author's personal details. They are not sample data.
- The confidentiality check covers bullets and achievement items only, and is silently off without a terms file.
- Tectonic's first run needs network access to download packages.

## License

MIT. The `classic` template's layout credit is in its source. See [LICENSE](LICENSE).
