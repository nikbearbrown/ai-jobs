# Software license and data provenance

The [MIT license](LICENSE) covers this project's original software and associated
original documentation, tests, and synthetic fixtures. It does **not** relicense
employer postings, advertisements, third-party datasets, logos, trademarks,
quoted research, or other material owned by others. Public accessibility and an
API response are not grants of redistribution rights. Existing notices continue
to apply. A field allowlist is a technical constraint, not a rights clearance.

## Current release boundary

This change provides code, schemas, documentation and invented fixtures with
`example.invalid` links. No real feed is released. Full collected state, ad text,
raw downloads and exported feeds remain ignored. Existing tracked public CSVs,
including `data/jobs/2026-10-24/entry-level.csv`, are unchanged; their presence does
not settle reuse rights. Removing them or rewriting history is a separate decision.
The research proposal email is not part of this change.

Employer data stays subject to the employer's and ATS provider's applicable terms.
A future public release needs a source-by-source review, explicit fields approved
for that use, direct attribution links, retention/removal policy and a dated review
record. Do not attach the software MIT license to an employer-data download.

## O*NET® database data

The official [database license](https://www.onetcenter.org/license_db.html),
checked on 2026-10-25, applies CC BY 4.0 to the covered downloadable database
files, subject to its stated scope and exceptions. Credit USDOL/ETA, identify the
exact release, link the [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/),
and identify modifications. Preserve the O*NET trademark attribution and do not
imply endorsement. This does not blanket-license career exploration tools or
all website content; check their separate terms. Do not infer that a crosswalk,
third-party index, or other standard has the same license.

Use the [official database page](https://www.onetcenter.org/database.html) and
[release archive](https://www.onetcenter.org/db_releases.html) to resolve a source.
The license page currently names 31.0; that is **not** evidence that any local
ratings use that release. Research drafts discuss unresolved source versions.
No O*NET dataset is downloaded, audited, or redistributed by this change.

## Required record for each third-party artifact

Before import or redistribution, keep a manifest alongside each validated version:

| Field | Required evidence |
|---|---|
| Identity | Dataset name, publisher, exact release/version; never just `latest` |
| Source | Direct original file URL plus release/dictionary URL; retain the original download |
| Rights | Exact license name and URL, attribution text, applicable exceptions, review date and release decision |
| Retrieval | UTC retrieval timestamp; do not substitute a publication date |
| Coverage | Geography, time period, occupation/SOC version, domains/tables, row counts, omissions and known gaps |
| Integrity | SHA-256 and byte length of original file and each derived artifact |
| Transformation | Script/version or commit, input hashes, field mappings, exclusions, modifications and output counts |
| Validation | Schema and crosswalk versions, checks/results, unresolved discrepancies, reviewer and acceptance date |

An unknown value remains explicitly unknown and blocks claims needing that fact.
A checksum detects changed bytes; it does not authenticate a publisher or license.
Keep attribution and modification notices with exports and in the consuming UI.
Check interpretations and derived values against the original data and dictionary;
code equality alone does not prove two occupation or skill definitions match.

We make no guarantee that stored data are the newest available. Show the exact
release, retrieval date, coverage and last successful observation. Newer uploads
become separate validated versions with their own provenance and checksums. Never
overwrite an accepted historical release or silently relabel it as a newer one.
An upload is not accepted merely because its filename or release number is newer.
