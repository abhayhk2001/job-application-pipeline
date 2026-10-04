# Render contract

The JSON an LLM must produce to get a PDF out of this repo. Paste this page into the tailoring
prompt, together with `data/master_resume.json` and the job description.

## The loop

```
read data/master_resume.json + the job description
          │
          ▼
write custom_resume.json            ← the shape below
          │
          ▼
resume-render -i custom_resume.json --validate-only --json
          │
          ├── exit 3 → fix the reported paths, repeat
          │
          ▼ exit 0
resume-render -i custom_resume.json -o build/resume.pdf --json
          │
          ▼
{"ok": true, "pdf_path": "...", "tex_path": "..."}
```

Exit codes are the signal: `0` success, `1` render or LaTeX failure, `2` missing file or unparseable
JSON, `3` the JSON is invalid. On `3`, every problem is printed as `path: message`, where `path` is a
JSON Pointer into the document you submitted. Fix those paths and re-run.

The authoritative shape is `schemas/rendered_resume.schema.json`. It sets
`additionalProperties: false` everywhere, so an invented field is an error rather than something
silently dropped — if you think a field should exist and it doesn't, the answer is that the renderer
has nowhere to put it.

## Shape

```json
{
  "basics": {
    "name": "Abhay Harish Kashyap",
    "contacts": [
      { "type": "email",    "label": "abhayhk2001@gmail.com", "url": "mailto:abhayhk2001@gmail.com" },
      { "type": "phone",    "label": "+1 217 305 1018",       "url": null },
      { "type": "linkedin", "label": "Linkedin",              "url": "https://www.linkedin.com/in/abhay-h-kashyap/" },
      { "type": "github",   "label": "Github",                "url": "https://github.com/abhayhk2001" }
    ]
  },
  "sections": [
    {
      "type": "education",
      "heading": "Education",
      "entries": [
        {
          "source_ref": "edu.uiuc",
          "institution": "University of Illinois Urbana-Champaign",
          "location": "Champaign, USA",
          "qualification": "Master of Computer Science",
          "date": "August 2026 - December 2027"
        }
      ]
    },
    {
      "type": "experience",
      "heading": "Work Experience",
      "entries": [
        {
          "source_ref": "work.qualcomm",
          "organization": "Qualcomm India Private Limited",
          "location": "Bengaluru, India",
          "title": "Software Engineer",
          "dateRange": "January 2023 - July 2026",
          "bullets": ["Designed and delivered a production-ready SoC upgrade framework ..."]
        }
      ]
    },
    {
      "type": "projects",
      "heading": "Project Experience",
      "entries": [
        {
          "source_ref": "proj.document-extraction",
          "name": "Business Documents Data Recognition and Table Extraction using Deep Learning Techniques",
          "bullets": [
            "Integrated DETR-based table extraction and YoloV5 object detection ...",
            "Presented at ICAIC 2025. [Paper Link](https://rdcu.be/wZSePwoXqLVa)"
          ]
        }
      ]
    },
    {
      "type": "skills",
      "heading": "Skills",
      "groups": [
        { "label": "Programming Languages", "items": ["Python", "Java", "C/C++"] }
      ]
    },
    {
      "type": "achievements",
      "heading": "Achievements",
      "items": ["Led the data-driven astronomy research division at Dhruva, RVCE's astrophysics club"]
    }
  ]
}
```

`tests/fixtures/test_resume.json` is a complete, valid, rendering example of exactly this.

## Section types

| `type` | Collection | Required per item |
|---|---|---|
| `education` | `entries` | `institution`, `location`, `qualification`, `date` |
| `experience` | `entries` | `organization`, `location`, `title`, `dateRange`, `bullets` |
| `projects` | `entries` | `name`, `bullets` |
| `skills` | `groups` | `label`, `items` |
| `achievements` | `items` | plain strings |

`sections` is **ordered** — it is the order the sections print in. Every section needs a `heading`,
which is the printed title. `source_ref` is optional everywhere but worth setting: it names the
`data/master_resume.json` id a line was drawn from, which is how a reviewer traces a claim back.

## Writing bullets

Bullets and achievement items are **plain strings**, never objects. Write finished resume prose:
start with a verb, keep one idea per line, carry the metric.

Links are markdown: `[Paper Link](https://rdcu.be/wZSePwoXqLVa)` renders as an underlined
hyperlink reading *Paper Link*. A bare URL also works and renders as its own label, but a label reads
better and costs less width. An empty target (`[Paper Link]()`) is a validation error.

Do not write LaTeX. `%`, `&`, `$`, `#`, `_`, `{`, `}` are escaped for you, and URLs are escaped by
different rules than prose, so hand-escaping actively breaks things.

## Rules inherited from the master

Two `metadata` blocks in `data/master_resume.json` bind what you may produce:

- **`presentation_preferences`** — order projects by relevance to the job and never
  chronologically; omit project dates; a single collapsed Qualcomm entry is preferred when space is
  tight; drop the achievements section first when space runs out; never print work authorization; and
  treat a future portfolio link as a replacement for the GitHub link rather than an addition.
- **`confidentiality`** — the two Intel customer identities are withheld; refer to them only as
  "an electric vehicle manufacturer" and "a national stock exchange". Qualcomm clients stay
  abstracted as "two major clients". Validation enforces this against an optional local denylist at
  `data/confidential_terms.txt`, which is gitignored so the names never enter version control.

Also honour `metadata.deliberate_exclusions`: one publication and one project are excluded by
choice and must not reappear.

## One page

The resume must stay on one page; the test suite asserts it. If content overflows, cut by the
`presentation_preferences` order — achievements first, then the least relevant project — rather than
shrinking type.
