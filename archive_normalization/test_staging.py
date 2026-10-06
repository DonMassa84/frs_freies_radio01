"""Synthetic tests for staging.py. Requires ffmpeg/ffprobe; skipped otherwise."""
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

from mutagen.id3 import APIC, ID3, TIT2, TPE1, TXXX

import staging
from pilot import run as pilot_run

def _png():
    """Valid 1x1 PNG so ffmpeg does not report a broken attached picture."""
    def chunk(kind, data):
        body = kind + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body))
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00')) + chunk(b'IEND', b''))


PNG = _png()

HAVE_FFMPEG = shutil.which('ffmpeg') is not None


def make_mp3(path, v2_version=4, with_v1=False, title='Café Radio', freq=440):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                    'sine=frequency=%d:duration=1' % freq, '-ac', '1', '-ar', '44100',
                    '-b:a', '128k', '-id3v2_version', '0', '-write_xing', '0',
                    str(path)], check=True)
    tags = ID3()
    tags.add(TIT2(encoding=1 if v2_version == 3 else 3, text=[title]))
    tags.add(TPE1(encoding=1 if v2_version == 3 else 3, text=['Synthetic Artist']))
    tags.add(APIC(encoding=0, mime='image/png', type=3, desc='cover', data=PNG))
    tags.save(path, v2_version=v2_version, v1=2 if with_v1 else 0)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@unittest.skipUnless(HAVE_FFMPEG, 'ffmpeg not available')
class StagingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.src = self.base / 'source'
        (self.src / 'sub').mkdir(parents=True)
        self.target = self.base / 'staging'
        self.catalog = self.base / 'catalog.sqlite'
        self.config = self.base / 'config.json'
        self.counter = 0
        self.write_config()

    def write_config(self, target=None):
        self.config.write_text(json.dumps({
            'sources': [{'namespace': 'synthetic', 'path': str(self.src)}],
            'target': str(target or self.target), 'reserve_ratio': 0.1}), encoding='utf-8')

    def catalog_all(self):
        records = [{'source_path': str(p.resolve()), 'sha256': digest(p), 'title': None}
                   for p in sorted(self.src.rglob('*.mp3'))]
        return pilot_run(records, self.catalog)

    def plan(self):
        self.counter += 1
        out = self.base / ('plan%d.json' % self.counter)
        self.assertEqual(staging.main(['plan', '--config', str(self.config),
                                       '--catalog', str(self.catalog), '--out', str(out)]), 0)
        return out, hashlib.sha256(out.read_bytes()).hexdigest()

    def apply(self, plan, sha):
        self.counter += 1
        out = self.base / ('apply%d.json' % self.counter)
        code = staging.main(['apply', '--plan', str(plan), '--plan-sha256', sha, '--out', str(out)])
        return code, (json.loads(out.read_text()) if out.exists() else None)

    def validate(self, plan):
        self.counter += 1
        out = self.base / ('report%d.json' % self.counter)
        code = staging.main(['validate', '--plan', str(plan), '--out', str(out)])
        return code, json.loads(out.read_text())

    def full_run(self):
        plan, sha = self.plan()
        code, _ = self.apply(plan, sha)
        self.assertEqual(code, 0)
        return plan, self.validate(plan)

    def test_original_unchanged_and_tag_written(self):
        mp3 = self.src / 'sub' / 'a.mp3'
        make_mp3(mp3)
        before = digest(mp3)
        file_id = self.catalog_all()['accepted'][0]['file_id']
        plan, (code, report) = self.full_run()
        self.assertEqual(code, 0)
        self.assertEqual(digest(mp3), before)
        copy = self.target / 'synthetic' / 'sub' / 'a.mp3'
        self.assertEqual([str(t) for t in ID3(copy).getall(staging.TAG_KEY)[0].text], [file_id])
        item = report['items'][0]
        self.assertEqual(item['status'], 'validated')
        self.assertTrue(all(item['checks'].values()))
        self.assertNotEqual(item['copy_id'], file_id)
        self.assertTrue(report['originals_unchanged'])

    def test_other_tags_and_audio_equal(self):
        make_mp3(self.src / 'a.mp3')
        self.catalog_all()
        _, (_, report) = self.full_run()
        checks = report['items'][0]['checks']
        self.assertTrue(checks['other_frames_equal'])
        self.assertTrue(checks['audio_equal'])
        src_tags = ID3(self.src / 'a.mp3')
        dst_tags = ID3(self.target / 'synthetic' / 'a.mp3')
        self.assertEqual(src_tags.getall('APIC')[0].data, dst_tags.getall('APIC')[0].data)

    def test_v23_kept_and_v1_preserved(self):
        make_mp3(self.src / 'a.mp3', v2_version=3, with_v1=True)
        self.catalog_all()
        _, (_, report) = self.full_run()
        copy = self.target / 'synthetic' / 'a.mp3'
        self.assertEqual(ID3(copy, translate=False).version[:2], (2, 3))
        self.assertEqual(Path(self.src / 'a.mp3').read_bytes()[-128:], copy.read_bytes()[-128:])
        self.assertEqual(report['items'][0]['status'], 'validated')

    def test_existing_target_not_overwritten(self):
        make_mp3(self.src / 'a.mp3')
        self.catalog_all()
        existing = self.target / 'synthetic' / 'a.mp3'
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b'keep me')
        plan, sha = self.plan()
        self.assertEqual(json.loads(plan.read_text())['entries'][0]['action'], 'target_exists')
        self.apply(plan, sha)
        self.assertEqual(existing.read_bytes(), b'keep me')

    def test_foreign_id_is_conflict(self):
        mp3 = self.src / 'a.mp3'
        make_mp3(mp3)
        tags = ID3(mp3)
        tags.add(TXXX(encoding=3, desc=staging.TAG_DESC, text=['foreign-id']))
        tags.save(mp3)
        self.catalog_all()
        plan, sha = self.plan()
        entry = json.loads(plan.read_text())['entries'][0]
        self.assertEqual((entry['action'], entry['note']), ('conflict', 'FOREIGN_SOURCE_ID'))
        self.apply(plan, sha)
        self.assertFalse((self.target / 'synthetic' / 'a.mp3').exists())

    def test_wrong_plan_hash_blocks_apply(self):
        make_mp3(self.src / 'a.mp3')
        self.catalog_all()
        plan, _ = self.plan()
        code, report = self.apply(plan, '0' * 64)
        self.assertEqual(code, 2)
        self.assertIsNone(report)
        self.assertFalse(self.target.exists() and any(self.target.rglob('*.mp3')))

    def test_changed_original_after_plan_rejected(self):
        mp3 = self.src / 'a.mp3'
        make_mp3(mp3)
        self.catalog_all()
        plan, sha = self.plan()
        with mp3.open('ab') as handle:
            handle.write(b'\0')
        code, report = self.apply(plan, sha)
        self.assertEqual(code, 1)
        self.assertEqual(report['results'][0]['detail'], 'SOURCE_CHANGED_SINCE_PLAN')
        self.assertFalse((self.target / 'synthetic' / 'a.mp3').exists())

    def test_target_inside_source_refused(self):
        make_mp3(self.src / 'a.mp3')
        self.catalog_all()
        self.write_config(target=self.src / 'staging')
        out = self.base / 'bad_plan.json'
        code = staging.main(['plan', '--config', str(self.config),
                             '--catalog', str(self.catalog), '--out', str(out)])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_repeat_run_changes_nothing(self):
        make_mp3(self.src / 'a.mp3')
        self.catalog_all()
        plan, sha = self.plan()
        self.apply(plan, sha)
        copy = self.target / 'synthetic' / 'a.mp3'
        first = digest(copy)
        code, report = self.apply(plan, sha)
        self.assertEqual(code, 0)
        self.assertEqual(report['summary'], {'already_done': 1})
        self.assertEqual(digest(copy), first)
        plan2, _ = self.plan()
        self.assertEqual(json.loads(plan2.read_text())['entries'][0]['action'], 'target_exists')

    def test_uncataloged_file_not_copied(self):
        make_mp3(self.src / 'a.mp3')
        pilot_run([], self.catalog)  # empty catalog
        plan, sha = self.plan()
        self.assertEqual(json.loads(plan.read_text())['entries'][0]['action'], 'not_cataloged')
        self.apply(plan, sha)
        self.assertFalse((self.target / 'synthetic' / 'a.mp3').exists())

    def test_missing_catalog_refused(self):
        make_mp3(self.src / 'a.mp3')
        out = self.base / 'plan_nocat.json'
        code = staging.main(['plan', '--config', str(self.config),
                             '--catalog', str(self.catalog), '--out', str(out)])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_byte_duplicates_get_separate_copies(self):
        make_mp3(self.src / 'a.mp3')
        shutil.copyfile(self.src / 'a.mp3', self.src / 'sub' / 'b.mp3')
        ids = {r['file_id'] for r in self.catalog_all()['accepted']}
        _, (_, report) = self.full_run()
        self.assertEqual(len(report['items']), 2)
        self.assertEqual({i['source_file_id'] for i in report['items']}, ids)
        self.assertEqual(len({i['copy_id'] for i in report['items']}), 2)


if __name__ == '__main__':
    unittest.main()
