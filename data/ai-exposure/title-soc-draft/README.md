# DRAFT: AI Jobs titles → BLS occupations (SOC 2018)

Built 2026-11-07. **A draft for a person to review, not a finished crosswalk.** No person has checked it. A first review pass by Claude on 2026-11-07 (a model review, which does not count as evidence that a mapping is right) read the low-confidence groups and the flagged medium/high groups and fixed about 40 misfiring rules; the remaining queue is for a person.

## What it is
Each of the 1,609 titles in `data/titles/titles.json` gets one BLS projections occupation (the 831-row list in `../bls/2026-11-07/`), a confidence, the rule that made the choice, and that occupation's BLS relative AI exposure category, 2025 employment, projected change and median wage.

Run: `python3 data/ai-exposure/title-soc-draft/build.py` from the `ai-jobs` root. Standard library only, no network. It stops if any rule names a code that is not in the BLS list.

## Files
- `title-soc-draft.csv`: all 1,609 titles.
- `review-queue.csv`: 964 rows to check first (low confidence, family default, no occupation, or a rule that disagrees with the family default).
- `family-summary.csv`: per family, confidence counts, exposure counts and top occupations.
- `summary.json`, `build.py` (the rules, in order; first match wins).

## Confidence
| Level | Titles | Meaning |
|---|---|---|
| high | 219 | A strong title word names the occupation (Software Engineer, Data Scientist, Technical Writer). |
| medium | 759 | A reasonable rule, but the SOC list has no dedicated occupation or two fit. |
| low | 272 | Weak or forced fit (Product Manager → Project management specialists; data raters → Data entry keyers). |
| family-default | 308 | No rule matched; the family's most common occupation was used. Treat as a guess. |
| none | 51 | Program names, not occupations ("New Grad", "Visa Sponsorship Available"). Left unmapped on purpose. |

Seniority words (Senior, Junior, Intern, Staff, Principal, Lead, Associate) are stripped before matching, so a title and its entry-level form map identically.

## Findings you should know before using it
1. **The BLS category barely discriminates across these titles.** Of the 1,558 mapped titles, 1,539 land in "Very high", 17 in "High" and 2 in "Moderate"; none in "Low". Almost all AI Jobs titles map to computer occupations, which BLS places in the top quarter. The category is relative to all 831 occupations, so it says these jobs are near the top of that ranking, not how they differ from each other. Inside this project, the percentile scores from the underlying sources (not in the BLS workbook) would be needed to separate them.
2. **Many-to-one and approximate.** 515 titles map to "Software developers" alone. 293 rows carry a `note` saying there is no dedicated SOC and the nearest was borrowed. BLS has no occupation for ML engineer, data engineer, product manager, devops or prompt engineer; those are borrowed from the nearest one.
3. **Title only.** No ad text was read. The same title can be a different job at different employers.
4. **Not validated against O*NET.** A title-to-O*NET-SOC match (the lexicon's job-title pilot is doing that against O*NET titles) would be a better key. When it exists, compare it with this file and prefer it.

## The borrowed guesses barely move the BLS category
For the main borrowed groups I swapped in the plausible alternate occupations and re-read the BLS category: product manager (Project management specialists, Marketing managers, Computer and information systems managers), data engineer (Software developers, Database architects, Data scientists, Network admins), data raters, evaluators, trust and safety, AI/ML engineer, developer relations, and forward-deployed engineer. Every alternate is "Very high" except Managers all other (High) and Sales managers (High). So the choice matters for projected growth, openings and wage, which differ a lot by occupation, and hardly at all for the exposure category.

## What the first review pass changed
Developer-relations and curriculum titles were being caught by the "developer" rule; ML-training titles were treated as trainers; AI/ML platform titles were sent to systems administrators; governance "specialist" titles were treated as engineers; smart-contract developers were labelled auditors; data and "AI auditors" were labelled accountants; and "Instructor, Data Science" was a data scientist. These are fixed. Family-restricted catch-all rules now map leftover engineer titles in software families, security titles, evaluation titles, cloud/devops titles and EHR titles, at medium or low confidence, so fewer rows rest on the bare family default.

## Still wrong or uncertain (known)
- Data raters and annotators → Data entry keyers is a poor fit but BLS has nothing closer.
- "Technical Evangelist", "Developer Advocate" and community roles are borrowed from trainers and PR specialists.
- Cloud/AI "Solutions Architect" titles go to Sales engineers; at some employers they build rather than sell.
- 308 titles still rest on the family default. Most are generic engineer or analyst titles in a family where the default is a fair guess, but that is a guess.

## Next
Review `review-queue.csv`, fix rules in `build.py` (not the CSV), rebuild.
