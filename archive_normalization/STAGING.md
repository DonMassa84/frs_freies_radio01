# Staging-Kopien mit Archiv-ID (`staging.py`)

Status: **PRE_PROJECT – technischer Prototyp**. Nur mit synthetischen MP3s getestet.
Keine IHK-Freigabe, keine FRS-Abnahme, keine freigegebene Realdatenmigration.

## Zweck

Echte Kopien freigegebener MP3s erzeugen und darin genau ein Tag ergänzen:

| Tag | Wert |
|---|---|
| `TXXX:FRS_ARCHIVE_SOURCE_FILE_ID` | Katalog-UUID der **Originaldatei** (aus `pilot.py`, Tabelle `assets`) |

Die Kopie erhält zusätzlich eine eigene UUID in der Tabelle `derived_copies`
(`relation = derived_from`). Originale werden ausschließlich gelesen.

## Ablauf

```bash
# 0. Voraussetzung: Inventar + Katalog
python inventory.py /QUELLE > /ARBEIT/inventory.json
python pilot.py /ARBEIT/inventory.json --catalog /ARBEIT/catalog.sqlite > /ARBEIT/pilot.json

# 1. Dry-run: schreibt nur die Plandatei, gibt deren SHA-256 aus
cp sources.example.json /ARBEIT/sources.json   # Pfade eintragen
python staging.py plan --config /ARBEIT/sources.json \
  --catalog /ARBEIT/catalog.sqlite --out /ARBEIT/plan.json

# 2. Plan prüfen und freigeben, dann ausführen (an den Plan-Hash gebunden)
python staging.py apply --plan /ARBEIT/plan.json --plan-sha256 <HASH> --out /ARBEIT/apply.json

# 3. Validieren
python staging.py validate --plan /ARBEIT/plan.json --out /ARBEIT/report.json
```

Ausgabedateien werden nie überschrieben (`--out` muss neu sein).
Der Quellpfad in der Konfiguration muss derselbe Ordner sein, der für `inventory.py` verwendet wurde,
damit die Katalogeinträge über den absoluten Pfad gefunden werden.

## Aktionen im Plan

| Aktion | Bedeutung |
|---|---|
| `copy_and_tag` | Kopie erstellen, TXXX ergänzen |
| `copy_only` | TXXX enthält bereits die richtige UUID; reine Kopie |
| `conflict` | TXXX enthält einen fremden Wert – nichts tun |
| `unsupported_id3` | kein/defektes ID3v2, Version ≠ 2.3/2.4 oder ID3v1-Extended – manuelle Entscheidung |
| `not_cataloged` | Datei fehlt im Katalog – zuerst `pilot.py` |
| `reject` | Inhalt weicht vom Katalog-Hash ab (`SOURCE_CONTENT_CHANGED`) |
| `target_exists` | Zieldatei existiert – wird nie überschrieben |

## Schutzmechanismen

- Ziel darf weder in einer Quelle liegen noch eine Quelle enthalten, Quellen dürfen nicht verschachtelt sein, Ziel nicht im Git-Repository.
- Symlinks werden nicht verfolgt; Kopien sind echte Byte-Kopien (`copyfileobj` + `fsync`).
- `apply` nur mit exakt passendem Plan-SHA-256; Original-Hash und Katalog werden je Datei erneut geprüft.
- Kopie zuerst als temporäre Datei im Zielordner, Byteidentität prüfen, dann Tag schreiben,
  dann per `os.link` unter dem Zielnamen veröffentlichen (schlägt fehl, wenn der Name existiert) und Temp-Datei entfernen.
- ID3v2-Version bleibt erhalten (`v2_version` = Originalversion), Laden mit `translate=False`.
- Vorhandenes ID3v1 wird als Rohblock (128 Byte) unverändert wieder angehängt.
- Speicherprüfung: Kopiervolumen × (1 + `reserve_ratio`) + 1 MiB.
- Exklusive Sperre `.frs-staging.lock` im Ziel: nur ein `apply` gleichzeitig. SQLite nur lokal verwenden, nicht über Netzwerkfreigaben.
- Wiederanlauf: bereits erzeugte, unveränderte Kopien → `already_done`; abweichende → `needs_review`.

## Validierung

Je Kopie: TXXX-Wert, alle übrigen Frames (inkl. Bilddaten, per Hash), ID3v2-Version, ID3v1-Rohblock,
vollständiger Decode beider Dateien (`ffmpeg -xerror`, PCM float32, MD5) und Vergleich der Audio-Hashes,
Original-SHA-256. Jede Decoder-Meldung auf stderr gilt als Prüfbefund (`DECODE_MESSAGES`).
Fehlgeschlagene Kopien werden als `failed` markiert; nichts wird automatisch repariert.

## Bekannte Grenzen

- Nur das eine Tag-Profil `frs-source-id-v1`; Titel, Datum, Rechte werden nicht in Tags geschrieben.
- Frame-Vergleich über `repr()` der Mutagen-Frames – semantisch, nicht byte-genau.
- APEv2-Tags und andere Anhänge werden nicht gesondert geprüft (Audio-Hash und ID3v1-Vergleich decken nur Teile ab).
- Plan enthält absolute Pfade – Plan, Katalog und Berichte **nicht** ins Repository übernehmen.
- Kein Mehrrechnerbetrieb: ein Katalog-Schreiber, sequenziell auf einem Rechner.
- Getestet mit Python 3.12 / Mutagen 1.47.0 / FFmpeg 8.0.1 an synthetischen Dateien; FFmpeg 7.0.2 auf dem Ryzen noch nicht geprüft.

## Tests

```bash
python -m unittest -v test_inventory test_pilot test_staging test_integration_ffmpeg
```

`test_staging.py` und `test_integration_ffmpeg.py` werden übersprungen, wenn `ffmpeg`/`ffprobe` fehlen.

## Kompletter Stichproben-Lauf (`run_sample_pipeline.py`)

Verkettet Inventur, Katalog, Plan und optional apply/validate für eine feste
Stichprobendatei (ein absoluter MP3-Pfad pro Zeile, `#`-Kommentare erlaubt).
Es werden nur die gelisteten Dateien erfasst — nicht das gesamte Quellverzeichnis.

```bash
# Dry-run (Standard): schreibt nur Berichte + Plan, kopiert nichts
python run_sample_pipeline.py --sample-list stichprobe_01.txt \
  --workdir /ARBEIT/pipeline --target /ARBEIT/staging \
  --expect-commit <VOLLSTÄNDIGER-COMMIT> --run-id dry01

# Nach Freigabe des Plans (neue run-id, Dateien werden nie überschrieben):
python run_sample_pipeline.py --sample-list stichprobe_01.txt \
  --workdir /ARBEIT/pipeline --target /ARBEIT/staging \
  --expect-commit <VOLLSTÄNDIGER-COMMIT> --run-id run01 --apply
```

Der Plan wird automatisch auf die Stichprobe gefiltert; `apply` ist an den
Plan-Hash gebunden. Erwartetes Ergebnis in `report_<run-id>.json`:
`validated` = Anzahl der Stichprobe, `failed` = 0, `originals_unchanged` = true.
Die Stichprobendatei enthält reale Pfade und gehört nicht ins Repository.

## Kompletter Stichproben-Lauf (`run_sample_pipeline.py`)

Verkettet Inventur, Katalog, Plan und optional apply/validate für eine feste
Stichprobendatei (ein absoluter MP3-Pfad pro Zeile, `#`-Kommentare erlaubt).
Es werden nur die gelisteten Dateien erfasst — nicht das gesamte Quellverzeichnis.
Basiert auf `staging.py` (plan/apply/validate), nicht auf `staging_writer.py`.

```bash
# Dry-run (Standard): schreibt nur Berichte + Plan, kopiert nichts
python run_sample_pipeline.py --sample-list stichprobe_01.txt \
  --workdir /ARBEIT/pipeline --target /ARBEIT/staging \
  --expect-commit <VOLLSTÄNDIGER-COMMIT> --run-id dry01

# Nach Freigabe des Plans (neue run-id, Dateien werden nie überschrieben):
python run_sample_pipeline.py --sample-list stichprobe_01.txt \
  --workdir /ARBEIT/pipeline --target /ARBEIT/staging \
  --expect-commit <VOLLSTÄNDIGER-COMMIT> --run-id run01 --apply
```

Der Plan wird automatisch auf die Stichprobe gefiltert; `apply` ist an den
Plan-Hash gebunden. Erwartetes Ergebnis in `report_<run-id>.json`:
`validated` = Anzahl der Stichprobe, `failed` = 0, `originals_unchanged` = true.
Die Stichprobendatei enthält reale Pfade und gehört nicht ins Repository.
