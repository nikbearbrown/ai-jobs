"""Optional USAJOBS Search API adapter. No credential persistence or automatic probes."""
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
import re
from urllib.parse import urlencode, urlsplit

from .source_api import (Result, SourceError, Transport, blank_fields, failure, https_url,
                         integer, iso_date, items, received, record, require, text)

ORIGIN = 'https://data.usajobs.gov'
ENDPOINT = ORIGIN + '/api/search'
FILTERS = {'Keyword', 'PositionTitle', 'JobCategoryCode', 'Organization', 'LocationName',
           'HiringPath', 'RemoteIndicator'}


@dataclass(frozen=True)
class Credentials:
    email: str = field(repr=False)
    api_key: str = field(repr=False)

    def headers(self):
        require(type(self.email) is str and re.fullmatch(r'[^\s@]+@[^\s@]+', self.email), 'invalid_credentials')
        require(type(self.api_key) is str and bool(self.api_key) and
                all(32 < ord(c) < 127 for c in self.api_key), 'invalid_credentials')
        return {'Host': 'data.usajobs.gov', 'User-Agent': self.email, 'Authorization-Key': self.api_key}


def credentials_from_environment():
    """Explicit opt-in helper. No writes, dotenv, credential search, or registration."""
    email, key = os.environ.get('AIJOBS_USAJOBS_EMAIL'), os.environ.get('AIJOBS_USAJOBS_API_KEY')
    return Credentials(email, key) if email and key else None


@dataclass(frozen=True)
class Config:
    filters: dict = field(default_factory=dict)
    page_size: int = 500
    max_pages: int = 20

    def query(self):
        require(type(self.filters) is dict and self.filters.keys() <= FILTERS, 'unsupported_filter')
        require(type(self.page_size) is int and 1 <= self.page_size <= 500, 'invalid_page_size')
        require(type(self.max_pages) is int and 1 <= self.max_pages <= 100, 'invalid_page_limit')
        for key, value in self.filters.items():
            require(type(value) is str and 0 < len(value) <= 200 and
                    all(ord(c) >= 32 for c in value), 'invalid_filter')
            if key == 'RemoteIndicator':
                require(value in ('True', 'False'), 'invalid_remote_filter')
        return {**self.filters, 'WhoMayApply': 'Public', 'Fields': 'Min'}

    def identity(self):
        # Fixed search scope, not the employer or a promise of nationwide coverage.
        raw = json.dumps(self.query(), sort_keys=True, separators=(',', ':')).encode()
        return 'public-' + hashlib.sha256(raw).hexdigest()[:16]


def numeric(value):
    if value in (None, ''):
        return None
    require(type(value) in (int, float, str), 'invalid_salary')
    try:
        number = float(value)
    except ValueError:
        raise SourceError('invalid_salary') from None
    require(math.isfinite(number) and number >= 0, 'invalid_salary')
    return number


def normalise(item):
    sid = item.get('MatchedObjectId')
    require(type(sid) in (str, int) and re.fullmatch(r'[0-9]+', str(sid)), 'invalid_control_number')
    sid = str(sid)
    d = item.get('MatchedObjectDescriptor')
    require(type(d) is dict, 'invalid_descriptor')
    url = https_url(d.get('PositionURI'), 'www.usajobs.gov')
    require(urlsplit(url).path.rstrip('/').split('/')[-1] == sid, 'job_url_identity_mismatch')
    f = {**blank_fields(), 'source_id': sid, 'title': text(d.get('PositionTitle'), True), 'url': url}
    applies = d.get('ApplyURI') or []
    require(type(applies) is list, 'invalid_apply_urls')
    if applies:
        f['apply_url'] = https_url(applies[0])  # Link only; never followed.
    locs = items(d.get('PositionLocation') or [])
    for loc in locs:
        name = text(loc.get('LocationName'))
        if name and name not in f['locations']:
            f['locations'].append(name)
        country = text(loc.get('CountryCode'))
        # API examples use country names, not always ISO codes. No geocoding guesses.
        code = {'United States': 'US'}.get(country)
        if country and re.fullmatch(r'[A-Za-z]{2}', country):
            code = country.upper()
        if code and code not in f['country_codes']:
            f['country_codes'].append(code)
    if not f['locations'] and d.get('PositionLocationDisplay'):
        f['locations'] = [text(d['PositionLocationDisplay'], True)]
    schedules = items(d.get('PositionSchedule') or [])
    codes = {text(s.get('Code')) for s in schedules}
    f['employment_type'] = {'1': 'full_time', '2': 'part_time'}.get(next(iter(codes))) if len(codes) == 1 else None
    f['department'] = text(d.get('DepartmentName'))
    f['posted_at'] = iso_date(d.get('PublicationStartDate'))
    # Query RemoteIndicator is a filter, not a record field; no workplace inference.
    salary = items(d.get('PositionRemuneration') or [])
    if len(salary) == 1:
        s = salary[0]
        low, high = numeric(s.get('MinimumRange')), numeric(s.get('MaximumRange'))
        require(low is None or high is None or low <= high, 'invalid_salary_range')
        if low is not None or high is not None:
            f['compensation'] = {'min': low, 'max': high, 'currency': None,
                                 'interval': {'PA':'year','PH':'hour','PD':'day','PM':'month'}.get(s.get('RateIntervalCode')),
                                 'raw': None}
    # Summary/min fields are not the complete advertisement: no misleading ad hash.
    return text(d.get('OrganizationName'), True), f


def fetch(config, credentials=None, *, transport=None, observed_at):
    """All pages or failure; no partial records escape a failed/capped search."""
    query = config.query()
    board = config.identity()
    source = ENDPOINT + '?' + urlencode(sorted(query.items()))
    if credentials is None:
        return failure('usajobs', board, source, 'credentials_required')
    retry_at = None
    try:
        headers = credentials.headers()
        transport = transport or Transport(ORIGIN)
        rows, ids, total = [], set(), None
        for page in range(1, config.max_pages + 1):
            reply = transport.request(source + '&' + urlencode({'Page':page, 'ResultsPerPage':config.page_size}), headers=headers)
            retry_at = reply.retry_at
            data = received(reply).get('SearchResult')
            require(type(data) is dict, 'missing_search_result')
            count_all = integer(data.get('SearchResultCountAll'))
            require(count_all < 10000, 'query_result_cap')
            require(total is None or total == count_all, 'changing_result_total')
            total = count_all
            batch = items(data.get('SearchResultItems'))
            require(integer(data.get('SearchResultCount')) == len(batch), 'page_count_mismatch')
            require(len(batch) <= config.page_size, 'oversized_page')
            for item in batch:
                company, fields = normalise(item)
                sid = fields['source_id']
                require(sid not in ids, 'duplicate_control_number')
                ids.add(sid)
                rows.append(record('usajobs', board, source, observed_at, company, None, fields))
            require(len(rows) <= total, 'result_count_overflow')
            if len(rows) == total:
                return Result('usajobs', board, source, True, tuple(rows), closure_safe=False)
            require(len(batch) == config.page_size, 'short_page_before_total')
        raise SourceError('page_limit_incomplete')
    except (SourceError, ValueError, TypeError, KeyError, OverflowError):
        # Only controlled codes are exposed; never raw exceptions from HTTP/JSON.
        import sys
        exc = sys.exc_info()[1]
        code = str(exc) if isinstance(exc, SourceError) else 'invalid_payload'
        return failure('usajobs', board, source, code, retry_at)
