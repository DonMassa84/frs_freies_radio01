# Mediathek-Scraper — Reparatur F-003

**Stand:** 22.10.2026 · **Status:** PRE_PROJECT · **Phase:** Vorbereitung, keine Freigabe,
kein Leistungsnachweis, keine Aussage über die Tauglichkeit für ein FRS-Archiv.

Gehört zu Auftrag **OC-03** aus `docs/research/perplexity/HANDOVER_OPENCODE_GO.yaml`
(Repository `DonMassa84/ihk-projektarbeit-frs-archiv`, Branch
`research/frs-media-audit-20261022`).

---

## 1. Befund (reproduziert am 22.10.2026)

| Nr | Befund | Nachweis |
|---|---|---|
| B-1 | `alles_scrapen.py::scrape_mediathek()` sucht `div.view-content` und `h3`. Diese Struktur existiert auf der Seite nicht mehr — der Selektor liefert **0 Treffer**. | Live-Abruf 22.10.2026: `view-content` = 0, `<h3>` = 1 (statischer Einleitungstext) |
| B-2 | Der eingecheckte Snapshot `data/mediathek.json` (13 Einträge, 19.11.2025) ist mit **keinem** eingecheckten Skript reproduzierbar: `alles_scrapen_mediathek.py` liest `mediathek.md` (2 Einträge, Platzhalter-URLs), `alles_scrapen.py` schreibt 3 statt 4 Felder. | Testlauf beider Skripte gegen die eigenen Eingaben |
| B-3 | In allen 13 Snapshot-Einträgen ist `title` leer. | Feldzählung über `data/mediathek.json` |
| B-4 | 5 Snapshot-Einträge teilen sich dieselbe URL (8 eindeutige URLs). Die URL allein identifiziert **keinen** Sendeplatz — dieselbe Sendung erscheint zu mehreren Uhrzeiten. | Eindeutigkeitszählung über `url` |
| B-5 | Es existieren drei `mediathek.json` mit **drei verschiedenen Schemata**: `data/` (13 Einträge, 4 Felder), `assets/` (68 Einträge, nur `text` = ganze Seitentexte), `docs/` (2 Einträge, `date`+`title`, Platzhalter). | Schema-Vergleich der drei Dateien |
| B-6 | Konsumiert wird ausschließlich `docs/data/mediathek.json` über `docs/app.js:39` (`${e.date} – ${e.title}`). Der 13-Einträge-Snapshot wird von **niemandem** gelesen. | Grep über `*.dart`, `*.js`, `*.html` |

**Ursache:** Der Scraper ist an eine Seitenstruktur gebunden, die ersetzt wurde, und
wurde nicht nachgeführt. Die Selektoren, nicht die Daten, sind der Defekt.

## 2. Heutige Seitenstruktur (gelesen am 22.10.2026)

```
div.views-row
├─ div.views-field-field-slot            → time[datetime]  (ISO 8601, Beginn und Ende)
├─ div.views-field-field-broadcast       → a[href^="/sendungsdetails/"]  (Sendungstitel)
│                                          span.font-bold                 (Teaser)
├─ div.views-field-field-teaser          → Teasertext
└─ div.views-field-field-media-audio-file→ source[src]                  (Audiodatei)
```

Die Sendeplätze liegen in `div.views-row`. `time[datetime]` liefert die Zeiten
maschinenlesbar — damit ist der geforderte Dublettenschlüssel **(url, Zeitbeginn)**
belastbar bildbar.

## 3. Reparatur

Neue Datei **`mediathek_scraper.py`** (nur Standardbibliothek, kein `bs4`, kein Netz
für die Tests):

* `parse_mediathek_html(html)` — reine Funktion, offline testbar. Liefert je Sendeplatz
  `title`, `date`, `url`, `description` (bestehendes Schema) **plus** `series`,
  `time_start`, `time_end`, `teaser`, `audio_url`.
* `dedupe(entries)` — entfernt Dubletten über `(url, time_start)`; liefert die
  entfernten Einträge zurück, damit nichts stillschweigend verloren geht.
* `fetch_mediathek(url)` — ausschließlich lesender GET auf `freies-radio.de/mediathek`.
  `robots.txt` erlaubt `User-agent: *` (gesperrt ist nur `/system/`). Eigener
  User-Agent mit Zweckangabe; ein Request pro Lauf, kein Massenabruf.
* `repair_snapshot(entries)` — **offline**-Reparatur des eingecheckten Snapshots aus
  dem gespeicherten Beschreibungstext (siehe Abschnitt 4).

**Nicht verändert:** `data/mediathek.json` (historischer Snapshot, bleibt unangetastet),
`assets/data/mediathek.json` (Flutter-Vertrag), `docs/data/mediathek.json` (Portal-Demo),
`alles_scrapen.py` / `alles_scrapen_mediathek.py` (Altwerkzeuge bleiben als Ist-Stand
nachvollziehbar).

## 4. Grenzen der Snapshot-Reparatur — ausdrücklich

Die 13 Snapshot-Einträge enthalten keinen Seitentitel, sondern nur den
Beschreibungstext im Muster `<Wochentag>, <Datum>, <von> - <bis> <Titel> <Beschreibung>`.
Daraus lässt sich ein Titel **ableiten**, nicht **belegen**:

* `titel_qualitaet: "abgeleitet"` und `rekonstruiert: true` werden je Eintrag gesetzt.
* Wo Sendungstitel und Untertitel nicht trennbar sind, bleibt der längere Text im Titel.
  Beispiel: „Surprise Medienprojektwoche Eine Sendung von Schüler_innen der
  Albert-Schweitzer-Schule Fellbach“ statt „Surprise Medienprojektwoche“.
* **Verbindliche Titel liefert nur der Abruf der Live-Seite** (`parse_mediathek_html`).

## 5. Nachweis

| Prüfung | Ergebnis |
|---|---|
| Live-Seite 22.10.2026, 98 `views-row`, 51 mit Sendeplatz-Link | 51 Einträge, **0 leere Titel**, **0 Dubletten** über (url, time_start) |
| Snapshot-Reparatur `data/mediathek.json` | 13 Einträge, **0 leere Titel**, **0 Dubletten** über (url, datum, zeit) |
| `python3 -m unittest discover -s tests -v` | **22 Tests, 0 Fehler** (davon 15 neue) |
| `node --test tests/research.test.cjs` | **5 Tests, 0 Fehler** (unveränderter Altbestand) |
| Originaldatei `data/mediathek.json` | unverändert (Test `test_original_snapshot_file_is_not_modified`) |
| `docs/app.js`-Vertrag `e.date` / `e.title` | weiterhin erfüllt (beide Felder vorhanden) |

Die Tests laufen **offline** gegen `tests/fixtures/mediathek_rows.html` (drei
`views-row`-Blöcke, abgeschnitten, ausschließlich öffentliche Sendemetadaten).
Es findet kein Netzzugriff in der Testsuite statt.

## 6. Offen — fachlich zu entscheiden, nicht technisch

1. **Welcher Titel ist der gültige?** Sendungstitel allein, Sendungstitel + Untertitel,
   oder ein aus dem Teaser abgeleiteter Episodentitel? Das ist eine FRS-Fachfrage und
   entscheidet, wie `title` und `series` belegt werden.
2. **Wie werden Wiederholungen geführt?** Dieselbe URL erscheint zu mehreren Uhrzeiten.
   Vorschlag: `episode` (Sendeplatz) und `broadcast` (Ausstrahlung) getrennt führen
   (entspricht dem Metadatenprofil vom 12.10.2026).
3. **Rechtsstand der Mediathek-Audiodateien.** Der Scraper erfasst nur Verweise
   (`audio_url`), keine Audiodaten. Ob und unter welchen Bedingungen FRS-Mitglieder
   die Dateien sichern dürfen, ist nicht geklärt.
4. **Der historische Snapshot** `data/mediathek.json` (13 Einträge, 19.11.2025) ist
   ungenutzt und nicht reproduzierbar. Aufbewahren, in ein Archiv verschieben oder
   löschen — Entscheidung des Eigentümers.
5. **`assets/data/mediathek.json`** (68 Einträge mit vollständigem Seitentext je Eintrag)
   ist ein unbereinigtes Screen-Scraping-Ergebnis ohne Titelstruktur. Die Flutter-App
   liest es aktuell nicht (`MediathekService` fragt `http://localhost:8000/mediathek`).
   Bereinigen oder entfernen — Eigentümerentscheidung.
6. **`docs/data/mediathek.json`** (2 Platzhalter-Einträge) speist die Portal-Anzeige.
   Aktuell Platzhalter, kein Bestand.

## 7. Nicht behauptet

* Keine Freigabe, keine Abnahme, kein Leistungsnachweis.
* Die Reparatur betrifft **nur** die Testumgebung dieses Repositories.
* Es wurde **nicht** gepusht, **nicht** gemergt, **nicht** in `main` geändert.
* Die 13 Snapshot-Titel sind **abgeleitet, nicht belegt** (Abschnitt 4).
