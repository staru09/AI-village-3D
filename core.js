// Shared by every module: small helpers, the village index, the replay state and the loaded day.
// The loaded day (D, M, C, agents, ...) changes only through setDay(); other modules read it as live bindings.

// Validated categorical palette (dataviz reference, slot order); colour follows the clan, never its rank.
export const CLAN_COLOR = { Google: '#2a78d6', Anthropic: '#eb6834', OpenAI: '#1baf7a', Zhipu: '#eda100',
  Moonshot: '#e87ba4', xAI: '#008300', DeepSeek: '#4a3aa7', Meta: '#e34948' };

export const $ = s => document.querySelector(s);
export const el = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); e.append(...kids); return e; };
export const pct = (a, b) => (b ? Math.round(100 * (a || 0) / b) : 0);
export const count = (s, ch) => s.split(ch).length - 1;
export const fmt = n => n.toLocaleString('en-US');
export const dur = s => (s < 60 ? `${Math.ceil(s)} s` : s < 3600 ? `${Math.round(s / 60)} min` : `${+(s / 3600).toFixed(1)} h`);
export const pad = n => String(n).padStart(2, '0');
export const YMD = { day: 'numeric', month: 'short', year: 'numeric' };
export const longDate = (d, o = { weekday: 'short', day: 'numeric', month: 'short' }) => new Date(`${d.slice(0, 10)}T12:00:00Z`).toLocaleDateString('en-US', { ...o, timeZone: 'UTC' });
// Dataset text stays text: **bold** becomes <b> by splitting, never through innerHTML.
export const bold = t => t.split('**').map((s, k) => (k % 2 ? el('b', { textContent: s }) : s));
export const rich = t => t.split(/\n\s*\n/).map(p => el('p', {}, ...bold(p)));

export let IX;
try {
  IX = await (await fetch('data/index.json')).json();
} catch {
  $('#loadmsg').replaceChildren('No data/index.json yet. Build it from the AI Village dataset, then serve this folder:',
    el('pre', { textContent: 'cd village-3d\npython3 extract.py\npython3 -m http.server 8000\n# open http://localhost:8000' }));
  throw new Error('data/index.json missing');
}
await document.fonts.load('28px "Lilita One"');

export const DAYS = IX.days, DAY = Object.fromEntries(DAYS.map((d, k) => [d.date, { ...d, k }]));
export const SLUGS = Object.keys(IX.agents);
export const clans = IX.clans.map(name => ({ name, color: CLAN_COLOR[name] || '#8a7a66' }));
// goal segments, runs of days with the same village goal: { a, b (first and last day's k), goal }; state.seg is the
// goal filter, an index in SEGS or -1 for all days
export const SEGS = [];
DAYS.forEach((d, k) => { const s = SEGS.at(-1), goal = d.goal || 'No village goal recorded'; if (s?.goal === goal) s.b = k; else SEGS.push({ a: k, b: k, goal }); });

// The loaded day; everything below that reads these is rebuilt by loadDay(). M: agent messages [v, agent, text, mentioned, room];
// C: what the chat shows, M plus human messages and requests to humans, [v, agent or HUMAN, text, mentioned, room, name or icon].
export const HUMAN = -2; // a human line's sender, and the #chat filter's "Humans" option (-1 is everyone)
export let D, M = [], C = [], agents = [], END = 1, SLICES = 1, dayPairs = new Map(), dayGroup = null, gaps = [], roomSigns = [];

export function setDay(o) { // loadDay() hands over the new day here; a key left out keeps its value
  ({ D = D, M = M, C = C, agents = agents, END = END, SLICES = SLICES, dayPairs = dayPairs, dayGroup = dayGroup, gaps = gaps, roomSigns = roomSigns } = o);
}

export const state = { v: 0, slice: -1, playing: true, speed: 30, sel: null, mp: 0, fly: null, names: true, tab: 'today', seg: -1, makers: new Set(), open: new Set() };
export const hm = v => { const m = Math.round(D.open * 60) + Math.floor(v / 60); return `${pad(Math.floor(m / 60) % 24)}:${pad(m % 60)}`; };
export function lowerBound(v, A = M) { let lo = 0, hi = A.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (A[mid][0] < v) lo = mid + 1; else hi = mid; } return lo; }
