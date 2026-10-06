import hashlib
import tempfile
import unittest
from pathlib import Path
from mutagen.id3 import ID3, TIT2, TXXX
import staging_writer

FIXTURE_SHA = None

def make_mp3(path):
    tags = ID3()
    tags.add(TIT2(encoding=3, text=['Test']))
    tags.save(path, v2_version=4)
    return hashlib.sha256(path.read_bytes()).hexdigest()

class StagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.src_dir = root / 'source'; self.src_dir.mkdir()
        self.staging = root / 'staging'; self.staging.mkdir()
        self.mp3 = self.src_dir / 'a.mp3'
        self.checksum = make_mp3(self.mp3)
        self.fid = '11111111-2222-3333-4444-555555555555'

    def plan(self, checksum=None, fid=None):
        return staging_writer.plan_item(self.mp3, self.staging,
                                        fid or self.fid, checksum or self.checksum)

    def test_dry_run_planned(self):
        item = self.plan()
        self.assertEqual(item['status'], 'planned')
        self.assertEqual(item['id3_version'], [2, 4, 0])
        self.assertEqual(self.checksum, staging_writer.sha256(self.mp3))

    def test_hash_mismatch_blocks(self):
        self.assertEqual(self.plan('0' * 64)['reason'], 'HASH_MISMATCH')

    def test_foreign_marker_blocks(self):
        tags = ID3(self.mp3)
        tags.add(TXXX(encoding=3, desc=staging_writer.TAG_DESC, text=['99999999-9999-9999-9999-999999999999']))
        tags.save(self.mp3)
        checksum = staging_writer.sha256(self.mp3)
        item = self.plan(checksum)
        self.assertEqual(item['status'], 'blocked')
        self.assertEqual(item['reason'], 'FOREIGN_ID_MARKER')

    def test_target_exists_blocks(self):
        (self.staging / (self.fid + '.mp3')).write_bytes(b'busy')
        item = self.plan()
        self.assertEqual(item['reason'], 'TARGET_EXISTS')

    def test_apply_stamps_id_and_preserves_original(self):
        original_bytes = self.mp3.read_bytes()
        item = self.plan()
        done = staging_writer.apply_item(item)
        self.assertEqual(done['status'], 'done')
        self.assertEqual(self.mp3.read_bytes(), original_bytes)
        tags = ID3(done['target_path'], translate=False)
        stamped = tags.getall('TXXX:' + staging_writer.TAG_DESC)
        self.assertEqual(str(stamped[0].text[0]), self.fid)
        with self.assertRaises(ValueError):
            staging_writer.plan_item(done['target_path'], self.staging, self.fid, staging_writer.sha256(done['target_path']))
        self.assertNotEqual(done['staging_sha256'], self.checksum)
        self.assertEqual(done['derived_from'], str(self.mp3.resolve()))

    def test_apply_blocked_item_no_write(self):
        item = self.plan('0' * 64)
        result = staging_writer.apply_item(item)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(list(self.staging.iterdir()), [])
