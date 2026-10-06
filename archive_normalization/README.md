# FRS Archivnormalisierung: Read-only-Prototyp

Status: Vorbereitung, keine abgeschlossene Bestandsaufnahme und keine Produktionsmigration. Keine Aussagen zu Drupal-Version, Archivumfang oder realer Datenqualitaet.

## Umfang

MP3-Dateien lesen, SHA-256 erfassen, ID3 ohne automatische Frame-Uebersetzung auslesen, Titel als Vorschlag normalisieren, ffprobe-Daten und byteidentische Dubletten berichten. Keine Tags schreiben, Dateien umbenennen, Audiodaten encodieren oder Dubletten loeschen. JSON-Ausgabe erfolgt ausschliesslich auf stdout. Rohdateien bleiben massgeblich; diagnostic_frames sind kein verlustfreier ID3-Export.

## Ausfuehrung

Python 3.10+ sowie ffprobe im PATH erforderlich.

```bash
cd archive_normalization
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s . -p 'test_*.py'
python inventory.py /PFAD/ZUM/READ_ONLY_SNAPSHOT > /PFAD/AUSSERHALB/QUELLE/inventory.json
```

Nur einen freigegebenen, technisch schreibgeschuetzten Snapshot scannen. Shell-Umleitung muss ausserhalb des Quellarchivs liegen: Die Shell oeffnet die Ausgabedatei bereits vor dem Programmstart. Keine realen Reports oder Audio-/Personendaten in Git committen. Ignore-Regeln ersetzen keine Datenschutzpruefung.

Exitcode 1 bedeutet Erfassungsfehler oder Qualitaetshinweise. Erfolgreiches ffprobe ist kein vollstaendiger Decode-Test. Symlink-Dateien werden ausgeschlossen; der Prototyp ersetzt keine Sicherheitsisolierung bei parallel veraenderten Verzeichnissen. Tests verwenden synthetische Tag-Dateien, keine gueltigen Audiofixtures. Tests sind hier beschrieben, aber noch nicht durch CI nachgewiesen.

## Zielmodell und naechste Schritte

Inhaltliches Objekt mit persistenter UUID getrennt von Dateirepraesentation modellieren. Jede Datei erhaelt eigene UUID, SHA-256, Herkunft und technische Daten. Ein Hash ist keine dauerhaft stabile Sendungs-ID. Titel, Sendereihe, Beteiligte mit Rollen, Beschreibung, Sprachen, Rechte und getrennte Aufnahme-/Sende-/Veroeffentlichungsereignisse im kanonischen Modell halten. Kandidaten mit Feldherkunft und Konflikten speichern. ID3-TDRC bedeutet Aufnahme, nicht automatisch Ausstrahlung. TALB und TPE1 nur nach Pruefung der lokalen Konvention zuordnen.

Noch zu implementieren: persistenter Katalog, kanonisches JSON-Schema, externe XML/TXT/JPG-/Drupal-Adapter, lokale Fingerprints, freigegebene Staging-Transformationen, vollstaendige Audiotests und CI. Keine automatische Objekt-ID pro Scan erzeugen.

Jetzt vorbereitbar: Schema, Testfixtures, Konfliktregeln und Abnahmekriterien. Erst nach Bestandsaufnahme entscheiden: Pflichtfelder, Quellenprioritaet, ID3-Ausgabeversion und Zielsystem. Nicht ohne Freigabe: Tag-Schreiben, Loeschen, Encoding, externe Uploads und Veroeffentlichung.

## Technische Quellen

- https://mutagen.readthedocs.io/en/latest/user/id3.html
- https://id3.org/id3v2.4.0-frames
- https://ffmpeg.org/ffprobe.html
- https://pbcore.org/elements
- https://acoustid.org/chromaprint
