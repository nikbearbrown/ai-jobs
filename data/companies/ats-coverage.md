# Which companies have a public job board we can read (2026-11-18)

## Executive summary

**What this is.** The result of asking six public applicant-tracking-system APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee) whether each of the 2574 companies in `companies.csv` has a board.
**What was found.** **722 companies (28%) have a confirmed readable board, listing 85,281 postings on the probe day.** 40 more have a board that could not be confirmed as theirs (kept out of collection until a person looks). **1812 (70%) have no board on any of the six**, which does not mean they have no jobs: it means they use a system we cannot yet read (Workday, iCIMS, Taleo, SuccessFactors, Oracle, or their own site).
**Read it carefully.** A company is *confirmed* only when the board names itself as that company or its ad text mentions it. A bare slug match is not evidence. The sector table below is dominated by who uses these six systems (startups and tech), not by who hires SEIS graduates; banks, hospitals, consultancies and government are mostly in the *no board* group because they use Workday-class systems.

## Coverage by sector

| Sector | Companies | Confirmed board | Share |
|---|---:|---:|---:|
| software | 605 | 245 | 40% |
| ai | 400 | 197 | 49% |
| health | 259 | 40 | 15% |
| finance | 227 | 23 | 10% |
| data | 174 | 70 | 40% |
| consulting | 159 | 13 | 8% |
| media | 149 | 27 | 18% |
| retail | 139 | 31 | 22% |
| regional | 109 | 24 | 22% |
| energy | 107 | 15 | 14% |
| nonprofit | 92 | 10 | 10% |
| travel | 81 | 19 | 23% |
| hardware | 73 | 8 | 10% |

## By ATS (confirmed boards)

| ATS | Companies | Postings on probe day |
|---|---:|---:|
| greenhouse | 388 | 36,815 |
| ashby | 200 | 9,657 |
| smartrecruiters | 75 | 33,912 |
| lever | 50 | 4,725 |
| recruitee | 7 | 140 |
| workable | 2 | 32 |

## Largest confirmed boards

| Company | ATS | Postings |
|---|---|---:|
| Domino's | smartrecruiters | 25121 |
| SpaceX | greenhouse | 2793 |
| Anduril | greenhouse | 2612 |
| AbbVie | smartrecruiters | 2045 |
| Carvana | greenhouse | 1663 |
| Databricks | greenhouse | 901 |
| Veeva Systems | lever | 865 |
| Veeva | lever | 865 |
| Intuitive Surgical | smartrecruiters | 853 |
| OpenAI | ashby | 836 |
| ServiceNow | smartrecruiters | 833 |
| Stripe | greenhouse | 789 |
| Delivery Hero | smartrecruiters | 774 |
| Gopuff | lever | 756 |
| Accenture Federal Services | greenhouse | 704 |
| Coupang | greenhouse | 686 |
| Anthropic | greenhouse | 658 |
| Expeditors | smartrecruiters | 542 |
| Accor | smartrecruiters | 539 |
| Rocket Lab | greenhouse | 535 |
| KIPP | smartrecruiters | 531 |
| Lucid Motors | greenhouse | 482 |
| Cloudflare | greenhouse | 482 |
| Lyra Health | lever | 481 |
| Esri | greenhouse | 479 |
| Grab | smartrecruiters | 424 |
| DoorDash | greenhouse | 416 |
| MongoDB | greenhouse | 394 |
| Experian | smartrecruiters | 384 |
| Hearst | greenhouse | 384 |
| Harvey | ashby | 383 |
| Elastic | greenhouse | 382 |
| Datadog | greenhouse | 382 |
| Waymo | greenhouse | 375 |
| Zscaler | greenhouse | 374 |
| Snowflake | ashby | 372 |
| Nebius | greenhouse | 371 |
| HelloFresh | greenhouse | 366 |
| Okta | greenhouse | 359 |
| One Medical | greenhouse | 348 |

## Boards found but not confirmed as the company's (a person must look)

| Company | Candidate | Postings | Why not confirmed |
|---|---|---:|---|
| 1X Technologies | ashby/1x | 101 | unverified |
| Ampere | recruitee/ampere | 15 | board-name-MISMATCH (board says: Ampère) |
| Applied Systems | ashby/applied-systems | 2 | unverified |
| Ava Labs | ashby/ava-labs | 5 | unverified |
| BP | recruitee/bp | 1 | board-name-MISMATCH (board says: Black Propeller) |
| BambooHR | recruitee/bamboohr | 2 | board-name-MISMATCH (board says: Cycle HR - Sandbox) |
| CMS | recruitee/cms | 27 | board-name-MISMATCH (board says: CMS Derks Star Busmann N.V.) |
| Code.org | greenhouse/codeorg | 2 | board-name-MISMATCH (board says: CodeAI) |
| DOE | ashby/doe | 3 | unverified |
| Disney | greenhouse/disney | 1 | board-name-MISMATCH (board says: Sgt. Pepper's Lonely Hearts Club Band) |
| EasyPost | recruitee/easypost | 9 | board-name-MISMATCH (board says: Postalia Belgium NV) |
| Ema | ashby/ema | 38 | unverified |
| Fox | greenhouse/fox | 9 | board-name-MISMATCH (board says: Fox Creek Veterinary Hospital - Wildwood) |
| Hex | ashby/hex | 41 | unverified |
| Intercom | greenhouse/intercom | 115 | board-name-MISMATCH (board says: Fin) |
| LinkedIn | lever/linkedin | 23 | unverified |
| Loop Returns | lever/loopreturns | 4 | unverified |
| Luma AI | ashby/lumaai | 12 | unverified |
| Meta | recruitee/meta | 1 | board-name-MISMATCH (board says: Addis Ababa University) |
| Mux | ashby/mux | 2 | unverified |
| Oliver Wyman | lever/oliverwyman | 2 | unverified |
| Opploans | greenhouse/opploans | 4 | board-name-MISMATCH (board says: OppFi) |
| Oura | greenhouse/oura | 95 | board-name-MISMATCH (board says: ŌURA) |
| Pure Storage | greenhouse/purestorage | 381 | board-name-MISMATCH (board says: Everpure) |
| R/GA | greenhouse/rga | 13 | board-name-MISMATCH (board says: R/GA Careers Page) |
| RWS | lever/rws | 148 | unverified |
| Radix | recruitee/radix | 4 | board-name-MISMATCH (board says: Superlinear) |
| Reka AI | ashby/reka | 3 | unverified |
| Rho | ashby/rho | 47 | unverified |
| Ro | lever/ro | 54 | unverified |
| SAS Institute | greenhouse/sas | 3 | board-name-MISMATCH (board says: Superior Alarm Systems) |
| SES AI | greenhouse/sesai | 43 | board-name-MISMATCH (board says: SES) |
| SRI International | recruitee/sri | 8 | board-name-MISMATCH (board says: SRI Rechtsanwaltsgesellschaft mbH) |
| TRM Labs | ashby/trm-labs | 117 | unverified |
| USC | greenhouse/usc | 2 | board-name-MISMATCH (board says: Urban Sports Club) |
| Wunderman Thompson | greenhouse/wundermanthompson | 391 | board-name-MISMATCH (board says: VML) |
| Zed Industries | ashby/zed | 2 | unverified |
| a16z crypto | ashby/a16z-crypto | 1 | unverified |
| n8n | ashby/n8n | 60 | unverified |
| xAI | greenhouse/xai | 302 | board-name-MISMATCH (board says: SpaceXSI) |
