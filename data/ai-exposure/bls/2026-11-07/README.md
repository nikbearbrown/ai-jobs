# BLS AI exposure data, downloaded 2026-11-07

Source: https://www.bls.gov/emp/publications/ai-exposure-categories.htm
Workbook: https://www.bls.gov/emp/ind-occ-matrix/ai-exposure-categories.xlsx

The original workbook was downloaded through the BLS webpage in Chrome. CSV exports preserve source headers and values. Employment figures are in thousands; occupation codes are strings. Missing values retain the source em dash. The workbook contains 831 unique detailed occupation codes and 13 columns: employment 2025/2035, changes, self-employment, annual openings, median wage, education, experience, training, and relative AI exposure. Category counts: Low 213; Moderate 206; High 206; Very high 206.

The workbook supplies final relative categories, NOT the five underlying source scores or percentile ranks. Exposure does not imply job loss, productivity gains, automation probability, or wage effects. Projections are forecasts, not realized outcomes. Read the included field descriptions and workbook notes before analysis.

## Coverage and gaps
Complete BLS exposure workbook and both worksheets are preserved. The separate occupation crosswalk and web methodology text have NOT been downloaded: browser subsequently returned `Debugger unattached`, and direct BLS HTTP returned 403. No files were overwritten. Original Downloads copies are untouched.

Crosswalk: https://www.bls.gov/emp/classifications-crosswalks/nem-occupational-coverage.xlsx
Related BLS documentation:
- https://www.bls.gov/emp/tables/factors-affecting-occupational-utilization.htm
- https://www.bls.gov/emp/factsheets/ai-impacts.htm
- https://www.bls.gov/news.release/ecopro.tn.htm
- https://www.bls.gov/opub/mlr/2025/article/incorporating-ai-impacts-in-bls-employment-projections.htm

## Broader source registry (not downloaded in this package)
These are discovery leads from the supplied guide, not a claim of independent verification or download:
- https://budgetlab.yale.edu/research/ai-exposure-what-do-we-know
- https://github.com/openai/GPTs-are-GPTs
- https://github.com/AIOE-Data/AIOE
- https://sites.google.com/view/gregorschubert/data
- https://github.com/microsoft/working-with-ai
- https://huggingface.co/datasets/Anthropic/EconomicIndex
