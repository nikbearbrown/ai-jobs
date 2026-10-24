# What the Abilities Cannot See: An Occupation Explorer for the Human Layer of AI Exposure

*Draft 0.1, 2026-10-24. Written by CRITIQ in silent mode from the project files listed under Sources. Working title, author order and every item marked [NEEDS HUMAN REVIEW] need a human decision. Builders credited on the live tool: Abisha Vadukoot, Milivoje (Mickey) Davidovic, Nik Bear Brown.*

## Status box (read this first)

**What this is.** A paper about the AI Exposure Explorer (https://www.irreducibly.xyz/onet): what it shows, what the O\*NET Abilities data it is built on cannot show, and a pre-specified plan for version 2 that adds the missing layer from data the project already holds.

**Why it matters.** The Explorer compares two occupations on employment (BLS, indexed 2018 = 100, against AI milestones) and on 52 O\*NET Abilities. For Graphic Designers vs. Carpenters the Abilities view makes the carpenter look like the "physical" job and the designer like the "cognitive" one, which is the intuitive story, and the audit data below suggest the picture changes when decision weight is added.

**What was found so far.** From a read-only database audit dated 14 August 2026 (one occupation pair, n = 8 raters per occupation on the Skills ratings): Skills descriptors do not separate the pair; Work Context descriptors separate it sharply and in the opposite direction from the intuitive story. This is a single pair and an audit, not a result. See 4.

**What is blocked or unverified (as of the 2026-10-24 seis.jobs audit).** No per-ability AI-tier map has been verified. The employment-weighted ability-demand pipeline and its CSV were not located. The AIOE comparison needs a SOC crosswalk and its repository has no licence file.

## Abstract

Occupation-level exposure measures typically rest on what workers must be able to do. The AI Exposure Explorer compares two occupations on 52 O\*NET Abilities and on BLS employment, and states on the page that the capacities hardest for AI to replicate sit largely above what those measures capture. We ask what a first measurement of that layer looks like using only government data the project already holds: the O\*NET Skills, Work Context and Work Styles files released alongside Abilities. In a read-only audit of the project's database, Skills descriptors were nearly flat across Graphic Designers and Carpenters (differences of 0.00 to 0.38 on a 5-point scale, n = 8 per occupation), while Work Context descriptors separated them: Consequence of Error was 3.80 for Carpenters and 2.00 for Designers, and Freedom to Make Decisions favoured Designers (4.10 vs 3.63). We propose version 2 features, each with a stated caveat, and pre-specify tests that could show the added layer is redundant with Abilities. We report no population-level result.

## 1. Introduction

**Territory.** Task- and ability-based measures of occupational exposure to automation and AI are widely used. One is the AI Occupational Exposure (AIOE) index of Felten, Raj and Seamans (2021, *Strategic Management Journal* 42(12): 2195-2217), built on O\*NET ability data of an older release (24.3 per the paper).

**Niche.** Ability data describe what an occupation requires of a worker. They contain no category for the selection judgment that protects an experienced designer from a tool that can generate ten options, and none for knowledge held by a group or for standards internal to a craft. The Explorer's own page says so; it does not yet measure any of it.

**Gap and contribution.** The project already holds Skills, Work Context and Work Styles data from the same O\*NET release. We (1) document what that data does and does not separate for a test pair, (2) map every O\*NET element in use to the seven dimensions of the Center for Curriculum Redesign's tacit-knowledge framework (Van Damme and Fadel, 2026) with a stated confidence, making the unmeasured dimensions visible, and (3) specify version 2 features and their tests.

**Research questions.**
- **RQ1.** Across all rated occupations, do Work Context decision-weight descriptors (Consequence of Error, Frequency of Decision Making, Impact of Decisions, Freedom to Make Decisions) carry information not already carried by the Abilities profile?
- **RQ2.** Do Skills descriptors such as Critical Thinking and Complex Problem Solving separate occupations, or are they uniformly high?
- **RQ3.** Which of the seven tacit-knowledge dimensions have no O\*NET proxy, and does that gap persist after adding every ingested domain?

**Hypotheses.**
- **H1 (RQ1).** Consequence of Error is not reducible to the physical and psychomotor Abilities: after those are controlled for, it still varies across occupations. *Falsified if* the variance in Consequence of Error is largely explained by the Abilities profile.
- **H2 (RQ2).** Critical Thinking and Complex Problem Solving have low between-occupation spread relative to their mean. *Falsified if* their spread is comparable to that of the Abilities items.
- **H3 (RQ3).** Social/collective and normative/identity-related remain without a proxy that measures the dimension itself, because O\*NET's unit of analysis is the incumbent worker. *Falsified if* a descriptor exists whose definition refers to group-held knowledge or to practice-internal standards of good work.

## 2. The tool and its data

**Architecture.** A server-rendered Next.js page; D3 charts in client components; the selected pair lives in the URL (`?soc=A,B`) so every view is shareable; data come from a Neon Postgres database via internal API routes. Source: design notes, `docs/onet-occupation-explorer-design-notes.md`.

**Chart 1.** BLS employment indexed to 2018 = 100 for two occupations, with AI milestones. **Chart 2.** O\*NET Abilities on the Level (LV) scale, 0 to 7, in four tabs (cognitive 21 elements, psychomotor 10, physical 9, sensory 12; 52 in all, all `1.A.*`).

**What else is in the database** (read-only audit, 14 August 2026): 16 tables; 894 occupations with ratings (1,016 occupations listed); ability rows 92,976; skills 62,580; knowledge 59,004; work activities 73,308; work context 49,170; work styles 37,422; BLS employment 20,540 rows. Skills, Work Context and Work Styles are ingested but not shown on any chart. These counts are from that audit, not from a current query, and the audit itself could not establish the release identity of the ability ratings [NEEDS HUMAN REVIEW: re-run the audit script (SELECT-only) before citing counts].

## 3. Method (for the findings in section 4 and the tests in section 6)

The audit queried the database with SELECT-only statements for two SOC codes, Graphic Designers (27-1024) and Carpenters (47-2031), on the importance scale (Skills, 1 to 5) and the Work Context CX scale (1 to 5). Work Styles values use a `WI` scale of unconfirmed meaning and were not compared numerically. The audit script (`scripts/audit-onet-tacit.mjs`) and its raw output (`audit-output.txt`) are in the Irreducibly-Human repository.

## 4. What the audit found (one pair; descriptive only)

**Skills (importance, 1 to 5, n = 8 per occupation).**

| Element | Designers | Carpenters |
|---|---|---|
| Critical Thinking (2.A.2.a) | 3.25 | 3.38 |
| Complex Problem Solving (2.B.2.i) | 3.12 | 3.00 |
| Judgment and Decision Making (2.B.4.e) | 3.12 | 3.00 |
| Systems Analysis (2.B.4.g) | 2.88 | 2.50 |
| Systems Evaluation (2.B.4.h) | 2.62 | 2.62 |

Differences of 0.00 to 0.38, one pointing toward Carpenters. With n = 8 these are not distinguishable from noise; they are reported to show that adding Skills to Chart 2 would draw two overlapping lines for this pair.

**Work Context (CX scale, 1 to 5).**

| Element | Designers | Carpenters |
|---|---|---|
| Consequence of Error (4.C.3.a.1) | 2.00 | 3.80 |
| Impact of Decisions on Co-workers or Company Results (4.C.3.a.2.a) | 3.25 | 4.37 |
| Frequency of Decision Making (4.C.3.a.2.b) | 3.26 | 4.22 |
| Freedom to Make Decisions (4.C.3.a.4) | 4.10 | 3.63 |

The carpenter's work carries more consequence, more frequent decisions and more impact on others; the designer's single advantage is discretion. Accountability and autonomy come apart. This inverts the reading Chart 2 currently invites, and is the observation that motivates the "Judgment and stakes" tab. It is one pair. It says nothing about how designers or carpenters in general compare, and it does not show that Consequence of Error measures a protective human capacity rather than occupational hazard.

**Work Styles.** In the revised taxonomy (`1.D.*`, 21 elements) Tolerance for Ambiguity was 1.33 for Designers and 0.06 for Carpenters; Independence, named in earlier planning, is not in the revised taxonomy. The seis.jobs importer describes the Work Styles source as AI/expert-rated rather than an incumbent survey, with no sample size or interval fields; these numbers are therefore not comparable to Skills or Work Context and are not used for inference [NEEDS HUMAN REVIEW: confirm with the O\*NET Scales Reference before any chart].

## 5. Mapping to the tacit-knowledge framework (editorial, not validated)

Van Damme and Fadel (Center for Curriculum Redesign, June 2026) name seven dimensions: articulability, embodied, cognitive/interpretive, social/collective, material/embedded, narrative/communicative, normative/identity-related. The 14 August audit proposed the following proxies; the seis.jobs project holds a separate, later interpretation with reasons. Neither is a measurement.

| Dimension | Best O\*NET proxy (audit) | Audit confidence |
|---|---|---|
| Embodied | psychomotor, physical, sensory Abilities | High |
| Cognitive/interpretive | Judgment and Decision Making, Critical Thinking, Complex Problem Solving | High as a construct, low as a discriminator (Skills were flat) |
| Material/embedded | Degree of Automation (4.C.3.b.2), software skills | Medium |
| Social/collective | Empathy, Cooperation and related Work Styles; social skills | Medium for interaction, low for collective |
| Articulability | Tolerance for Ambiguity (Work Styles) | Low to medium |
| Narrative/communicative | Instructing, Training and Teaching Others; Job Zone | Low (the training and experience domain is not ingested) |
| Normative/identity-related | Integrity, Dependability (traits of an incumbent) | Low; effectively un-proxied |

The structural limit, stated by the audit: O\*NET is built from articulated self-report, so the framework's core variable (what cannot be articulated) is the instrument's blind spot. The page should show the un-proxied dimensions rather than let their absence read as coverage.

## 6. Version 2 features and their tests (nothing below is built in the live tool)

1. **"Judgment and stakes" tab** next to the four Abilities tabs, using the Work Context items on their native 1 to 5 scale (no shared axis with the 0 to 7 Abilities scale). *Test of H1/H2:* across all rated occupations, regress Consequence of Error on the Abilities profile; report spread of the Skills items. *Caveats:* different scales; Critical Thinking and Complex Problem Solving may not separate occupations; confirm element IDs and names against the 30.2 files (the audit already found that Work Context frequency and impact items have four-segment IDs and that Independence is absent).
2. **Tacit-knowledge mapping on the page**, with a one-sentence reason and a confidence for each mapping, and the un-proxied dimensions shown.
3. **Ability Demand Index features** from the original spec: employment-weighted ability demand over time with 95% intervals; per-ability AI tier labels as colour; search by ability; a tier browse panel; PNG export with citation, embed code and a formatted citation; a fuller "What ONET Can't See" section for Tiers 4, 6 and 7; a methodology note with the dataset version; employment before 2018. *Status per the 2026-10-24 seis.jobs audit:* the weighted-demand pipeline and CSV were not located and the official BLS national archive returned HTTP 403, so no national estimate or interval has been computed; no verified per-ability tier map exists (only five illustrative abilities, three conflicting); the current statistics are unweighted across occupations (mean and standard error), not workforce-weighted; earlier employment history needs verified SOC crosswalks.
4. **AIOE comparison**: show an occupation's AIOE score beside its tier profile. *Caveats:* AIOE uses O\*NET 24.3 and an older SOC structure, the repository has no licence file (redistribution unresolved), and a code-equality check against six roles found four same-code and same-title matches and two missing. No AIOE data has been copied or joined.

## 7. Limitations

One occupation pair and one audit date; n = 8 per occupation on Skills; descriptive differences only. The ability-rating release is unresolved; Work Styles scales are unconfirmed; the tier mapping is editorial. Exposure is not adoption, job loss or hiring outcomes.

## 8. CRITIQ self-review (silent mode)

1. **[CRITICAL] Single-pair evidence.** The title claim ("what the Abilities cannot see") rests on one comparison. *Fix:* run the H1/H2 tests over all 894 rated occupations (SELECT-only; needs database access, not new data collection). *Why:* a reviewer will ask whether designers vs carpenters is cherry-picked.
2. **[CRITICAL] Confound.** Consequence of Error may measure physical hazard, not judgment. *Fix:* include Abilities as covariates (H1) and discuss.
3. **[MAJOR] Unverified inputs.** Tier map, weighted-demand pipeline and ability-rating release are unresolved; section 6 item 3 must not be described as built.
4. **[MAJOR] No literature section.** Only AIOE and the CCR framework are cited, both from project files. A real search is needed on task-based exposure measures and occupational AI exposure; this draft adds none from memory as evidence.
5. **[MINOR]** Audit counts are dated; re-run before submission.

**What works.** The paper states its own blind spot, keeps caveats attached to each item, and chooses a test that can show its main idea is redundant.

## Sources

- Irreducibly-Human: `docs/onet-tacit-knowledge-audit.md` (14 August 2026), `docs/onet-occupation-explorer-design-notes.md`, `CLAUDE.md` (site structure, builder credits)
- seis.jobs: `docs/explorer-extensions.md`, `docs/ability-tier-audit.md`, `docs/weighted-demand-audit.md`, `docs/aioe-source-audit.md` (all 2026-10-24)
- Felten, E., Raj, M., & Seamans, R. (2021). *Strategic Management Journal*, 42(12), 2195-2217. https://doi.org/10.1002/smj.3286
- Van Damme, D., with Fadel, C. (2026). Tacit Knowledge (Center for Curriculum Redesign, June 2026). Title as given by Professor Bear: "Tacit Knowledge, Human Cognition and Artificial Intelligence" [VERIFY against the PDF cover].
- Email proposing the v2 features to the builders: `email-v2-proposal.md` (draft, not sent)
