# Which companies have a public job board we can read (2026-11-11)

## Executive summary

**What this is.** The result of asking six public applicant-tracking-system APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee) whether each of the 2574 companies in `companies.csv` has a board.
**What was found.** **720 companies (27%) have a confirmed readable board, listing 85,942 postings on the probe day.** 40 more have a board that could not be confirmed as theirs (kept out of collection until a person looks). **1814 (70%) have no board on any of the six**, which does not mean they have no jobs: it means they use a system we cannot yet read (Workday, iCIMS, Taleo, SuccessFactors, Oracle, or their own site).
**Read it carefully.** A company is *confirmed* only when the board names itself as that company or its ad text mentions it. A bare slug match is not evidence. The sector table below is dominated by who uses these six systems (startups and tech), not by who hires SEIS graduates; banks, hospitals, consultancies and government are mostly in the *no board* group because they use Workday-class systems.

## Coverage by sector

| Sector | Companies | Confirmed board | Share |
|---|---:|---:|---:|
| software | 605 | 245 | 40% |
| ai | 400 | 198 | 49% |
| health | 259 | 40 | 15% |
| finance | 227 | 23 | 10% |
| data | 174 | 70 | 40% |
| consulting | 159 | 13 | 8% |
| media | 149 | 26 | 17% |
| retail | 139 | 30 | 21% |
| regional | 109 | 24 | 22% |
| energy | 107 | 14 | 13% |
| nonprofit | 92 | 10 | 10% |
| travel | 81 | 19 | 23% |
| hardware | 73 | 8 | 10% |

## By ATS (confirmed boards)

| ATS | Companies | Postings on probe day |
|---|---:|---:|
| greenhouse | 387 | 37,128 |
| ashby | 197 | 9,527 |
| smartrecruiters | 75 | 33,876 |
| lever | 51 | 5,235 |
| recruitee | 8 | 144 |
| workable | 2 | 32 |

## Largest confirmed boards

| Company | ATS | Postings |
|---|---|---:|
| Domino's | smartrecruiters | 24970 |
| SpaceX | greenhouse | 2908 |
| Anduril | greenhouse | 2583 |
| AbbVie | smartrecruiters | 2052 |
| Carvana | greenhouse | 1672 |
| Databricks | greenhouse | 920 |
| Delivery Hero | smartrecruiters | 901 |
| Veeva Systems | lever | 861 |
| Veeva | lever | 861 |
| Intuitive Surgical | smartrecruiters | 852 |
| OpenAI | ashby | 827 |
| Gopuff | lever | 785 |
| Stripe | greenhouse | 779 |
| ServiceNow | smartrecruiters | 769 |
| Accenture Federal Services | greenhouse | 719 |
| Anthropic | greenhouse | 678 |
| Shield AI | lever | 677 |
| Coupang | greenhouse | 667 |
| Expeditors | smartrecruiters | 554 |
| Accor | smartrecruiters | 549 |
| Rocket Lab | greenhouse | 548 |
| KIPP | smartrecruiters | 520 |
| Esri | greenhouse | 491 |
| Lyra Health | lever | 485 |
| Cloudflare | greenhouse | 473 |
| Lucid Motors | greenhouse | 461 |
| Grab | smartrecruiters | 443 |
| DoorDash | greenhouse | 442 |
| Elastic | greenhouse | 423 |
| Experian | smartrecruiters | 395 |
| Datadog | greenhouse | 394 |
| Waymo | greenhouse | 380 |
| Okta | greenhouse | 379 |
| MongoDB | greenhouse | 377 |
| Nebius | greenhouse | 375 |
| Zscaler | greenhouse | 375 |
| Snowflake | ashby | 374 |
| Harvey | ashby | 373 |
| HelloFresh | greenhouse | 371 |
| Hearst | greenhouse | 370 |

## Boards found but not confirmed as the company's (a person must look)

| Company | Candidate | Postings | Why not confirmed |
|---|---|---:|---|
| 1X Technologies | ashby/1x | 99 | unverified |
| Ampere | recruitee/ampere | 15 | board-name-MISMATCH (board says: Ampère) |
| Ava Labs | ashby/ava-labs | 4 | unverified |
| BP | recruitee/bp | 1 | board-name-MISMATCH (board says: Black Propeller) |
| BambooHR | recruitee/bamboohr | 2 | board-name-MISMATCH (board says: Cycle HR - Sandbox) |
| CMS | recruitee/cms | 27 | board-name-MISMATCH (board says: CMS Derks Star Busmann N.V.) |
| Code.org | greenhouse/codeorg | 2 | board-name-MISMATCH (board says: CodeAI) |
| DOE | ashby/doe | 3 | unverified |
| Disney | greenhouse/disney | 2 | board-name-MISMATCH (board says: Sgt. Pepper's Lonely Hearts Club Band) |
| EasyPost | recruitee/easypost | 12 | board-name-MISMATCH (board says: Postalia Belgium NV) |
| Ema | ashby/ema | 39 | unverified |
| Fox | greenhouse/fox | 9 | board-name-MISMATCH (board says: Fox Creek Veterinary Hospital - Wildwood) |
| Hex | ashby/hex | 37 | unverified |
| Intercom | greenhouse/intercom | 110 | board-name-MISMATCH (board says: Fin) |
| LinkedIn | lever/linkedin | 23 | unverified |
| Loop Returns | lever/loopreturns | 3 | unverified |
| Luma AI | ashby/lumaai | 17 | unverified |
| Meta | recruitee/meta | 1 | board-name-MISMATCH (board says: Addis Ababa University) |
| Mux | ashby/mux | 2 | unverified |
| Oliver Wyman | lever/oliverwyman | 2 | unverified |
| Opploans | greenhouse/opploans | 5 | board-name-MISMATCH (board says: OppFi) |
| Oura | greenhouse/oura | 95 | board-name-MISMATCH (board says: ŌURA) |
| Pure Storage | greenhouse/purestorage | 374 | board-name-MISMATCH (board says: Everpure) |
| R/GA | greenhouse/rga | 12 | board-name-MISMATCH (board says: R/GA Careers Page) |
| RWS | lever/rws | 132 | unverified |
| Radix | recruitee/radix | 4 | board-name-MISMATCH (board says: Superlinear) |
| Reka AI | ashby/reka | 9 | unverified |
| Rho | ashby/rho | 47 | unverified |
| Ro | lever/ro | 54 | unverified |
| SAS Institute | greenhouse/sas | 3 | board-name-MISMATCH (board says: Superior Alarm Systems) |
| SES AI | greenhouse/sesai | 43 | board-name-MISMATCH (board says: SES) |
| SRI International | recruitee/sri | 8 | board-name-MISMATCH (board says: SRI Rechtsanwaltsgesellschaft mbH) |
| Sila | lever/sila | 221 | unverified |
| TRM Labs | ashby/trm-labs | 115 | unverified |
| USC | greenhouse/usc | 2 | board-name-MISMATCH (board says: Urban Sports Club) |
| Wunderman Thompson | greenhouse/wundermanthompson | 392 | board-name-MISMATCH (board says: VML) |
| Zed Industries | ashby/zed | 2 | unverified |
| a16z crypto | ashby/a16z-crypto | 1 | unverified |
| n8n | ashby/n8n | 50 | unverified |
| xAI | greenhouse/xai | 297 | board-name-MISMATCH (board says: SpaceXSI) |
