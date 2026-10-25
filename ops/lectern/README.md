# Lectern on the Hetzner box

## Executive summary

**What this is.** Lectern, Professor Bear's job watch (the six watched boards, the new-listing posts and the faculty feed in `#professor-bear`), set up to run once a day on the always-on Hetzner box instead of on a laptop. Lectern's own code is not changed: the box runs its `ops/daily.sh` as it is.

**Why.** Lectern had no scheduler. It ran only when someone started it ("run it again"), so it posted only on days a person remembered. On the box it runs every day.

**State on 2026-10-24.** Installed and tested on the box, **timer off, no webhook yet**. A dry run on a scratch copy collected the real boards and showed what the first real run will post: 10 new listings (OpenAI 5, Anthropic 2, Canva 2, Figma 1) and 9 new faculty listings, in two messages each. It posted nothing. The box's Lectern files match the Mac's byte for byte (93 of 93).

**To switch on.** Bear creates a webhook for `#professor-bear`, pastes it on the box (below), runs one test line, and the timer is enabled. The first run is then the next 12:30 UTC.

## How it is arranged

| Piece | Where |
|---|---|
| User | `lectern` (no sudo, no login shell; separate from `jobs`, which holds the ai-jobs webhook and deploy key) |
| Code | a sparse, read-only clone of the PUBLIC course repo at `/home/lectern/course` (only `fall-2026/nik-bear-brown/lectern`); no key needed |
| Working copy | `/home/lectern/lectern`, mirrored from the clone before each run. `runs/` and `faculty-runs/` are the box's own state and are never overwritten or deleted |
| Wrapper | `/home/lectern/bin/run-lectern.sh` (copy of `ops/lectern/run-lectern.sh`) |
| Failure notice | `/home/lectern/bin/lectern_notice.py`: one line to `#professor-bear` if a run does not complete. Public-channel rules: no path, email or webhook URL; pings nobody |
| Schedule | `lectern-daily.timer`, 12:30 UTC daily (about 08:30 US Eastern) |
| Webhook | `/home/lectern/.discord-webhooks/professor-bear`, mode 600, dir 700. Lectern's own code finds it there |
| Limits | one core, 1 GB, Nice 10, sandboxed (`ProtectSystem=strict`, network and `/home/lectern` only) |

## What was seeded, and why it matters

Lectern remembers what it has already posted in `runs/posted-to-discord.json`, a file that is **not in git** (31 ids, copied from the Mac). Without it the first run would repost old listings. `runs/published-state.json` (as of 2026-10-18) and `faculty-runs/state/seen.json` came from the repo. The box now owns these files. The Mac's copies stop being current the day the timer is enabled.

## Two things that would hurt, and the guard against each

* **A real run before the webhook exists.** Lectern's faculty feed marks items as seen *before* it tries to post, so a run with no webhook would use up the day's listings without showing them. That is why the timer stays off until the webhook is in place.
* **Running Lectern on the Mac with posting after the cutover.** The Mac does not know what the box posted, so it would repost. On the Mac use `./ops/daily.sh --no-post`, and treat the box as the poster.

## Switching it on

1. In Discord (SEIS AI Lab), `#professor-bear`, Edit Channel, Integrations, Webhooks, **New Webhook**. A separate one for the box is better than reusing the Mac's: either can be deleted without breaking the other.
2. On your Mac, paste it when asked (it does not echo and does not enter chat or history):

```bash
ssh -t hetz 'read -rs -p "Paste the #professor-bear webhook URL (not echoed): " U && echo && printf "%s\n" "$U" | sudo -u lectern tee /home/lectern/.discord-webhooks/professor-bear >/dev/null && sudo chown lectern:lectern /home/lectern/.discord-webhooks/professor-bear && sudo chmod 600 /home/lectern/.discord-webhooks/professor-bear && unset U && echo written'
```

3. Test line (HTTP 204 means Discord accepted it):

```bash
ssh hetz 'sudo -u lectern -H python3 /home/lectern/bin/lectern_notice.py 2026-10-24 test'
```

4. Enable the timer: `ssh hetz 'sudo systemctl enable --now lectern-daily.timer'`

## Operating it

```bash
ssh hetz 'systemctl list-timers lectern-daily.timer --no-pager'
ssh hetz 'sudo journalctl -u lectern-daily.service -n 60 --no-pager'
ssh hetz 'sudo systemctl start --no-block lectern-daily.service'        # run now (posts, if the webhook exists)
ssh hetz 'sudo -u lectern touch /home/lectern/STOP'                      # halt; rm to resume
```

Update the code by pushing to the course repo as usual (Rule 3 in its CLAUDE.md); the box pulls it before each run. Update the wrapper by copying `ops/lectern/*` to `/home/lectern/bin/` and the units to `/etc/systemd/system/`.

**Remove it:** `sudo systemctl disable --now lectern-daily.timer`, delete `/etc/systemd/system/lectern-daily.*`, `sudo userdel -r lectern`, and delete the box's webhook in Discord.

## Not moved

The big-four collectors (Google, Amazon, Microsoft, Meta; they take hours and use a local database) and the lab-outreach records (they name people and stay off any server). Lectern's n8n and other "forms" are not run here.

## Open

* The daily run commits and pushes nothing, as before. The published state on GitHub will fall behind the box's; pushing a delta needs Bear's word and a run on a copy of the box's state.
* Lectern is a subset of what ai-jobs reads. A later step could make Lectern a filter over ai-jobs' postings instead of its own collector; not done, because Lectern's filter was tested against its own collector's output.
* The course folder's `CLAUDE.md` (Rule 4) and `HISTORY.md` still describe `daily.sh` as run by hand. They are shared files in a repo with other changes in flight, so they were not edited here.
