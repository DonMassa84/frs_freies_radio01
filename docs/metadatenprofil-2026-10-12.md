# Metadaten- und ID-Profil (Entwurf)

**Stand:** 12.10.2026 · **Status:** PRE_PROJECT · **Kein FRS-Bestandsschema, keine Festlegung auf Drupal/AURA/eigenen Dienst.**

## Ausgangspunkt

Langfristig verbinden Sendereihe, Episode und Dateien nicht gemeinsame Dateinamen, sondern getrennte, stabile **Identitäten** und ausdrücklich gespeicherte Beziehungen:

```text
Sendereihe [Reihen-ID]
  └─ Episode [Episoden-ID] → gehört zur Sendereihe
       ├─ Audio [Datei-ID] → repräsentiert die Episode
       ├─ Bild [Datei-ID]  → illustriert die Episode
       └─ Text [Datei-ID]  → beschreibt / transkribiert die Episode

Ausstrahlung [Ereignis-ID] → verweist auf die Episode
Bearbeitete Datei [neue Datei-ID] → wurde abgeleitet aus [Original-Datei-ID]
```

Grundlage: EBUCore beschreibt Reihen, Episoden, Teilbeziehungen und unterschiedliche mediale Ausprägungen; PREMIS trennt geistige Inhalte, Repräsentationen, Dateien sowie Erhaltungsereignisse und verknüpft sie über Identifikatoren.

## Vorgeschlagenes Mindestprofil

Nicht jedes Feld ist in jedem Standard verpflichtend; die konkrete Pflichtfeldliste muss FRS fachlich bestätigen.

| Ebene | Vorgeschlagene Metadaten | Verbindung und Begründung |
|---|---|---|
| Sendereihe | `series_id`, Haupttitel, alternative/frühere Titel, Beschreibung, verantwortliche Redaktion bzw. Beteiligte mit Rollen | Episode verweist auf Reihen-ID, nicht auf wechselnden Titel. EBUCore unterstützt Gruppen und Beziehungen wie `isEpisodeOf`. |
| Episode | `episode_id`, `series_id`, Titel, Beschreibung, Sprache, Themen/Genre, Beteiligte mit Rollen, ggf. belegte Episodennummer | Inhaltliche Identität getrennt von Dateiformat und Speicherort. EBUCore unterscheidet redaktionelle Objekte und deren Ausprägungen. |
| Ausstrahlung | `broadcast_id`, `episode_id`, Beginn, Ende, Zeitzone/UTC-Offset, Sender/Kanal, Status „geplant“/„tatsächlich“ | Wiederholungen als zusätzliche Ausstrahlungsereignisse derselben Episode. |
| Datei | `file_id`, Medientyp, MIME-Typ, Dateigröße, ursprünglicher Dateiname, aktuelle Speicherorte, Prüfsummenalgorithmus und Prüfsumme | PREMIS trennt Objektidentifikator und Integrität. Speicherort ist veränderbare Adresse, nicht Identität. |
| Technische Details | Audio: Dauer, Codec, Abtastrate, Kanäle; Bild: Format/Abmessungen; Text: Format, Sprache, ggf. Zeichencodierung | EBUCore technische/strukturelle Metadaten; im Pilot nur für gewählte Formate konkretisieren. |
| Beziehungen | Quell-ID, Beziehungstyp, Ziel-ID, ggf. Reihenfolge/Zeitbereich | „Audiofassung“, „Episodenbild“, „Reihenlogo“, „Transkript“, „Sendungsbeschreibung“ typisiert; EBUCore/PREMIS als Grundlage. |
| Rechte und Herkunft | Rechteinhaber, Nutzungs-/Veröffentlichungsbedingungen, Gültigkeitszeitraum, Nachweisquelle; Metadatenquelle, Erfassungszeit, Bearbeiter/Software, Prüfstatus | EBUCore Rechte; PREMIS Rechte, Ereignisse, Agenten. Feldgenaue Herkunftsführung als Pilotanforderung. |
| Versionsstand Episode (Ergänzung) | `episode_version_id`, Versionsnummer, Änderungsdatum, Zusammenfassung, Bezug zur Vorgängerversion | Auch redaktionelle Inhalte versionieren (Textkorrekturen, neue Fassung); Datei allein reicht nicht. PREMIS-Beziehungen. |
| Person/Rolle (Ergänzung) | `person_id` (pseudonymisierbar), Rolle, Zeitraum der Beteiligung | Personen nicht inline in Episode/Reihe; wiederverwendbar, DSGVO-konform (siehe unten). |

## IDs und Integrität

- Jede Reihe, Episode und archivierte Dateiversion erhält eine eigene UUID (`urn:uuid:…`, RFC 9562). Einmal vergebene IDs bleiben bei Export/Reimport erhalten.
- Vorhandene Drupal-/AURA-/andere Quell-IDs werden zusätzlich mit Quellsystem und Namensraum gespeichert (PREMIS: Geltungsbereich eines Identifikators kennen).
- Prüfsumme (z. B. SHA-256) wird separat gespeichert: „Sind diese Bytes unverändert?“ ≠ „Zu welcher Sendereihe gehört dieser Inhalt?“
- Veränderte Datei = neue Dateiversion mit eigener ID, Prüfsumme und Ableitungsbeziehung; Episoden-ID bleibt, solange derselbe redaktionelle Inhalt gemeint ist.
- UUID allein ist kein dauerhaft erreichbarer Katalogeintrag. Langfristigkeit braucht Vergabe-, Erhaltungs- und Zuordnungspolitik. HTTPS-Resolver als mögliche Ergänzung; Betreiber/Domain/Weiterleitung offen.

## Mindest-Event-Set (PREMIS-orientiert, Ergänzung)

Für Nachvollziehbarkeit im Pilot mindestens:

| Event | Trigger | Pflichtfelder |
|---|---|---|
| Ingest | Datei nimmt Archiv auf | Datei-ID, Quelle, Zeitstempel, Prüfsumme (Algorithmus + Wert), ausführende Software/Person |
| Fixity-Check | Periodisch oder bei Zugriff | Datei-ID, Zeitstempel, Ergebnis (OK/FAIL), erwartete und tatsächliche Prüfsumme |
| Metadaten-Update | Feldwert geändert | Datensatz-ID, Feld, alter/neuer Wert (oder Differenz), Zeitstempel, Agent, Begründung |
| Ableitung | Neue Dateiversion | Ursprungs-Datei-ID, neue Datei-ID, Zeitstempel, Tool/Prozess |

## Export und Austausch (Ergänzung)

- **Vorschlag:** JSON Lines oder JSON-LD als neutraler Austausch; XML-Export optional (EBUCore/PREMIS-nah).
- Jeder Export enthält: Schemaversion, Exportzeit, Quellsystem, vollständige IDs, Beziehungen, Prüfsummen.
- Reimport muss IDs erhalten; Reimport in leeres System muss Relationen wiederherstellbar machen.

## DSGVO / Datenschutz (Ergänzung)

- „Beteiligte mit Rollen“ sind personenbezogene Daten: Einwilligung oder öffentlich-rechtliche Aufgabe prüfen, Löschfristen/Nachweispflichten klären.
- Unterscheidung: öffentlich angezeigte Metadaten (Name, Rolle) vs. interne Audit-Logik (Agent, Bearbeiter).
- Pseudonymisierte `person_id` für interne Verknüpfung vorsehen; Realname nur bei berechtigtem Interesse und Dokumentation.

## Variantenvergleich (unverändert, knapp)

| Variante | Belegte Grundlage | Eignung für Pilot (Schlussfolgerung) | Vor Entscheidung zu prüfen |
|---|---|---|---|
| Drupal-Erweiterung | Entity-UUIDs, Media, JSON:API | Geeignet, wenn CMS-Pflege und Redaktion im bestehenden System bestätigt sind | Version/Module, Export ohne neue IDs, Berechtigungen |
| AURA-orientiert | Steering/Tank/Engine, API-Dokumentation | Geeignet, wenn Programmplanung und Systemaustausch Ziele sind; Playout-Umfang für reinen Archivpilot ggf. zu groß | API-Schemata, ID-Lebensdauer, Bild/Text |
| Plattformneutraler Dienst | EBUCore/PREMIS technologieneutral | Geeignet für Identität/Beziehungen/Prüfsummen unabhängig von Plattform; ersetzt keine Redaktionsoberfläche | Betrieb, Schema-Versionierung, Adapter, Resolver-Politik |

**Vorläufige Empfehlung:** Zuerst gemeinsames Metadatenprofil und identische synthetische Prüffälle; danach drei Varianten gegen dieselbe Kriterienliste bewerten. Neutrales Austauschschema als Vergleichsinstrument, nicht als vorgezogene Entscheidung für eigenen Dienst.

## Offene Fragen (unverändert)

### Fachlich / organisatorisch

1. Was gilt als Episode: redaktioneller Beitrag, komplette Sendung oder Sendeabschnitt?
2. Kann eine Episode mehreren Reihen zugeordnet sein? Wiederholungen vs. überarbeitete Fassungen?
3. Welche vorhandenen IDs existieren, in welchem System werden sie verbindlich vergeben?
4. Welche Bilder/Texte gehören zur Reihe, welche zur Episode? Gemeinsam genutzte Dateien?
5. Welche Rechte erlauben interne Aufbewahrung, Nachhören und öffentliche Metadatenanzeige getrennt?
6. Wer verantwortet Metadatenkorrekturen, ID-Vergabe, Speicherorte, ggf. Resolver?
7. Welche Ergebnisse müssen IHK-Zielvereinbarung und FRS-Abnahme verlangen?

### Nächste Prüfschritte (PRE_PROJECT)

1. Ziel- und Freigabegrenzen dokumentieren (Pilotziel, erlaubte Daten, Schreibzugriffe, Veröffentlichung, Abnahme getrennt). Bis Freigabe synthetische Daten.
2. Metadatenprofil: Feldbedeutung, Datentyp, Pflichtstatus, Mehrfachwerte, Herkunft, Standard-Mapping. Unbelegte Angaben als unbekannt/ungeprüft.
3. ID-Politik: Vergabe, Namensraum, Unveränderlichkeit, Quell-ID-Mapping, Versionsbildung, Systemwechsel.
4. Kleinen synthetischen Testbestand: 1 Reihe, mehrere Episoden, 1 Wiederholung, 1 gemeinsames Bild, 1 Transkript, 1 abgeleitete Audiofassung.
5. Gleiche Prüfungen für alle Varianten: Beziehungen vollständig auflösbar; IDs nach Export/Reimport unverändert; Umbenennen/Verschieben ändert Identität nicht; Dateiveränderung per Prüfsumme erkennbar; Ableitungen nachvollziehbar.
6. Erst nach Freigabe reale Stichprobe; Mapping-Lücken dokumentieren; Migration als eigener freizugebender Schritt.

## Quellen (Abruf 12.10.2026)

| Quelle | Datum/Stand | Relevanz/Grenze |
|---|---|---|
| [EBU Tech 3293 – EBUCore](https://tech.ebu.ch/docs/tech/tech3293.pdf) | v1.10, April 2020 | Reihen/Episoden/Ausprägungen; kein FRS-Schema |
| [PREMIS 3.0 Data Dictionary](https://www.loc.gov/standards/premis/v3/premis-3-0-final.pdf) | Juni/Nov 2015 | Identifikatoren, Beziehungen, Integrität, Events, Rechte |
| [RFC 9562 – UUIDs](https://www.rfc-editor.org/info/rfc9562/) | Mai 2024 | UUID-Format/URN; ersetzt RFC 4122 |
| [Drupal JSON:API](https://api.drupal.org/api/drupal/core!modules!jsonapi!jsonapi.api.php/group/jsonapi_architecture/11.x), [Media Entity](https://api.drupal.org/api/drupal/core!modules!media!src!Entity!Media.php/class/Media/11.x) | 11.x-Doku | Entity-UUIDs; kein Nachweis über FRS-Installation |
| [AURA Overview](https://docs.aura.radio/en/1.0.0-alpha3/administration/overview-and-features.html), [API](https://docs.aura.radio/en/latest/developer/api/index.html) | alpha3 | Steering/Tank/Engine; PID-Politik nicht belegt |

**Hinweis:** EBUCore 1.10 und PREMIS 3.0 sind ältere Fassungen; neuere Errata/Versionen vor Einreichung prüfen. RFC 9562 abwärtskompatibel zu RFC 4122-UUIDs.
