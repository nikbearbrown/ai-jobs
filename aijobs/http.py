"""One polite HTTP GET for every provider: identifies itself, times out, retries 429/5xx once with backoff."""
import json
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

UA = "ai-jobs/0.1 (public job-board research; contact bear@bearbrown.co)"

# Minimum seconds between requests to one host, across all threads. Workable answered 429 to an unthrottled probe
# (2026-10-24), and a 429 must never be read as "no such board".
MIN_INTERVAL = {"apply.workable.com": 1.2, "api.smartrecruiters.com": 0.1, "api.lever.co": 0.1,
                "boards-api.greenhouse.io": 0.05, "api.ashbyhq.com": 0.1}
_last, _lock = {}, threading.Lock()
_blocked_until = {}  # host -> epoch seconds; set when a host answers 429 with a long Retry-After, honoured until then
LONG_RETRY = 300


def _throttle(url):
    host = urlparse(url).netloc
    gap = MIN_INTERVAL.get(host, 0.0)  # unknown hosts, including every {slug}.recruitee.com, are not throttled
    if not gap:
        return
    with _lock:
        now = time.monotonic()
        wait = _last.get(host, 0.0) + gap - now
        _last[host] = max(now, _last.get(host, 0.0) + gap)
    if wait > 0:
        time.sleep(wait)


def get_json(url, timeout=25, retries=2):
    """Returns (status, data). status is the HTTP code, or a short string for network errors. data is None unless 200 + JSON."""
    last = "error"
    host = urlparse(url).netloc
    if _blocked_until.get(host, 0) > time.time():
        return 429, None  # told to stay away; do not ask again until the Retry-After has passed
    for attempt in range(retries + 1):
        try:
            _throttle(url)
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                try:
                    return r.status, json.loads(body)
                except ValueError:
                    return r.status, None
        except urllib.error.HTTPError as e:
            last = e.code
            ra = int(e.headers.get("Retry-After", "0") or 0) if str(e.headers.get("Retry-After", "")).isdigit() else 0
            if e.code == 429 and ra > LONG_RETRY:
                _blocked_until[host] = time.time() + ra
                return 429, None
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = ra or 5 * (attempt + 1)
                time.sleep(min(wait, 60))
                continue
            return e.code, None
        except Exception as e:  # DNS failure, timeout, reset
            last = type(e).__name__
            if attempt < retries:
                time.sleep(1 + attempt)
                continue
    return last, None
