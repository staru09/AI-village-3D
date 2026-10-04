// 🔎 Ask AI: a question about one village goal, answered by the research harness (`village ask` in the AI-Village-CLI repo).
// The page calls the CLI's web server (`village web`, which Caddy proxies at /api/) and shows the answer with its record refs.
// ?askapi=http://host:port points it elsewhere. An answer takes 20 s to a few minutes: the agent runs 5-40 CLI commands.
import { $, el, rich, SEGS, DAY, state } from './core.js';

const API = new URLSearchParams(location.search).get('askapi') || '';
const dlg = $('#ask'), goal = $('#askGoal'), q = $('#askQ'), out = $('#askOut'), go = $('#askGo');
goal.append(...SEGS.map((s, k) => el('option', { value: k, textContent: s.goal.replaceAll('**', '') })).reverse());

$('#askBtn').onclick = () => { // preselect the goal being watched
  const k = state.seg >= 0 ? state.seg : SEGS.findIndex(s => s.a <= DAY[state.date]?.k && DAY[state.date].k <= s.b);
  if (k >= 0) goal.value = k;
  dlg.showModal();
  q.focus();
};
$('#askClose').onclick = () => dlg.close();

$('#askForm').onsubmit = async e => {
  e.preventDefault();
  const question = q.value.trim(), g = SEGS[goal.value].goal.replaceAll('**', '');
  if (!question) return;
  go.disabled = true;
  out.replaceChildren(el('p', { className: 'note', textContent: '⏳ The harness is reading the village records. This can take a few minutes…' }));
  const cmd = `ask ${JSON.stringify(question)} --goal ${JSON.stringify(g)}`;
  try {
    const r = await (await fetch(`${API}/api/run?cmd=${encodeURIComponent(cmd)}`)).json();
    if (r.error) throw new Error(r.error);
    const [answer, , note] = r.blocks; // ['text', question, answer], ['table', commands], ['note', model, cost, citations]
    out.replaceChildren(...rich(answer.at(-1)), el('p', { className: 'note', textContent: `${note.at(-1)} · ${Math.round(r.secs)} s` }));
  } catch (err) {
    out.replaceChildren(el('p', { className: 'note', textContent: `❌ No answer: ${err.message}. Is \`village web\` running behind /api/?` }));
  }
  go.disabled = false;
};
