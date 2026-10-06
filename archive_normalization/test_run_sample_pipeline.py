import json
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

if __name__ == '__main__':
    unittest.main()
