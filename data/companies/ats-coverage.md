# Which companies have a public job board we can read (2026-10-24)

## Executive summary

**What this is.** The result of asking six public applicant-tracking-system APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee) whether each of the 2574 companies in `companies.csv` has a board.
**What was found.** **719 companies (27%) have a confirmed readable board, listing 85,268 postings on the probe day.** 37 more have a board that could not be confirmed as theirs (kept out of collection until a person looks). **1818 (70%) have no board on any of the six**, which does not mean they have no jobs: it means they use a system we cannot yet read (Workday, iCIMS, Taleo, SuccessFactors, Oracle, or their own site).
**Workable was not read.** The first probe was unthrottled and Workable answered HTTP 429 with a Retry-After of about 23 hours, so every Workable check in this file is an error, not a 'no'. Companies hosted there (Hugging Face and similar) are counted below as having no board when they may have one.
**Read it carefully.** A company is *confirmed* only when the board names itself as that company or its ad text mentions it. A bare slug match is not evidence. The sector table below is dominated by who uses these six systems (startups and tech), not by who hires SEIS graduates; banks, hospitals, consultancies and government are mostly in the *no board* group because they use Workday-class systems.

## Coverage by sector

| Sector | Companies | Confirmed board | Share |
|---|---:|---:|---:|
| software | 605 | 244 | 40% |
| ai | 400 | 196 | 49% |
| health | 259 | 40 | 15% |
| finance | 227 | 22 | 9% |
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
| greenhouse | 391 | 36,632 |
| ashby | 191 | 10,082 |
| smartrecruiters | 74 | 33,523 |
| lever | 53 | 4,874 |
| recruitee | 10 | 157 |

## Largest confirmed boards

| Company | ATS | Postings |
|---|---|---:|
| Domino's | smartrecruiters | 24833 |
| SpaceX | greenhouse | 2820 |
| Anduril | greenhouse | 2508 |
| AbbVie | smartrecruiters | 1922 |
| Carvana | greenhouse | 1681 |
| Delivery Hero | smartrecruiters | 948 |
| Veeva Systems | lever | 918 |
| Veeva | lever | 918 |
| Databricks | greenhouse | 896 |
| OpenAI | ashby | 796 |
| Gopuff | lever | 787 |
| Intuitive Surgical | smartrecruiters | 774 |
| Stripe | greenhouse | 719 |
| ServiceNow | smartrecruiters | 715 |
| Accenture Federal Services | greenhouse | 705 |
| Coupang | greenhouse | 693 |
| Shield AI | ashby | 692 |
| Anthropic | greenhouse | 681 |
| Accor | smartrecruiters | 571 |
| Rocket Lab | greenhouse | 563 |
| Expeditors | smartrecruiters | 525 |
| KIPP | smartrecruiters | 517 |
| Esri | greenhouse | 508 |
| Lyra Health | lever | 473 |
| DoorDash | greenhouse | 459 |
| Cloudflare | greenhouse | 454 |
| Lucid Motors | greenhouse | 441 |
| Grab | smartrecruiters | 439 |
| Datadog | greenhouse | 433 |
| Elastic | greenhouse | 402 |
| One Medical | greenhouse | 395 |
| Okta | greenhouse | 390 |
| HelloFresh | greenhouse | 385 |
| Nebius | greenhouse | 384 |
| Experian | smartrecruiters | 384 |
| MongoDB | greenhouse | 382 |
| Waymo | greenhouse | 366 |
| Harvey | ashby | 358 |
| Snowflake | ashby | 355 |
| Zscaler | greenhouse | 352 |

## Boards found but not confirmed as the company's (a person must look)

| Company | Candidate | Postings | Why not confirmed |
|---|---|---:|---|
| 1X Technologies | ashby/1x | 101 | unverified |
| Ampere | recruitee/ampere | 11 | board-name-MISMATCH (board says: Ampère) |
| Ava Labs | ashby/ava-labs | 4 | unverified |
| BP | recruitee/bp | 1 | board-name-MISMATCH (board says: Black Propeller) |
| BambooHR | recruitee/bamboohr | 2 | board-name-MISMATCH (board says: Cycle HR - Sandbox) |
| CMS | recruitee/cms | 29 | board-name-MISMATCH (board says: CMS Derks Star Busmann N.V.) |
| Code.org | greenhouse/codeorg | 5 | board-name-MISMATCH (board says: CodeAI) |
| Disney | greenhouse/disney | 2 | board-name-MISMATCH (board says: Sgt. Pepper's Lonely Hearts Club Band) |
| EasyPost | recruitee/easypost | 6 | board-name-MISMATCH (board says: Postalia Belgium NV) |
| Ema | ashby/ema | 38 | unverified |
| Fox | greenhouse/fox | 9 | board-name-MISMATCH (board says: Fox Creek Veterinary Hospital - Wildwood) |
| Hex | ashby/hex | 39 | unverified |
| Intercom | greenhouse/intercom | 104 | board-name-MISMATCH (board says: Fin) |
| LinkedIn | lever/linkedin | 23 | unverified |
| Loop Returns | lever/loopreturns | 2 | unverified |
| Meta | recruitee/meta | 1 | board-name-MISMATCH (board says: Addis Ababa University) |
| Mux | ashby/mux | 1 | unverified |
| Oliver Wyman | lever/oliverwyman | 2 | unverified |
| Opploans | greenhouse/opploans | 3 | board-name-MISMATCH (board says: OppFi) |
| Oura | greenhouse/oura | 86 | board-name-MISMATCH (board says: Ōura) |
| Pure Storage | greenhouse/purestorage | 364 | board-name-MISMATCH (board says: Everpure) |
| R/GA | greenhouse/rga | 11 | board-name-MISMATCH (board says: R/GA Careers Page) |
| RWS | lever/rws | 137 | unverified |
| Radix | recruitee/radix | 4 | board-name-MISMATCH (board says: Superlinear) |
| Reka AI | ashby/reka | 9 | unverified |
| Rho | ashby/rho | 43 | unverified |
| Ro | lever/ro | 52 | unverified |
| SAS Institute | greenhouse/sas | 3 | board-name-MISMATCH (board says: Superior Alarm Systems) |
| SES AI | greenhouse/sesai | 43 | board-name-MISMATCH (board says: SES) |
| SRI International | recruitee/sri | 8 | board-name-MISMATCH (board says: SRI Rechtsanwaltsgesellschaft mbH) |
| Sila | lever/sila | 214 | unverified |
| TRM Labs | ashby/trm-labs | 113 | unverified |
| Wunderman Thompson | greenhouse/wundermanthompson | 395 | board-name-MISMATCH (board says: VML) |
| Zed Industries | ashby/zed | 1 | unverified |
| a16z crypto | ashby/a16z-crypto | 1 | unverified |
| n8n | ashby/n8n | 41 | unverified |
| xAI | greenhouse/xai | 298 | board-name-MISMATCH (board says: SpaceXSI) |
