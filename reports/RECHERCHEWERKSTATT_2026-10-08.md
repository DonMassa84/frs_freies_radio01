# Recherchewerkstatt für das FRS-Projektportal

## Umfang

Die bestehende statische Website erhält unter `#recherche` eine Recherchevorbereitung mit vier Themen: Metadaten/IDs, Lösungsalternativen, Pilotmigration und Rechte/Datenschutz. Eine eigene Frage ergänzt den öffentlichen PRE_PROJECT-Kontext. Der Auftrag lässt sich kopieren oder durch einen bewussten Klick an Perplexity übergeben. Falls die Such-URL nicht übernommen wird, kann der Auftrag manuell eingefügt werden.

Dies ist keine Einbettung aller Perplexity-Pro-Funktionen und kein KI-Backend. Antworten entstehen im eigenen Perplexity-Konto. Modelle, Research-Modi und Kontolimits werden dort gewählt. Keine API-Schlüssel, API-Abrechnung oder automatisch gestarteten KI-Anfragen.

## Quellen

Titel, HTTP(S)-Adresse ohne Zugangsdaten, Erfassungs-/Prüfdatum, eigener Prüfstatus und Notiz werden im localStorage des aktuellen Browsers gespeichert. Maximal 100 Quellen; Titel 160 und Notizen 2000 Zeichen. Lokale Liste, Entfernen und JSON-Export. Kein Upload, keine Zusammenarbeit oder Synchronisierung zwischen Browsern/Domains. Der Export ist eine Sicherung zur Weiterverarbeitung, kein geprüfter Projektnachweis. Es gibt in dieser Version keinen JSON-Import.

Ungültige und ausführbare URLs werden abgewiesen. Nutzereingaben werden als Text dargestellt. Blockierter Speicher führt zu einer Fehlermeldung; eine beschädigte Liste wird nicht automatisch überschrieben. Lokale Browserdaten können verloren gehen: wichtige Ergebnisse exportieren.

## Projektgrenzen

PRE_PROJECT bleibt erhalten, Freigabe und Zielvereinbarung offen. Öffentliche Recherche ist Vorbereitung und wird nicht als Prüfungsprojektzeit oder Testmigration ausgegeben. Keine privaten Prüfungsunterlagen, Unterschriften, Zahlungsdaten oder Zugangsdaten veröffentlichen bzw. in Recherchefragen eingeben.

## Dateien

- `docs/projektportal/index.html`: Navigation und Recherchebereich.
- `docs/projektportal/research.css`: responsive Darstellung in bestehender Farbpalette.
- `docs/projektportal/research.js`: Rechercheauftrag, Validierung, Browserliste, Export.
- `tests/research.test.cjs`, `tests/package.json`: ausführbare DOM-Funktionstests.

## Verifikation

Node 24, jsdom 30.1.2: fünf DOM-Funktionstests bestanden. Frage einschließlich Sonderzeichen/Projektstatus, Wiederherstellung/Export/Löschen, sichere URL-Protokolle und Textausgabe, blockierter Speicher, Schutz beschädigter gespeicherter Daten. JavaScript-Syntaxprüfung bestanden.

Reproduktion: `cd tests && npm install --ignore-scripts && npm test` (Node >=22). Die Tests laufen ohne externe Rechercheanfragen. Kein echter Browser-Layouttest: die Chromium-Bereitstellung war in der Arbeitsumgebung nicht möglich.

## Veröffentlichung

GitHub Pages verarbeitet Änderungen unter `docs/**` bereits. Netlify-Publish-Verzeichnis bleibt `docs/projektportal`. Änderungen müssen aus diesem Repository/Branch auf der vorhandenen Netlify-Seite veröffentlicht werden; automatische Git-Anbindung und tatsächlich sichtbare Version nach dem Commit überprüfen. Keine vorhandene PWA überschreiben.

## Öffentlich geprüfter Stand

Implementierungscommit: `7ff5cdac5e76ba7739f0272fbd2fd865f753f724`. GitHub-Pages-Workflow `37800938078` erfolgreich. Öffentliches HTML, `research.js` und `research.css` liefern HTTP 200 und stimmen mit den Repository-Dateien überein:

https://donmassa84.github.io/frs_freies_radio01/projektportal/#recherche

Netlify lieferte bei der Prüfung nach dem Commit weiterhin die alte HTML-Fassung; `research.js` und `research.css` lieferten HTTP 404. Die automatische Übernahme des GitHub-Standes ist daher nicht belegt. Ohne Zugriff auf die Netlify-Projektkonfiguration kann die genaue Einstellung (Git-Verbindung, gestoppte Builds oder ausstehender manueller Deploy) nicht bestimmt werden.

Für die vorhandene Seite `archiv-bruecke-frs` die Repository-Einstellung unter Project configuration / Developer settings / Continuous deployment prüfen. Quelle: `DonMassa84/frs_freies_radio01`, Branch `main`, Publish directory `docs/projektportal`, Build command leer. Falls die Verbindung schon korrekt ist, den aktuellen Branch-Stand erneut deployen. Keine neue Website oder Repository anlegen. Öffentlich prüfen, bevor Netlify als aktualisiert gemeldet wird.

Zugriffsblocker: Die TinyFish-Verbindung liefert weiterhin nur `prof_b4e9534f542644b0` ohne gespeicherte Netlify-Anmeldung; die in der Nutzeroberfläche gespeicherte Sitzung eines anderen Profils ist nicht verfügbar. Es wurden keine Zugangsdaten abgefragt und keine kostenpflichtigen API-Anfragen eingerichtet.
