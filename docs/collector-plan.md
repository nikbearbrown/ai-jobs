# Running the collector on the Hetzner box

## Executive summary

**What this is.** How `aijobs` runs on the `hetz` box since 2026-10-24, what leaves the box, and how to stop or remove it.
**What was done.** A new unprivileged user `jobs` (no sudo, no shell login, not in `docker`) owns `/home/jobs/ai-jobs`, a clone of this repo. A systemd timer runs `ops/run-daily.sh` at 04:30 UTC (up to 10 min random delay): it pulls the repo, reads every confirmed board, and commits only `summary.json`, `boards.json` and `seis-fit.md` for the day. A second timer re-probes which ATS each company uses on Wednesdays at 03:00 UTC. No keys of any kind are on the box except one write-only-to-this-repo GitHub deploy key.
**What was measured.** The test run took 1 min 56 s wall, 19 s CPU and 642 MB peak memory for 715 boards and 84,282 postings; the box is 2 cores and 3.8 GB with the auditor alongside. The units cap it at 1 core, 1.8 GB, `Nice=10`, idle I/O.
**What has not happened.** The first scheduled run (2026-10-25) and the first real push from the box. The test run produced the same files already in the repo, so "nothing new to commit" was the correct result; the deploy key's write access was proven with a throwaway branch that was deleted.

## What leaves the box, and what does not

| Leaves (committed to the repo) | Stays on the box |
|---|---|
| `data/jobs/DATE/summary.json` (counts) | `data/jobs/DATE/jobs.jsonl`, `data/jobs/current.jsonl` (the postings; last 7 days kept) |
| `data/jobs/DATE/boards.json` (per-board read status and counts) | `data/jobs/DATE/entry-level.csv` (titles and links of individual postings; gitignored) |
| `data/jobs/DATE/seis-fit.md` (aggregates by family and company) | |
| one Discord status post per run (counts only; see below) | |
| weekly: `data/probes/probe-DATE.jsonl` + `.done`, `boards.csv`, `ats-coverage.md` (which company is on which ATS; no postings) | |

`run-daily.sh` stages these paths by name (`git add -- <three files>`), so nothing else can be committed by it.

## Who and what

* User `jobs`, uid 994, home `/home/jobs` (mode 750, so `auditor` and `scanner` cannot read it). Not `auditor` (holds the auditor's deploy key) and not `bbc` (root via sudo).
* Deploy key: `/home/jobs/.ssh/id_ed25519`, registered on `nikbearbrown/ai-jobs` only, read-write, titled "hetz jobs user (daily collector)". GitHub's host key was checked against the fingerprint GitHub publishes before it was trusted.
* Units in `/etc/systemd/system/`: `ai-jobs-daily.{service,timer}`, `ai-jobs-weekly-probe.{service,timer}` (copies of `ops/`). Sandbox: `NoNewPrivileges`, `ProtectSystem=strict` with `/home/jobs` writable, `PrivateTmp`, network families restricted to IP and unix sockets.
* **Code updates itself**: each run starts with `git pull --rebase`, so whatever is on `main` runs on the box the next morning as the unprivileged user. Treat pushes to `main` accordingly.

## Daily Discord status post

After each run the box can post one message to a Discord channel: how many postings were new and closed that day, how the new ones split by title family (the SEIS course areas), and how many carry an entry-level or internship marker. **Counts only**: no posting, company ad, person, address or path is ever in it, and `allowed_mentions` is empty so it cannot ping anyone. A failed or self-halted run posts a one-line notice instead, so a missing report is not the only sign of trouble. It cannot report a run that never started (box down, timer off): the absence of a post is itself the signal.

It does nothing until a webhook exists. The webhook URL is a secret and must not pass through chat, a command line or shell history. Create a channel and webhook in Discord (channel settings, Integrations, Webhooks), then on your own machine:

```bash
ssh -t hetz 'read -rs -p "Paste the Discord webhook URL (not echoed): " U && echo && printf "%s\n" "$U" | sudo -u jobs tee /home/jobs/.discord-webhook >/dev/null && sudo chown jobs:jobs /home/jobs/.discord-webhook && sudo chmod 600 /home/jobs/.discord-webhook && unset U && echo written'
ssh hetz "sudo -u jobs -H bash -c 'cd /home/jobs/ai-jobs && python3 -m aijobs.notify 2026-10-24 --status test'"   # posts a harmless test line; HTTP 204 means accepted
```

The file must be mode 600; the notifier refuses a file that group or others can read. To stop the posts, delete `/home/jobs/.discord-webhook`; to rotate, run the first command again. On the first run on a fresh machine every posting counts as new, so the post says so instead of reporting a daily figure.

## Operating it

```bash
ssh hetz 'systemctl list-timers "ai-jobs-*" --no-pager'
ssh hetz 'sudo journalctl -u ai-jobs-daily.service -n 60 --no-pager'
ssh hetz 'sudo systemctl start --no-block ai-jobs-daily.service'      # run now
ssh hetz 'sudo -u jobs touch /home/jobs/STOP'                         # safe halt: runs exit quietly
ssh hetz 'sudo -u jobs rm /home/jobs/STOP'                            # resume
```

**Self-halt.** If more than half the boards fail to load in a run (network down, or a block), the collector exits 2, `run-daily.sh` writes `/home/jobs/STOP` itself and commits nothing. A STOP file nobody created means that happened; the journal says why. A single failed board never closes its postings.

**Remove it entirely:**

```bash
ssh hetz 'sudo systemctl disable --now ai-jobs-daily.timer ai-jobs-weekly-probe.timer && sudo rm /etc/systemd/system/ai-jobs-*.{service,timer} && sudo systemctl daemon-reload && sudo userdel -r jobs'
gh repo deploy-key list --repo nikbearbrown/ai-jobs      # then: gh repo deploy-key delete <id> --repo nikbearbrown/ai-jobs
```

## Known limits

* **Workable** is not read (HTTP 429 with a Retry-After of about 23 h hit my Mac's address on 2026-10-24). The weekly probe will try it again on Wednesday, throttled to one request per 1.2 s; it was deliberately not run from the box earlier, to avoid going around the block.
* **Workday-class employers** (most banks, hospitals, consultancies, government) have no adapter yet.
* `current.jsonl` on the box started empty, so its `new_this_run` for 2026-10-24 counts every posting as new; real "new today" figures begin with the 2026-10-25 run.
* The box has one disk (25 GB free). A week of full postings is about 600 MB.
