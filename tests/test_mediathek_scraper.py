"""Regressionstests fuer den Mediathek-Scraper (F-003-Reparatur).

Offline: die Tests laufen gegen ein festes HTML-Fixture, nie gegen die
Live-Site. Sie pruefen die Extraktionslogik, die Dublettenkontrolle und die
Snapshot-Reparatur.

Aufruf:  python3 -m unittest discover -s tests -v
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mediathek_scraper import (dedupe, parse_mediathek_html,  # noqa: E402
                               repair_snapshot, _split_title)

FIXTURE = ROOT / "tests" / "fixtures" / "mediathek_rows.html"
SNAPSHOT = ROOT / "data" / "mediathek.json"


class ParseTests(unittest.TestCase):
    """Extraktion aus der heutigen Seitenstruktur."""

    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.entries = parse_mediathek_html(cls.html)

    def test_fixture_yields_entries(self):
        self.assertGreaterEqual(len(self.entries), 3)

    def test_no_entry_has_an_empty_title(self):
        for e in self.entries:
            self.assertTrue(e["title"].strip(), f"leerer Titel: {e}")

    def test_title_is_taken_from_the_sendung_link(self):
        titles = {e["title"] for e in self.entries}
        self.assertIn("Radio Synthesis", titles)
        self.assertIn("Kulturpalast", titles)

    def test_extended_fields_are_present(self):
        for key in ("series", "time_start", "time_end", "teaser", "audio_url"):
            self.assertIn(key, self.entries[0])
            self.assertTrue(self.entries[0][key], f"Feld {key} leer")

    def test_timestamps_are_iso_8601(self):
        self.assertTrue(self.entries[0]["time_start"].startswith("2026-10-21T23:00:00"))

    def test_date_is_derived_from_the_timestamp(self):
        self.assertEqual(self.entries[0]["date"], "21.10.2026")

    def test_url_is_absolute(self):
        for e in self.entries:
            self.assertTrue(e["url"].startswith("https://www.freies-radio.de/"))

    def test_no_duplicate_url_time_combinations(self):
        unique, removed = dedupe(self.entries)
        keys = [(e["url"], e["time_start"]) for e in unique]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(removed, [])

    def test_broken_markup_yields_no_bogus_titles(self):
        """Ohne Sendeplatz-Link darf kein Eintrag entstehen."""
        html = '<div class="views-row"><div class="views-field views-field-field-slot">' \
               '<span class="field-content"><time datetime="2026-10-21T23:00:00+02:00">x</time>' \
               '</span></div></div>'
        self.assertEqual(parse_mediathek_html(html), [])

    def test_legacy_selector_returns_nothing(self):
        """Regression: die alte Struktur 'div.view-content' existiert nicht mehr."""
        legacy = '<div class="view-content"><h3>Titel</h3></div>'
        self.assertEqual(parse_mediathek_html(legacy), [])


class DedupeTests(unittest.TestCase):
    def test_same_url_and_time_is_removed(self):
        base = {"url": "u", "time_start": "t", "date": "d", "title": "T"}
        unique, removed = dedupe([dict(base), dict(base)])
        self.assertEqual(len(unique), 1)
        self.assertEqual(len(removed), 1)

    def test_same_url_different_time_is_kept(self):
        a = {"url": "u", "time_start": "t1", "date": "d", "title": "T"}
        b = {"url": "u", "time_start": "t2", "date": "d", "title": "T"}
        unique, removed = dedupe([a, b])
        self.assertEqual(len(unique), 2)
        self.assertEqual(removed, [])


class SnapshotRepairTests(unittest.TestCase):
    """Reparatur des eingecheckten 13-Eintraege-Snapshots."""

    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        cls.entries, cls.problems = repair_snapshot(cls.raw)

    def test_snapshot_has_13_entries(self):
        self.assertEqual(len(self.raw), 13)

    def test_all_titles_are_filled(self):
        self.assertEqual(self.problems, [])
        self.assertEqual(len(self.entries), 13)
        for e in self.entries:
            self.assertTrue(e["title"].strip())

    def test_no_duplicate_url_date_time_combinations(self):
        keys = [(e["url"], e["date"], e["time_start"]) for e in self.entries]
        self.assertEqual(len(keys), len(set(keys)))

    def test_time_slots_are_extracted(self):
        times = {(e["time_start"], e["time_end"]) for e in self.entries}
        self.assertIn(("14:00", "15:00"), times)
        self.assertIn(("07:00", "08:00"), times)

    def test_reconstruction_is_flagged_as_derived(self):
        for e in self.entries:
            self.assertTrue(e["rekonstruiert"])
            self.assertEqual(e["titel_qualitaet"], "abgeleitet")

    def test_original_snapshot_file_is_not_modified(self):
        """Die Reparatur darf die eingecheckte Datei nicht veraendern."""
        before = SNAPSHOT.read_bytes()
        repair_snapshot(json.loads(before.decode("utf-8")))
        self.assertEqual(SNAPSHOT.read_bytes(), before)


class TitleSplitTests(unittest.TestCase):
    def test_dash_separates_title_and_teaser(self):
        title, teaser = _split_title("Refugee Radio Common Voices #494 - Frauenrechte in Mali")
        self.assertEqual(title, "Refugee Radio Common Voices #494")
        self.assertEqual(teaser, "Frauenrechte in Mali")

    def test_sentence_end_separates_title_and_teaser(self):
        title, teaser = _split_title("Inforedaktion: Mit Janka Der Medienspiegel. Erstsendung 16.11.2025")
        self.assertEqual(title, "Inforedaktion: Mit Janka Der Medienspiegel.")
        self.assertEqual(teaser, "Erstsendung 16.11.2025")

    def test_lowercase_continuation_is_not_split(self):
        """Konservativ: ohne eindeutige Grenze bleibt der Text im Titel."""
        title, teaser = _split_title("frizles radiosendung alltäglicher irr & wahnsinn. be & entschleunigung")
        self.assertEqual(title, "frizles radiosendung alltäglicher irr & wahnsinn. be & entschleunigung")
        self.assertEqual(teaser, "")

    def test_unseparable_text_stays_in_title(self):
        title, teaser = _split_title("Caribe Afro Latina Caribe Afro Latina")
        self.assertEqual(title, "Caribe Afro Latina Caribe Afro Latina")
        self.assertEqual(teaser, "")


if __name__ == "__main__":
    unittest.main()
