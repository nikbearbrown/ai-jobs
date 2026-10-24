# From Syllabus to Vacancy: Faculty-Verified Course Skill Assertions Against Job-Posting Demand

*Draft 0.1, 2026-10-24. Written by CRITIQ in silent mode. This is a registered-report-style proposal: no study has been run. Authorship, faculty reviewers and the IRB question are [NEEDS HUMAN REVIEW].*

## Status box (read this first)

**What this is.** A pre-specified study design to test whether a program can state, with evidence and with each claim reviewed by the teaching faculty member, which job-posting skill requirements its courses address, and which they do not.

**Why it matters.** Course catalogues and job boards use different vocabularies. Today the link is a title-to-course guess (the ai-jobs title families are tied to the 22 seisai.site AI courses by editorial judgment, unvalidated). A claim like "80% of data-engineering postings require AWS" is only meaningful with an explicit numerator and denominator and evidence that the ad *requires* it.

**What exists.** Six local courses and 19 source-linked skill proposals in seis.jobs, none faculty-confirmed; a legacy tag file of 4,274 rows and 81 proposed concepts (none reviewed); a collector that read 84,282 postings on one day but stores ad hashes, not text. **There are no results.** Everything in sections 4 to 6 is a plan.

## Abstract

We propose to measure the alignment between what SEIS courses teach and what employers ask for, in a way that keeps three kinds of evidence separate: what a syllabus says (a span of text), what a faculty member confirms the course teaches and assesses, and what a job posting requires (a span of ad text, classified as required, preferred, responsibility or mention). Skills are drawn from a typed, versioned concept graph so that related tools are not counted as synonyms. The primary outcome is the share of required skills, in a pre-registered sample of postings for a target role, that are asserted and assessed by at least one confirmed course. We pre-specify the comparison to a title-only baseline and the conditions under which the approach would be judged no better than that baseline.

## 1. Introduction

**Territory.** Programs are asked to show that curricula match labour-market demand.
**Niche.** Existing practice is (a) matching course titles to job titles, which this project currently does editorially, or (b) keyword counts over postings, which count mentions rather than requirements and cannot say what a course teaches. A syllabus listing a topic is also not evidence that students were assessed on it, and a course asserting a skill is not evidence an individual student has it.
**Research questions.**
- **RQ1.** For a target role, what share of required skills in postings is asserted by a faculty-confirmed course, and at what taught depth and assessment level?
- **RQ2.** Does the skill-level alignment rank courses for a target role differently from the title-family mapping?
- **RQ3.** How often do automated syllabus and posting extractions disagree with faculty and human annotators?

**Hypotheses.**
- **H1.** Skill-level alignment ranks courses differently from the title-family mapping for at least some target roles, because titles hide skills (a course titled for one area may assert a skill required in another). *Falsified if* the two rankings are indistinguishable across all target roles tested [ASSUMPTION: a rank-correlation statistic and a threshold to be fixed before analysis].
- **H2.** Extraction disagreement is larger for abstract skills (methods, practices) than for named tools and languages. *Falsified if* error rates do not differ by concept type.

## 2. Related work

[NEEDS HUMAN REVIEW: no literature search has been done. Topics to search: curriculum-to-labour-market alignment, skill extraction from job postings, syllabus analysis, competency frameworks. No citation is offered here as evidence.]

## 3. Design

### 3.1 Sources
- **Courses and syllabi.** The authoritative SEIS catalogue and rosters must be acquired; coverage is reported as a denominator (all catalogue courses, syllabi available, parsed, faculty-reviewed). Term, section and instructor are part of course identity. Syllabi are stored with a hash and version; restricted text is linked, not redistributed.
- **Postings.** From the ai-jobs collector, for pre-selected target roles. The collector keeps only a hash of each ad, so ad text must be fetched again or stored under an explicit decision about copying companies' ads [ASSUMPTION]. Postings are deduplicated and the countable-description denominator is reported.
- **Skills.** The typed concept graph from the skills-taxonomy paper; unmapped is a legal state.

### 3.2 Assertions
*Course assertions:* canonical skill, literal syllabus phrase and span, taught depth, prerequisites, assessment, extraction confidence, review state. Review states: inferred, proposed, faculty-confirmed, disputed, stale. A syllabus change makes earlier approvals stale; approvals do not transfer between instructors or terms.
*Job assertions:* skill, evidence span, required/preferred/responsibility/mention, negation, OR-alternatives, and how an OR contributes (full, fractional or set membership).

### 3.3 Measures
- **Alignment (primary):** among required-skill assertions in the sampled postings for a role, the share matched by a faculty-confirmed course assertion with an assessment. Numerator, denominator and exclusions (unmapped, suppressed, no description) are always reported.
- **Gap list:** required skills with no confirmed course.
- **Title-family baseline:** the course sets implied by `data/titles/titles.json` (27 families to 22 courses).
- **Extraction error:** precision and recall against faculty-labelled syllabus samples and human-annotated posting samples, by concept type and source format.

### 3.4 Sample and roles
Target roles are chosen before any alignment is computed. [ASSUMPTION: start with a small number of SEIS-relevant families such as data engineering, ML engineering and AI engineering, because those have the most courses in the 22 listed.] For each role, a random sample of postings from one collection day is drawn with the sampling frame stated; with one day of data the study cannot speak to change over time.

## 4. Analysis plan (fixed before data are examined)

1. Compute alignment per role with the count definitions above; report the full table of unmapped terms.
2. Compare course rankings from skill alignment and from the title mapping (H1).
3. Estimate extraction error by concept type (H2).
4. Sensitivity: treat OR-alternatives under each of the three weightings and report whether conclusions change.
No composite "job readiness" score is computed.

## 5. Threats to validity

- **Faculty burden and selection.** Only reviewed courses can count; if reviewers are few, alignment is biased toward the courses whose instructors engage.
- **Visible market only.** Postings come from employers with a public ATS board (about 28% of listed employers, tilted to technology), so alignment describes that slice.
- **Mentions vs requirements.** Misclassifying a preferred skill as required inflates the gap list.
- **Taught is not learned.** A confirmed assertion shows coverage, not student mastery; no claim about graduates' skills follows.
- **One day of postings** and a small number of roles limit generalisation.

## 6. Ethics

Student work, rosters and resumes never enter the public dataset. Faculty review needs consent and an audit trail; no emails or invitations are sent by the tooling without a person's action. No claim that a course guarantees a job.

## 7. CRITIQ self-review (silent mode)

1. **[CRITICAL] No literature and no data.** Both are prerequisites for a reviewer to take the question seriously. *Fix:* a literature search, then a pilot on one role and two courses.
2. **[CRITICAL] The primary outcome depends on faculty confirmation that does not yet exist** (0 of 19 proposals confirmed). *Fix:* secure at least two faculty reviewers before registering the plan.
3. **[MAJOR] Ad-text policy undecided**; extraction cannot start without it.
4. **[MAJOR] H1 has no threshold.** Set the statistic and the minimum difference now.
5. **[MINOR] Define "assessment"** so a project that uses a skill incidentally does not count.

**What works.** Three evidence types stay separate; every count carries its numerator and denominator; the baseline is stated and can win.

## Sources

seis.jobs `docs/course-skills-analysis.md`, `docs/skills-taxonomy.md`, `data/courses/public-catalog.json`; ai-jobs `data/courses.json`, `data/titles/titles.json`, `docs/canonical-form.md`.
