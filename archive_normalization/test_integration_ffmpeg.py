"""Integration test: inventory.py with real ffprobe and a synthetic MP3."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mutagen.id3 import ID3, TIT2

import inventory

HAVE_TOOLS = shutil.which('ffmpeg') and shutil.which('ffprobe')


@unittest.skipUnless(HAVE_TOOLS, 'ffmpeg/ffprobe not available')
class InventoryFfprobeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.mp3 = self.root / 'tone.mp3'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                        'sine=frequency=440:duration=2', '-ac', '1', '-ar', '44100',
                        '-b:a', '128k', str(self.mp3)], check=True)
        tags = ID3()
        tags.add(TIT2(encoding=3, text=['  Cafe\u0301   Radio ']))
        tags.save(self.mp3)
        shutil.copyfile(self.mp3, self.root / 'COPY.MP3')
        (self.root / 'note.txt').write_text('ignored')

    def test_real_probe(self):
        before = hashlib.sha256(self.mp3.read_bytes()).hexdigest()
        record = inventory.inspect(self.mp3)
        self.assertEqual(record['quality_issues'], [])
        self.assertEqual(record['title'], 'Caf\u00e9 Radio')
        stream = record['technical']['streams'][0]
        self.assertEqual((stream['codec_name'], stream['sample_rate'], stream['channels']),
                         ('mp3', '44100', 1))
        self.assertAlmostEqual(float(record['technical']['format']['duration']), 2.0, delta=0.1)
        self.assertEqual(hashlib.sha256(self.mp3.read_bytes()).hexdigest(), before)

    def test_cli_directory_scan(self):
        res = subprocess.run([sys.executable, str(Path(inventory.__file__)), str(self.root)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0, res.stderr)
        report = json.loads(res.stdout)
        self.assertEqual(len(report['records']), 2)
        self.assertEqual(len(report['byte_duplicates']), 1)
        self.assertEqual(report['errors'], [])

    def test_full_decode(self):
        res = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(self.mp3),
                              '-map', '0:a:0', '-f', 'null', '-'], capture_output=True, text=True)
        self.assertEqual((res.returncode, res.stderr.strip()), (0, ''))


if __name__ == '__main__':
    unittest.main()
