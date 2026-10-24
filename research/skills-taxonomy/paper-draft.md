# A Typed, Versioned Concept Graph for Skills: Linking Courses, Job Postings and Learners Without Collapsing Distinctions

*Draft 0.1, 2026-10-24. Written by CRITIQ in silent mode from the project files listed under Sources. Working title and author list are [NEEDS HUMAN REVIEW].*

## Status box (read this first)

**What this is.** A design-and-evaluation-plan paper (a "registered report" shape) for the SEIS skills taxonomy: a graph of typed skill concepts with scoped aliases and broader/narrower edges, built so that course syllabi, job postings and student evidence can be compared without merging things that are only related.

**Why it matters.** Every claim of the form "80% of these jobs need AWS" or "this course teaches Docker" depends on what counts as the same skill. The legacy tag list has no IDs or definitions, and the standards that could anchor it (ESCO, O*NET, SFIA, CaSS, ACSF) differ in scope.

**What exists today (measured, 2026-10-24).** 4,274 legacy tag rows preserved; 81 proposed concepts in the registry, all `proposed`, none reviewed; 3 concepts have a relation; **0 have an external-standard mapping**. There is therefore **no result yet**: the paper's findings section is a pre-specified plan, not data.

**What is locked and what is not.** Locked: the design principles and the legacy-data counts. Not locked: the hierarchy itself (see 3.4), the evaluation thresholds, the reviewers, the authors.

## Abstract

Skills labels are ambiguous (Swift, Oracle, Apache), versioned (PHP 7), and typed differently by different sources (Ajax filed as a language, a degree filed as a skill). Matching courses to jobs on raw labels therefore inflates or hides demand. We describe a governed concept graph for the SEIS programs in which every concept has an immutable ID, a type, a definition and scoped aliases; related, broader and narrower concepts are separate edges rather than synonyms; and every job or course claim is an assertion with evidence, not a tag. We start from a legacy file of 4,274 tags and a proposed registry of 81 concepts across 15 types, and we pre-specify how the design will be evaluated: false-merge rate on regression fixtures, coverage of phrases extracted from real postings, reviewer agreement on merge/split/alias decisions, and the effect of the graph on demand counts relative to flat tag normalisation. No evaluation results are reported because none exist yet.

## 1. Introduction

**Territory.** Skills-based matching of learners, courses and vacancies needs a shared vocabulary. Public standards exist: O\*NET (occupations with abilities, skills, knowledge, work activities and software skills), ESCO (a multilingual European classification of skills, competences, qualifications and occupations), SFIA (IT skills), CaSS (an open framework for documenting competencies) and ACSF (Australian core literacy and numeracy skills) [AI4ED Personalized Co-op and Job Pathway System, README].

**Niche.** Two problems remain. First, the standards have different units and levels of granularity: BLS publishes 17 aggregate skill categories derived from O\*NET, which are useful reporting groups but "not a granular tool/language ontology" [seis.jobs docs/skills-taxonomy.md], and O\*NET occupation importance is not personal proficiency. Second, our own legacy file, `Skills_Tags.csv`, has 4,274 rows with only `Tag` and `Class`, no stable IDs, definitions or provenance, and 20 case-insensitive duplicate pairs including conflicting classifications.

**Prior design in this project.** The AI4ED job-pathway design proposes consolidating ESCO, O\*NET, SFIA, CaSS and ACSF into one unified ontology, vectorising skills (TF-IDF or embeddings) in a vector database and matching individuals to jobs by similarity with thresholds. This paper takes a more conservative position: keep concepts typed and distinct, and let similarity propose candidate links for human review rather than create them.

**Research questions.**
- **RQ1.** Does a typed graph with context-scoped aliases make fewer false merges than flat normalisation of tag strings?
- **RQ2.** Does representing related tools as broader/narrower/related edges, instead of synonyms, change demand counts for a skill, and in which direction?
- **RQ3.** Can independent reviewers agree on alias, merge and split decisions well enough for the graph to be maintained by more than one person?

**Hypotheses (each names a mechanism and can fail).**
- **H1.** Flat normalisation merges distinct concepts that share a label (Swift the language vs Swift the organisation; Angular vs AngularJS) and so produces false merges that scoped aliases avoid. *Falsified if* the false-merge rate on the regression fixtures is not lower for the graph than for the flat baseline.
- **H2.** Treating a related tool as a synonym of a skill inflates that skill's demand count (a posting asking for OpenTelemetry is counted as asking for observability). *Falsified if* counts under synonym-merge and under edge-based counting differ by less than reviewer noise [ASSUMPTION: noise level to be measured in RQ3 before this test is run].
- **H3.** Reviewer agreement on merge/split/alias decisions is high for programming languages and tools and low for methods and abstract skills. *Falsified if* agreement does not differ by concept type.

## 2. Background and sources

All source facts below are from files in this project; none was re-fetched for this draft.
- O\*NET database 31.0 is described as current at the parent's research check; the release must be pinned per import. In 30.3 the dictionary renamed Technology Skills to Software Skills and changed field names, so adapters must be version-specific.
- BLS skills data: 17 aggregate categories derived from O\*NET (2024 methodology article).
- O\*NET is released under CC BY 4.0 with attribution, version and modification notice; other standards need their own rights check.
- Published O\*NET crosswalks exist; a SOC/O\*NET occupation mapping is not an exact skill mapping.

**Literature to locate before submission** (named from memory; none is cited as evidence in this draft; [VERIFY] each): work on skills taxonomies and skills-based hiring; ESCO documentation; Polanyi on tacit knowledge is relevant to *Abilities* papers, not this one. [NEEDS HUMAN REVIEW: a real literature search on skill ontology alignment, entity linking and job-posting skill extraction is required; this draft contains none.]

## 3. Design

### 3.1 Concept record
Immutable internal ID; canonical name; definition; concept type; domains; context-scoped aliases with ambiguity flags; status and version; source evidence; review and replacement history. Types in the current registry (counts below) include skill, method, knowledge, programming-language, library, framework, markup-language, modeling-language, style-language, human-language, platform, tool, credential, organization and ability. Occupations live in a separate namespace.

### 3.2 Aliases and relations
Aliases are lexical equivalences *in context*; one label can refer to more than one concept. Broader, narrower and related relations are separate edges. Examples proposed for review: C Sharp to C# (alias, original row preserved); PHP 7 as a version-specific concept under PHP; XML as markup language and UML as modeling language (neither a general programming language); Ajax reclassified as a method; AngularJS kept distinct from Angular; Observability and OpenTelemetry related but not synonymous.

### 3.3 External mappings and assertions
An external mapping records source, version, ID, relation (exact, close, broader, narrower, related), direction, evidence, reviewer and confidence; "unmapped" is a legal state. Job assertions carry the exact evidence span, required/preferred/responsibility class, negation and OR-alternatives; course assertions carry mentioned/taught/practised/assessed/prerequisite and depth; student evidence is separate. Counts must say whether an OR requirement contributes full, fractional or set-membership weight.

### 3.4 The hierarchy (open design question)
[ASSUMPTION: "skills taxonomy hierarchy" means layered broader/narrower structure over the typed concepts; confirm with Professor Bear.] Three candidate sources of hierarchy exist and are not yet reconciled:
1. BLS's 17 aggregate skill categories as top-level reporting groups.
2. The O\*NET content-model domains (abilities, skills, knowledge, work activities) as the upper structure for human capacities, which the Explorer already uses for abilities.
3. Local broader/narrower edges for tools and methods that O\*NET does not model (frameworks, libraries, practices such as guardrails or LLM observability).

The open question is whether one tree can hold all three, or whether the graph should keep them as separate views over the same concepts. The draft's position is the second, because a tool (React) has a broader language (JavaScript) and a broader practice (front-end development) at once.

### 3.5 Evolution
Unknown terms enter a candidate queue (literal phrase, source span, context, frequency, ambiguity). A reviewer chooses alias, new concept, related concept or noise. Merge: survivor ID plus redirect. Split: new child IDs; ambiguous old assertions are queued, not copied. Retired IDs are never reused. Historical references replay under their original taxonomy version.

## 4. Current state of the data (measured 2026-10-24)

| Measure | Value | Source |
|---|---|---|
| Legacy rows | 4,274 (Skill 3,725; Certification 401; Language 148) | `data/skills/import-manifest.json` |
| Legacy file SHA-256 | `b00ae7dbe30c7e6a8ac52c7d891984d07f6cdd61dfabe7be691072239cdceb43` | same |
| Case-insensitive duplicate groups | 20 | same |
| Proposed canonical concepts | 81 (registry version `2026-10-24.proposed.2`) | `data/skills/registry.json` |
| Concepts by type | skill 24, method 16, knowledge 12, programming-language 11, library 4, framework 3, markup-language 2, credential 2, and one each of ability, platform, modeling-language, human-language, organization, tool, style-language | same |
| Review status | 81 of 81 `proposed` | same |
| Concepts with at least one relation | 3 | same |
| Concepts with an external-standard mapping | 0 | same |
| Concepts linked to legacy rows | 14 | same |

**Inconsistency to resolve** [NEEDS HUMAN REVIEW]: the registry's `scope` string and an older note say "36 proposed canonical concepts"; the registry file and the README now say 81. Use 81 (the file) until the owner confirms.

## 5. Evaluation plan (pre-specified; nothing below has been run)

**Data.** (a) The 4,274 legacy tags. (b) Job postings: the ai-jobs collection holds 84,282 open postings from 715 boards on 2026-10-24, but it stores a hash of each ad and not the text, so skill extraction needs the ad text re-fetched or stored under a decision about copying companies' ads [ASSUMPTION]. (c) SEIS syllabi: six local courses, 19 source-linked skill proposals, none faculty-confirmed.

**Measures.**
- *False-merge rate* on regression fixtures (C#, PHP 7, AngularJS vs Angular, Swift, CPC), graph vs flat baseline (H1).
- *Coverage*: share of skill phrases extracted from a stratified sample of postings that map to a concept, an alias, or an explicit "unknown" (and the queue length).
- *Demand count difference* for a pre-selected set of skills under synonym-merge vs edge-based counting, with numerator and denominator stated for each (H2). A posting counts only if the ad text supports a *requirement*, not a mention.
- *Reviewer agreement*: at least two reviewers on a stratified sample of proposed alias/merge/split decisions, reported by concept type (H3). Statistic: Cohen's kappa [ASSUMPTION: confirm the reviewer count and statistic].

**Thresholds.** Not set. They must be written down before the reviewers or the postings sample are looked at, otherwise H1 to H3 cannot fail. [NEEDS HUMAN REVIEW]

## 6. Threats to validity

- **No results yet.** The paper cannot support a causal or comparative claim today.
- **Reviewer scarcity.** One taxonomy owner is not a reviewer panel; RQ3 needs at least a second person.
- **Posting sample bias.** The ai-jobs boards are tilted to technology employers (about 28% of 2,574 companies have a readable public board; the rest are on systems not yet read), so coverage measured on them will overstate how well the graph handles other sectors.
- **Alias drift.** Scoped aliases protect against false merges at the cost of more concepts; the queue could grow faster than review.
- **Standards licensing.** Only O\*NET's licence is checked here; ESCO, SFIA, CaSS and ACSF terms are not.

## 7. Ethics

Demographic and non-skill attributes found in the legacy file are quarantined, never used as matching features. Student evidence stays separate from course assertions; a course asserting a skill is not evidence of student mastery. Private attachments and student data do not enter public routes.

## 8. CRITIQ self-review (silent mode)

1. **[CRITICAL] No data.** Until at least H1 has a result this is a design note. *Fix:* run the regression fixtures against a flat baseline first; it needs no new data and no reviewers. *Why:* it is the cheapest result that can falsify the paper's central claim.
2. **[CRITICAL] Related work is absent.** The literature section is a placeholder by design (no fabricated citations). *Fix:* a real search on skill extraction, entity linking and skill ontology alignment before drafting further.
3. **[MAJOR] The hierarchy is undefined.** Section 3.4 states three sources and no decision. *Fix:* decide tree vs views, then restate RQ2 around it.
4. **[MAJOR] Thresholds unset**, so H1 to H3 are not yet falsifiable.
5. **[MINOR] 36 vs 81 concepts** inconsistency in the repo.

**What works.** The design refuses silent synonymy, keeps original rows, makes "unmapped" legal, and ties every count to a numerator and denominator.

## Sources (all in this repository tree)

- `books/seis.jobs/docs/skills-taxonomy.md`, `skill-reconciliation.md`, `course-skills-analysis.md`
- `books/seis.jobs/data/skills/registry.json`, `import-manifest.json`
- `books/AI4ED/Personalized_Co-op_and_Job_Pathway_System/README.md` (`Semesterization/README.md` also lists ESCO and O\*NET)
- ai-jobs collection summary: `data/jobs/2026-10-24/summary.json`
