# Research

## Executive summary

**What this is.** The papers that can come out of the ai-jobs work and the folders next to it: jobs research, AI-jobs research, and the data that supports both. One folder per paper, each with a `paper-draft.md`.

**Why.** The collector, the skills taxonomy and the AI Exposure Explorer are each a paper-sized question, and each already has real material behind it. Writing the drafts now shows exactly where the evidence is thin.

**What is here (2026-10-24).** Four drafts, written with the CRITIQ protocol in silent mode (draft immediately, flag assumptions, no gates). Each opens with a status box, ends with a CRITIQ self-review ranking its own problems, and cites only files in this tree. **No draft has results beyond what is stated in its own status box**, and no literature search has been done for any of them.

| Folder | Paper | State of the evidence |
|---|---|---|
| [`ai-exposure-explorer/`](ai-exposure-explorer/paper-draft.md) | What the Abilities Cannot See: an Explorer for the human layer of AI exposure | One occupation pair from a 14 Aug 2026 database audit; v2 features specified; weighted-demand pipeline and tier map not located/verified. Also holds the draft email to the builders ([`email-v2-proposal.md`](ai-exposure-explorer/email-v2-proposal.md), not sent). |
| [`skills-taxonomy/`](skills-taxonomy/paper-draft.md) | A typed, versioned concept graph for skills | Design and evaluation plan; 4,274 legacy tags, 81 proposed concepts, 0 external mappings, 0 reviewed. No results. |
| [`seis-job-market-data/`](seis-job-market-data/paper-draft.md) | What a public job-board collector can and cannot see | Real one-day data: 2,574 employers, 719 readable boards, 84,282 postings. Biggest flaw: the title list was tuned on the same data it is scored on. |
| [`course-to-job-skills-alignment/`](course-to-job-skills-alignment/paper-draft.md) | From syllabus to vacancy | Registered-report plan. No faculty-confirmed assertions yet. |

## Other possible papers (not drafted)

| Candidate | Where the material is | Why not drafted yet |
|---|---|---|
| False friends in job-title filters | Lectern `config/title_families.json` (25 of 27 teaching-word titles at an AI lab turned out to be model training) and the title-family audit | Needs the audit rerun on current data for numbers |
| Do postings turn over? (churn) | Lectern `audit/churn.py`, `runs/*/churn-*.md` | Needs the churn outputs read; one day of ai-jobs data is not enough |
| Two views of exposure: tier profile vs AIOE | seis.jobs `docs/aioe-source-audit.md` | Blocked on SOC crosswalk (AIOE uses O\*NET 24.3) and redistribution terms |
| Employment-weighted ability demand | seis.jobs `docs/weighted-demand-audit.md`; `the-reallocation-engine-fresh/archive/data-notes/ability_demand_boondoggle.md` | The pipeline and CSV were not located; BLS archive returned 403 |
| Employer sponsorship evidence | seis.jobs `docs/backlog.md` (LCA/approval evidence design) | Raw DOL/USCIS releases not in hand |
| Personalized co-op and job pathway matching | `books/AI4ED/Personalized_Co-op_and_Job_Pathway_System/README.md` | Design note only; needs the taxonomy paper first |
| AI-washing reverse filter for Data/AI OPT students | `books/the-reallocation-engine-fresh/` (research-source doc) | Not read for this pass |

## Papers already in AI4ED (not jobs research)

`books/AI4ED/Papers/` holds three drafts in progress: *Enhancing Trust in LLMs: Algorithms for Comparing and Interpreting LLMs*, *Evaluating Tools for AI in Education: A Structured Framework*, and *The AI4ED Framework for Building Educational AI Tools*. They are about educational AI, not labour markets, so they are listed here and not copied.

## Reading list to verify (named from memory; none is cited as evidence in any draft)

Autor, Levy and Murnane (2003), *The Skill Content of Recent Technological Change*, QJE. Frey and Osborne (2017), *The Future of Employment*, Technological Forecasting and Social Change. Acemoglu and Restrepo (2019), *Automation and New Tasks*, Journal of Economic Perspectives. Eloundou, Manning, Mishkin and Rock (2023), *GPTs are GPTs*. Brynjolfsson, Li and Raymond (2023), *Generative AI at Work*. Webb (2020), *The Impact of Artificial Intelligence on the Labor Market*. Polanyi (1966), *The Tacit Dimension*. Check every detail before citing; a real search is also needed for skills ontologies and vacancy-data coverage.

## Conventions

- One folder per paper; `paper-draft.md` is the manuscript, other files are support.
- Flags in a draft: `[ASSUMPTION: ...]` was inferred, `[NEEDS HUMAN REVIEW]` needs a decision, `[VERIFY]` is unchecked.
- Numbers come from `data/` or a named source file. A claim with no file behind it is flagged.
- Drafts that name people (builders, reviewers) do not decide authorship; that is a human call.
