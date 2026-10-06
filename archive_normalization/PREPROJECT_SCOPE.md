# PRE_PROJECT: synthetischer Pilotkern

Keine IHK-Freigabe, keine Realdatenmigration, keine abschliessende Plattformentscheidung. SQLite ist eine austauschbare Testimplementierung.

## Start

```bash
cd archive_normalization
python -m unittest discover -s . -p 'test_pilot.py'
python pilot.py /extern/inventory.json --catalog /extern/catalog.sqlite > /extern/export.json
```

Nur synthetische oder separat freigegebene Inputs verwenden. Katalog und Export ausserhalb des Quellarchivs halten. Der Pilot liest keine Audiodateien und schreibt keine Tags. Er schreibt ausschliesslich den explizit angegebenen SQLite-Katalog; stdout-Umleitung liegt in Verantwortung des Aufrufers. Pfadpruefung garantiert keine Trennung vom Quellarchiv. Keine echten Kataloge/Reports committen. Gleiche Quellenpfade aus unterschiedlichen Bestaenden vorab mit eindeutigen Namensraeumen versehen.

## Regeln

Datei-ID einmalig als UUID vergeben; Quelle ist vorlaeufig source_path. Gleicher Pfad und SHA-256 behalten die ID, auch nach erneutem Oeffnen der Datenbank. Geaenderter Hash am selben Pfad wird abgelehnt, nicht ersetzt. Unterschiedliche Pfade mit identischen Bytes behalten getrennte IDs und werden als Dublettenkandidaten gemeldet. Fehlender Titel ist eine Warnung, kein Erfassungshindernis. Rohwerte bleiben im Export erhalten, Rechte bleiben unknown.

## Grenzen

Kein vollstaendiges kanonisches Archivschema: Episode/Sendereihe, Referenzintegritaet, stabile quellsystemuebergreifende IDs, Ereignisse, Audit-Historie, Versionierung und Formatadapter folgen separat. Eingabepruefungen sind handgeschriebene Pilotregeln, keine JSON-Schema-Validierung. SHA-256 wird aus dem Inventar uebernommen, nicht erneut am Audio verifiziert. Bestehende quality_issues bleiben in raw_record, sind noch keine Freigaberegel. Keine Veroeffentlichungs- oder Migrationsfreigabe durch successful Import. Warnungen verursachen keinen Fehler-Exitcode; Rejects schon. Export ist bei gleichem Input und erhaltenem Katalog reproduzierbar. Katalog sichern: sein Verlust fuehrt zu neuen UUIDs.

## Nachweis

Sieben synthetische Unit-Tests in isolierter Python-Umgebung erfolgreich vor Commit; noch kein GitHub-Actions-Nachweis. Vorbereitungsnachweise ersetzen weder FRS-Abnahme noch IHK-Freigabe. Mediathek-Adapter ist nicht Teil dieses Pakets.
