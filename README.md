# FRS Archiv-Brücke – öffentliches Projektportal

**Öffentliche Webseite:** https://archiv-bruecke-frs.netlify.app/

**Stand:** 10.11.2026 · **Status:** `PRE_PROJECT` – Planungs- und Beratungsmaterial, **keine abgeschlossene Projektleistung**.

## Zweck

Das Portal dient als öffentliches Anschauungs- und Orientierungsmaterial für das geplante IHK-Projekt „Plattformunabhängiges Sendungsarchiv beim Freien Radio Stuttgart“. Es visualisiert vorläufige Anforderungen, Metadatenbeziehungen, drei offene Lösungsalternativen, einen **70-Stunden-Plan** sowie Risiken und Qualitätsvorgaben.

Das Portal ist **keine offizielle Webseite des Freien Radios**, kein funktionsfähiger FRS-Archivdienst und kein Nachweis einer IHK-Freigabe, Migration, fachlichen Abnahme oder realen Datenbestandsaufnahme.

## Öffentlicher Webseiten-Code

- Quelldateien: `docs/projektportal/`
- Einstieg: `docs/projektportal/index.html`
- Deploymentverzeichnis: `docs/projektportal` laut [netlify.toml](netlify.toml)
- GitHub-Workflow: [deploy-netlify.yml](.github/workflows/deploy-netlify.yml)
- Dokumentierte Veröffentlichungsprüfung: [NETLIFY_SETUP.md](reports/NETLIFY_SETUP.md)
- Kommunikationsupdate 10.11.2026: [PORTAL_SYNC_2026-11-10.md](reports/PORTAL_SYNC_2026-11-10.md)

Das **private** IHK-Projektrepository lautet `DonMassa84/ihk-projektarbeit-frs-archiv`. Es enthält interne Projektplanung und Nachweise; die hier öffentliche Website ist hiervon getrennt.

## Projektstatus und Grenzen

- `PRE_PROJECT`: formale IHK-Zielvereinbarung und Projektfreigabe nicht nachgewiesen.
- Die 70 Stunden (`10 + 14 + 24 + 10 + 12`) sind **Planwerte**, keine Ist-Stunden.
- Keine technische Vorentscheidung zwischen Drupal-Erweiterung, AURA-orientierter Integration und plattformneutralem Archivdienst.
- Keine reale Testmigration oder verifizierten Produktivzugriffe.
- Verbindliche Ansprechpartner, Datenfreigaben, Ist-Daten und Abnahmekriterien stehen noch zur Klärung.

## Historischer Quellbestand

Das Repository enthält neben dem Projektportal auch ältere Flutter-Dateien. Der ursprüngliche generische Flutter-README beschrieb lediglich das Framework-Startprojekt und ist für die öffentlich bereitgestellte Archiv-Brücke nicht die maßgebliche Projektbeschreibung.

## Datenschutz und Rechte

Die öffentliche Seite enthält Impressums- und Datenschutzhinweise, deren Vollständigkeit rechtlich nicht abschließend geprüft wurde. Keine privaten Prüfungsunterlagen, E-Mails, Zugangsdaten oder realen FRS-Bestandsdaten auf der Website veröffentlichen.
