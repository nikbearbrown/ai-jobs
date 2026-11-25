# Which companies have a public job board we can read (2026-11-25)

## Executive summary

**What this is.** The result of asking six public applicant-tracking-system APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee) whether each of the 2574 companies in `companies.csv` has a board.
**What was found.** **724 companies (28%) have a confirmed readable board, listing 85,446 postings on the probe day.** 39 more have a board that could not be confirmed as theirs (kept out of collection until a person looks). **1811 (70%) have no board on any of the six**, which does not mean they have no jobs: it means they use a system we cannot yet read (Workday, iCIMS, Taleo, SuccessFactors, Oracle, or their own site).
**Read it carefully.** A company is *confirmed* only when the board names itself as that company or its ad text mentions it. A bare slug match is not evidence. The sector table below is dominated by who uses these six systems (startups and tech), not by who hires SEIS graduates; banks, hospitals, consultancies and government are mostly in the *no board* group because they use Workday-class systems.

## Coverage by sector

| Sector | Companies | Confirmed board | Share |
|---|---:|---:|---:|
| software | 605 | 246 | 40% |
| ai | 400 | 197 | 49% |
| health | 259 | 40 | 15% |
| finance | 227 | 22 | 9% |
| data | 174 | 71 | 40% |
| consulting | 159 | 13 | 8% |
| media | 149 | 27 | 18% |
| retail | 139 | 31 | 22% |
| regional | 109 | 24 | 22% |
| energy | 107 | 15 | 14% |
| nonprofit | 92 | 10 | 10% |
| travel | 81 | 19 | 23% |
| hardware | 73 | 9 | 12% |

## By ATS (confirmed boards)

| ATS | Companies | Postings on probe day |
|---|---:|---:|
| greenhouse | 390 | 36,659 |
| ashby | 202 | 9,763 |
| smartrecruiters | 75 | 34,220 |
| lever | 48 | 4,636 |
| recruitee | 7 | 132 |
| workable | 2 | 36 |

## Largest confirmed boards

| Company | ATS | Postings |
|---|---|---:|
| Domino's | smartrecruiters | 25221 |
| SpaceX | greenhouse | 2849 |
| Anduril | greenhouse | 2606 |
| AbbVie | smartrecruiters | 2008 |
| Carvana | greenhouse | 1582 |
| ServiceNow | smartrecruiters | 991 |
| Databricks | greenhouse | 889 |
| OpenAI | ashby | 877 |
| Veeva Systems | lever | 874 |
| Veeva | lever | 874 |
| Intuitive Surgical | smartrecruiters | 850 |
| Delivery Hero | smartrecruiters | 794 |
| Stripe | greenhouse | 771 |
| Gopuff | lever | 751 |
| Accenture Federal Services | greenhouse | 715 |
| Coupang | greenhouse | 676 |
| Anthropic | greenhouse | 636 |
| Expeditors | smartrecruiters | 563 |
| KIPP | smartrecruiters | 562 |
| Rocket Lab | greenhouse | 547 |
| Cloudflare | greenhouse | 513 |
| Lucid Motors | greenhouse | 498 |
| Accor | smartrecruiters | 498 |
| Esri | greenhouse | 478 |
| Grab | smartrecruiters | 451 |
| Lyra Health | lever | 420 |
| MongoDB | greenhouse | 418 |
| Experian | smartrecruiters | 407 |
| Hearst | greenhouse | 401 |
| DoorDash | greenhouse | 399 |
| Harvey | ashby | 394 |
| Zscaler | greenhouse | 393 |
| Elastic | greenhouse | 389 |
| Datadog | greenhouse | 388 |
| Okta | greenhouse | 373 |
| Snowflake | ashby | 371 |
| HelloFresh | greenhouse | 360 |
| Harvard University | smartrecruiters | 360 |
| Waymo | greenhouse | 358 |
| One Medical | greenhouse | 351 |

## Boards found but not confirmed as the company's (a person must look)

| Company | Candidate | Postings | Why not confirmed |
|---|---|---:|---|
| 1X Technologies | ashby/1x | 116 | unverified |
| Ampere | recruitee/ampere | 17 | board-name-MISMATCH (board says: Ampère) |
| Ava Labs | ashby/ava-labs | 8 | unverified |
| BP | recruitee/bp | 1 | board-name-MISMATCH (board says: Black Propeller) |
| BambooHR | recruitee/bamboohr | 2 | board-name-MISMATCH (board says: Cycle HR - Sandbox) |
| CMS | recruitee/cms | 29 | board-name-MISMATCH (board says: CMS Derks Star Busmann N.V.) |
| Code.org | greenhouse/codeorg | 2 | board-name-MISMATCH (board says: CodeAI) |
| DOE | ashby/doe | 3 | unverified |
| Disney | greenhouse/disney | 1 | board-name-MISMATCH (board says: Sgt. Pepper's Lonely Hearts Club Band) |
| EasyPost | recruitee/easypost | 10 | board-name-MISMATCH (board says: Postalia Belgium NV) |
| Ema | ashby/ema | 39 | unverified |
| Fox | greenhouse/fox | 9 | board-name-MISMATCH (board says: Fox Creek Veterinary Hospital - Wildwood) |
| Hex | ashby/hex | 44 | unverified |
| Intercom | greenhouse/intercom | 124 | board-name-MISMATCH (board says: Fin) |
| LinkedIn | lever/linkedin | 25 | unverified |
| Loop Returns | lever/loopreturns | 3 | unverified |
| Luma AI | ashby/lumaai | 11 | unverified |
| Meta | recruitee/meta | 1 | board-name-MISMATCH (board says: Addis Ababa University) |
| Mux | ashby/mux | 1 | unverified |
| Oliver Wyman | lever/oliverwyman | 2 | unverified |
| Opploans | greenhouse/opploans | 4 | board-name-MISMATCH (board says: OppFi) |
| Oura | greenhouse/oura | 96 | board-name-MISMATCH (board says: ŌURA) |
| Pure Storage | greenhouse/purestorage | 389 | board-name-MISMATCH (board says: Everpure) |
| R/GA | greenhouse/rga | 13 | board-name-MISMATCH (board says: R/GA Careers Page) |
| RWS | lever/rws | 148 | unverified |
| Radix | recruitee/radix | 5 | board-name-MISMATCH (board says: Superlinear) |
| Reka AI | ashby/reka | 3 | unverified |
| Rho | ashby/rho | 48 | unverified |
| Ro | lever/ro | 54 | unverified |
| SAS Institute | greenhouse/sas | 3 | board-name-MISMATCH (board says: Superior Alarm Systems) |
| SES AI | greenhouse/sesai | 43 | board-name-MISMATCH (board says: SES) |
| SRI International | recruitee/sri | 8 | board-name-MISMATCH (board says: SRI Rechtsanwaltsgesellschaft mbH) |
| TRM Labs | ashby/trm-labs | 112 | unverified |
| USC | greenhouse/usc | 2 | board-name-MISMATCH (board says: Urban Sports Club) |
| Wunderman Thompson | greenhouse/wundermanthompson | 378 | board-name-MISMATCH (board says: VML) |
| Zed Industries | ashby/zed | 2 | unverified |
| a16z crypto | ashby/a16z-crypto | 1 | unverified |
| n8n | ashby/n8n | 69 | unverified |
| xAI | greenhouse/xai | 297 | board-name-MISMATCH (board says: SpaceXSI) |
