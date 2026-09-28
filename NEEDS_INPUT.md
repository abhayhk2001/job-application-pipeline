# Open Questions — `master_resume.json`

**Last updated:** 2026-09-26 · **1 open · 21 resolved**

This file is the human-facing mirror of `metadata.needs_input` in `master_resume.json`, and it is kept
current: the moment a question is answered or otherwise resolved it moves from **Open** to the
**Resolved log**, and any new gap introduced while editing the master resume is added to **Open**. The
two should never disagree — if `metadata.needs_input` has an entry, there is an open block for it here.

Question numbers are stable and never reused, so `Q17` means the same thing in any conversation.

## How to answer

Type inside the fenced block under a question. Prose is fine — it gets normalized into the right field
and type.

- **Don't know / doesn't exist / don't want it on the resume?** Write `SKIP`. The field is deleted and
  the question closes for good.
- **Partial is fine.** Blank blocks stay open; nothing is invented to fill them.
- **Don't edit the `Field` lines** — they're the mapping back into the JSON.

Priority reflects how much a gap blocks resume generation. **High** means a resume can't be written
correctly without it.

---

# Open (1)

### Q21 — Best Presentation conference · Medium
**Field:** `award.best-presentation`
**Asks:** At which conference did the team receive the Best Presentation award for the NSCLC paper, and in what year?
**Known:** A judge commended the clarity of the explanation and its graph/diagram support. The award went to the team, not to you individually.
**Format:** `Conference name, year`

```

```

---

# Resolved log

21 questions, all answered 2026-09-25 and merged the same day. Answers below are condensed; the
verbatim originals are in the git history at commit `9d2850a`.

## A. Identity and contact

| # | Question | Answer | Applied |
|---|---|---|---|
| Q01 | Current location | Champaign, IL, USA | `basics.location` set |
| Q02 | Work authorization | F-1 student — must not appear on the resume | `basics.work_authorization` set; hard rule added to `metadata.confidentiality` and `presentation_preferences` |
| Q03 | Extra profile links | LinkedIn + GitHub are enough; a future portfolio replaces GitHub | `basics.profiles_policy` added; no new profiles |

## B. Employment chronology

| # | Question | Answer | Applied |
|---|---|---|---|
| Q04 | Qualcomm promotion month | Jan 2025; not needed on the resume, space is tight | Associate Engineer `2023-01`→`2024-12`, Software Engineer from `2025-01`; `award.qualcomm-promotion` dated; collapse-to-one-line preference recorded |
| Q05 | Epsilon team and manager | Neither — it was an exploratory project | `work.epsilon.team` = null with a note |

## C. Publications

| # | Question | Answer | Applied |
|---|---|---|---|
| Q06 | Paper titles, authors, years | Pull from ORCID `0009-0001-8017-4400`; exclude the 4th paper | All three filled from ORCID + DOI metadata: titles, full author lists, author positions, venues, volumes, pages, DOIs, ISBNs. IEEE Access 2025 paper logged in `metadata.deliberate_exclusions` |
| Q07 | Citation count | 51 | `proj.nsclc-biomarkers` citations metric = 51, `as_of: 2026-09` |

## D. Project dates

| # | Question | Answer | Applied |
|---|---|---|---|
| Q08, Q09, Q10, Q11, Q12, Q14 | Dates for NSCLC, document extraction, RCoT, Samsung, DIET, Redis+SQLite (one answer covered all six) | Not needed — they cost space, and projects should be ordered by relevance to the job, not chronologically | All six `period.start`/`period.end` left null with an explanatory note; `duration_stated` and `academic_stage` retained. Ordering rule recorded in `metadata.presentation_preferences` |
| Q13 | AR education website dates | *Sidenote:* the AR website and the DIET Ramanagara work are the same thing | **Merged** into `proj.diet-ramanagara` (AR website, teacher workshops, animated content, RAG lesson generation all now one project). `proj.ar-education-website` deleted; skills `evidence_refs` retargeted |

## E. Project details

| # | Question | Answer | Applied |
|---|---|---|---|
| Q15 | Document extraction sponsor | SCII | `proj.document-extraction.organization` set to SCII, cleared for public use |
| Q16 | Intel benchmark scale | Correct | 1.8 GB / 100,000 records confirmed; `needs_input` marker removed |
| Q17 | Naming the EV manufacturer | Abstract both — private info | Both customer identities withheld. Project id renamed `work.intel.ather-telemetry` → **`work.intel.ev-telemetry`** because the id itself leaked the name. Only "an electric vehicle manufacturer" and "a national stock exchange" remain in the file |
| Q18 | Hackathon names | Not required — achievements are lowest priority | Gap closed as intentionally untracked; achievements-droppable-first rule recorded |
| Q19 | SCII collaboration | It's the document extraction project, funded and overseen by SCII | `collaborating_organizations.notes` records it; linked to `proj.document-extraction` |
| Q20 | Silkworm selective breeding | Remove from the data lake | `proj.silkworm-breeding` deleted; reference pulled from the computational-biology domain; logged in `metadata.deliberate_exclusions` so it can't return |

## F. Awards and affiliations

| # | Question | Answer | Applied |
|---|---|---|---|
| Q22 | Dhruva division lead dates | August 2021 – August 2022 | `affil.dhruva` `2021-08` → `2022-08` |

---

## Note on two field paths

Answers to **Q16** and **Q17** referenced `work.intel.ather-telemetry.*`; that project is now
`work.intel.ev-telemetry`. **Q13** referenced `proj.ar-education-website.period`, which no longer
exists — that project was merged into `proj.diet-ramanagara`.
