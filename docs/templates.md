# Templates

A template is a **directory**, not a file. Pick one by name at render time; edit the files in it
whenever you like. The agent that emits resume JSON never writes LaTeX — it names a template, and
the worst it can get wrong is choosing an ugly one.

```bash
resume-render --list-templates                               # the menu
resume-render --list-templates --json                        # the same, for an agent
resume-render -i resume.json -o out.pdf                      # the default: classic
resume-render -i resume.json -o out.pdf --template serif
resume-render -i resume.json -o out.pdf --templates-dir ~/my-templates -t mine
```

Or carry the choice in the resume JSON itself, which is the one-artefact route for an LLM:

```json
{ "template": "serif", "basics": { ... }, "sections": [ ... ] }
```

`--template` beats the JSON key, which beats the default (`classic`). `build_resume` reports what
it actually used as `BuildResult.template`, and `--json` echoes it as `"template"`.

## Where templates are found

Searched in this order, **first match wins** — so a template of yours shadows a built-in of the
same name:

| Order | Directory | Use |
|---|---|---|
| 1 | `--templates-dir DIR` | A directory passed per render. |
| 2 | `templates/` at the repo root | **Yours.** Not tracked by the package; edit freely. |
| 3 | `src/resume_builder/templates/` | Ships with the package: `classic`, `serif`. |

A directory is a template if it holds `resume.tex.j2` and its name does not start with `_` or `.`.
That is what keeps `_shared/` — the inherited section partials — out of the menu.

## Anatomy

```
templates/
  mine/
    template.json      optional: name, description, best_for  (shown by --list-templates)
    resume.tex.j2      required: the preamble and the document skeleton
    experience.tex.j2  optional: overrides the shared partial of the same name
```

Everything a template does not define is inherited from
`src/resume_builder/templates/_shared/`. That is the whole mechanism — the Jinja loader is given
`[<your template>, _shared]` and searches in order — and it is why `serif` is a single file.

`template.json` is optional. A directory with nothing but `resume.tex.j2` works; it just lists
with an empty description.

## Adding one

```bash
mkdir -p templates
cp -r src/resume_builder/templates/classic templates/mine
# edit templates/mine/resume.tex.j2
resume-render -i tests/fixtures/test_resume.json -o /tmp/mine.pdf --template mine
```

The tests pick it up automatically: everything in `tests/test_templates_registry.py` that is
parametrised over discovered templates will now check yours for the macro contract, for rendering
the fixture, and — with Tectonic installed — for compiling to a single page.

## The contract a template must meet

**`resume.tex.j2` receives three variables:**

| Variable | What it is |
|---|---|
| `heading_tex` | The rendered name-and-contacts block. Emit it once, as `{{ heading_tex }}`. |
| `sections_tex` | A list of rendered section blocks, in order. Loop over it. |
| `basics` | The raw `basics` object, if the preamble needs the name (e.g. for PDF metadata). |

Sections arrive **already rendered**, as strings. A template controls the page, not the content of
a section; to change a section's shape, override its partial.

**It must define three macros,** because the shared partials use them and nothing else:

```latex
\newcommand{\resumename}{\Large\scshape}   % the name in the heading
\newcommand{\resumesec}{\Large\scshape}    % section titles
\newcommand{\resumesub}{\small}            % every sub-heading and bullet
```

That contract is what makes inheritance safe across different fonts and geometry, and
`test_every_template_meets_the_macro_contract` enforces it.

**It must load** `hyperref` (bullets contain `\href`), `enumitem` (the lists use
`[leftmargin=..., label={}]`), `titlesec` (`\titleformat{\section}`), `geometry` and `setspace`.

**The section partials** each take one variable, `section`, and expect the shape in
`schemas/rendered_resume.schema.json`:

| Partial | Reads |
|---|---|
| `heading.tex.j2` | `basics.name`, `basics.contacts[].label/.url` |
| `education.tex.j2` | `section.entries[].institution/.location/.qualification/.date` |
| `experience.tex.j2` | `section.entries[].organization/.location/.title/.dateRange/.bullets[]` |
| `projects.tex.j2` | `section.entries[].name/.bullets[]` |
| `skills.tex.j2` | `section.groups[].label/.items[]` |
| `achievements.tex.j2` | `section['items'][]` |

Use `| latex_escape` on every plain field and `| richtext` on prose that may contain markdown
links. Never interpolate a raw string: `25%` or `C_style` is a LaTeX error, and `richtext` is also
what turns `[Paper Link](https://…)` into an `\href`. See `src/resume_builder/url_filters.py` for
why escaping must happen *inside* the link-aware pass rather than before it.

## Choosing a font that actually works

Tectonic is XeTeX, and it **silently falls back to Latin Modern** for the old Type1 NFSS families.
`\usepackage{helvet}` plus `\renewcommand{\familydefault}{phv}` compiles without a warning and
changes nothing — which is exactly what `classic` does, so despite its font table `classic` renders
in Latin Modern, not Helvetica. Packages that ship OpenType faces do take effect; these are
verified on this machine:

| Package | Face |
|---|---|
| `\usepackage{newtxtext}` | Times (TeX Gyre Termes) — what `serif` uses |
| `\usepackage[default]{sourcesanspro}` | Source Sans |
| `\usepackage[default]{FiraSans}` | Fira Sans |
| `\usepackage[default]{roboto}` | Roboto |

A font switch that compiles is not a font switch that happened, so check the embedded fonts rather
than trusting the source:

```bash
python -c "
from pypdf import PdfReader
for p in PdfReader('out.pdf').pages:
    for f in (p['/Resources']['/Font']).values():
        print(f.get_object().get('/BaseFont'))"
```

`test_serif_actually_changes_the_embedded_font` is that check, automated.

## Editing `classic`

`classic` is pinned by `tests/golden/resume.tex` and by the PDF/font-parity assertions in
`tests/test_renderer.py` against `tests/fixtures/resume.pdf`. Changing it will fail those tests by
design. If the change is intended, refresh the golden file:

```bash
python -c "import json; from resume_builder import TEST_RESUME, GOLDEN_TEX; \
from resume_builder.renderer import render; \
GOLDEN_TEX.write_text(render(json.loads(TEST_RESUME.read_text())))"
```

Then read the diff before committing — that diff *is* the review. The parity tests against the
base PDF will still fail, and should be updated or retired deliberately, not worked around.

**If you only want a different look, copy `classic` to a new name instead.** Nothing is pinned to
your own templates, so there is no golden file to refresh and nothing to break.
