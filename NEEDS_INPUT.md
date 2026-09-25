# Open Questions — MERGED 2026-09-25

> **Status: 21 of 22 answered and merged into `master_resume.json`.**
> Your answers are preserved below as the record of what was applied. Only **Q21 (Best Presentation
> conference)** is still open — it was left blank and remains the single entry in
> `metadata.needs_input`. Fill that block and hand it back when you have it.
>
> Publication details for Q06 came from your ORCID record (`0009-0001-8017-4400`) and DOI metadata.
> The IEEE Access paper is recorded in `metadata.deliberate_exclusions` so it is never re-added.

---

22 gaps in `master_resume.json`. Each one corresponds to an entry in
`metadata.needs_input` and to a field that is currently `null` or incomplete.

## How to fill this in

Type your answer inside the fenced block under each question. Prose is fine — I'll
normalize it into the right shape and field type.

- **Don't know / doesn't exist / don't want it in the resume?** Write `SKIP`. I'll delete the
  field and its `needs_input` entry so it stops being an open question.
- **Partial answers are fine.** Answer what you can and leave the rest empty; empty blocks stay
  open and nothing is invented to fill them.
- **Don't edit the `Field` lines** — that's how I map your answer back into the JSON.

When you're done, tell me and I'll merge everything into `master_resume.json`, clear the resolved
`needs_input` entries, and report anything still outstanding.

Priority reflects how much it blocks resume generation: **High** means a resume can't be written
correctly without it.

---

## A. Identity and contact

### Q01 — Current location · High
**Field:** `basics.location`
**Asks:** What city and country should the resume show as your current location?
**Format:** `City, Region, Country` — e.g. `Champaign, IL, USA` or `Bengaluru, India`

```
`Champaign, IL, USA`
```

### Q02 — Work authorization · Medium
**Field:** `basics.work_authorization`
**Asks:** What US work authorization status should applications assume? This drives the
"are you authorized to work" questions on application forms, not the resume body.
**Format:** Free text — e.g. `F-1 student, CPT/OPT eligible from <date>`, or `SKIP` to leave it out

```
F-1 Student, but make sure it is not in the resume
```

### Q03 — Extra profile links · Low
**Field:** `basics.profiles`
**Asks:** Do you want a personal website, Google Scholar profile or portfolio added alongside
LinkedIn and GitHub?
**Format:** One `Label: URL` per line, or `SKIP`

```
No Linkedin and Github is enough, when I make a personal portfolio, I will attach it instead of GitHub
```

---

## B. Employment chronology

### Q04 — Qualcomm promotion month · High
**Field:** `work.qualcomm.positions[1].startDate`
**Asks:** In which month and year were you promoted from Associate Engineer to Software Engineer?
**Why it matters:** The Qualcomm entry currently shows two titles with no boundary between them,
so neither can be dated on a resume.
**Format:** `YYYY-MM` — e.g. `2023-07`

```
I was promoted in Jan 2025. But such detail is not required in the resume as there isnt that much space.
```

### Q05 — Epsilon team and manager · Low
**Field:** `work.epsilon.team`
**Asks:** Which team or product did you work on at Epsilon, and who was your manager?
**Format:** Free text, or `SKIP`

```
No manager and product, it was a explorative project. 
```

---

## C. Publications

### Q06 — Paper titles, authors and years · High
**Field:** `publications[*].name`
**Asks:** The exact title and author list for each of the three papers, plus publication years
for the Cancer Informatics and JAIT papers. All three titles are currently `null`, so no
publications section can be generated.
**Format:** One block per paper, like:

```
Cancer Informatics:
  title:
  authors:
  year:

JAIT (RCoT):
  title:
  authors:
  year:

ICAIC 2025 (document extraction):
  title:
  authors:

Can you extract the required stuff from my orcid profile page ?
https://orcid.org/0009-0001-8017-4400

There is a 4th publication which should not be included.
```

### Q07 — Citation count · Low
**Field:** `proj.nsclc-biomarkers.metrics.citations`
**Asks:** Current citation count for the Cancer Informatics paper, and the date you checked.
The file records "10 in two years" with no as-of date, so it can't be used as-is.
**Format:** `<count> as of <YYYY-MM>`, or `SKIP`

```
51
```

---

## D. Project dates

All seven are `null`. Approximate is fine — `Spring 2022`, `late 2021`, a semester, or just a year
all work. Write `SKIP` on any you'd rather leave undated.

### Q08 — NSCLC biomarker project · Medium
**Field:** `proj.nsclc-biomarkers.period`
**Known:** Ran roughly six months during your junior year.

```
Project dates are not necessary, as it consumes space and I want to order them not chronologically but more based on relvance to the job.
```

### Q09 — Document extraction project · Medium
**Field:** `proj.document-extraction.period`

```
Project dates are not necessary, as it consumes space and I want to order them not chronologically but more based on relvance to the job.
```

### Q10 — RCoT / HPCC Systems · Medium
**Field:** `proj.rcot-hpcc.period`
**Known:** Started around your third semester.

```
Project dates are not necessary, as it consumes space and I want to order them not chronologically but more based on relvance to the job.
```

### Q11 — Samsung SRIB instant-apps worklet · Medium
**Field:** `proj.samsung-instant-apps.period`

```
Project dates are not necessary, as it consumes space and I want to order them not chronologically but more based on relvance to the job.
```

### Q12 — DIET Ramanagara · Medium
**Field:** `proj.diet-ramanagara.period`
**Known:** Six months total, including three months of stakeholder coordination.

```
Project dates are not necessary, as it consumes space and I want to order them not chronologically but more based on relvance to the job.
```

### Q13 — AR education website · Low
**Field:** `proj.ar-education-website.period`
**Known:** Third year of undergrad.

```
Sidenote : AR education website and DIET ramnagara work are the same. 
```

### Q14 — Redis + SQLite cache · Low
**Field:** `proj.redis-sqlite-cache.period`
**Asks:** Which semester was the Database Design course project?

```
Project dates are not necessary, as it consumes space and I want to order them not chronologically but more based on relvance to the job.
```

---

## E. Project details

### Q15 — Document extraction sponsor · Medium
**Field:** `proj.document-extraction.organization`
**Asks:** Which organization sponsored the invoice/business-document extraction project? It's
currently recorded only as "an industry-driven project". If it's the SCII collaboration in Q18,
say so and I'll link them.
**Format:** Organization name, plus whether you can name them publicly

```
It is SCII.
```

### Q16 — Intel benchmark scale · High
**Field:** `work.intel.ather-telemetry.metrics`
**Asks:** Was the 100,000-record / 1.8 GB figure the real benchmark scale for the Intel telemetry work? You withdrew the 80% parsing claim that sat next to it, so this number needs confirming
before it's used.
**Format:** `Confirmed`, a corrected scale, or `SKIP` to drop the metric

```
It is correct. 
```

### Q17 — Naming the EV manufacturer · High
**Field:** `work.intel.ather-telemetry.client`
**Asks:** Two things — is it spelled `Ather` or `Aether`, and are you permitted to name them on a
public resume? Same question for the National Stock Exchange. If not, the fallbacks stay
"an electric vehicle manufacturer" and "a national stock exchange".
**Format:** e.g. `Ather — OK to name` / `Abstract both`

```
Abstract the names as they will be private info
```

### Q18 — Hackathon names · Medium
**Field:** `proj.blockchain-misinformation`
**Asks:** Names and dates of the two national hackathons you won, and a public certificate or
repository link if one exists.
**Format:** One per line: `Name — date — link`

```
Not required, achievements section will be the least priority. 
```

### Q19 — SCII collaboration · Low
**Field:** `collaborating_organizations`
**Asks:** Your old resume listed SCII among your collaborations but nothing records what it was.
What was it, and which project does it belong to?
**Format:** Free text, or `SKIP` to drop SCII from the list

```
This is the document data extractiona and business document analysis project. It was funded and overseen by SCII company.
```

### Q20 — Silkworm selective breeding · Low
**Field:** `proj.silkworm-breeding`
**Asks:** What exactly did you contribute, and when? This is currently a one-line entry with no
technical detail, no dates and no outcome — too thin to use. Worth filling in or deleting.
**Format:** Free text, or `SKIP` to remove the project entirely

```
Remove this project from the data lake. 
```

---

## F. Awards and affiliations

### Q21 — Best Presentation conference · Medium
**Field:** `award.best-presentation`
**Asks:** At which conference did the team receive the Best Presentation award for the NSCLC
paper, and in what year?
**Format:** `Conference name, year`

```

```

### Q22 — Dhruva division lead dates · Low
**Field:** `affiliations.affil.dhruva`
**Asks:** Which years did you lead the data-driven astronomy research division at Dhruva?
**Format:** `YYYY-MM to YYYY-MM`, or just the academic years

```
I led it from August 2021 - AUg 2022. 
```
