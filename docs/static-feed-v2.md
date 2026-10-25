# Static feed v2: optional adapters to accepted snapshots

Implemented offline with synthetic end-to-end tests. V2 connects already captured
USAJOBS and Workday results to the existing immutable snapshot and local acceptance
architecture. It does not call an adapter, provision credentials, approve a source,
schedule collection, host a feed or alter production.

## Versions and compatibility

| Contract | Manifest version | Job projection | Providers |
|---|---|---|---|
| V1 (unchanged default) | `aijobs-static-v1` | `feed-job-v1` | Original provider enum |
| V2 (explicit opt-in) | `aijobs-static-v2` | `feed-job-v2` | V1 providers plus `usajobs`, `workday` |

The two v1 schema files, fixtures and wire shape are unchanged. The old synthetic
manifest's exact hash is pinned by a regression test. Default `feed.export()` and
`feed.accept()` still use v1 and reject the new providers. The validator dispatches
only on a supported manifest version and rejects mismatched job-schema versions;
`expected_version` pins a consumer to one supported contract. The pointer's version
must equal the pointed manifest's version.

V2 job records use the same canonical fields and `schema_version: 1`; the **feed**
version changes, not the canonical field meanings. The only job-schema validation
change is the provider enum. No sponsorship, visa, citizenship, eligibility or
other inferred eligibility fields are added. The same public-field candidate
allowlist excludes ad text, hashes, compensation, provenance URLs and credentials.
Both versions keep `rights: review-required`; successful validation is not public
release approval. [DATA-PROVENANCE.md](../DATA-PROVENANCE.md) continues to apply.

Use separate local export/acceptance roots, for example `data/feed/v1` and
`data/feed/v2`. Each retains `DATE/RUN/{manifest.json,snapshot.jsonl}` plus its own
`latest-accepted.json`. Acceptance refuses to mix versions in an existing store,
including rollback. Bootstrap a new v2 store from a full retained prior state plus
new captured results; keep the v1 store serving unchanged until the consumer is
explicitly upgraded. Reusing a date/run with different bytes remains an error.

## Observation and closure evidence

V2 adds `observed_in_run: boolean` to each JSONL envelope. The job projection stays
under `job`, beside `freshness`. Each source-health entry adds `closure_safe`.
Counts (`postings`) mean **records observed in the successful current capture**,
not all retained open records. The same coverage fields count source states only;
they do not measure employer-market coverage.

| Evidence | State retained in snapshot |
|---|---|
| Observed in a successful source capture | Open, current; last_seen equals the capture completion date |
| Missing from a complete USAJOBS search | Previous job unchanged, stale_unknown; no closure |
| Missing from a complete closure-safe board | Previous fields retained, status gone, current absence evidence |
| Failed, blocked or unattempted source | Previous job unchanged, stale_unknown |

USAJOBS source entries must have `closure_safe: false`; v2 rejects USAJOBS `gone`
records because this adapter provides no authoritative closure evidence. Workday
returns closure-safe results only after every unfiltered page and detail validates.
An observed record must be open and belong to an `ok` source. A closure-safe `ok`
source cannot retain an unobserved open record. Counts reconcile to observation
flags, not dates guessed from prior state. This distinguishes two captures on the
same day: an old last_seen date alone never marks a row newly observed.

During forward acceptance, prior IDs cannot disappear. New IDs must be observed;
first_seen is preserved and last_seen cannot regress. Unobserved prior rows cannot
change fields; only a closure-safe successful board can change their status to
gone. Invalid state, corrupt bytes or a failed pointer switch retains prior good
state. Explicit rollback selects a retained validated snapshot of the same version.

## Offline captured-result bridge

```python
from aijobs import feed

# previous: all retained canonical job records, including gone/stale rows.
# captures: already obtained source_api.Result objects; never raw ad payloads.
bundle = feed.export_results(
    "data/feed/v2-candidates", previous, captures,
    run_id="approved-capture-001",
    started_at="2026-10-25T11:59:00Z",
    completed_at="2026-10-25T12:01:00Z",
    generated_at="2026-10-25T12:02:00Z",
)
feed.validate_bundle(bundle, expected_version=feed.VERSION_V2)
feed.accept("data/feed/v2-accepted", bundle, version=feed.VERSION_V2)
```

This is an interface example, not authorization to collect. `export_results` merges
captured complete results using the existing conservative state helper and derives
source counts/observation IDs. Failed results must contain no partial records or
closure permission. Duplicate source captures/IDs, USAJOBS closure permission and
mismatched record identities fail. Missing source captures become unknown for
retained records. `provenance.collected_at` for newly observed input records must
be UTC seconds (`...Z`) within the supplied capture window; retained records need
no new timestamp. Captures must use the completion UTC date, as in v1. The bridge
exports only the public projection, never the private input provenance or ad hash.

The bridge takes existing `Result` values; it does not authenticate fabricated
captures or independently verify source permission. Keep the original gated
capture path and source-review evidence as the trust boundary. Full retained
canonical state can be reconstructed from accepted `row['job']` projections for
this feed's purposes. That projection is not a backup of excluded private fields.
Persist operational error codes and Retry-After in the scheduler's private state;
the public manifest carries only safe source status/counts and closure capability.

## CLI for a future captured full-state pair

`python3 -m aijobs.feed export --version aijobs-static-v2` uses the existing
`--current`, `--boards`, `--out`, run ID and time arguments. V2 board inputs require
explicit `closure_safe` and `observed_ids` in addition to provider/board/read_ok/
postings. A successful board's IDs must exactly match its observed open rows;
failed boards have no observed IDs and cannot authorize closure. Do not derive
observation IDs from last_seen, or feed the collector's dated subset as full state.
For adapters, prefer the captured-result bridge, which constructs this evidence.

`python3 -m aijobs.feed validate BUNDLE --version aijobs-static-v2` pins validation;
omitting the flag detects either supported version and rejects unknown versions.
The default export remains v1. All raw/candidate paths above are beneath ignored
`data/feed/`. Committed tests generate temporary synthetic bundles only.

The [v1 consumer acceptance checklist](static-feed-v1.md#importer-acceptance-checklist-seisjobs-handoff)
continues to apply: fixed HTTPS origin, bounded input/decompression, hash/size/count
checks, SHA-256 as corruption detection rather than authentication, transactional
consumer imports, retained prior good state, freshness display and explicit rollback.
V2 additionally requires consumers to preserve observation/closure semantics and
pin the supported version before switching their configured feed root.

## Verification and remaining prerequisites

`python3 -m unittest discover -s tests` covers both mocked adapters through canonical
records, v2 export/validation and atomic acceptance; complete empty searches versus
boards; gates, failed/unattempted sources, recovery, version mismatches, corruption,
retries and rollback. V1 fixtures still pass and v1 rejects each new provider.

Live prerequisites are unchanged: separately approved USAJOBS credential provisioning;
a permitted Workday source with current terms/robots and endpoint/payload evidence;
atomic capture handoff; source/field redistribution review; production consumer,
hosting, freshness policy and operational scheduling. No live collection or public
feed was performed to validate this integration.
