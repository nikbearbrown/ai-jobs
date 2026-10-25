"""One-line failure notice to #professor-bear from the box. Stdlib only.   usage: lectern_notice.py DATE STEP

Same rules as Lectern's own posts: the channel is public, so text with a local path, an email address or a webhook URL is
refused; the webhook is read from ~/.discord-webhooks/professor-bear (mode 600) and never printed; nobody is pinged.
With no webhook file it does nothing.
"""
import json, os, re, stat, sys, urllib.request

date, step = (sys.argv + ["", ""])[1:3]
path = os.path.expanduser("~/.discord-webhooks/professor-bear")
if not os.path.exists(path):
    print("no webhook file; no notice sent"); sys.exit(0)
if os.stat(path).st_mode & (stat.S_IRWXG | stat.S_IRWXO):
    print("webhook file is readable by group or others; refusing to use it"); sys.exit(0)
url = open(path).read().strip()
if not re.fullmatch(r"https://(discord|discordapp)\.com/api/webhooks/\d+/[\w-]+", url):
    print("webhook file does not hold a Discord webhook URL"); sys.exit(0)
if step == "test":
    title, text = "Lectern: test post", "This is a test post from the server. No action needed."
else:
    title = f"Lectern: run failed ({date})"
    text = f"Lectern's daily run on the server did not complete (step: {step}). Nothing was posted for this date. The server journal has the details."
if re.search(r"/[U]sers/|/home/\w+|[\w.+-]+@[\w-]+\.[\w.]+|discord(app)?\.com/api/webhooks", title + text):
    print("NOT SENT: text contains a local path, email address or webhook URL"); sys.exit(0)
payload = {"embeds": [{"title": title, "description": text}], "allowed_mentions": {"parse": []}}
req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                             headers={"Content-Type": "application/json", "User-Agent": "lectern-box/0.1"})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print(f"discord: HTTP {r.status}")
except Exception as e:
    print(f"discord post failed: {type(e).__name__}")
