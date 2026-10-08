# Netlify-Veröffentlichung

Status 08.10.2026: Die bestehende Website ist unter https://archiv-bruecke-frs.netlify.app/ öffentlich erreichbar. Der zunächst beobachtete HTTP-401-Zugriffsschutz war bei der erneuten Prüfung nicht mehr vorhanden. Portalinhalt, CSS und JavaScript waren abrufbar. Änderungen im GitHub-Repository müssen zusätzlich auf dieser vorhandenen Netlify-Seite veröffentlicht werden; die automatische Git-Anbindung ist noch zu verifizieren.

## Ziel

Kostenloser Free-Tarif. Projektname: ArchivBrücke FRS. Öffentliche Adresse: https://archiv-bruecke-frs.netlify.app/. Keine neue Seite anlegen; vorhandene Seite verwenden.

## Git-Verbindung

Repository DonMassa84/frs_freies_radio01, Branch main. netlify.toml veröffentlicht ausschließlich docs/projektportal. Kein Build-Befehl erforderlich: HTML, CSS und JavaScript liegen fertig vor. Private IHK-Dateien sind nicht Teil dieses Verzeichnisses.

## Einrichtung

Bei Netlify anmelden, gegebenenfalls Google-Anmeldung verwenden. Neues Projekt aus GitHub importieren und ausschließlich dieses Repository freigeben. Free-Tarif wählen, keine kostenpflichtigen Optionen oder automatische Aufladung aktivieren. Publish directory docs/projektportal; Build command leer. Die vorhandene Seite archiv-bruecke-frs weiterverwenden. Falls noch keine Git-Verbindung besteht, diese Seite mit dem Repository/Branch verbinden. Kein Pro-Abo oder kostenpflichtige Funktionen aktivieren.

## Abnahme

Öffentlicher Aufruf ohne Anmeldung; Projektportal direkt am URL-Einstieg; CSS/JS und FRS-Logo laden; Stream erst nach Nutzereingabe; Stand 07.10.2026, PRE_PROJECT und Beratung 10.11.2026 vorhanden. Erst danach den neuen Link weitergeben. Bestehende GitHub-Pages-Veröffentlichung bleibt erhalten.

