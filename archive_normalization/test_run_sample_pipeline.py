"""End-to-end test for run_sample_pipeline.py with synthetic MP3."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

class RunnerTests(unittest.TestCase):
    def test_end_to_end_with_real_mp3(self):
        mod_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src = tmp / 'src'; src.mkdir()
            work = tmp / 'work'
            mp3 = src / 'tone.mp3'
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi',
                            '-i', 'sine=frequency=440:duration=1', '-c:a', 'libmp3lame',
                            str(mp3)], check=True)
            fl = tmp / 'list.txt'
            fl.write_text(str(mp3.resolve()) + '\n')
            proc = subprocess.run([sys.executable, str(mod_dir / 'run_sample_pipeline.py'),
                                   str(fl), str(work)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            s = json.loads(proc.stdout)
            self.assertEqual(s['files_requested'], 1)
            self.assertEqual(s['inventory_records'], 1)
            self.assertEqual(s['inventory_errors'], 0)
            self.assertEqual(s['accepted'], 1)
            self.assertEqual(s['staging_planned'], 1)
            self.assertEqual(s['staging_blocked'], 0)

HERE = Path(__file__).resolve().parent
HAVE_FFMPEG = shutil.which('ffmpeg') is not None


def make_mp3(path, duration=1):
    """Generate a 1-second synthetic MP3 using ffmpeg."""
    subprocess.run([
        'ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
        'sine=frequency=440:duration=1', '-ac', '1', '-ar', '44100',
        '-b:a', '128k', '-id3v2_version', '0', '-write_xing', '0',
        str(path)
    ], check=True)
    # Add ID3v2.4 tags
    from mutagen.id3 import ID3, TIT2, TPE1
    tags = ID3()
    tags.add(TIT2(encoding=3, text=['Test Title']))
    tags.add(TPE1(encoding=3, text=['Test Artist']))
    tags.save(path, v2_version=4)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@unittest.skipUnless(HAVE_FFMPEG, 'ffmpeg not available')
class RunSamplePipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.filelist = self.base / 'filelist.txt'
        self.workdir = self.base / 'workdir'

    def test_e2e_pipeline(self):
        # Create synthetic MP3
        mp3 = self.base / 'test.mp3'
        make_mp3(mp3)
        self.filelist.write_text(str(mp3) + '\n', encoding='utf-8')

        # Run pipeline
        res = subprocess.run([
            sys.executable, str(HERE / 'run_sample_pipeline.py'),
            str(self.filelist), str(self.workdir)
        ], capture_output=True, text=True, cwd=HERE)

        self.assertEqual(res.returncode, 0, f'stderr: {res.stderr}')

        # Parse summary
        summary = json.loads(res.stdout.strip())
        self.assertEqual(summary['files_requested'], 1)
        self.assertEqual(summary['inventory_records'], 1)
        self.assertEqual(summary['inventory_errors'], 0)
        self.assertEqual(summary['duplicate_groups'], 0)
        self.assertEqual(summary['pilot_exit'], 0)
        self.assertEqual(summary['accepted'], 1)
        self.assertEqual(summary['rejected'], 0)

        # Check staging dry-run output
        staging_json = self.workdir / 'reports' / 'staging_dryrun.json'
        self.assertTrue(staging_json.exists())
        plan = json.loads(staging_json.read_text())
        self.assertEqual(plan['schema_version'], '0.1-staging')
        self.assertEqual(plan['mode'], 'dry-run')
        self.assertEqual(len(plan['items']), 1)
        self.assertEqual(plan['items'][0]['status'], 'planned')

        # Verify catalog was created
        catalog_db = self.workdir / 'catalog' / 'archive.sqlite'
        self.assertTrue(catalog_db.exists())

        # Verify source_file_id in plan matches catalog
        import sqlite3
        with sqlite3.connect(catalog_db) as db:
            row = db.execute('SELECT file_id FROM assets WHERE source=?', (str(mp3),)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(plan['items'][0]['source_file_id'], row[0])

    def test_pipeline_with_unicode_filename(self):
        # Create synthetic MP3 with unicode name
        mp3 = self.base / 'Tést_Datei – mit Ümläuten & Leerzeichen.mp3'
        make_mp3(mp3)
        self.filelist.write_text(str(mp3) + '\n', encoding='utf-8')

        res = subprocess.run([
            sys.executable, str(HERE / 'run_sample_pipeline.py'),
            str(self.filelist), str(self.workdir)
        ], capture_output=True, text=True, cwd=HERE)

        self.assertEqual(res.returncode, 0)
        summary = json.loads(res.stdout.strip())
        self.assertEqual(summary['files_requested'], 1)
        self.assertEqual(summary['inventory_records'], 1)
        self.assertEqual(summary['accepted'], 1)

        # Check that staging uses file_id as filename (no unicode issues)
        staging_json = self.workdir / 'reports' / 'staging_dryrun.json'
        plan = json.loads(staging_json.read_text())
        self.assertEqual(plan['items'][0]['status'], 'planned')
        target_name = Path(plan['items'][0]['target_path']).name
        self.assertTrue(target_name.endswith('.mp3'))
        # Target should be UUID.mp3, not unicode
        uuid_part = target_name[:-4]
        import uuid
        uuid.UUID(uuid_part)  # should not raise


if __name__ == '__main__':
    unittest.main()
