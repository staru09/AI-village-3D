// 🔎 Ask AI: a question about one village goal, answered by the research harness (`village ask` in the AI-Village-CLI repo).
// The page calls the CLI's web server (`village web`, which Caddy proxies at /api/) and shows the answer with its record refs.
// ?askapi=http://host:port points it elsewhere. An answer takes 20 s to a few minutes: the agent runs 5-40 CLI commands;
// "what is happening?" is quicker (about 20 s): one model call over that day's records up to the replay time.
import { $, el, rich, SEGS, DAY, state, hm } from './core.js';

const API = new URLSearchParams(location.search).get('askapi') || '';
const dlg = $('#ask'), goal = $('#askGoal'), q = $('#askQ'), out = $('#askOut'), go = $('#askGo');
goal.append(...SEGS.map((s, k) => el('option', { value: k, textContent: s.goal.replaceAll('**', '') })).reverse());

// A panel, not a modal: it opens along the bottom, just above the replay bar, the map stays usable behind it, and its
// title bar drags it anywhere (kept on screen).
const keep = (x, y) => Object.assign(dlg.style, {
  left: `${Math.max(0, Math.min(x, innerWidth - dlg.offsetWidth))}px`, top: `${Math.max(0, Math.min(y, innerHeight - dlg.offsetHeight))}px` });
let placed = false;
// new content makes the panel taller: grow it upwards from the replay bar, or, once dragged, keep it on screen
const grow = () => keep(dlg.offsetLeft, placed ? dlg.offsetTop : $('#bottom').getBoundingClientRect().top - dlg.offsetHeight - 10);
$('#askBtn').onclick = () => { // preselect the goal being watched
  const k = state.seg >= 0 ? state.seg : SEGS.findIndex(s => s.a <= DAY[state.date]?.k && DAY[state.date].k <= s.b);
  if (k >= 0) goal.value = k;
  if (!dlg.open) dlg.show();
  if (!out.childElementCount) showPast();
  if (!placed) keep((innerWidth - dlg.offsetWidth) / 2, $('#bottom').getBoundingClientRect().top - dlg.offsetHeight - 10);
  q.focus();
};
$('#askClose').onclick = () => dlg.close();

// Past answers: what the harness answered when it was tested on questions with verified answers (ask_examples.json,
// from the AI-Village-CLI experiments E21 and E22). Shown when nothing has been asked yet, and from the 📚 button.
let past;
async function showPast() {
  past ??= await fetch('ask_examples.json').then(r => r.json()).catch(() => []);
  out.replaceChildren(el('p', { className: 'note', textContent: past.length
      ? `How the harness answers: ${past.length} questions it was tested on, each with a verified answer to check it against. Click one to read its answer.`
      : 'No earlier answers available.' }),
    el('ol', { className: 'past' }, ...past.map((x, i) => el('li', {}, el('button', { type: 'button', onclick: () => showOne(x) },
      el('small', { textContent: `Question ${i + 1}` }), x.question.length > 170 ? `${x.question.slice(0, 170).replace(/\s\S*$/, '')}…` : x.question)))));
  grow();
}
function showOne(x) {
  q.value = x.question;
  out.replaceChildren(el('p', {}, el('b', { textContent: x.question })), ...rich(x.answer));
  out.scrollTop = 0;
  grow();
}
$('#askPast').onclick = showPast;

dlg.addEventListener('keydown', e => { if (e.key === 'Escape') dlg.close(); });
const bar = dlg.querySelector('header');
bar.addEventListener('pointerdown', e => {
  if (e.target.closest('button')) return;
  const r = dlg.getBoundingClientRect(), dx = e.clientX - r.left, dy = e.clientY - r.top;
  bar.setPointerCapture(e.pointerId);
  bar.onpointermove = m => { placed = true; keep(m.clientX - dx, m.clientY - dy); };
  bar.onpointerup = () => { bar.onpointermove = bar.onpointerup = null; };
});

// Enter asks; Shift+Enter or Ctrl+Enter starts a new line (not while an input method is composing text)
q.addEventListener('keydown', e => {
  if (e.key !== 'Enter' || e.isComposing) return;
  e.preventDefault();
  if (e.shiftKey || e.ctrlKey) q.setRangeText('\n', q.selectionStart, q.selectionEnd, 'end');
  else if (!go.disabled) $('#askForm').requestSubmit();
});

$('#askForm').onsubmit = async e => {
  e.preventDefault();
  const question = q.value.trim(), g = SEGS[goal.value].goal.replaceAll('**', '');
  if (!question) return;
  go.disabled = true;
  out.replaceChildren(el('p', { className: 'note', textContent: '⏳ The harness is reading the village records. This can take a few minutes…' }));
  // the day and replay time being watched: "what is happening?" is answered for that moment (a fast path in `village ask`)
  const cmd = `ask ${JSON.stringify(question)} --goal ${JSON.stringify(g)} --date ${JSON.stringify(`${state.date} ${hm(state.v)}`)}`;
  try {
    const r = await (await fetch(`${API}/api/run?cmd=${encodeURIComponent(cmd)}`)).json();
    if (r.error) throw new Error(r.error);
    const [answer, , note] = r.blocks; // ['text', question, answer], ['table', commands], ['note', model, cost, citations]
    out.replaceChildren(...rich(answer.at(-1)), el('p', { className: 'note', textContent: `${note.at(-1)} · ${Math.round(r.secs)} s` }));
    grow();
  } catch (err) {
    out.replaceChildren(el('p', { className: 'note', textContent: `❌ No answer: ${err.message}. Is \`village web\` running behind /api/?` }));
  }
  go.disabled = false;
  grow();
};
