"""Tests for run_sample_pipeline.py (synthetic MP3s; skipped without ffmpeg)."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from mutagen.id3 import ID3

import run_sample_pipeline as rsp
from test_staging import digest, make_mp3

HAVE_TOOLS = shutil.which('ffmpeg') and shutil.which('ffprobe')


@unittest.skipUnless(HAVE_TOOLS, 'ffmpeg/ffprobe not available')
class PipelineTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.src = self.base / 'music'
        (self.src / 'sub').mkdir(parents=True)
        make_mp3(self.src / 'a.mp3')
        make_mp3(self.src / 'sub' / 'b.mp3')
        make_mp3(self.src / 'c.mp3')  # deliberately not in the sample
        self.sample = self.base / 'stichprobe.txt'
        self.sample.write_text(
            '\n'.join([str(self.src / 'a.mp3'), str(self.src / 'sub' / 'b.mp3')]) + '\n',
            encoding='utf-8')
        self.work = self.base / 'work'
        self.target = self.base / 'staging'

    def run_pipe(self, extra, run_id='t1'):
        return rsp.main(['--sample-list', str(self.sample), '--workdir', str(self.work),
                         '--target', str(self.target), '--run-id', run_id] + extra)

    def test_dry_run_plans_only_the_sample(self):
        self.assertEqual(self.run_pipe([]), 0)
        plan = json.loads((self.work / 'plan_t1.json').read_text())
        self.assertEqual({e['relative_path'] for e in plan['entries']},
                         {'a.mp3', 'sub/b.mp3'})
        self.assertTrue(plan['summary']['sample_filtered'])
        self.assertFalse(self.target.exists() and any(self.target.rglob('*.mp3')))

    def test_apply_and_validate(self):
        self.assertEqual(self.run_pipe(['--apply']), 0)
        copied = {p.relative_to(self.target).as_posix() for p in self.target.rglob('*.mp3')}
        self.assertEqual(copied, {'sample/a.mp3', 'sample/sub/b.mp3'})
        report = json.loads((self.work / 'report_t1.json').read_text())
        self.assertEqual(report['summary']['validated'], 2)
        self.assertEqual(report['summary']['found'], 2)
        self.assertTrue(report['originals_unchanged'])
        tags = ID3(self.target / 'sample' / 'a.mp3')
        self.assertEqual(len(tags.getall(rsp.staging.TAG_KEY)), 1)

    def test_originals_unchanged(self):
        before = {p: digest(p) for p in sorted(self.src.rglob('*.mp3'))}
        self.assertEqual(self.run_pipe(['--apply']), 0)
        after = {p: digest(p) for p in sorted(self.src.rglob('*.mp3'))}
        self.assertEqual(before, after)

    def test_target_inside_source_refused(self):
        with self.assertRaises(SystemExit):
            rsp.main(['--sample-list', str(self.sample), '--workdir', str(self.work),
                      '--target', str(self.src / 'staging'), '--run-id', 't2'])
        self.assertFalse((self.src / 'staging').exists())

    def test_non_mp3_in_sample_refused(self):
        bad = self.base / 'note.txt'
        bad.write_text('x')
        self.sample.write_text(str(bad) + '\n')
        with self.assertRaises(SystemExit):
            self.run_pipe([], run_id='t3')

    def test_second_run_reuses_catalog_ids(self):
        self.assertEqual(self.run_pipe(['--apply'], run_id='r1'), 0)
        self.assertEqual(self.run_pipe(['--apply'], run_id='r2'), 0)
        first = json.loads((self.work / 'plan_r1.json').read_text())['entries']
        second = json.loads((self.work / 'plan_r2.json').read_text())['entries']
        self.assertEqual([e['source_file_id'] for e in first],
                         [e['source_file_id'] for e in second])
        self.assertEqual({e['action'] for e in second}, {'target_exists'})


if __name__ == '__main__':
    unittest.main()
