import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mutagen.id3 import ID3, TIT2
import inventory


class InventoryTests(unittest.TestCase):
    def test_unicode_title(self):
        self.assertEqual(inventory.normalize_title('  Cafe\u0301  Radio '), 'Caf\u00e9 Radio')

    def test_byte_duplicates(self):
        records = [{'sha256': 'abc', 'source_path': 'a'},
                   {'sha256': 'abc', 'source_path': 'b'},
                   {'sha256': 'xyz', 'source_path': 'c'}]
        self.assertEqual(inventory.duplicate_groups(records),
                         [{'sha256': 'abc', 'paths': ['a', 'b']}])

    def test_read_only_tag_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.mp3'
            tags = ID3()
            tags.add(TIT2(encoding=3, text=['  Test  Radio  ']))
            tags.save(path, v2_version=4)
            original = path.read_bytes()
            with patch('inventory.subprocess.run', side_effect=FileNotFoundError):
                record = inventory.inspect(path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(record['sha256'], hashlib.sha256(original).hexdigest())
            self.assertEqual(record['title'], 'Test Radio')
            self.assertIn('PROBE_ERROR:FileNotFoundError', record['quality_issues'])

    def test_missing_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'empty.mp3'
            path.write_bytes(b'')
            with patch('inventory.subprocess.run', side_effect=FileNotFoundError):
                record = inventory.inspect(path)
            self.assertIn('ID3_MISSING', record['quality_issues'])
            self.assertIn('TITLE_MISSING', record['quality_issues'])


if __name__ == '__main__':
    unittest.main()
