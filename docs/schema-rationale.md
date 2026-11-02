# Structured Knowledge Representation via Extended JSON
Professional experience is stored as a structured data object rather than in a vector store, because retrieval can lose context. The format extends the open-source JSON Resume Schema with the detail an agent needs when it reads a career history.
Strict structure guides the LLM through the candidate's history without the ambiguity of raw text. The data lives in one version-controlled file, the "career data lake".

## Schema Section

1. Core Identity (basics)
Contains fundamental identity markers, contact information, and multiple generalized summaries. The agent leverages this section to select the most appropriate summary variation based on the cultural and technical tone of the target job description.

2. Professional Chronology (work)
An array of objects detailing companies, titles, dates, and an array of granular projects. This hierarchical organization prevents the LLM from conflating tasks across different employers and preserves the timeline required for Applicant Tracking Systems (ATS).

3. Granular Experience (projects)
Sub-objects within the work array containing technical descriptions, technologies_used, outcomes, and metrics. This lets the agent pick relevant projects and write bullet points for the target role.

4. Competency Matrix (skills)
Categorized arrays detailing languages, frameworks, cloud infrastructure, and soft skills. This section enables deterministic keyword matching against the target job description.

5. Agentic Directives (metadata)
Generation directives, presentation preferences, and confidentiality rules. These tell the agent what it may state and what must stay abstracted. Ordering and fields carry no emphasis per role.


The whole JSON object can be placed in the LLM's context, so the agent sees the complete record.