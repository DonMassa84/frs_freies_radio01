#!/usr/bin/env python3
"""Mediathek-Scraper: robuste Extraktion der Sendeplätze von freies-radio.de.

Reparatur zu F-003 (Version vom 22.10.2026, siehe
docs/mediathek-scraper-reparatur-2026-10-22.md).

AUSGANGSFEHLER
  Die bisherige Extraktion in 'alles_scrapen.py' suchte nach
  'div.view-content' und 'h3'. Diese Struktur existiert auf der Seite nicht
  mehr; die Seite liefert heute 0 Treffer. Der eingecheckte Snapshot
  data/mediathek.json (13 Eintraege vom 19.11.2025) stammt aus einer
  Skriptversion, die nicht im Repository liegt - er ist mit keinem
  eingecheckten Skript reproduzierbar. Zusaetzlich sind in diesem Snapshot
  alle 13 'title'-Felder leer und 5 Eintraege teilen sich dieselbe URL.

HEUTIGE SEITENSTRUKTUR (pro 'div.views-row')
  div.views-field-field-slot        -> time[datetime] (ISO 8601, Beginn/Ende)
  div.views-field-field-broadcast   -> a[href^="/sendungsdetails/"] (Sendung)
                                       span (Teaser/Beschreibung)
  div.views-field-field-teaser      -> Teasertext
  div.views-field-field-media-audio-file -> source[src] (Audiodatei)

GRENZEN
  * ausschliesslich lesender Zugriff (GET) auf freies-radio.de
  * robots.txt erlaubt 'User-agent: *' (nur /system/ gesperrt); dieser
    Scraper fragt /mediathek ab, nicht /system/
  * keine Anmeldung, keine Schreibzugriffe, keine Umgehung von Massnahmen
  * ausschliesslich oeffentliche Sendemetadaten; keine personenbezogenen
    Inhalte werden erfasst, nichts wird veroeffentlicht

Aufruf
  python3 mediathek_scraper.py --html seite.html --out data/mediathek.live.json
  python3 mediathek_scraper.py --fetch --out data/mediathek.live.json
  python3 mediathek_scraper.py --repair data/mediathek.json --out <datei>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

BASE_URL = "https://www.freies-radio.de"
MEDIATHEK_URL = f"{BASE_URL}/mediathek"
USER_AGENT = ("FRS-Archiv-Audit/1.0 (IHK-Projektarbeit FRS-Archiv; "
               "read-only Metadatenerhebung der Mediathek)")
REQUEST_TIMEOUT = 60

# Feldsatz: bestehendes Schema (title, date, url, description) PLUS neue
# Felder. Bestehende Schluessel bleiben erhalten und behalten ihre Bedeutung.
FIELDS = ["title", "date", "url", "description",
          "series", "time_start", "time_end", "teaser", "audio_url"]


# --------------------------------------------------------------------------
# HTML-Extraktion
# --------------------------------------------------------------------------
class _RowParser(HTMLParser):
    """Sammelt die fuer einen 'div.views-row' relevanten Teilstuecke."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[dict] = []
        self._row: dict | None = None
        self._depth = 0
        self._field: str | None = None
        self._capture: str | None = None
        self._buf: list[str] = []

    # -- Hilfen -----------------------------------------------------------
    @staticmethod
    def _classes(attrs: dict) -> set[str]:
        return set((attrs.get("class") or "").split())

    def _field_of(self, attrs: dict) -> str | None:
        for cls in self._classes(attrs):
            if cls.startswith("views-field-field-"):
                return cls[len("views-field-field-"):]
        return None

    # -- HTMLParser -------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "views-row" in self._classes(a):
            self._row = {"times": [], "link": None, "link_text": [],
                         "teaser": [], "audio": None, "bold": []}
            self._depth = 1
            return
        if self._row is None:
            return
        if tag == "div":
            self._depth += 1
            f = self._field_of(a)
            if f:
                self._field = f
            return
        if tag == "time":
            dt = a.get("datetime")
            if dt:
                self._row["times"].append(dt)
            self._capture = "time_text"
            self._buf = []
            return
        if tag == "a":
            href = a.get("href") or ""
            if "/sendungsdetails/" in href:
                self._row["link"] = href
                self._capture = "link"
                self._buf = []
            return
        if tag == "br":
            if self._capture == "link":
                self._row["link_text"].append(" ".join(self._buf).strip())
                self._buf = []
                self._capture = None
            return
        if tag == "span":
            classes = self._classes(a)
            if self._field == "broadcast" and "font-bold" in classes:
                self._capture = "bold"
                self._buf = []
                return
            if self._field == "teaser":
                self._capture = "teaser"
                self._buf = []
                return
            return
        if tag == "source" and self._field == "media-audio-file":
            self._row["audio"] = a.get("src")

    def handle_endtag(self, tag):
        if self._row is None:
            return
        if tag in ("time", "a", "span"):
            if self._capture == "link" and tag == "a":
                self._row["link_text"].append(" ".join(self._buf).strip())
                self._buf = []
                self._capture = None
            elif self._capture == "time_text" and tag == "time":
                self._buf = []
                self._capture = None
            elif self._capture == "bold" and tag == "span":
                text = " ".join(self._buf).strip()
                if text:
                    self._row["bold"].append(text)
                self._buf = []
                self._capture = None
            elif self._capture == "teaser" and tag == "span":
                text = " ".join(self._buf).strip()
                if text:
                    self._row["teaser"].append(text)
                self._buf = []
                self._capture = None
        if tag == "div":
            self._depth -= 1
            if self._depth == 0 and self._row is not None:
                self.rows.append(self._row)
                self._row = None
                self._field = None
            elif self._depth == 1:
                self._field = None

    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)


def _de_slash(html: str) -> str:
    """Drupal liefert Teile der Mediathek ueber einen Ajax-Endpunkt
    ('frs-media-library js-view-dom-id-...'). Fuer den Offline-Fall wird nur
    das, was vorhanden ist, verwendet."""
    return html


def parse_mediathek_html(html: str) -> list[dict]:
    """Extrahiert die Sendeplaetze aus einem Mediathek-HTML-Dokument.

    Liefert eine Liste von Dicts mit den Feldern aus FIELDS. Eintraege ohne
    verwertbaren Titel oder ohne URL werden verworfen."""
    parser = _RowParser()
    parser.feed(html)
    out: list[dict] = []
    for row in parser.rows:
        url = row["link"]
        if not url:
            continue
        if url.startswith("/"):
            url = BASE_URL + url
        texts = [t for t in row["link_text"] if t]
        title = texts[0] if texts else ""
        teaser = texts[1] if len(texts) > 1 else ""
        if not teaser and row["bold"]:
            teaser = row["bold"][0]
        if not teaser and row["teaser"]:
            teaser = row["teaser"][0]
        if not title:
            # Fallback: Teaser als Titel verwenden, aber nur wenn eindeutig.
            title = row["bold"][0] if row["bold"] else ""
        if not title.strip():
            continue
        times = row["times"]
        time_start = times[0] if times else ""
        time_end = times[1] if len(times) > 1 else ""
        date = ""
        if time_start:
            try:
                date = datetime.fromisoformat(time_start).strftime("%d.%m.%Y")
            except ValueError:
                date = ""
        description = teaser or title
        audio = row["audio"]
        out.append({
            "title": title.strip(),
            "date": date,
            "url": url,
            "description": description.strip(),
            "series": title.strip(),
            "time_start": time_start,
            "time_end": time_end,
            "teaser": teaser.strip(),
            "audio_url": (BASE_URL + audio) if audio and audio.startswith("/") else (audio or ""),
        })
    return out


# --------------------------------------------------------------------------
# Dublettenkontrolle
# --------------------------------------------------------------------------
def dedupe(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """Entfernt Dubletten ueber (url, Zeitbeginn).

    Rueckgabe: (eindeutige Eintraege, entfernte Dubletten).
    """
    seen: set[tuple] = set()
    unique: list[dict] = []
    removed: list[dict] = []
    for e in entries:
        key = (e.get("url", ""), e.get("time_start") or e.get("date", ""))
        if key in seen:
            removed.append(e)
            continue
        seen.add(key)
        unique.append(e)
    return unique, removed


# --------------------------------------------------------------------------
# Snapshot-Reparatur (offline, ohne Netzwerk)
# --------------------------------------------------------------------------
TIME_PREFIX_RE = re.compile(
    r"^\s*(?:\w{2,3}\.,?)?\s*(\d{1,2}\.\d{1,2}\.\d{4}),\s*"
    r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s+(.*)$", re.DOTALL)


def _split_title(rest: str) -> tuple[str, str]:
    """Trennt die Beschreibung in (Titel, Teaser).

    Konservative Regel: der Titel endet an der ersten klaren Trennstelle -
    ' - ' (Titel - Untertitel) oder am Ende des ersten Satzes. Was nicht
    eindeutig trennbar ist, bleibt im Titel; das Ergebnis wird in
    'titel_qualitaet' als 'abgeleitet' gekennzeichnet.
    """
    rest = rest.strip()
    # 1) ' - ' als Titelgrenze, aber nur wenn es frueh kommt (< 80 Zeichen)
    dash = rest.find(" - ")
    if 0 < dash <= 80:
        return rest[:dash].strip(), rest[dash + 3:].strip()
    # 2) Satzgrenze: Punkt gefolgt von Grossbuchstabe/Leerzeichen
    m = re.search(r"(?<=[a-zäöüß0-9])\.\s+(?=[A-ZÄÖÜ0-9])", rest)
    if m:
        return rest[:m.start() + 1].strip(), rest[m.end():].strip()
    # 3) untrennbar
    return rest, ""


def repair_snapshot(entries: list[dict]) -> tuple[list[dict], list[str]]:
    """Repariert einen eingecheckten Snapshot, in dem die Titel leer sind.

    Der Snapshot enthaelt den Sendeplatz im 'description'-Feld mit dem Muster
    '<Wochentag>, <Datum>, <von> - <bis> <Titel> <Beschreibung>'. Daraus werden
    Titel, Datum und die beiden Uhrzeiten abgeleitet.

    Das ist eine ABGELEITETE Rekonstruktion aus dem gespeicherten Text, KEIN
    Neuabruf und KEINE Originalangabe der Website. Der aus der Beschreibung
    abgeleitete Titel kann vom Seitentitel der Website abweichen (z. B. wenn
    Sendungstitel und Untertitel nicht eindeutig trennbar sind). Jeder
    reparierte Eintrag wird deshalb mit 'rekonstruiert': true und
    'titel_qualitaet' gekennzeichnet. Verbindliche Titel liefert nur der
    Abruf der Live-Seite (parse_mediathek_html).

    Rueckgabe: (reparierte Eintraege, Liste der nicht reparierbaren Faelle)."""
    out: list[dict] = []
    problems: list[str] = []
    for i, e in enumerate(entries):
        desc = (e.get("description") or "").strip()
        m = TIME_PREFIX_RE.match(desc)
        new = dict(e)
        if m:
            date_de, t_start, t_end, rest = m.groups()
            title, teaser = _split_title(rest)
            new["title"] = title
            new["series"] = title
            new["date"] = date_de
            new["time_start"] = t_start
            new["time_end"] = t_end
            new["teaser"] = teaser
            new["description"] = teaser or title
            new["rekonstruiert"] = True
            new["titel_qualitaet"] = "abgeleitet"
        elif not (e.get("title") or "").strip():
            problems.append(f"Index {i}: kein Titel ableitbar (url={e.get('url','')})")
            continue
        out.append(new)
    return out, problems


# --------------------------------------------------------------------------
# Abruf
# --------------------------------------------------------------------------
def fetch_mediathek(url: str = MEDIATHEK_URL) -> str:
    """Read-only GET der Mediathek-Seite. Kein Schreibzugriff."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} von {url}")
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, "replace")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--html", help="lokale HTML-Datei (offline)")
    src.add_argument("--fetch", action="store_true", help="Seite live abrufen (nur lesend)")
    src.add_argument("--repair", help="eingecheckten JSON-Snapshot reparieren")
    ap.add_argument("--out", help="Zieldatei (JSON)")
    ap.add_argument("--stdout", action="store_true", help="Ergebnis auf stdout")
    args = ap.parse_args()

    problems: list[str] = []
    if args.repair:
        data = json.loads(Path(args.repair).read_text(encoding="utf-8"))
        entries, problems = repair_snapshot(data)
    else:
        html = Path(args.html).read_text(encoding="utf-8", errors="replace") if args.html \
            else fetch_mediathek()
        entries = parse_mediathek_html(html)

    unique, removed = dedupe(entries)
    leere_titel = [e for e in unique if not (e.get("title") or "").strip()]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "live (read-only GET)" if args.fetch else
                  ("snapshot-reparatur" if args.repair else "lokale HTML-Datei"),
        "entries_before_dedupe": len(entries),
        "entries": len(unique),
        "duplicates_removed": len(removed),
        "empty_titles": len(leere_titel),
        "unrepairable": problems,
        "data": unique,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"{len(unique)} Eintraege -> {p} "
              f"(Dubletten entfernt: {len(removed)}, leere Titel: {len(leere_titel)})")
    if args.stdout or not args.out:
        print(text)
    if problems:
        for pr in problems:
            print(f"WARN: {pr}", file=sys.stderr)
    return 0 if not leere_titel and not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
