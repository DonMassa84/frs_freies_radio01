# Staging-Schreibmodul (staging_writer.py)

Schreibt kontrolliert ID3-Tags an Staging-Kopien von Dateien, die der
Pilotkatalog bereits erfasst hat. Originale werden ausschliesslich gelesen.

## Umfang

- Dry-run ist Standard: Ohne --apply wird nur ein Plan ausgegeben, keine Datei verändert.
- Eine einzige Tagschreibung: TXXX:FRS_ARCHIVE_SOURCE_FILE_ID mit der UUID der katalogisierten Originaldatei.
- Echte Kopien (keine Hardlinks/Symlinks), keine Überschreibung bestehender Zieldateien.
- Plan ist an den SHA-256 des Originals gebunden; Abweichung blockiert die Ausführung.
- Nur MP3 mit ID3v2.3 oder ID3v2.4; andere Stände werden zur manuellen Entscheidung zurückgestellt.
- Ein vorhandenes fremdes ID-Marker-Feld ist ein Konflikt (FOREIGN_ID_MARKER), kein Überschreiben.
- Fehlgeschlagene Schreibvorgänge löschen die angefangene Kopie und werden als failed gemeldet.

## Verwendung

```bash
python staging_writer.py export.json /pfad/zum/staging            # Dry-run: Plan anzeigen
python staging_writer.py export.json /pfad/zum/staging --apply    # freigegebenen Plan ausführen
python -m unittest discover -s . -p 'test_staging_writer.py' -v
```

Eingabe ist der Pilot-Export (accepted-Liste). Das Staging-Verzeichnis muss
existieren und darf weder Quelle sein noch die Quelle enthalten. Zieldateiname
ist <source_file_id>.mp3; daraus folgt, dass eine Quelldatei nicht in denselben
Staging-Ordner geschrieben werden kann.

## Keine Automatik für

Titel, Autoren, Sendereihe, Datum, Lizenz und Bilder bleiben in dieser Stufe
unverändert. Ihre Übernahme braucht freigegebene Quellenwerte und ein eigenes
Mapping-Profil.

## Grenzen

- getestet nur mit synthetischen ID3-Dateien; ein echter Audio-Integrationstest
  (ffprobe + kompletter Decode der Kopie) ist noch auszuführen, bevor reale
  Dateien bearbeitet werden.
- Nach dem Schreiben wird audioinhaltliche Gleichheit derzeit nicht innerhalb
  des Moduls geprüft; dies ist Aufgabe der Validierungsphase.
- Gleicher ID3-Inhalt mit gleicher Version kann beim Speichern Frames
  normalisieren (z. B. Padding). Das Modul prüft deshalb Version und Rücklesbarkeit
  des Markers, vergleicht aber noch nicht jeden Einzelframe semantisch.
