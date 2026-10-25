"""Invented API responses; no API key lookup, network or real job data."""
import copy
from email.message import Message
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from aijobs import usajobs as U
from aijobs import source_api as S
from aijobs import providers, probe

NOW = '2026-10-25T12:00:00Z'


def job(sid='100001'):
    return {'MatchedObjectId': sid, 'MatchedObjectDescriptor': {
        'PositionID':'SYNTHETIC-ANNOUNCEMENT', 'PositionTitle':'Synthetic Software Engineer',
        'PositionURI': 'https://www.usajobs.gov/job/'+sid,
        'ApplyURI':['https://www.usajobs.gov/job/'+sid+'?PostingChannelID=RESTAPI'],
        'OrganizationName':'Synthetic Federal Agency', 'DepartmentName':'Synthetic Department',
        'PositionLocation':[{'LocationName':'Synthetic US City','CountryCode':'United States'},
                            {'LocationName':'Synthetic Overseas City','CountryCode':'GB'}],
        'PositionSchedule':[{'Name':'Full Time','Code':'1'}],
        'PositionOfferingType':[{'Name':'Permanent','Code':'15317'}],
        'PublicationStartDate':'2026-10-01T00:00:00Z',
        'PositionRemuneration':[{'MinimumRange':'100','MaximumRange':'200','RateIntervalCode':'PA'}],
        'QualificationSummary':'INVENTED TEXT: must not be persisted'}}


def page(jobs, total=None):
    return S.Reply(200, {'SearchResult':{'SearchResultCount':len(jobs),
                        'SearchResultCountAll':len(jobs) if total is None else total,
                        'SearchResultItems':jobs}})


class Fake:
    def __init__(self, replies):
        self.replies, self.calls = iter(replies), []

    def request(self, url, **kwargs):
        self.calls.append((url,kwargs))
        return next(self.replies)


class USAJOBS(unittest.TestCase):
    def fetch(self, replies, **kwargs):
        fake = Fake(replies)
        result = U.fetch(U.Config(page_size=1), U.Credentials('synthetic@example.invalid','synthetic-test-key'),
                         transport=fake, observed_at=NOW, **kwargs)
        return result, fake

    def test_optional_credentials_no_network_and_no_auto_registration(self):
        fake = Fake([])
        result = U.fetch(U.Config(), transport=fake, observed_at=NOW)
        self.assertEqual(result.error, 'credentials_required')
        self.assertEqual(fake.calls, [])
        self.assertNotIn('usajobs', providers.PROVIDERS)
        self.assertNotIn('usajobs', probe.ORDER)
        self.assertNotIn('synthetic-test-key', repr(U.Credentials('x@example.invalid','synthetic-test-key')))

    def test_two_pages_are_complete_canonical_records(self):
        result, fake = self.fetch([page([job()],2),page([job('100002')],2)])
        self.assertTrue(result.complete)
        self.assertFalse(result.closure_safe)
        self.assertEqual(len(result.records),2)
        r=result.records[0]
        self.assertEqual(r['source_id'],'100001')
        self.assertEqual(r['company'],'Synthetic Federal Agency')
        self.assertIsNone(r['company_id'])
        self.assertEqual(r['country_codes'],['US','GB'])
        self.assertEqual(r['employment_type'],'full_time')
        self.assertEqual(r['posted_at'],'2026-10-01T00:00:00Z')
        self.assertIsNone(r['workplace'])
        self.assertIsNone(r['compensation']['currency'])
        self.assertNotIn('INVENTED TEXT',json.dumps(r))
        self.assertIn('Page=2',fake.calls[1][0])
        self.assertEqual(fake.calls[0][1]['headers']['Host'],'data.usajobs.gov')
        self.assertNotIn('synthetic-test-key',r['provenance']['source_url'])
        S.check_schema(r,S.schema('job.schema.json'))

    def test_missing_optional_fields_stay_unknown(self):
        j=job()
        d=j['MatchedObjectDescriptor']
        for k in ['PositionSchedule','PositionLocation','PositionRemuneration','PublicationStartDate','ApplyURI','DepartmentName']:
            d.pop(k)
        result,_=self.fetch([page([j])])
        self.assertTrue(result.complete)
        r=result.records[0]
        self.assertEqual(r['locations'],[])
        self.assertIsNone(r['posted_at'])
        self.assertIsNone(r['employment_type'])  # Permanent offering is not full-time.

    def test_late_failure_duplicates_total_drift_and_cap_discard_all(self):
        cases=[([page([job()],2),S.Reply(429,retry_at=9999999999)],'http_429'),
               ([page([job()],2),page([job()],2)],'duplicate_control_number'),
               ([page([job()],2),page([job('100002')],3)],'changing_result_total'),
               ([page([],2)],'short_page_before_total'),
               ([page([],10000)],'query_result_cap'),
               ([S.Reply(200,{})],'missing_search_result'),
               ([S.Reply(401)],'http_401')]
        for replies,code in cases:
            with self.subTest(code=code):
                result,_=self.fetch(replies)
                self.assertFalse(result.complete)
                self.assertEqual(result.records,())
                self.assertEqual(result.error,code)
        result,_=self.fetch([S.Reply(429,retry_at=9999999999)])
        self.assertEqual(result.retry_at,9999999999)

    def test_identity_and_types_fail_closed(self):
        for change in ({'PositionURI':'https://example.invalid/job/100001'}, {'PositionTitle':None},
                       {'PositionURI':'https://www.usajobs.gov/job/999'}, {'PublicationStartDate':'not-a-date'}):
            j=job(); j['MatchedObjectDescriptor'].update(change)
            result,_=self.fetch([page([j])])
            self.assertFalse(result.complete)
        p=page([]); p.data['SearchResult']['SearchResultCountAll']=True
        self.assertFalse(self.fetch([p])[0].complete)

    def test_query_changes_identity_and_rejects_unapproved_fields(self):
        self.assertNotEqual(U.Config().identity(), U.Config({'JobCategoryCode':'2210'}).identity())
        with self.assertRaises(S.SourceError): U.Config({'WhoMayApply':'All'}).query()
        with self.assertRaises(S.SourceError): U.Config({'DatePosted':'1'}).query()
        with self.assertRaises(S.SourceError): U.Config(page_size=501).query()
        self.assertEqual(U.Config().query()['WhoMayApply'],'Public')

    def test_empty_query_does_not_close_previous_and_failure_preserves_it(self):
        prior=self.fetch([page([job()])])[0]
        empty=self.fetch([page([])])[0]
        self.assertTrue(empty.complete)
        self.assertEqual(S.merge(prior.records,empty),list(prior.records))
        failed=self.fetch([S.Reply(403)])[0]
        self.assertEqual(S.merge(prior.records,failed),list(prior.records))

    def test_page_limit_is_not_complete(self):
        result=U.fetch(U.Config(page_size=1,max_pages=1),U.Credentials('x@example.invalid','fake'),
                       transport=Fake([page([job()],2)]),observed_at=NOW)
        self.assertEqual(result.error,'page_limit_incomplete')


class Transport(unittest.TestCase):
    def test_retry_after_seconds_and_http_date_are_not_shortened(self):
        self.assertEqual(S.retry_time('86400',100),86500)
        self.assertEqual(S.retry_time('Thu, 01 Jan 1970 01:00:00 GMT',100),3600)
        self.assertEqual(S.retry_time(None,100),3700)

    def test_429_blocks_repeated_requests_without_sleep_or_body_leak(self):
        class Opener:
            calls=0
            def open(self,request,timeout):
                self.calls+=1
                headers=Message(); headers['Retry-After']='86400'
                raise urllib.error.HTTPError(request.full_url,429,'do not log',headers,io.BytesIO(b'secret body'))
        opener=Opener()
        t=S.Transport(U.ORIGIN,opener=opener,clock=lambda:100,sleep=lambda _:self.fail('unexpected sleep'))
        first=t.request(U.ENDPOINT)
        second=t.request(U.ENDPOINT)
        self.assertEqual(first.retry_at,86500)
        self.assertEqual(second.retry_at,86500)
        self.assertEqual(opener.calls,1)
        self.assertNotIn('secret',repr(first))

    def test_redirects_and_cross_origin_credentials_are_rejected(self):
        self.assertIsNone(S.NoRedirect().redirect_request(None,None,302,'',{},'https://example.invalid'))
        t=S.Transport(U.ORIGIN)
        with self.assertRaises(S.SourceError):
            t.request('https://example.invalid',headers={'Authorization-Key':'synthetic'})
        with self.assertRaises(S.SourceError):
            t.request('http://data.usajobs.gov/api/search')

    def test_response_size_encoding_and_json_are_bounded(self):
        class Response(io.BytesIO):
            status=200
            def __init__(self, raw, encoding='identity', content_type='application/json'):
                super().__init__(raw)
                self.headers=Message(); self.headers['Content-Type']=content_type
                self.headers['Content-Encoding']=encoding
            def geturl(self): return U.ENDPOINT
        class Opener:
            def __init__(self,response): self.response=response
            def open(self,*args,**kwargs): return self.response
        for response,expected in [(Response(b'{}','gzip'),'unexpected_encoding'),
                                  (Response(b'<html>',content_type='text/html'),'unexpected_content_type'),
                                  (Response(b'{"x":1,"x":2}'),'transport_or_json_error')]:
            reply=S.Transport(U.ORIGIN,opener=Opener(response)).request(U.ENDPOINT)
            self.assertEqual(reply.status,expected)
        t=S.Transport(U.ORIGIN,opener=Opener(Response(b'12345'))); t.MAX_BYTES=4
        self.assertEqual(t.request(U.ENDPOINT).status,'response_too_large')


if __name__ == '__main__': unittest.main()
