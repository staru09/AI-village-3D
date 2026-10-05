// ⭐ Key findings: what the research on "Perform novel research!" found, each with one or two exact phrases from the records.
// key_findings.json is built by harness/evals/export_key_findings.py from the verified ground truth.
import { $, el } from './core.js';

const dlg = $('#keys'), list = $('#keysList');
const when = w => `${new Date(`${w.slice(0, 10)}T12:00:00Z`).toLocaleDateString('en-US', { day: 'numeric', month: 'short', timeZone: 'UTC' })}, ${w.slice(11, 16)} PT`;
let loaded = false;
$('#keyBtn').onclick = async () => {
  if (!loaded) {
    loaded = true;
    const k = await fetch('key_findings.json').then(r => r.json()).catch(() => []);
    list.replaceChildren(...k.map((f, i) => el('details', {},
      el('summary', {}, el('span', { className: 'n', textContent: i + 1 }), f.title),
      el('p', { textContent: f.line }),
      ...f.quotes.map(q => el('blockquote', {}, el('q', { textContent: q.text }), el('cite', { textContent: `${q.agent}, ${when(q.when)}` }))))));
  }
  dlg.showModal();
};
$('#keysClose').onclick = () => dlg.close();
