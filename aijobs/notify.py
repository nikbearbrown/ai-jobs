"""Post a daily status line to a Discord channel: how many postings the collector added, and what types.

    python3 -m aijobs.notify DATE [--status ok|halted|failed|test] [--step NAME] [--dry-run]

COUNTS ONLY. The message never lists a posting, a company's ad, a person, an address or a path. It says how many new
postings the day's run found, how many closed, and how the new ones split by title family (SEIS course area) and by
entry-level / internship markers in the title.

The webhook URL is a secret. It is read from a file (default ~/.discord-webhook, override with AIJOBS_DISCORD_WEBHOOK_FILE),
which must not be readable by group or others. It is never printed, logged or put on a command line. With no file the
module does nothing (and says so), so deploying the code before the webhook exists is safe.

A failed or halted run posts a one-line notice instead, so a missing report is not the only sign of trouble.
"""
import argparse
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .paths import JOBS, TITLES

UA = "ai-jobs/0.1 (daily status; contact bear@bearbrown.co)"
REPO = "https://github.com/nikbearbrown/ai-jobs"
TOP_FAMILIES = 8
NO_FAMILY = "(no SEIS title family)"
FORBIDDEN = [re.compile(p) for p in (r"discord(app)?\.com/api/webhooks", r"/Users/", r"/home/", r"[\w.+-]+@[\w-]+\.[\w.-]+")]


class Unsafe(ValueError):
    pass


def check_safe(text):
    """The same refusals as Bear's discord_post.py: no webhook URL, local path or email address in a public post."""
    for rx in FORBIDDEN:
        if rx.search(text):
            raise Unsafe(f"refusing to post: text matches {rx.pattern!r}")


def family_labels():
    try:
        return {f["key"]: f["label"] for f in json.loads(TITLES.read_text())["families"]}
    except (OSError, ValueError, KeyError):
        return {}


def _n(x):
    return f"{x:,}"


def build_ok(summary, labels=None):
    labels = labels or family_labels()
    d = summary["date"]
    ok, req = summary["boards_read_ok"], summary["boards_requested"]
    opened = summary["postings_open"]
    if summary.get("first_run"):
        head = f"First run on this server: {_n(opened)} postings are open across {ok} of {req} boards. Every posting counts as new on a first run, so there is no daily figure yet."
        return {"title": f"ai-jobs: first collection ({d})", "description": head, "url": f"{REPO}/blob/main/data/jobs/{d}/summary.json",
                "footer": "Counts only. Daily figures start with the next run."}
    new, gone = summary["new_this_run"], summary["gone_this_run"]
    fam = summary.get("new_by_title_family", {})
    sen = summary.get("new_by_seniority", {})
    seis = {k: v for k, v in fam.items() if k not in (NO_FAMILY, "leadership")}
    lines = [f"Read {ok} of {req} boards. {_n(opened)} postings are open: {_n(new)} new, {_n(gone)} closed."]
    if new:
        lines.append("")
        lines.append(f"New postings with a title in a SEIS family: {_n(sum(seis.values()))} of {_n(new)}")
        for k, v in list(seis.items())[:TOP_FAMILIES]:
            lines.append(f"- {labels.get(k, k)}: {_n(v)}")
        rest = len(seis) - TOP_FAMILIES
        if rest > 0:
            lines.append(f"- {rest} more families")
        early = sen.get("entry", 0) + sen.get("intern", 0)
        lines.append("")
        lines.append(f"Entry-level or internship by title: {_n(early)} of the new postings")
    failed = summary.get("boards_failed") or []
    if failed:
        lines.append("")
        lines.append(f"{len(failed)} board(s) could not be read this run; their postings were left as they were, not closed.")
    return {"title": f"ai-jobs daily: {_n(new)} new postings ({d})", "description": "\n".join(lines),
            "url": f"{REPO}/blob/main/data/jobs/{d}/summary.json",
            "footer": "Counts only. Types come from reading titles, not from judging the roles. Entry-level counts are a floor: most titles carry no level word."}


def build_notice(date, status, step=None):
    if status == "test":
        return {"title": "ai-jobs: test post", "description": "This is a test of the daily status post from the server. No action needed.",
                "footer": "Status notice. No postings are listed here."}
    if status == "halted":
        text = ("The daily run stopped itself: more than half of the boards failed to load, so nothing was published and no posting was "
                "closed. It will not run again until its STOP file is removed.")
        title = f"ai-jobs: run halted ({date})"
    else:
        text = f"The daily run did not complete{f' (step: {step})' if step else ''}. Nothing was published for this date. The server journal has the details."
        title = f"ai-jobs: run failed ({date})"
    return {"title": title, "description": text, "footer": "Status notice. No postings are listed here."}


def to_payload(embed):
    check_safe(" ".join(str(embed.get(k, "")) for k in ("title", "description", "footer", "url")))
    e = {"title": embed["title"], "description": embed["description"], "footer": {"text": embed["footer"]}}
    if embed.get("url"):
        e["url"] = embed["url"]
    return {"embeds": [e], "allowed_mentions": {"parse": []}}  # a status post must never ping anyone


def read_webhook():
    path = Path(os.environ.get("AIJOBS_DISCORD_WEBHOOK_FILE", "~/.discord-webhook")).expanduser()
    if not path.exists():
        return None, "no webhook file configured; not posting"
    if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        return None, f"webhook file {path.name} is readable by group or others; refusing to use it (chmod 600)"
    url = path.read_text().strip()
    if not url.startswith("https://discord.com/api/webhooks/"):
        return None, "webhook file does not hold a Discord webhook URL; not posting"
    return url, None


def send(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # network error: report the type only, never the URL
        return type(e).__name__


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--status", choices=["ok", "halted", "failed", "test"], default="ok")
    ap.add_argument("--step")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.status == "ok":
        embed = build_ok(json.loads((JOBS / a.date / "summary.json").read_text()))
    else:
        embed = build_notice(a.date, a.status, a.step)
    payload = to_payload(embed)  # raises Unsafe before anything is sent
    if a.dry_run:
        print(embed["title"]); print(embed["description"]); print("--", embed["footer"])
        return 0
    url, why = read_webhook()
    if not url:
        print(why)
        return 0
    result = send(url, payload)
    print(f"discord: HTTP {result}")  # 204 means accepted
    return 0 if result in (200, 204) else 1


if __name__ == "__main__":
    sys.exit(main())
