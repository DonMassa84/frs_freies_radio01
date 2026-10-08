const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require(process.env.JSDOM_PATH || 'jsdom');
const root = path.resolve(__dirname, '../docs/projektportal');
function page(saved, blocked = false) {
  const dom = new JSDOM(fs.readFileSync(path.join(root, 'index.html'), 'utf8'), {url:'https://archiv-bruecke-frs.netlify.app/', runScripts:'outside-only'});
  const w = dom.window;
  if (saved) w.localStorage.setItem('frs-research-v1', saved);
  if (blocked) w.Storage.prototype.setItem = () => {throw new Error('blocked');};
  let downloaded;
  w.Blob = Blob;
  w.URL.createObjectURL = blob => {downloaded = blob; return 'blob:test';};
  w.URL.revokeObjectURL = () => {};
  w.HTMLAnchorElement.prototype.click = () => {};
  for (const script of w.document.querySelectorAll('script[src]')) {
    const file = path.join(root, script.getAttribute('src').split('?')[0]);
    if (fs.existsSync(file)) w.eval(fs.readFileSync(file, 'utf8'));
  }
  const get = id => w.document.getElementById(id);
  return {w, get, download: () => downloaded, close: () => w.close()};
}
function add(p, url = 'https://docs.aura.radio/') {
  assert.ok(p.get('source-form'), 'source form is available');
  p.get('source-title').value = 'AURA Metadaten'; p.get('source-url').value = url;
  p.get('source-note').value = '<img src=x onerror=alert(1)> Relevanz prüfen';
  p.get('source-status').value = 'geprüft';
  p.get('source-form').dispatchEvent(new p.w.Event('submit', {cancelable:true}));
}
test('question and PRE_PROJECT travel intact to Perplexity including URL special characters', () => {
  const p = page(); assert.ok(p.get('research-question'), 'research question input is available');
  p.get('research-question').value = 'Wie bleiben IDs stabil? A&B #1'; p.get('research-build').click();
  const prompt = p.get('research-prompt').value;
  assert.match(prompt, /A&B #1/); assert.match(prompt, /PRE_PROJECT/);
  const url = new URL(p.get('research-open').href);
  assert.equal(url.origin, 'https://www.perplexity.ai'); assert.equal(url.searchParams.get('q'), prompt);
  p.close();
});
test('sources persist across reload, render notes as text and export faithfully', async () => {
  const p = page(); add(p); const saved = p.w.localStorage.getItem('frs-research-v1'); p.close();
  const restored = page(saved);
  assert.equal(restored.get('research-sources').querySelectorAll('article').length, 1);
  assert.match(restored.get('research-sources').textContent, /AURA Metadaten/);
  assert.equal(restored.get('research-sources').querySelectorAll('img').length, 0);
  restored.get('sources-export').click();
  const output = JSON.parse(await restored.download().text());
  assert.equal(output.sources[0].status, 'geprüft'); assert.equal(output.sources[0].title, 'AURA Metadaten');
  assert.equal(output.project_status, 'PRE_PROJECT');
  restored.get('research-sources').querySelector('button').click();
  assert.deepEqual(JSON.parse(restored.w.localStorage.getItem('frs-research-v1')), []);
  restored.close();
});
test('unsafe source URL is rejected without storing it', () => {
  const p = page(); add(p, 'javascript:alert(1)');
  assert.equal(p.get('research-sources').querySelectorAll('article').length, 0);
  assert.match(p.get('research-status').textContent, /https|http/i);
  assert.equal(p.w.localStorage.getItem('frs-research-v1'), null); p.close();
});
test('blocked storage reports failure instead of claiming a successful save', () => {
  const p = page(null, true); add(p);
  assert.match(p.get('research-status').textContent, /nicht gespeichert/);
  assert.equal(p.get('research-sources').querySelectorAll('article').length, 0); p.close();
});
test('invalid persisted data is not silently overwritten', () => {
  const p = page('{broken'); add(p);
  assert.equal(p.w.localStorage.getItem('frs-research-v1'), '{broken');
  assert.match(p.get('research-status').textContent, /nicht gelesen/); p.close();
});
