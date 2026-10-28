# Which companies have a public job board we can read (2026-10-28)

## Executive summary

**What this is.** The result of asking six public applicant-tracking-system APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee) whether each of the 2574 companies in `companies.csv` has a board.
**What was found.** **724 companies (28%) have a confirmed readable board, listing 85,311 postings on the probe day.** 39 more have a board that could not be confirmed as theirs (kept out of collection until a person looks). **1811 (70%) have no board on any of the six**, which does not mean they have no jobs: it means they use a system we cannot yet read (Workday, iCIMS, Taleo, SuccessFactors, Oracle, or their own site).
**Read it carefully.** A company is *confirmed* only when the board names itself as that company or its ad text mentions it. A bare slug match is not evidence. The sector table below is dominated by who uses these six systems (startups and tech), not by who hires SEIS graduates; banks, hospitals, consultancies and government are mostly in the *no board* group because they use Workday-class systems.

## Coverage by sector

| Sector | Companies | Confirmed board | Share |
|---|---:|---:|---:|
| software | 605 | 245 | 40% |
| ai | 400 | 199 | 49% |
| health | 259 | 40 | 15% |
| finance | 227 | 23 | 10% |
| data | 174 | 69 | 39% |
| consulting | 159 | 14 | 8% |
| media | 149 | 26 | 17% |
| retail | 139 | 31 | 22% |
| regional | 109 | 25 | 22% |
| energy | 107 | 14 | 13% |
| nonprofit | 92 | 11 | 11% |
| travel | 81 | 19 | 23% |
| hardware | 73 | 8 | 10% |

## By ATS (confirmed boards)

| ATS | Companies | Postings on probe day |
|---|---:|---:|
| greenhouse | 390 | 36,941 |
| ashby | 195 | 10,083 |
| smartrecruiters | 74 | 33,318 |
| lever | 53 | 4,784 |
| recruitee | 10 | 155 |
| workable | 2 | 30 |

## Largest confirmed boards

| Company | ATS | Postings |
|---|---|---:|
| Domino's | smartrecruiters | 24602 |
| SpaceX | greenhouse | 2834 |
| Anduril | greenhouse | 2526 |
| AbbVie | smartrecruiters | 1917 |
| Carvana | greenhouse | 1660 |
| Delivery Hero | smartrecruiters | 945 |
| Databricks | greenhouse | 897 |
| Veeva Systems | lever | 897 |
| Veeva | lever | 897 |
| OpenAI | ashby | 801 |
| Gopuff | lever | 794 |
| Intuitive Surgical | smartrecruiters | 779 |
| ServiceNow | smartrecruiters | 734 |
| Accenture Federal Services | greenhouse | 716 |
| Stripe | greenhouse | 714 |
| Coupang | greenhouse | 697 |
| Shield AI | ashby | 689 |
| Anthropic | greenhouse | 681 |
| Accor | smartrecruiters | 582 |
| Rocket Lab | greenhouse | 555 |
| Expeditors | smartrecruiters | 528 |
| KIPP | smartrecruiters | 510 |
| Esri | greenhouse | 508 |
| Lyra Health | lever | 470 |
| Cloudflare | greenhouse | 461 |
| Lucid Motors | greenhouse | 443 |
| DoorDash | greenhouse | 442 |
| Grab | smartrecruiters | 439 |
| Datadog | greenhouse | 424 |
| Elastic | greenhouse | 405 |
| Experian | smartrecruiters | 392 |
| Okta | greenhouse | 387 |
| One Medical | greenhouse | 384 |
| HelloFresh | greenhouse | 377 |
| Nebius | greenhouse | 375 |
| Waymo | greenhouse | 369 |
| Harvey | ashby | 367 |
| MongoDB | greenhouse | 363 |
| Snowflake | ashby | 361 |
| Zscaler | greenhouse | 357 |

## Boards found but not confirmed as the company's (a person must look)

| Company | Candidate | Postings | Why not confirmed |
|---|---|---:|---|
| 1X Technologies | ashby/1x | 104 | unverified |
| Ampere | recruitee/ampere | 12 | board-name-MISMATCH (board says: Ampère) |
| Ava Labs | ashby/ava-labs | 4 | unverified |
| BP | recruitee/bp | 1 | board-name-MISMATCH (board says: Black Propeller) |
| BambooHR | recruitee/bamboohr | 2 | board-name-MISMATCH (board says: Cycle HR - Sandbox) |
| CMS | recruitee/cms | 28 | board-name-MISMATCH (board says: CMS Derks Star Busmann N.V.) |
| Code.org | greenhouse/codeorg | 5 | board-name-MISMATCH (board says: CodeAI) |
| DOE | ashby/doe | 3 | unverified |
| Disney | greenhouse/disney | 2 | board-name-MISMATCH (board says: Sgt. Pepper's Lonely Hearts Club Band) |
| EasyPost | recruitee/easypost | 8 | board-name-MISMATCH (board says: Postalia Belgium NV) |
| Ema | ashby/ema | 39 | unverified |
| Fox | greenhouse/fox | 9 | board-name-MISMATCH (board says: Fox Creek Veterinary Hospital - Wildwood) |
| Hex | ashby/hex | 38 | unverified |
| Intercom | greenhouse/intercom | 102 | board-name-MISMATCH (board says: Fin) |
| LinkedIn | lever/linkedin | 23 | unverified |
| Loop Returns | lever/loopreturns | 1 | unverified |
| Luma AI | ashby/lumaai | 30 | unverified |
| Meta | recruitee/meta | 1 | board-name-MISMATCH (board says: Addis Ababa University) |
| Mux | ashby/mux | 1 | unverified |
| Oliver Wyman | lever/oliverwyman | 2 | unverified |
| Opploans | greenhouse/opploans | 3 | board-name-MISMATCH (board says: OppFi) |
| Oura | greenhouse/oura | 93 | board-name-MISMATCH (board says: Ōura) |
| Pure Storage | greenhouse/purestorage | 362 | board-name-MISMATCH (board says: Everpure) |
| R/GA | greenhouse/rga | 13 | board-name-MISMATCH (board says: R/GA Careers Page) |
| RWS | lever/rws | 149 | unverified |
| Radix | recruitee/radix | 4 | board-name-MISMATCH (board says: Superlinear) |
| Reka AI | ashby/reka | 9 | unverified |
| Rho | ashby/rho | 43 | unverified |
| Ro | lever/ro | 50 | unverified |
| SAS Institute | greenhouse/sas | 3 | board-name-MISMATCH (board says: Superior Alarm Systems) |
| SES AI | greenhouse/sesai | 43 | board-name-MISMATCH (board says: SES) |
| SRI International | recruitee/sri | 8 | board-name-MISMATCH (board says: SRI Rechtsanwaltsgesellschaft mbH) |
| Sila | lever/sila | 218 | unverified |
| TRM Labs | ashby/trm-labs | 114 | unverified |
| Wunderman Thompson | greenhouse/wundermanthompson | 381 | board-name-MISMATCH (board says: VML) |
| Zed Industries | ashby/zed | 1 | unverified |
| a16z crypto | ashby/a16z-crypto | 1 | unverified |
| n8n | ashby/n8n | 38 | unverified |
| xAI | greenhouse/xai | 308 | board-name-MISMATCH (board says: SpaceXSI) |
