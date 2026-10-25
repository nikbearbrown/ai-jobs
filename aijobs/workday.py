"""Optional Workday public-career CXS adapter; source review required, no discovery.

The conservative payload contract is tested synthetically, not live-verified.
No tenant is enabled by shipping this module.
"""
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import re
from urllib.parse import unquote, urlsplit

from .source_api import (Result, SourceError, Transport, blank_fields, failure, https_url,
                         integer, items, received, record, require, text)


@dataclass(frozen=True)
class Review:
    """Operator-owned evidence, not an automatic assertion that a site permits use."""
    employer_careers_url: str
    observed_board_url: str
    observed_jobs_endpoint: str
    terms_url: str
    robots_url: str
    evidence_sha256: str
    reviewed_on: str
    permission_basis: str
    access_allowed: bool = False


@dataclass(frozen=True)
class Config:
    tenant: str
    host: str
    site: str
    board_url: str
    company: str
    company_id: str
    review: Review = None
    page_size: int = 20
    max_pages: int = 100
    max_jobs: int = 2000

    def endpoint(self):
        require(type(self.tenant) is str and re.fullmatch('[a-z0-9-]+',self.tenant), 'invalid_tenant')
        require(type(self.host) is str and re.fullmatch(
            re.escape(self.tenant)+r'\.wd[0-9]+\.myworkdayjobs\.com',self.host), 'tenant_host_mismatch')
        require(type(self.site) is str and re.fullmatch('[A-Za-z0-9_-]+',self.site), 'invalid_site')
        https_url(self.board_url, self.host)
        u=urlsplit(self.board_url)
        require(not u.query and u.path.rstrip('/') in ('/'+self.site,'/en-US/'+self.site), 'board_site_mismatch')
        text(self.company,True); text(self.company_id,True)
        require(type(self.page_size) is int and 1 <= self.page_size <= 20, 'invalid_page_size')
        require(type(self.max_pages) is int and 1 <= self.max_pages <= 100, 'invalid_page_limit')
        require(type(self.max_jobs) is int and 1 <= self.max_jobs <= 2000, 'invalid_job_limit')
        return f'https://{self.host}/wday/cxs/{self.tenant}/{self.site}/jobs'

    def board(self):
        return self.host+'/'+self.site

    def check_review(self, observed_at):
        r=self.review
        require(isinstance(r,Review) and r.access_allowed is True, 'source_review_required')
        https_url(r.employer_careers_url)
        require(r.observed_board_url == self.board_url and r.observed_jobs_endpoint == self.endpoint(), 'review_endpoint_mismatch')
        https_url(r.terms_url)
        require(r.robots_url == f'https://{self.host}/robots.txt', 'review_robots_mismatch')
        require(re.fullmatch('[a-f0-9]{64}',r.evidence_sha256 or '') is not None, 'review_evidence_required')
        text(r.permission_basis,True)
        try:
            age=(datetime.fromisoformat(observed_at.replace('Z','+00:00')).date()-date.fromisoformat(r.reviewed_on)).days
        except (ValueError,TypeError):
            raise SourceError('invalid_review_date') from None
        require(0 <= age <= 30, 'source_review_expired')


def job_path(value):
    text(value,True)
    require(len(value) <= 2048 and value.startswith('/job/'), 'invalid_job_path')
    u=urlsplit(value)
    require(not u.scheme and not u.netloc and not u.query and not u.fragment, 'invalid_job_path')
    require(re.fullmatch(r'[A-Za-z0-9_./%()~!$&+,;=:@-]+',value) is not None, 'invalid_job_path')
    require(not re.search(r'%(?![0-9A-Fa-f]{2})',value), 'invalid_job_path')
    decoded=unquote(value)
    require(not any(c in decoded for c in ('\\','?','#','%','\x00')) and
            all(ord(c) >= 32 for c in decoded), 'invalid_job_path')
    require(all(part not in ('','.','..') for part in decoded[1:].split('/')), 'invalid_job_path')
    return value


def normalise(config, card, detail):
    path=job_path(card.get('externalPath'))
    info=detail.get('jobPostingInfo')
    require(type(info) is dict, 'missing_job_detail')
    sid=text(info.get('jobReqId'),True)
    require(re.fullmatch('[A-Za-z0-9_-]+',sid) is not None, 'invalid_requisition_id')
    require(unquote(path).endswith('_'+sid), 'path_requisition_mismatch')
    bullets=card.get('bulletFields')
    require(type(bullets) is list and all(type(v) is str for v in bullets) and sid in bullets, 'card_requisition_mismatch')
    title=text(info.get('title'),True)
    require(title == text(card.get('title'),True), 'card_detail_title_mismatch')
    expected=config.board_url.rstrip('/')+path
    if info.get('externalUrl') is not None:
        require(https_url(info['externalUrl'],config.host) == expected, 'detail_url_mismatch')
    f={**blank_fields(),'source_id':sid,'title':title,'url':expected}
    primary=text(info.get('location'))
    if primary:
        f['locations'].append(primary)
    additional=([] if info.get('additionalLocations') is None else info['additionalLocations'])
    require(type(additional) is list and all(type(v) is str for v in additional), 'invalid_locations')
    for loc in additional:
        if loc and loc not in f['locations']:
            f['locations'].append(loc)
    # Never turn listing text such as "5 Locations" into a location.
    country=info.get('country')
    if country is not None:
        require(type(country) is dict, 'invalid_country')
        label=text(country.get('descriptor'))
        code={'United States of America':'US','United States':'US','United Kingdom':'GB','Canada':'CA'}.get(label)
        if code:
            f['country_codes']=[code]
    remote=text(info.get('remoteType'))
    f['workplace']={'remote':'remote','hybrid':'hybrid','on-site':'onsite','onsite':'onsite'}.get((remote or '').lower())
    schedule=text(info.get('timeType'))
    f['employment_type']={'full time':'full_time','full-time':'full_time','part time':'part_time','part-time':'part_time'}.get((schedule or '').lower())
    # Relative postedOn and unverified startDate semantics are not publication dates.
    description=text(info.get('jobDescription'))
    f['description_sha256']=hashlib.sha256(description.encode('utf-8')).hexdigest() if description else None
    return f


def fetch(config, *, observed_at, transport=None):
    """Full unfiltered board plus each detail, or failure with no partial records."""
    source=config.endpoint()
    board=config.board()
    retry_at=None
    try:
        config.check_review(observed_at)
        transport=transport or Transport(f'https://{config.host}')
        cards, paths, total = [], set(), None
        for number in range(config.max_pages):
            reply=transport.request(source,body={'appliedFacets':{},'limit':config.page_size,
                                                'offset':len(cards),'searchText':''})
            retry_at=reply.retry_at
            payload=received(reply)
            count=integer(payload.get('total'))
            require(count <= config.max_jobs, 'job_limit_incomplete')
            require(total is None or count == total, 'changing_result_total')
            total=count
            batch=items(payload.get('jobPostings'))
            require(len(batch) <= config.page_size, 'oversized_page')
            for card in batch:
                path=job_path(card.get('externalPath'))
                require(path not in paths, 'duplicate_job_path')
                paths.add(path); cards.append(card)
            require(len(cards) <= total, 'result_count_overflow')
            if len(cards) == total:
                break
            require(len(batch) == config.page_size, 'short_page_before_total')
        else:
            raise SourceError('page_limit_incomplete')
        rows, ids=[],set()
        for card in cards:
            detail_url=source.removesuffix('/jobs')+job_path(card['externalPath'])
            reply=transport.request(detail_url)
            retry_at=reply.retry_at
            fields=normalise(config,card,received(reply))
            require(fields['source_id'] not in ids, 'duplicate_requisition_id')
            ids.add(fields['source_id'])
            rows.append(record('workday',board,detail_url,observed_at,config.company,config.company_id,fields))
        return Result('workday',board,source,True,tuple(rows),closure_safe=True)
    except (SourceError,ValueError,TypeError,KeyError,OverflowError):
        import sys
        exc=sys.exc_info()[1]
        return failure('workday',board,source,str(exc) if isinstance(exc,SourceError) else 'invalid_payload',retry_at)
