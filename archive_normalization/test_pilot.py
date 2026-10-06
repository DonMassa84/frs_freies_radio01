import tempfile
import unittest
from pathlib import Path
from pilot import run

class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'catalog.sqlite'
        self.item = {'source_path': 'synthetic/a.mp3', 'sha256': 'a' * 64, 'title': '  Cafe\u0301  Radio '}

    def test_repeat_and_reopen(self):
        self.assertEqual(run([self.item], self.db), run([self.item], self.db))

    def test_normalized_and_raw_preserved(self):
        record = run([self.item], self.db)['accepted'][0]
        self.assertEqual(record['title'], 'Caf\u00e9 Radio')
        self.assertEqual(record['raw_record'], self.item)

    def test_duplicate_bytes_keep_distinct_ids(self):
        other = dict(self.item, source_path='synthetic/b.mp3')
        report = run([self.item, other], self.db)
        self.assertEqual(len(report['byte_duplicate_candidates']), 1)
        self.assertNotEqual(report['accepted'][0]['file_id'], report['accepted'][1]['file_id'])

    def test_changed_source_rejected(self):
        first = run([self.item], self.db)
        report = run([dict(self.item, sha256='b' * 64)], self.db)
        self.assertEqual(report['rejected'][0]['code'], 'SOURCE_CONTENT_CHANGED')
        self.assertEqual(first, run([self.item], self.db))

    def test_missing_title_warning(self):
        report = run([dict(self.item, title=None)], self.db)
        self.assertEqual(len(report['accepted']), 1)
        self.assertEqual(report['findings'][0]['severity'], 'warning')

    def test_invalid_hash_rejected(self):
        report = run([dict(self.item, sha256='invalid')], self.db)
        self.assertEqual(report['rejected'][0]['code'], 'INVALID_SHA256')

    def test_repeated_source_in_batch_rejected(self):
        report = run([self.item, self.item], self.db)
        self.assertEqual(len(report['accepted']), 1)
        self.assertEqual(report['rejected'][0]['code'], 'DUPLICATE_SOURCE_IN_BATCH')
