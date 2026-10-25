"""Synthetic only. No HTTP or production data access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aijobs import feed

FIXTURES = Path(__file__).parent / 'fixtures' / 'feed'


class Feed(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.records = feed.rows_from_bytes((FIXTURES / 'current.jsonl').read_bytes())
        self.boards = json.loads((FIXTURES / 'boards.json').read_text())

    def export(self, day='24', run='run1', records=None, boards=None):
        return feed.export(self.root / 'exports', self.records if records is None else records,
                           self.boards if boards is None else boards, run_id=run,
                           started_at=f'2026-10-{day}T11:59:00Z', completed_at=f'2026-10-{day}T12:00:00Z',
                           generated_at=f'2026-10-{day}T12:01:00Z')

    def partial(self):
        records = copy.deepcopy(self.records)
        records[0]['last_seen'] = '2026-10-25'
        boards = copy.deepcopy(self.boards)
        boards[1].update(read_ok=False, postings=None)
        return records, boards

    def test_projection_uses_canonical_fields_and_no_ad_material(self):
        bundle = self.export()
        manifest, rows, _, _ = feed.validate_bundle(bundle)
        self.assertEqual(manifest['snapshot']['records'], 2)
        self.assertEqual(manifest['coverage'], {'known_boards':2,'ok':2,'failed':0,'unknown':0})
        for row in rows.values():
            self.assertEqual(set(row['job']), set(feed.FIELDS))
            self.assertNotIn('description_sha256', row['job'])
            self.assertIsNone(row['job']['workplace'])

    def test_partial_failure_carries_stale_unknown_without_false_closure(self):
        store = self.root / 'store'
        feed.accept(store, self.export())
        records, boards = self.partial()
        bundle = self.export('25', records=records, boards=boards)
        feed.accept(store, bundle)
        _, rows, _, _ = feed.read_pointer(store)
        row = rows[self.records[1]['id']]
        self.assertEqual(row['freshness'], 'stale_unknown')
        self.assertEqual(row['job']['status'], 'open')
        self.assertEqual(row['job']['last_seen'], '2026-10-24')

    def test_unattempted_source_is_unknown(self):
        bundle = self.export(boards=self.boards[:1])
        manifest, rows, _, _ = feed.validate_bundle(bundle)
        self.assertEqual(manifest['coverage']['unknown'], 1)
        self.assertEqual(rows[self.records[1]['id']]['freshness'], 'stale_unknown')

    def test_false_closure_on_failed_board_keeps_prior_good(self):
        store = self.root / 'store'
        feed.accept(store, self.export())
        pointer = (store/'latest-accepted.json').read_bytes()
        records, boards = self.partial()
        records[1]['status'] = 'gone'
        candidate = self.export('25', records=records, boards=boards)
        with self.assertRaisesRegex(ValueError, 'unread source'):
            feed.accept(store, candidate)
        self.assertEqual((store/'latest-accepted.json').read_bytes(), pointer)

    def test_successful_empty_board_can_close_prior_job(self):
        store = self.root / 'store'
        feed.accept(store, self.export())
        records, boards = self.partial()
        records[1]['status'] = 'gone'
        boards[1].update(read_ok=True, postings=0)
        feed.accept(store, self.export('25', records=records, boards=boards))
        self.assertEqual(feed.read_pointer(store)[1][records[1]['id']]['job']['status'], 'gone')

    def test_corruption_retains_prior_good(self):
        store = self.root/'store'
        feed.accept(store, self.export())
        before = (store/'latest-accepted.json').read_bytes()
        records, boards = self.partial()
        bad = self.export('25', records=records, boards=boards)
        with (bad/'snapshot.jsonl').open('ab') as stream:
            stream.write(b'corrupt')
        with self.assertRaises(ValueError):
            feed.accept(store, bad)
        self.assertEqual((store/'latest-accepted.json').read_bytes(), before)

    def test_idempotency_collision_and_rollback(self):
        store = self.root/'store'
        first = self.export()
        self.assertEqual(first, self.export())
        original = feed.accept(store, first)
        self.assertEqual(original, feed.accept(store, first))
        self.records[0]['title'] = 'Different synthetic title'
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.export()
        records, boards = self.partial()
        feed.accept(store, self.export('25', records=records, boards=boards))
        with self.assertRaisesRegex(ValueError, 'rollback'):
            feed.accept(store, first)
        self.assertEqual(feed.accept(store, first, rollback=True), original)

    def test_missing_previous_ids_rejected(self):
        store = self.root/'store'
        feed.accept(store, self.export())
        records, boards = self.partial()
        bad = self.export('25', records=records[:1], boards=boards)
        with self.assertRaisesRegex(ValueError, 'lost prior ids'):
            feed.accept(store, bad)

    def test_malformed_canonical_data_and_duplicate_ids_rejected(self):
        for change in ({'workplace':'guessed'}, {'schema_version':True}, {'secret':'no'},
                       {'first_seen':'2026-10-30'}, {'id':'invented'}, {'title':23}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.export(records=[{**self.records[0], **change}])
        with self.assertRaisesRegex(ValueError, 'duplicate job'):
            self.export(records=self.records+self.records)

    def test_manifest_tampering_is_rejected(self):
        for field, value in [('schema','v99'), ('run_id','../../escape'), ('coverage',{}),
                             ('started_at','2026-10-30T00:00:00Z')]:
            bundle = self.export(run='tamper-'+field)
            manifest = json.loads((bundle/'manifest.json').read_text())
            manifest[field] = value
            (bundle/'manifest.json').write_bytes(feed.encoded(manifest))
            with self.assertRaises(ValueError):
                feed.validate_bundle(bundle)

    def test_strict_json_and_limits(self):
        for raw in (b'{"a":1,"a":2}', b'{"n":NaN}'):
            with self.assertRaises(ValueError):
                feed.loads(raw)
        with patch.object(feed, 'MAX_LINE', 10), self.assertRaises(ValueError):
            feed.rows_from_bytes(b'{"long":"xxxxxxxxxxxxxxxx"}\n')
        with patch.object(feed, 'MAX_SNAPSHOT', 1), self.assertRaises(ValueError):
            feed.validate_bundle(self.export())

    def test_recovery_refreshes_source_without_losing_history(self):
        store = self.root/'store'
        feed.accept(store, self.export())
        records, boards = self.partial()
        feed.accept(store, self.export('25', records=records, boards=boards))
        for record in records:
            record['last_seen'] = '2026-10-26'
        feed.accept(store, self.export('26', records=records))
        _, rows, _, _ = feed.read_pointer(store)
        self.assertTrue(all(row['freshness'] == 'current' for row in rows.values()))
        self.assertTrue(all(row['job']['first_seen'] == '2026-10-24' for row in rows.values()))

    def test_count_mismatch_and_extra_public_fields_fail(self):
        boards = copy.deepcopy(self.boards)
        boards[0]['postings'] = 99
        with self.assertRaisesRegex(ValueError, 'board posting count'):
            self.export(boards=boards)
        bundle = self.export()
        manifest, rows, _, _ = feed.validate_bundle(bundle)
        row = next(iter(rows.values()))
        row['job']['provenance'] = {'source_url':'https://example.invalid/private'}
        payload = b''.join(feed.encoded(r) for r in rows.values())
        manifest['snapshot'].update(bytes=len(payload), sha256=feed.digest(payload))
        (bundle/'snapshot.jsonl').write_bytes(payload)
        (bundle/'manifest.json').write_bytes(feed.encoded(manifest))
        with self.assertRaisesRegex(ValueError, 'unexpected fields'):
            feed.validate_bundle(bundle)

    def test_pointer_path_escape_and_hash_mismatch_fail(self):
        store = self.root/'store'
        pointer = feed.accept(store, self.export())
        for change in ({'manifest':'../escape/manifest.json'}, {'sha256':'0'*64}):
            (store/'latest-accepted.json').write_bytes(feed.encoded({**pointer, **change}))
            with self.assertRaises(ValueError):
                feed.read_pointer(store)

    def test_lock_rejects_concurrent_writer(self):
        with feed.locked(self.root/'exports'):
            with self.assertRaises(FileExistsError):
                self.export()

    def test_failed_atomic_switch_retains_old_pointer(self):
        store = self.root/'store'
        feed.accept(store, self.export())
        before = (store/'latest-accepted.json').read_bytes()
        records, boards = self.partial()
        candidate = self.export('25', records=records, boards=boards)
        with patch.object(feed.os, 'replace', side_effect=OSError('synthetic failure')):
            with self.assertRaises(OSError):
                feed.accept(store, candidate)
        self.assertEqual((store/'latest-accepted.json').read_bytes(), before)
        self.assertIsNotNone(feed.read_pointer(store))


if __name__ == '__main__':
    unittest.main()
