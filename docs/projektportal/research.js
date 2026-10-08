(() => {
  'use strict';
  const section = document.getElementById('recherche');
  if (!section) return;
  const get = id => document.getElementById(id);
  const key = 'frs-research-v1';
  const topics = {
    metadata: 'Welche Metadaten und persistenten IDs verbinden Sendereihe, Episode und Audio-, Bild- und Textdateien langfristig?',
    alternatives: 'Vergleiche Drupal-Erweiterung, AURA-orientierte Architektur und einen plattformneutralen Archivdienst für freie Radios.',
    migration: 'Wie lässt sich eine Testmigration mit Prüfsummen, Pflichtfeldern, Reject-Protokollen und wiederholbarem Import prüfen?',
    rights: 'Welche Fragen zu Nutzungsrechten und Datenschutz müssen für ein öffentliches Radioarchiv geklärt werden?'
  };
  function message(text) { get('research-status').textContent = text; }
  function prepare() {
    const question = get('research-question').value.trim() || topics[get('research-topic').value];
    const prompt = `Recherchiere auf Deutsch für die Vorbereitung eines Archiv- und Metadatenprojekts beim Freien Radio Stuttgart (FRS).\n\nFrage: ${question}\n\nKontext: PRE_PROJECT. IHK-Projektfreigabe und Zielvereinbarung sind offen. Die Auswahl zwischen Drupal-Erweiterung, AURA-orientierter Architektur und plattformneutralem Dienst ist nicht getroffen. Es liegen keine Ergebnisse einer realen Migration vor.\n\nNutze vorzugsweise öffentlich zugängliche Primärquellen und offizielle Dokumentation. Nenne pro Aussage die Quelle mit direktem Link und Datum, soweit belegt. Trenne belegte Fakten, Schlussfolgerungen und offene Fragen. Erfinde keine FRS-Bestandsdaten, Freigaben, Testergebnisse oder Kosten. Vergleiche die Eignung für einen begrenzten Pilot und formuliere nächste Prüfschritte.\n\nAntwortformat: Kurzantwort, Quellen, Vergleich, offene Fragen.`;
    get('research-prompt').value = prompt;
    get('research-open').href = 'https://www.perplexity.ai/search?q=' + encodeURIComponent(prompt);
  }
  function normalize(source) {
    if (!source || typeof source !== 'object') throw new Error('Ungültige Quelle.');
    const title = String(source.title || '').trim();
    const note = String(source.note || '').trim();
    const date = String(source.date || '');
    const status = source.status;
    if (!title || title.length > 160 || note.length > 2000) throw new Error('Titel und Notiz prüfen (160 bzw. 2000 Zeichen).');
    let url;
    try { url = new URL(String(source.url || '')); } catch { throw new Error('Bitte eine vollständige http- oder https-Adresse eingeben.'); }
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Nur http- und https-Quellen sind erlaubt.');
    if (url.username || url.password) throw new Error('Keine Zugangsdaten in Quellen-URLs verwenden.');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(Date.parse(date)) || new Date(date).toISOString().slice(0, 10) !== date) throw new Error('Bitte ein gültiges Prüfdatum eingeben.');
    if (!['ungeprüft', 'geprüft', 'verworfen'].includes(status)) throw new Error('Bitte einen Prüfstatus wählen.');
    return {title, url: url.href, date, status, note};
  }
  function read() {
    try {
      const raw = localStorage.getItem(key);
      const sources = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(sources) || sources.length > 100) throw new Error('Ungültiges Quellenformat.');
      return sources.map(normalize);
    } catch { throw new Error('Die gespeicherte Quellenliste konnte nicht gelesen werden. Vorhandene Daten wurden nicht überschrieben.'); }
  }
  function write(sources) {
    try { localStorage.setItem(key, JSON.stringify(sources)); }
    catch { throw new Error('Quelle nicht gespeichert: Der Browser blockiert den lokalen Speicher oder der Speicher ist voll.'); }
  }
  function render(sources) {
    const list = get('research-sources'); list.replaceChildren();
    get('sources-export').disabled = !sources.length;
    if (!sources.length) { const p = document.createElement('p'); p.textContent = 'Noch keine eigenen Quellen in diesem Browser gespeichert.'; list.append(p); return; }
    sources.forEach(source => {
      const card = document.createElement('article'); card.className = 'research-source';
      const heading = document.createElement('h4');
      const link = document.createElement('a'); link.href = source.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = source.title + ' ↗'; heading.append(link);
      const meta = document.createElement('p'); meta.className = 'research-source-meta'; meta.textContent = source.status + ' · geprüft/notiert am ' + source.date;
      const note = document.createElement('p'); note.textContent = source.note;
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'btn'; remove.textContent = 'Entfernen'; remove.setAttribute('aria-label', 'Quelle entfernen: ' + source.title);
      remove.addEventListener('click', () => { try { const remaining = read().filter(item => item.url !== source.url); write(remaining); render(remaining); message('Quelle aus diesem Browser entfernt.'); } catch (error) { message(error.message); } });
      card.append(heading, meta, note, remove); list.append(card);
    });
  }
  get('research-build').addEventListener('click', () => { prepare(); message('Frage vorbereitet. Erst „In Perplexity recherchieren“ übermittelt sie an Perplexity.'); });
  get('research-copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(get('research-prompt').value); message('Rechercheauftrag kopiert.'); }
    catch { get('research-prompt').focus(); get('research-prompt').select(); message('Bitte den markierten Rechercheauftrag manuell kopieren.'); }
  });
  get('source-form').addEventListener('submit', event => {
    event.preventDefault();
    try {
      const source = normalize({title:get('source-title').value, url:get('source-url').value, date:get('source-date').value, status:get('source-status').value, note:get('source-note').value});
      const sources = read();
      if (sources.some(item => item.url === source.url)) throw new Error('Diese URL ist bereits gespeichert. Entferne den alten Eintrag, um ihn zu ersetzen.');
      if (sources.length >= 100) throw new Error('Maximal 100 Quellen pro Browser. Bitte zuerst exportieren und alte Einträge entfernen.');
      sources.push(source); write(sources); render(sources);
      get('source-form').reset(); get('source-date').value = new Date().toISOString().slice(0, 10);
      message('Quelle lokal in diesem Browser gespeichert. Ein JSON-Export sichert deine Liste.');
    } catch (error) { message(error.message); }
  });
  get('sources-export').addEventListener('click', () => {
    try {
      const sources = read();
      const output = {version:1, project_status:'PRE_PROJECT', exported_at:new Date().toISOString(), notice:'Persönliche Quellennotizen aus diesem Browser. Kein geprüfter Projektnachweis; Prüfstatus vom Nutzer vergeben.', sources};
      const url = URL.createObjectURL(new Blob([JSON.stringify(output, null, 2)], {type:'application/json;charset=utf-8'}));
      const link = document.createElement('a'); link.href = url; link.download = 'frs-recherche-quellen-' + new Date().toISOString().slice(0, 10) + '.json';
      document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      message('Quellenexport zum Download bereitgestellt.');
    } catch (error) { message(error.message); }
  });
  get('source-date').value = new Date().toISOString().slice(0, 10);
  prepare();
  try { render(read()); } catch (error) { get('sources-export').disabled = true; message(error.message); }
})();
