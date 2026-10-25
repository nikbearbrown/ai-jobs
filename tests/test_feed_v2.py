"""Offline adapter -> canonical state -> versioned feed -> accepted pointer."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from aijobs import feed, usajobs, workday
from aijobs.source_api import Reply
from test_usajobs import job, page, Fake, NOW
from test_workday import CONFIG, card, detail, listing

FIXTURES=Path(__file__).parent/'fixtures'/'feed'


class FeedV2(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def metadata(self, day='25', run='synthetic'):
        return dict(run_id=run,started_at=f'2026-10-{day}T11:59:00Z',
                    completed_at=f'2026-10-{day}T12:01:00Z',generated_at=f'2026-10-{day}T12:02:00Z')

    def captures(self, day='25'):
        now=f'2026-10-{day}T12:00:00Z'
        usa=usajobs.fetch(usajobs.Config(),usajobs.Credentials('synthetic@example.invalid','synthetic-key'),
                          transport=Fake([page([job()])]),observed_at=now)
        wd=workday.fetch(CONFIG,transport=Fake([listing([card()]),Reply(200,detail())]),observed_at=now)
        self.assertTrue(usa.complete)
        self.assertTrue(wd.complete)
        return usa,wd

    def bundle(self, previous=(), results=None, day='25', run='synthetic'):
        return feed.export_results(self.root/'exports',previous,self.captures(day) if results is None else results,
                                   **self.metadata(day,run))

    def accept(self,bundle):
        return feed.accept(self.root/'accepted',bundle,version=feed.VERSION_V2)

    def previous(self):
        return [r['job'] for r in feed.read_pointer(self.root/'accepted')[1].values()]

    def test_adapter_to_accepted_v2_with_same_public_allowlist(self):
        bundle=self.bundle()
        manifest,rows,_,_=feed.validate_bundle(bundle,expected_version=feed.VERSION_V2)
        self.assertEqual(manifest['job_schema'],'feed-job-v2')
        self.assertEqual(manifest['snapshot']['records'],2)
        self.assertEqual({r['job']['provider'] for r in rows.values()},{'workday','usajobs'})
        self.assertTrue(all(r['observed_in_run'] and r['freshness']=='current' for r in rows.values()))
        for row in rows.values():
            self.assertEqual(set(row['job']),set(feed.FIELDS))
            self.assertNotIn('sponsorship',row['job'])
            self.assertNotIn('eligibility',row['job'])
        pointer=self.accept(bundle)
        self.assertEqual(pointer['schema'],feed.VERSION_V2)
        self.assertEqual(self.accept(bundle),pointer)
        self.assertEqual(feed.read_pointer(self.root/'accepted',expected_version=feed.VERSION_V2)[0],manifest)

    def test_v1_fixtures_and_exact_wire_bytes_unchanged(self):
        records=feed.rows_from_bytes((FIXTURES/'current.jsonl').read_bytes())
        boards=json.loads((FIXTURES/'boards.json').read_text())
        bundle=feed.export(self.root/'v1',records,boards,run_id='synthetic-001',
                           started_at='2026-10-24T11:59:00Z',completed_at='2026-10-24T12:00:00Z',
                           generated_at='2026-10-24T12:01:00Z')
        manifest,rows,raw,_=feed.validate_bundle(bundle)
        self.assertEqual(manifest['schema'],feed.VERSION)
        # Existing synthetic CLI demo hash recorded before v2 integration.
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'9dfe0780d0dfc4a98c85194716167a6a06a6982e4ebe997e16a45aa2c35b7bec')
        self.assertTrue(all(set(r)=={'job','freshness'} for r in rows.values()))
        feed.accept(self.root/'v1-accepted',bundle)

    def test_new_providers_rejected_by_v1_export_and_accept(self):
        for result in self.captures():
            boards=[{'provider':result.provider,'board':result.board,'read_ok':True,'postings':1}]
            with self.assertRaises(ValueError):
                feed.export(self.root/'v1',result.records,boards,**self.metadata())
        bundle=self.bundle()
        with self.assertRaisesRegex(ValueError,'unexpected feed version'):
            feed.accept(self.root/'v1-accepted',bundle)
        with self.assertRaises(ValueError):
            feed.validate_bundle(bundle,expected_version=feed.VERSION)

    def test_complete_empty_search_retains_stale_but_complete_board_closes(self):
        usa,wd=self.captures()
        self.accept(self.bundle(results=[usa,wd]))
        usa_empty=replace(usa,records=())
        wd_empty=replace(wd,records=())
        bundle=self.bundle(self.previous(),[usa_empty,wd_empty],day='26')
        self.accept(bundle)
        manifest,rows,_,_=feed.read_pointer(self.root/'accepted')
        u=rows[usa.records[0]['id']]; w=rows[wd.records[0]['id']]
        self.assertEqual((u['job']['status'],u['freshness'],u['observed_in_run']),('open','stale_unknown',False))
        self.assertEqual((w['job']['status'],w['freshness'],w['observed_in_run']),('gone','current',False))
        self.assertTrue(all(h['postings']==0 for h in manifest['source_health']))
        self.assertEqual(manifest['coverage']['ok'],2)

    def test_credential_and_review_gates_remain_no_network_failures(self):
        self.accept(self.bundle())
        fake=Fake([])
        usa=usajobs.fetch(usajobs.Config(),transport=fake,observed_at=NOW)
        wd=workday.fetch(replace(CONFIG,review=None),transport=fake,observed_at=NOW)
        self.assertEqual(fake.calls,[])
        self.assertEqual(usa.error,'credentials_required')
        self.assertEqual(wd.error,'source_review_required')
        old=self.previous()
        bundle=self.bundle(old,[usa,wd],day='26')
        self.accept(bundle)
        _,rows,_,_=feed.read_pointer(self.root/'accepted')
        self.assertTrue(all(r['freshness']=='stale_unknown' for r in rows.values()))
        self.assertEqual(sorted(self.previous(),key=lambda r:r['id']),sorted(old,key=lambda r:r['id']))

    def test_unattempted_source_and_recovery(self):
        self.accept(self.bundle())
        usa,_=self.captures('26')
        partial=self.bundle(self.previous(),[usa],day='26')
        self.accept(partial)
        manifest,rows,_,_=feed.read_pointer(self.root/'accepted')
        self.assertEqual(manifest['coverage']['unknown'],1)
        self.assertEqual(next(r for r in rows.values() if r['job']['provider']=='workday')['freshness'],'stale_unknown')
        recovery=self.bundle(self.previous(),self.captures('27'),day='27')
        self.accept(recovery)
        self.assertTrue(all(r['freshness']=='current' for r in feed.read_pointer(self.root/'accepted')[1].values()))
        self.assertTrue(all(r['first_seen']=='2026-10-25' for r in self.previous()))

    def tamper(self,bundle,change):
        manifest,rows,_,_=feed.validate_bundle(bundle)
        change(manifest,rows)
        raw=b''.join(feed.encoded(row) for row in rows.values())
        manifest['snapshot'].update(bytes=len(raw),sha256=feed.digest(raw))
        (bundle/'snapshot.jsonl').write_bytes(raw)
        (bundle/'manifest.json').write_bytes(feed.encoded(manifest))

    def test_invalid_version_pairs_and_pointer_version_mismatch_rejected(self):
        for field,value in [('schema','aijobs-static-v99'),('job_schema','feed-job-v1')]:
            bundle=self.bundle(run=field)
            self.tamper(bundle,lambda m,r:m.update({field:value}))
            with self.assertRaises(ValueError):feed.validate_bundle(bundle)
        bundle=self.bundle(run='pointer')
        pointer=self.accept(bundle)
        pointer['schema']=feed.VERSION
        (self.root/'accepted'/'latest-accepted.json').write_bytes(feed.encoded(pointer))
        with self.assertRaises(ValueError):feed.read_pointer(self.root/'accepted')

    def test_false_usa_closure_or_observation_rejected(self):
        for case in ('closure','observation'):
            usa,wd=self.captures()
            bundle=self.bundle(results=[replace(usa,records=()),wd],run=case)
            def change(m,rows):
                u=next(h for h in m['source_health'] if h['provider']=='usajobs')
                if case=='closure':u['closure_safe']=True
                else:
                    row=next(iter(rows.values()));row['observed_in_run']=False
            self.tamper(bundle,change)
            with self.assertRaises(ValueError):feed.validate_bundle(bundle)

    def test_forged_captures_and_stale_timestamps_rejected(self):
        usa,wd=self.captures()
        cases=[[replace(usa,closure_safe=True)], [usa,usa],
               [replace(wd,complete=False)], [replace(usa,records=usa.records+usa.records)]]
        for captures in cases:
            with self.assertRaises(ValueError):self.bundle(results=captures)
        with self.assertRaisesRegex(ValueError,'observation outside capture window'):
            self.bundle(results=[usa,wd],day='26')

    def test_unobserved_mutation_does_not_replace_prior_good(self):
        usa,wd=self.captures()
        self.accept(self.bundle(results=[usa,wd]))
        old_pointer=(self.root/'accepted'/'latest-accepted.json').read_bytes()
        bundle=self.bundle(self.previous(),[replace(usa,records=()),replace(wd,records=())],day='26')
        def change(m,rows):
            next(r for r in rows.values() if r['job']['provider']=='usajobs')['job']['title']='Forged synthetic title'
        self.tamper(bundle,change)
        with self.assertRaisesRegex(ValueError,'unobserved record changed'):self.accept(bundle)
        self.assertEqual((self.root/'accepted'/'latest-accepted.json').read_bytes(),old_pointer)

    def test_corruption_idempotency_and_v2_rollback(self):
        first=self.bundle()
        original=self.accept(first)
        later=self.bundle(self.previous(),self.captures('26'),day='26')
        self.accept(later)
        with self.assertRaises(ValueError):self.accept(first)
        self.assertEqual(feed.accept(self.root/'accepted',first,version=feed.VERSION_V2,rollback=True),original)
        broken=self.bundle(self.previous(),self.captures('27'),day='27')
        with (broken/'snapshot.jsonl').open('ab') as stream:stream.write(b'bad')
        with self.assertRaises(ValueError):self.accept(broken)
        self.assertEqual(json.loads((self.root/'accepted'/'latest-accepted.json').read_text()),original)

    def test_v1_store_isolated_while_legacy_rows_bootstrap_v2(self):
        records=feed.rows_from_bytes((FIXTURES/'current.jsonl').read_bytes())
        boards=json.loads((FIXTURES/'boards.json').read_text())
        old=feed.export(self.root/'old-export',records,boards,**self.metadata('24'))
        old_pointer=feed.accept(self.root/'old-accepted',old)
        new=self.bundle(previous=records)
        manifest,rows,_,_=feed.validate_bundle(new)
        self.assertEqual(len(rows),4)
        self.assertEqual(manifest['coverage']['unknown'],2)
        self.accept(new)
        with self.assertRaisesRegex(ValueError,'unexpected pointer version'):
            feed.accept(self.root/'old-accepted',new,version=feed.VERSION_V2)
        self.assertEqual(json.loads((self.root/'old-accepted'/'latest-accepted.json').read_text()),old_pointer)

    def test_same_day_search_absence_is_stale_without_changing_seen_date(self):
        usa,wd=self.captures()
        self.accept(self.bundle(results=[usa,wd]))
        later=feed.export_results(self.root/'exports',self.previous(),[replace(usa,records=())],
            run_id='later-same-day',started_at='2026-10-25T12:59:00Z',
            completed_at='2026-10-25T13:01:00Z',generated_at='2026-10-25T13:02:00Z')
        self.accept(later)
        row=feed.read_pointer(self.root/'accepted')[1][usa.records[0]['id']]
        self.assertEqual(row['job']['last_seen'],'2026-10-25')
        self.assertFalse(row['observed_in_run'])
        self.assertEqual(row['freshness'],'stale_unknown')

    def test_undeclared_job_fields_and_missing_prior_ids_are_rejected(self):
        first=self.bundle();self.accept(first)
        old_pointer=(self.root/'accepted'/'latest-accepted.json').read_bytes()
        usa,_=self.captures('26')
        lost=self.bundle(results=[usa],day='26',run='lost')
        with self.assertRaisesRegex(ValueError,'lost prior ids'):self.accept(lost)
        bad=self.bundle(self.previous(),self.captures('26'),day='26',run='extra-field')
        def change(m,rows):next(iter(rows.values()))['job']['sponsorship']='invented'
        self.tamper(bad,change)
        with self.assertRaisesRegex(ValueError,'unexpected fields'):self.accept(bad)
        self.assertEqual((self.root/'accepted'/'latest-accepted.json').read_bytes(),old_pointer)

    def test_observation_source_matches_exact_board_not_id_prefix(self):
        rec=feed.rows_from_bytes((FIXTURES/'current.jsonl').read_bytes())[0]
        rec.update(provider='custom',board='b:x',source_id='1',id='custom:b:x:1')
        boards=[{'provider':'custom','board':'b','read_ok':True,'postings':0,
                 'closure_safe':False,'observed_ids':[rec['id']]},
                {'provider':'custom','board':'b:x','read_ok':True,'postings':1,
                 'closure_safe':False,'observed_ids':[]}]
        with self.assertRaisesRegex(ValueError,'observation source mismatch'):
            feed.export(self.root/'invalid', [rec],boards,version=feed.VERSION_V2,**self.metadata('24'))

    def test_cli_versioned_export_and_validation(self):
        result=self.captures()[0]
        current=self.root/'current.jsonl';current.write_bytes(b''.join(feed.encoded(r) for r in result.records))
        boards=self.root/'boards.json';boards.write_bytes(feed.encoded([{
            'provider':result.provider,'board':result.board,'read_ok':True,'postings':1,
            'closure_safe':False,'observed_ids':[r['id'] for r in result.records]}]))
        args=[sys.executable,'-m','aijobs.feed','export','--current',str(current),'--boards',str(boards),
              '--out',str(self.root/'cli'),'--version',feed.VERSION_V2]
        for key,value in self.metadata().items():args += ['--'+key.replace('_','-'),value]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        validate=subprocess.run([sys.executable,'-m','aijobs.feed','validate',run.stdout.strip(),
                                 '--version',feed.VERSION_V2],capture_output=True,text=True)
        self.assertEqual(validate.returncode,0,validate.stderr)
        self.assertIn('aijobs-static-v2',validate.stdout)


if __name__=='__main__':unittest.main()
