# Static feed v1: offline architecture and consumer contract

Status: architecture implemented and tested with synthetic data only. Nothing is
hosted, scheduled, collected, or published by this module. The existing collector
and deployment scripts are unchanged. The seis.jobs builder is a separate project.

## Shape and versions

The feed is a full replacement snapshot, including all known `open` and `gone`
records. Identity remains canonical `provider:board:source_id`; it is not a new
feed-specific key. A consumer can bootstrap from one accepted snapshot. Changes
are informational initially: there is no required delta stream, cursor or replay
chain. Optional future change summaries must not become necessary for correctness.

```text
<local-feed-root>/
  2026-10-24/synthetic-001/
    manifest.json
    snapshot.jsonl
  latest-accepted.json
```

Date is the UTC run-completion date; run IDs match
`[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}`. Multiple runs per day have different IDs. A run
ID's files are immutable: exact-byte retries are idempotent; changed bytes with
the same date/run fail. Corrections get a new run ID. File paths contain no URL,
query, fragment, traversal or user-controlled host.

`manifest.json` follows [feed-manifest-v1.schema.json](../schema/feed-manifest-v1.schema.json):

| Field | Meaning |
|---|---|
| `schema`, `job_schema` | Exact supported versions: `aijobs-static-v1`, `feed-job-v1` |
| `date`, `run_id` | Immutable snapshot identity |
| `started_at`, `completed_at`, `generated_at` | UTC timestamps at second precision; start ≤ completion ≤ generation |
| `mode` | `full`; no inference of closures from omission |
| `rights` | `review-required`; this implementation does not approve public data release |
| `snapshot` | Fixed `snapshot.jsonl` path, SHA-256 of exact uncompressed bytes, byte size, record count |
| `source_health` | One entry per known `(provider, board)`: `ok`, `failed`, or `unknown`; successful current posting count, otherwise null |
| `coverage` | `known_boards`, `ok`, `failed`, `unknown`, reconciled to the health entries |

Here “known” is the union of boards attempted this run and boards represented in
full current state. It is not the number of employers, all discoverable boards,
or a labor-market denominator. Empty never-attempted boards cannot be inferred
from posting state. A wider source inventory and sector/geographic denominators
are future metadata, requiring a new compatible contract decision. A dropped or
unattempted source with retained postings is `unknown`. Do not describe this as
complete market coverage.

Every UTF-8 JSONL line is `{"job": <canonical projection>, "freshness": <state>}`.
The public-candidate job shape is frozen in
[feed-job-v1.schema.json](../schema/feed-job-v1.schema.json), copied from the actual
canonical v1 field definitions. Required/optional fields and null meanings remain
canonical; unknown values are not fabricated. JSON rejects duplicate keys,
nonfinite numbers, unknown fields and duplicate posting IDs. The Python validator
implements the keyword subset used in these pinned schemas; it is not a general
JSON Schema implementation. Unsupported schema versions fail closed. Do not widen
v1 fields silently; version the contract, validator and consumer together.

## Fields and rights

The exhaustive candidate allowlist in `aijobs.feed.FIELDS` is:

```text
schema_version id provider board source_id company company_id title url apply_url
locations country_codes workplace department team employment_type posted_at
updated_at inferred first_seen last_seen status
```

The `inferred` object retains the canonical rule names and versions; conclusions
are not promoted to board facts. Compensation (including `raw`), ad text, ad
hashes, provenance source URLs, error bodies, contact details, credentials and
unrecognized fields do not enter the feed. Canonical input itself is validated,
so unexpected top-level or nested fields fail rather than leak through.

These fields are candidates, **not blanket permission to publish them**. No
real-data publishing command exists here. Before any public feed, record approved
sources and fields, applicable terms and attribution per [DATA-PROVENANCE.md](../DATA-PROVENANCE.md).
The MIT software license grants no rights to third-party employer data. A later
release policy must be validated explicitly, not by changing `rights` informally.

## Freshness and closure semantics

`job.status` stays canonical `open` or `gone`. `freshness` is `current` only when
the source was successfully read in this run; otherwise it is `stale_unknown`.
A stale `open` record means “last observed open; current availability unknown.”
A stale `gone` record retains a historical observation, not a new closure.
`first_seen` and `last_seen` are dates, not exact observation times. `current`
means checked during this run, not guaranteed available now. Show run completion,
last-seen date and source health in the UI; as time passes a previously current
snapshot becomes old. The consumer must apply an explicit age policy (initial
suggestion: show a stale banner after 48 hours and retain the prior data).

Only a successful full board read supports changing a prior open record to gone.
Failure, rate limits, unsupported systems, missing boards, transport errors and
invalid imports never imply closure. An importer keeps all previous IDs; a full
snapshot omitting one fails acceptance. A failed/unattempted source must carry
its previous job records unchanged, tagged stale/unknown. Successful board counts
must match its open rows, whose `last_seen` equals the run date. Cross-board
identity deduplication is not implemented.

## Offline exporter and local acceptance reference

The collector's dated `jobs.jsonl` is **not** a safe full-state input: it can omit
older open postings on failed boards. Use a captured `current.jsonl` and the
matching run's `boards.json`. The existing collector overwrites current state and
dated outputs; it does not provide an atomic multi-file handoff. Before future
integration, capture both files after successful completion under a single-writer
lock, assign run timestamps/ID, and prove they belong to the same run. The exporter
cannot independently prove their common origin. Do not export while collection
or reinference is running. Failed overall collection must not promote a feed.

Safe demo, using only committed synthetic input:

```bash
python3 -m unittest discover -s tests
python3 -m aijobs.feed export \
  --current tests/fixtures/feed/current.jsonl \
  --boards tests/fixtures/feed/boards.json \
  --out data/feed-demo \
  --run-id synthetic-001 \
  --started-at 2026-10-24T11:59:00Z \
  --completed-at 2026-10-24T12:00:00Z \
  --generated-at 2026-10-24T12:01:00Z
python3 -m aijobs.feed validate data/feed-demo/2026-10-24/synthetic-001
```

`export()` writes staging files, validates all bytes and counts, then renames the
bundle to its immutable date/run path. It does not advance a pointer.
`accept(local_store, candidate)` is a local Python reference for consumer staging:
it validates the candidate and prior pointer, checks transitions, copies a verified
bundle into the local store, then uses `os.replace` to switch `latest-accepted.json`.
The pointer contains only `schema`, the relative `manifest` path, and the manifest's
exact-byte `sha256`. Readers see the whole old or new pointer. The candidate store
must be local and trusted; the helper is not an HTTP client or a database importer.

Repeated identical acceptance is safe. An older completion timestamp requires
explicit `accept(..., rollback=True)` and an already retained valid local bundle.
Equal timestamps with different manifests fail as ambiguous. Validation or pointer
write failure leaves the prior pointer intact. Retain previous snapshots and record
acceptance/rollback decisions in the real consumer's audit log. The local helper
has an exclusive `.feed.lock`; competing writers fail. After a process crash,
confirm no writer remains before removing a stale lock. Staging directories and
unreferenced bundles may remain; neither is accepted merely by existing. This is
process-level atomic visibility, not a guarantee of power-loss durability across
all filesystems. Hosting/object-storage promotion needs its own conditional-write
and durability implementation before use.

## Importer acceptance checklist (seis.jobs handoff)

- [ ] Configure one fixed HTTPS origin and base path outside feed content. Fetch
  the pointer, manifest and snapshot only from that origin. Reject credentials,
  non-HTTPS URLs, redirects, cross-origin resolution, traversal and unexpected
  filenames. Never fetch a job's `url`/`apply_url` or a manifest-supplied host.
- [ ] Set connect/read/total timeouts, bounded retries and response limits. Honor
  Retry-After. No alternate-host or proxy workarounds. Default to identity content
  encoding: v1 files are uncompressed. If gzip is added later, limit both compressed
  input and expanded output, bound expansion ratio, and reject archive containers
  or multiple members. Never trust Content-Length alone.
- [ ] Enforce hard ceilings while streaming: pointer 4 KiB, manifest 4 MiB, snapshot
  256 MiB, JSONL line 64 KiB, 500,000 records. Limit JSON nesting (e.g. 32), string
  lengths and parse time before allocation in the network importer. The local
  reference bounds bytes/lines/counts; it is not a hardened streaming network parser.
- [ ] Pin supported schema versions. Verify manifest hash from pointer, snapshot
  size/hash/count, canonical types/enums/IDs, source health, coverage, dates, unique
  IDs and rights policy. SHA-256 checks corruption; **it does not authenticate the
  producer**. HTTPS origin configuration and controlled publishing access are the
  initial trust boundary; signatures would be a separate design.
- [ ] Reject implausible/future timestamps, excessive snapshot age and unexpected
  count/coverage changes using agreed policy. Treat an empty successful board as
  possible, but do not accept an unexplained feed-wide collapse automatically.
- [ ] Stage into an isolated table/version; validate against the previous accepted
  state. Carry failed/unattempted sources, reject dropped IDs and false closures,
  preserve first-seen dates, and never regress last-seen dates on forward imports.
- [ ] Commit imported rows and accepted version in one database transaction, then
  invalidate caches. A failed batch keeps the prior accepted version serving with
  an age/health banner. An interrupted attempt is retryable by run ID plus hash.
- [ ] Provide rollback to a retained validated version, with an audit reason and
  explicit cache refresh. Do not silently follow older/equal-time changed pointers.
- [ ] Render text as escaped text; allow only safe HTTP(S) outbound links without
  credentials; never render source HTML, execute fields or auto-fetch links.
- [ ] Show attribution, source coverage, source failures and freshness. Title-based
  seniority/family labels are unvalidated inferences, not eligibility guarantees.
- [ ] Pass synthetic tests for partial source failure, recovery, corrupt/truncated
  files, bad types, duplicate IDs, missing prior IDs, unknown versions, immutable
  collisions, idempotency and rollback before enabling any production import.

Remaining integration: source/field rights approval, atomic collector handoff,
production consumer transaction and audit log, agreed freshness/drop thresholds,
fixed hosting origin and publisher access, cache policy and operational monitoring.
None of those is configured by this architecture change.
