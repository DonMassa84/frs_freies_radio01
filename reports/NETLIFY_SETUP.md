# Netlify-Veröffentlichung – Archiv-Brücke FRS

**Stand: 10.11.2026.** Die öffentliche Root-Seite https://archiv-bruecke-frs.netlify.app/ ist ohne Anmeldung abrufbar. Nach dem Update des öffentlichen Quellrepositorys am 10.11.2026 wurde der **neue Textstand live** festgestellt: „Stand 10.11.2026“ sowie IHK-Empfangsbestätigung vom 23.10.2026 und fortlaufendes Prüfungsverfahren.

## Veröffentlichungsquelle

- Repository: `DonMassa84/frs_freies_radio01`
- Branch: `main`
- Source: `docs/projektportal/index.html` mit CSS/JS im selben Ordner
- Publish-Ordner laut `netlify.toml`: `docs/projektportal`
- GitHub-Workflow-Datei: `.github/workflows/deploy-netlify.yml` (Netlify-Deployment bei `main`-Änderungen im Portal vorgesehen; benötigt gültige Repository-Secrets)
- Website-Quellcommit 10.11.: `38840e6c9c375a01fcc32d07310c4e40f9083f3d`

**Verifiziert:** Öffentlicher Abruf der Root-Seite mit dem aktualisierten Textstand am 10.11.2026. Damit ist die Veröffentlichung der Textänderungen bestätigt.

**Nicht durch diesen Abruf verifiziert:** genauer Deployment-Auslöser (GitHub-Workflow oder zusätzliche Netlify-Git-Verbindung), Browserinteraktionen, externe Bilder/Streams, Barrierefreiheit, mobile Darstellung und vollständige rechtliche Konformität.

## Inhaltliche Grenzen

Das Portal ist ausschließlich eine **PRE_PROJECT-Vorbereitung** für das IHK-Beratungsgespräch. Die Website darf keine freigegebene Projektphase, erfolgreiche Migration, reale Datenanalyse oder beschlossene Zielarchitektur suggerieren.

- Geplante 70 Stunden: 10 / 14 / 24 / 10 / 12.
- Architekturvarianten: Drupal, AURA-orientiert, plattformneutral – Entscheidung offen.
- Eingangsbestätigung des Projektvorschlags durch IHK am 23.10.2026, laufendes Prüfungsverfahren bestätigt am 03.11.2026.
- Keine Zielvereinbarung oder freigegebener Datenzugang nachgewiesen.

## Nachprüfung nach zukünftigen Änderungen

1. Öffentliche Root-URL (ohne `/projektportal/`) aufrufen.
2. Im HTML/Seiteninhalt richtigen Stand und `PRE_PROJECT` prüfen.
3. CSS, JavaScript, Menüs und mobile Darstellung interaktiv testen.
4. Keine privaten IHK-/FRS-Daten in öffentlicher Quelle veröffentlichen.
5. GitHub-Deploy-Workflow und Netlify-Protokolle kontrollieren, wenn weitere Updates nicht erscheinen.

Siehe auch [Portal-Synchronisation vom 10.11.2026](PORTAL_SYNC_2026-11-10.md).
