"""Offline versioned static-feed exporter/validator (v1 default, v2 opt-in). No collection, HTTP, or publication."""
import argparse
from contextlib import contextmanager
from datetime import date, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = "aijobs-static-v1"  # Preserve the existing default and wire format.
VERSION_V2 = "aijobs-static-v2"
VERSIONS = {VERSION: "v1", VERSION_V2: "v2"}


def version_tag(version):
    require(type(version) is str and version in VERSIONS, "unsupported feed version")
    return VERSIONS[version]


def row_freshness(job, health, observed):
    checked = health["state"] == "ok"
    confirmed_absence = job["status"] == "gone" and health["closure_safe"]
    return "current" if checked and (observed or confirmed_absence) else "stale_unknown"


FIELDS = tuple("schema_version id provider board source_id company company_id title url apply_url locations country_codes workplace department team employment_type posted_at updated_at inferred first_seen last_seen status".split())
MAX_MANIFEST = 4 * 1024 * 1024
MAX_SNAPSHOT = 256 * 1024 * 1024
MAX_RECORDS = 500000
MAX_LINE = 64 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def loads(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False, "nonfinite JSON number"))


def read_limited(path, limit):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "file size limit exceeded")
    return data


def check_schema(value, schema):
    """Validate the small keyword subset used by our pinned schemas, using stdlib."""
    types = {"object": lambda v: type(v) is dict, "array": lambda v: type(v) is list,
             "string": lambda v: type(v) is str, "null": lambda v: v is None,
             "integer": lambda v: type(v) is int,
             "number": lambda v: type(v) in (int, float) and math.isfinite(v),
             "boolean": lambda v: type(v) is bool}
    if "type" in schema:
        choices = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        require(any(types[t](value) for t in choices), "wrong field type")
    if "const" in schema:
        require(type(value) is type(schema["const"]) and value == schema["const"], "wrong version/constant")
    if "enum" in schema:
        require(any(type(value) is type(v) and value == v for v in schema["enum"]), "invalid enum")
    if isinstance(value, dict):
        require(set(schema.get("required", [])) <= value.keys(), "missing required fields")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            require(value.keys() <= props.keys(), "unexpected fields")
        for key in value.keys() & props.keys():
            check_schema(value[key], props[key])
    if isinstance(value, list) and "items" in schema:
        for item in value:
            check_schema(item, schema["items"])
    if isinstance(value, str) and "pattern" in schema:
        require(re.fullmatch(schema["pattern"], value) is not None, "invalid string format")
    if type(value) in (int, float):
        require(value >= schema.get("minimum", -math.inf), "value below minimum")
        require(value <= schema.get("maximum", math.inf), "value above maximum")


def schema(name):
    return loads((ROOT / "schema" / name).read_bytes())


def timestamp(value):
    require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), "UTC seconds timestamp required")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def day(value):
    require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "ISO date required")
    return date.fromisoformat(value)


def rows_from_bytes(data):
    require(len(data) <= MAX_SNAPSHOT, "snapshot too large")
    lines = data.splitlines()
    require(len(lines) <= MAX_RECORDS, "too many records")
    require(all(0 < len(line) <= MAX_LINE for line in lines), "invalid line size")
    return [loads(line) for line in lines]


def coverage(health):
    return {"known_boards": len(health),
            **{k: sum(h["state"] == k for h in health) for k in ("ok", "failed", "unknown")}}


def validate_bundle(bundle, *, expected_version=None):
    bundle = Path(bundle)
    manifest_bytes = read_limited(bundle / "manifest.json", MAX_MANIFEST)
    manifest = loads(manifest_bytes)
    require(type(manifest) is dict, "invalid manifest")
    version = manifest.get("schema")
    tag = version_tag(version)
    require(expected_version is None or version == expected_version, "unexpected feed version")
    check_schema(manifest, schema(f"feed-manifest-{tag}.schema.json"))
    started, completed, generated = [timestamp(manifest[k]) for k in
                                     ("started_at", "completed_at", "generated_at")]
    require(started <= completed <= generated, "run times out of order")
    require(day(manifest["date"]) == completed.date(), "date must be UTC completion date")
    health = {}
    for h in manifest["source_health"]:
        key = (h["provider"], h["board"])
        require(key not in health, "duplicate source")
        require((h["state"] == "ok") == (h["postings"] is not None), "invalid source count")
        if version == VERSION_V2:
            require(h["state"] == "ok" or h["closure_safe"] is False, "unread source permits closure")
            require(h["provider"] != "usajobs" or h["closure_safe"] is False, "USAJOBS search cannot close postings")
        health[key] = h
    require(manifest["coverage"] == coverage(list(health.values())), "coverage mismatch")
    raw = read_limited(bundle / "snapshot.jsonl", MAX_SNAPSHOT)
    require(len(raw) == manifest["snapshot"]["bytes"], "snapshot size mismatch")
    require(digest(raw) == manifest["snapshot"]["sha256"], "snapshot checksum mismatch")
    rows = rows_from_bytes(raw)
    require(len(rows) == manifest["snapshot"]["records"], "snapshot count mismatch")
    job_schema = schema(f"feed-job-{tag}.schema.json")
    indexed, counts = {}, {}
    for row in rows:
        keys = {"job", "freshness", "observed_in_run"} if version == VERSION_V2 else {"job", "freshness"}
        require(type(row) is dict and set(row) == keys, "invalid row envelope")
        job = row["job"]
        check_schema(job, job_schema)
        require(job["id"] == f'{job["provider"]}:{job["board"]}:{job["source_id"]}', "identity mismatch")
        require(all(job[k] for k in ("id", "source_id", "board", "title", "company", "url")), "empty identity/display field")
        require(day(job["first_seen"]) <= day(job["last_seen"]) <= completed.date(), "invalid seen dates")
        require(job["id"] not in indexed, "duplicate job id")
        indexed[job["id"]] = row
        key = (job["provider"], job["board"])
        require(key in health, "missing source health")
        state = health[key]["state"]
        if version == VERSION_V2:
            observed = row["observed_in_run"]
            require(type(observed) is bool, "invalid observation flag")
            require(not observed or (state == "ok" and job["status"] == "open"), "invalid observed record")
            require(job["provider"] != "usajobs" or job["status"] == "open", "USAJOBS closure unsupported")
            require(not (state == "ok" and health[key]["closure_safe"] and job["status"] == "open") or observed,
                    "complete board has unobserved open record")
            expected = row_freshness(job, health[key], observed)
            count_record = observed
        else:
            expected = "current" if state == "ok" else "stale_unknown"
            count_record = job["status"] == "open" and state == "ok"
        require(row["freshness"] == expected, "invalid freshness")
        if count_record:
            require(job["last_seen"] == manifest["date"], "successful board has stale open row")
            counts[key] = counts.get(key, 0) + 1
    for key, h in health.items():
        if h["state"] == "ok":
            require(h["postings"] == counts.get(key, 0), "board posting count mismatch")
    return manifest, indexed, manifest_bytes, raw


def build_bundle(records, boards, *, run_id, started_at, completed_at, generated_at, version=VERSION):
    """Project FULL captured current state, never the collector's dated subset."""
    tag = version_tag(version)
    health, observed_ids, observation_sources = {}, set(), {}
    for board in boards:
        require(type(board.get("read_ok")) is bool, "read_ok must be boolean")
        key = (board["provider"], board["board"])
        require(key not in health, "duplicate board")
        health[key] = {"provider": key[0], "board": key[1],
                       "state": "ok" if board["read_ok"] else "failed",
                       "postings": board["postings"] if board["read_ok"] else None}
        if version == VERSION_V2:
            require(type(board.get("closure_safe")) is bool, "closure evidence required")
            ids = board.get("observed_ids")
            require(type(ids) is list and all(type(pid) is str for pid in ids), "observation evidence required")
            require(len(ids) == len(set(ids)), "duplicate observed id")
            require(all(pid.startswith(f"{key[0]}:{key[1]}:") for pid in ids), "observation source mismatch")
            require(not (observed_ids & set(ids)), "duplicate observation across sources")
            require(board["read_ok"] or not ids, "unread source has observations")
            health[key]["closure_safe"] = board["closure_safe"]
            observed_ids.update(ids)
            observation_sources.update({pid: key for pid in ids})
    rows = []
    canonical = schema("job.schema.json")
    for record in records:
        check_schema(record, canonical)
        key = (record["provider"], record["board"])
        h = health.setdefault(key, {"provider": key[0], "board": key[1], "state": "unknown", "postings": None})
        job = {key: record[key] for key in FIELDS if key in record}
        if version == VERSION_V2:
            h.setdefault("closure_safe", False)
            observed = job["id"] in observed_ids
            if observed:
                require(observation_sources[job["id"]] == key, "observation source mismatch")
                collected_at = record.get("provenance", {}).get("collected_at")
                require(timestamp(started_at) <= timestamp(collected_at) <= timestamp(completed_at),
                        "observation outside capture window")
            rows.append({"job": job, "freshness": row_freshness(job, h, observed), "observed_in_run": observed})
        else:
            rows.append({"job": job, "freshness": "current" if h["state"] == "ok" else "stale_unknown"})
    require(observed_ids <= {row["job"]["id"] for row in rows}, "observed ids missing from full state")
    rows.sort(key=lambda row: row["job"]["id"])
    payload = b"".join(encoded(row) for row in rows)
    sources = [health[key] for key in sorted(health)]
    manifest = {"schema": version, "job_schema": f"feed-job-{tag}", "date": completed_at[:10],
                "run_id": run_id, "started_at": started_at, "completed_at": completed_at,
                "generated_at": generated_at, "mode": "full", "rights": "review-required",
                "snapshot": {"path": "snapshot.jsonl", "sha256": digest(payload), "bytes": len(payload), "records": len(rows)},
                "source_health": sources, "coverage": coverage(sources)}
    return encoded(manifest), payload


@contextmanager
def locked(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".feed.lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def install(root, manifest_bytes, payload):
    """Validate in staging, then rename to immutable date/run. Caller holds lock."""
    root = Path(root)
    with tempfile.TemporaryDirectory(prefix=".feed-stage-", dir=root) as temp:
        staging = Path(temp) / "bundle"
        staging.mkdir()
        (staging / "manifest.json").write_bytes(manifest_bytes)
        (staging / "snapshot.jsonl").write_bytes(payload)
        manifest, _, _, _ = validate_bundle(staging)
        target = root / manifest["date"] / manifest["run_id"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            _, _, old_manifest, old_payload = validate_bundle(target)
            require((old_manifest, old_payload) == (manifest_bytes, payload), "immutable run id collision")
        else:
            os.rename(staging, target)
        return target


def export(root, records, boards, **metadata):
    manifest, payload = build_bundle(records, boards, **metadata)
    with locked(root):
        return install(root, manifest, payload)


def export_results(root, previous, results, **metadata):
    """Offline v2 bridge from already captured source_api.Result values.

    Previous is the full retained canonical state (accepted job projections work).
    No fetch, credential lookup, source approval, scheduling, or publication occurs.
    """
    from .source_api import Result, merge
    previous = list(previous)
    require(len({r["id"] for r in previous}) == len(previous), "duplicate prior id")
    boards, sources, current = [], set(), previous
    canonical = schema("job.schema.json")
    for result in results:
        require(isinstance(result, Result), "captured Result required")
        require(type(result.complete) is bool and type(result.closure_safe) is bool, "invalid capture flags")
        key = (result.provider, result.board)
        require(key not in sources, "duplicate captured source")
        sources.add(key)
        require(result.complete or (not result.records and not result.closure_safe), "partial capture has records or closure permission")
        require(result.provider != "usajobs" or not result.closure_safe, "USAJOBS search cannot close postings")
        ids = []
        for rec in result.records:
            check_schema(rec, canonical)
            require((rec["provider"], rec["board"]) == key and rec["status"] == "open", "capture identity/status mismatch")
            ids.append(rec["id"])
        require(len(ids) == len(set(ids)), "duplicate captured id")
        current = merge(current, result)
        boards.append({"provider": result.provider, "board": result.board, "read_ok": result.complete,
                       "postings": len(ids) if result.complete else None,
                       "closure_safe": result.closure_safe, "observed_ids": ids})
    return export(root, current, boards, version=VERSION_V2, **metadata)


def read_pointer(root, *, expected_version=None):
    path = Path(root) / "latest-accepted.json"
    if not path.exists():
        return None
    pointer = loads(read_limited(path, 4096))
    require(type(pointer) is dict and set(pointer) == {"schema", "manifest", "sha256"}, "invalid pointer")
    version_tag(pointer["schema"])
    require(expected_version is None or pointer["schema"] == expected_version, "unexpected pointer version")
    require(type(pointer["manifest"]) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}/[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}/manifest.json", pointer["manifest"]), "invalid pointer path")
    bundle = Path(root) / Path(pointer["manifest"]).parent
    result = validate_bundle(bundle, expected_version=pointer["schema"])
    require(pointer["manifest"] == f'{result[0]["date"]}/{result[0]["run_id"]}/manifest.json', "pointer identity mismatch")
    require(digest(result[2]) == pointer["sha256"], "pointer checksum mismatch")
    return result


def accept(root, candidate, *, rollback=False, version=VERSION):
    """Local acceptance reference; never an HTTP importer or public publisher."""
    version_tag(version)
    manifest, indexed, manifest_bytes, payload = validate_bundle(candidate, expected_version=version)
    root = Path(root)
    with locked(root):
        previous = read_pointer(root, expected_version=version)
        target = root / manifest["date"] / manifest["run_id"]
        if rollback:
            require(target.is_dir(), "rollback requires a retained validated local snapshot")
            retained = validate_bundle(target)
            require(retained[2:] == (manifest_bytes, payload), "rollback content mismatch")
        elif previous:
            old_manifest, old_rows, old_bytes, _ = previous
            require(manifest["completed_at"] >= old_manifest["completed_at"], "older snapshot requires explicit rollback")
            require(manifest["completed_at"] != old_manifest["completed_at"] or manifest_bytes == old_bytes,
                    "ambiguous equal completion time")
            require(old_rows.keys() <= indexed.keys(), "full snapshot lost prior ids")
            states = {(h["provider"], h["board"]): h["state"] for h in manifest["source_health"]}
            source_health = {(h["provider"], h["board"]): h for h in manifest["source_health"]}
            for pid in indexed.keys() - old_rows.keys():
                job = indexed[pid]["job"]
                require(states[(job["provider"], job["board"])] == "ok", "unread source added posting")
                if version == VERSION_V2:
                    require(indexed[pid]["observed_in_run"], "new record was not observed")
            for pid, old in old_rows.items():
                new = indexed[pid]
                require(all(new["job"][k] == old["job"][k] for k in ("provider", "board", "source_id")), "source identity changed")
                require(new["job"]["first_seen"] == old["job"]["first_seen"], "first_seen changed")
                require(new["job"]["last_seen"] >= old["job"]["last_seen"], "last_seen regressed")
                key = (old["job"]["provider"], old["job"]["board"])
                if version == VERSION_V2:
                    if old["job"]["status"] == "open" and new["job"]["status"] == "gone":
                        require(source_health[key]["closure_safe"] and states[key] == "ok", "closure lacks source evidence")
                    if not new["observed_in_run"]:
                        expected_job = old["job"]
                        if source_health[key]["closure_safe"] and states[key] == "ok":
                            expected_job = {**expected_job, "status": "gone"}
                        require(new["job"] == expected_job, "unobserved record changed")
                elif states[key] != "ok":
                    require(new["job"] == old["job"], "unread source changed prior posting")
        target = install(root, manifest_bytes, payload)
        pointer = {"schema": version, "manifest": str(target.relative_to(root) / "manifest.json"), "sha256": digest(manifest_bytes)}
        fd, temporary = tempfile.mkstemp(prefix=".pointer-", dir=root)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded(pointer))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, root / "latest-accepted.json")
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return pointer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("export")
    p.add_argument("--current", required=True)
    p.add_argument("--boards", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--version", choices=VERSIONS, default=VERSION)
    for key in ("run-id", "started-at", "completed-at", "generated-at"):
        p.add_argument("--" + key, required=True)
    p = sub.add_parser("validate")
    p.add_argument("bundle")
    p.add_argument("--version", choices=VERSIONS, default=None, help="require this version, or detect supported version")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            manifest, _, _, _ = validate_bundle(args.bundle, expected_version=args.version)
            print(f'valid {manifest["schema"]}: {manifest["snapshot"]["records"]} records')
        else:
            result = export(args.out, rows_from_bytes(read_limited(args.current, MAX_SNAPSHOT)),
                            loads(read_limited(args.boards, MAX_MANIFEST)), version=args.version,
                            **{k: getattr(args, k) for k in ("run_id", "started_at", "completed_at", "generated_at")})
            print(result)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"feed rejected: {error}\n")


if __name__ == "__main__":
    main()
