"""Only invented Workday-shaped payloads. No real tenant is queried or enabled."""
from dataclasses import replace
import hashlib
import json
import unittest

from aijobs import workday as W
from aijobs import source_api as S
from aijobs import providers,probe

NOW='2026-10-25T12:00:00Z'
HOST='synthetic.wd5.myworkdayjobs.com'
BOARD='https://'+HOST+'/en-US/SyntheticCareers'
ENDPOINT='https://'+HOST+'/wday/cxs/synthetic/SyntheticCareers/jobs'
REVIEW=W.Review('https://example.invalid/careers',BOARD,ENDPOINT,'https://example.invalid/terms',
                'https://'+HOST+'/robots.txt','0'*64,'2026-10-25','Synthetic test evidence only',True)
CONFIG=W.Config('synthetic',HOST,'SyntheticCareers',BOARD,'Synthetic Employer','synthetic',REVIEW,page_size=1)


def card(sid='R100'):
    return {'title':'Synthetic Data Engineer','externalPath':'/job/Synthetic-City/Synthetic-Role_'+sid,
            'locationsText':'3 Locations','postedOn':'Posted Yesterday','bulletFields':[sid]}


def detail(sid='R100'):
    return {'jobPostingInfo':{'jobReqId':sid,'title':'Synthetic Data Engineer',
            'externalUrl':BOARD+card(sid)['externalPath'], 'location':'Synthetic City',
            'additionalLocations':['Synthetic Second City','Synthetic Third City'],
            'country':{'descriptor':'United States of America','id':'opaque-not-iso'},
            'timeType':'Full time','remoteType':'Hybrid','postedOn':'Posted Yesterday',
            'startDate':'2026-10-24','jobDescription':'<p>Invented fixture text only.</p>'}}


def listing(cards,total=None):
    return S.Reply(200,{'total':len(cards) if total is None else total,'jobPostings':cards})


class Fake:
    def __init__(self,replies): self.replies,self.calls=iter(replies),[]
    def request(self,url,**kwargs):
        self.calls.append((url,kwargs))
        return next(self.replies)


class Workday(unittest.TestCase):
    def fetch(self,replies,config=CONFIG):
        fake=Fake(replies)
        return W.fetch(config,observed_at=NOW,transport=fake),fake

    def test_no_review_denied_expired_and_no_auto_registration(self):
        for review in (None,replace(REVIEW,access_allowed=False),replace(REVIEW,reviewed_on='2026-08-01')):
            result,fake=self.fetch([],replace(CONFIG,review=review))
            self.assertFalse(result.complete)
            self.assertEqual(fake.calls,[])
        self.assertNotIn('workday',providers.PROVIDERS)
        self.assertNotIn('workday',probe.ORDER)

    def test_complete_pagination_and_canonical_detail_mapping(self):
        result,fake=self.fetch([listing([card()],2),listing([card('R200')],2),
                               S.Reply(200,detail()),S.Reply(200,detail('R200'))])
        self.assertTrue(result.complete)
        self.assertTrue(result.closure_safe)
        self.assertEqual(len(result.records),2)
        r=result.records[0]
        S.check_schema(r,S.schema('job.schema.json'))
        self.assertEqual(r['source_id'],'R100')
        self.assertEqual(r['company'],'Synthetic Employer')
        self.assertEqual(r['locations'],['Synthetic City','Synthetic Second City','Synthetic Third City'])
        self.assertEqual(r['country_codes'],['US'])
        self.assertEqual(r['workplace'],'hybrid')
        self.assertEqual(r['employment_type'],'full_time')
        self.assertIsNone(r['posted_at'])
        self.assertIsNone(r['apply_url'])
        self.assertNotIn('Invented fixture text',json.dumps(r))
        self.assertEqual(r['description_sha256'],hashlib.sha256(detail()['jobPostingInfo']['jobDescription'].encode()).hexdigest())
        self.assertEqual(fake.calls[1][1]['body']['offset'],1)
        self.assertEqual(fake.calls[0][1]['body']['appliedFacets'],{})
        self.assertEqual(fake.calls[0][1]['body']['searchText'],'')
        self.assertEqual(fake.calls[2][0],ENDPOINT.removesuffix('/jobs')+card()['externalPath'])

    def test_unknown_fields_are_not_inferred_from_listing_or_opaque_country(self):
        d=detail()
        for key in ('location','additionalLocations','timeType','remoteType','jobDescription'):
            d['jobPostingInfo'].pop(key)
        d['jobPostingInfo']['country']={'id':'US-like-opaque-id'}
        result,_=self.fetch([listing([card()]),S.Reply(200,d)])
        self.assertTrue(result.complete)
        r=result.records[0]
        self.assertEqual(r['locations'],[])
        self.assertEqual(r['country_codes'],[])
        self.assertIsNone(r['workplace'])
        self.assertIsNone(r['employment_type'])
        self.assertIsNone(r['description_sha256'])

    def test_tenant_domain_site_and_review_identity_are_required(self):
        for change in ({'tenant':'other'}, {'host':'synthetic.wd5.myworkdayjobs.com.evil.invalid'},
                       {'site':'../escape'}, {'board_url':'https://'+HOST+'/en-US/Other'},
                       {'board_url':'https://user:pass@'+HOST+'/en-US/SyntheticCareers'}):
            with self.subTest(change=change),self.assertRaises(S.SourceError):
                replace(CONFIG,**change).endpoint()
        for change in ({'observed_jobs_endpoint':ENDPOINT+'/other'}, {'observed_board_url':'https://example.invalid'},
                       {'robots_url':'https://example.invalid/robots.txt'}, {'evidence_sha256':'bad'}):
            result,fake=self.fetch([],replace(CONFIG,review=replace(REVIEW,**change)))
            self.assertFalse(result.complete)
            self.assertEqual(fake.calls,[])

    def test_path_escapes_are_rejected_before_detail_requests(self):
        for path in ('https://example.invalid/job/x','//example.invalid/job/x','/job/../x',
                     '/job/%2e%2e/x','/job/%252e%252e/x','/job/x?secret=value','/job/x%5c..','/job/x%00'):
            c=card();c['externalPath']=path
            result,fake=self.fetch([listing([c])])
            self.assertFalse(result.complete)
            self.assertEqual(len(fake.calls),1)

    def test_list_detail_id_and_title_mismatches_discard_all(self):
        for change in ({'jobReqId':'OTHER'},{'externalUrl':'https://example.invalid/job/R100'},
                       {'title':'Changed during pagination'}):
            d=detail();d['jobPostingInfo'].update(change)
            result,_=self.fetch([listing([card()]),S.Reply(200,d)])
            self.assertFalse(result.complete)
            self.assertEqual(result.records,())
        c=card();c['bulletFields']=['WRONG']
        self.assertFalse(self.fetch([listing([c]),S.Reply(200,detail())])[0].complete)

    def test_late_http_failure_duplicate_page_and_changing_totals_fail(self):
        cases=[([listing([card()],2),S.Reply(429,retry_at=9999999999)],'http_429'),
               ([listing([card()],2),listing([card()],2)],'duplicate_job_path'),
               ([listing([card()],2),listing([card('R200')],3)],'changing_result_total'),
               ([listing([],1)],'short_page_before_total'),
               ([listing([card()]),S.Reply(403)],'http_403'),
               ([listing([card()]),S.Reply(404)],'http_404'),
               ([S.Reply(200,{'total':0})],'invalid_items')]
        for replies,code in cases:
            with self.subTest(code=code):
                result,_=self.fetch(replies)
                self.assertFalse(result.complete)
                self.assertEqual(result.error,code)
                self.assertEqual(result.records,())

    def test_invalid_optional_locations_are_rejected(self):
        d=detail();d['jobPostingInfo']['additionalLocations']=False
        result,_=self.fetch([listing([card()]),S.Reply(200,d)])
        self.assertEqual(result.error,'invalid_locations')

    def test_limits_are_failures_not_partial_success(self):
        result,_=self.fetch([listing([card()],2)],replace(CONFIG,max_jobs=1))
        self.assertEqual(result.error,'job_limit_incomplete')
        result,_=self.fetch([listing([card()],2)],replace(CONFIG,max_pages=1))
        self.assertEqual(result.error,'page_limit_incomplete')

    def test_complete_empty_board_closes_but_error_never_closes(self):
        first,_=self.fetch([listing([card()]),S.Reply(200,detail())])
        failed,_=self.fetch([S.Reply(429,retry_at=9999999999)])
        self.assertEqual(S.merge(first.records,failed),list(first.records))
        empty,_=self.fetch([listing([])])
        self.assertTrue(empty.complete)
        self.assertEqual(S.merge(first.records,empty)[0]['status'],'gone')
        self.assertEqual(failed.retry_at,9999999999)


if __name__=='__main__': unittest.main()
