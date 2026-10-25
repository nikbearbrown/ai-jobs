"""Opt-in source support: bounded transport and all-or-nothing canonical results.

No automatic registration with the existing credential-free probe/collector.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from . import __version__, infer
from .feed import check_schema, schema


_BLOCKED_UNTIL = {}  # Same-origin cooldown survives new Transport instances in this process.


class SourceError(ValueError):
    """A short safe code only; never include response bodies or credentials."""


def require(condition, code):
    if not condition:
        raise SourceError(code)


def text(value, required=False):
    require(value is None or type(value) is str, 'invalid_text')
    require(not required or bool(value and value.strip()), 'missing_text')
    return value or None


def integer(value):
    require(type(value) is int and value >= 0, 'invalid_count')
    return value


def items(value):
    require(type(value) is list and all(type(v) is dict for v in value), 'invalid_items')
    return value


def iso_date(value):
    if value in (None, ''):
        return None
    require(type(value) is str, 'invalid_date')
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise SourceError('invalid_date') from None
    return value


def https_url(value, host=None):
    text(value, required=True)
    try:
        u = urlsplit(value)
        valid = u.scheme == 'https' and bool(u.hostname) and u.port in (None, 443)
    except ValueError:
        raise SourceError('invalid_url') from None
    require(valid and not u.username and not u.password and not u.fragment, 'invalid_url')
    require(host is None or u.hostname == host, 'unexpected_host')
    return value


def retry_time(value, now):
    """Honor delta seconds or HTTP-date. Unknown 429 cooldown defaults to one hour."""
    if value and value.strip().isdigit():
        return now + max(1, int(value.strip()))
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(now + 1, parsed.timestamp())
    except (TypeError, ValueError, OverflowError):
        return now + 3600


@dataclass(frozen=True)
class Reply:
    status: object
    data: object = None
    retry_at: float = None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Transport:
    """One origin, sequential requests, no redirects/retries/cookies or proxy bypass.

    Caller must retain retry_at across process restarts before scheduling another run.
    """
    MAX_BYTES = 8 * 1024 * 1024

    def __init__(self, origin, *, opener=None, clock=time.time, sleep=time.sleep):
        https_url(origin)
        require(urlsplit(origin).path in ('', '/') and not urlsplit(origin).query, 'invalid_origin')
        self.origin = origin.rstrip('/')
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.clock, self.sleep = clock, sleep
        self.blocked_until = 0
        self.next_request = 0

    def request(self, url, *, headers=None, body=None):
        https_url(url)
        require(f'{urlsplit(url).scheme}://{urlsplit(url).netloc}' == self.origin, 'unexpected_origin')
        now = self.clock()
        blocked_until = max(self.blocked_until, _BLOCKED_UNTIL.get(self.origin, 0))
        if now < blocked_until:
            return Reply(429, retry_at=blocked_until)
        if self.next_request > now:
            self.sleep(min(2, self.next_request - now))
        self.next_request = self.clock() + 1.0
        request_headers = {'Accept': 'application/json', 'Accept-Encoding': 'identity',
                           'User-Agent': 'ai-jobs/optional-sources'}
        request_headers.update(headers or {})
        data = None
        if body is not None:
            data = json.dumps(body, allow_nan=False).encode('utf-8')
            request_headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(url, data=data, headers=request_headers)
        try:
            with self.opener.open(request, timeout=30) as response:
                if response.status != 200:
                    return Reply(response.status)
                if response.geturl() != url:
                    return Reply('unexpected_response_url')
                if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                    return Reply('unexpected_encoding')
                if response.headers.get_content_type() != 'application/json':
                    return Reply('unexpected_content_type')
                raw = response.read(self.MAX_BYTES + 1)
                if len(raw) > self.MAX_BYTES:
                    return Reply('response_too_large')
                # Strict duplicate-key and nonfinite-number handling, shared with the feed.
                from .feed import loads
                return Reply(200, loads(raw))
        except urllib.error.HTTPError as error:
            status = error.code
            retry_at = None
            if status == 429 or error.headers.get('Retry-After'):
                retry_at = retry_time(error.headers.get('Retry-After'), self.clock())
                self.blocked_until = retry_at
                _BLOCKED_UNTIL[self.origin] = retry_at
            error.close()
            return Reply(status, retry_at=retry_at)
        except (OSError, ValueError, RecursionError):
            return Reply('transport_or_json_error')


@dataclass(frozen=True)
class Result:
    provider: str
    board: str
    source_url: str
    complete: bool
    records: tuple = ()
    error: str = None
    retry_at: float = None
    closure_safe: bool = False


def failure(provider, board, url, error, retry_at=None):
    return Result(provider, board, url, False, error=error, retry_at=retry_at)


def received(reply):
    require(reply.status == 200, 'http_' + str(reply.status))
    require(type(reply.data) is dict, 'invalid_response')
    return reply.data


def record(provider, board, source_url, observed_at, company, company_id, fields):
    moment = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
    require(moment.tzinfo is not None and moment.utcoffset().total_seconds() == 0, 'utc_observation_required')
    today = moment.date().isoformat()
    title = text(fields.get('title'), required=True)
    sid = text(fields.get('source_id'), required=True)
    rec = {'schema_version': 1, 'id': f'{provider}:{board}:{sid}', 'provider': provider,
           'board': board, 'company': text(company, required=True), 'company_id': company_id,
           **fields, 'first_seen': today, 'last_seen': today, 'status': 'open',
           'inferred': {'seniority': infer.seniority(title), 'seniority_rule': infer.SENIORITY_RULE,
                        'title_family': infer.title_family(title), 'title_rule': infer.TITLE_RULE},
           'provenance': {'collected_at': observed_at, 'source_url': source_url,
                          'collector': f'aijobs {__version__} optional-sources-v1'}}
    check_schema(rec, schema('job.schema.json'))
    return rec


def blank_fields():
    return {'apply_url': None, 'locations': [], 'country_codes': [], 'workplace': None,
            'department': None, 'team': None, 'employment_type': None, 'posted_at': None,
            'updated_at': None, 'compensation': None, 'description_sha256': None}


def merge(previous, result):
    """Pure state helper. Incomplete reads never change prior state or close jobs.

    For search scopes (USAJOBS), absence is not proof of closure even after a
    complete query. The caller must retain source health/observed IDs separately.
    """
    merged = {r['id']: dict(r) for r in previous}
    if not result.complete:
        return list(merged.values())
    seen = set()
    for rec in result.records:
        require(rec['provider'] == result.provider and rec['board'] == result.board, 'result_identity_mismatch')
        old = merged.get(rec['id'])
        merged[rec['id']] = {**rec, 'first_seen': old['first_seen'] if old else rec['first_seen']}
        seen.add(rec['id'])
    if result.closure_safe:
        for pid, old in merged.items():
            if (old['provider'], old['board']) == (result.provider, result.board) and pid not in seen:
                old['status'] = 'gone'
    return list(merged.values())
