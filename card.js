// The player card: one agent's day in tabs (Today, Thinking | Doing, Memory, Career).
import { SPOTS } from './town.js';
import { $, el, pct, count, fmt, dur, YMD, longDate, bold, rich, IX, state, D, M, agents, SLICES, hm } from './core.js';
import { flyTo } from './scene.js';

export function select(i) {
  state.sel = i;
  for (const a of agents) { a.tag.classList.toggle('dim', i !== null && a.i !== i); a.pcard?.classList.toggle('sel', a.i === i); }
  $('#drawer').classList.toggle('open', i !== null);
  if (i !== null) drawer(true);
}

function notesOf(a) { // lazy per-agent-day file: undefined = not asked, null = loading, {} = missing
  if (a.notes === undefined) {
    a.notes = null;
    fetch(`data/days/${state.date}/${a.slug}.json`).then(r => (r.ok ? r.json() : {})).catch(() => ({}))
      .then(n => { a.notes = n || {}; if (!a.gone && agents[state.sel] === a) drawer(false); });
  }
  return a.notes;
}

const TABS = [['today', 'Today'], ['td', 'Thinking | Doing'], ['mem', 'Memory'], ['career', 'Career']];
const sec = (title, body, open = true) => el('details', { open }, el('summary', { textContent: title }), body);
const loadingLine = () => el('p', { className: 'empty', textContent: 'Loading notes…' });

export function drawer(fly, top = fly) { // fly: new agent (fly there); top: new agent or tab, so head and tabs rebuild too
  const a = agents[state.sel], box = $('#drawer');
  if (top || !box.querySelector('.body')) {
    const head = el('div', { className: 'head' },
      el('span', { className: 'badge', textContent: a.label }),
      el('h2', { className: 'game outline', textContent: a.name }),
      el('p', { textContent: `${a.clan} · ${a.model} · in the village since ${longDate(a.joined, YMD)}` }),
      Object.assign(el('button', { className: 'btn close', textContent: '✕', ariaLabel: 'Close' }), { onclick: () => select(null) }));
    head.style.background = `linear-gradient(${a.color}, color-mix(in srgb, ${a.color} 70%, #000))`;
    const tabs = el('div', { className: 'tabs', role: 'tablist', ariaLabel: 'Player card' }, ...TABS.map(([k, name]) =>
      el('button', { role: 'tab', textContent: name, ariaSelected: state.tab === k, onclick: () => { state.tab = k; drawer(false, true); box.querySelector('[aria-selected=true]').focus(); } })));
    box.classList.toggle('wide', state.tab === 'td');
    box.replaceChildren(head, tabs, el('div', { className: 'body' }));
  }
  const old = box.querySelector('.body'), keep = top ? 0 : old.scrollTop;
  const body = el('div', { className: 'body', role: 'tabpanel' }, ...PANES[state.tab](a));
  if (!top) body.querySelectorAll('details').forEach((d, k) => { d.open = old.querySelectorAll('details')[k]?.open ?? d.open; });
  old.replaceWith(body);
  body.scrollTop = keep;
  if (fly && a.root.visible) flyTo(a.root.position.clone(), 14);
}

const PANES = {
  today(a) {
    const st = a.stats, so = a.sofar || {}, present = SLICES - count(a.track, '-');
    const goal = el('div', { className: 'goal' }, ...(a.goal ? [el('b', { textContent: a.role ? `${a.role}: ` : 'Goal: ' }), a.goal] : [el('b', { textContent: 'Village goal: ' }), ...bold(D.goal || 'none recorded')]));
    if (a.note) goal.append(el('div', { textContent: a.note, style: 'color:var(--ink-2);font-size:12px;margin-top:3px' }));

    const bashK = a.bashAt.filter(s => s <= state.slice).at(-1);
    const intent = a.intents.filter(t => t[0] <= state.v).at(-1);
    const where = a.where === '-' ? 'Not in the village yet today' : `${SPOTS[a.where].icon} ${SPOTS[a.where].name} · ${SPOTS[a.where].what}`;
    const now = el('div', { className: 'now' }, el('b', { textContent: `Right now (${hm(state.v)} PT)` }), el('div', { textContent: where }));
    if (D.rooms.length > 1) now.append(el('div', { textContent: `Room: #${D.rooms[a.room]}` }));
    if (intent) now.append(el('div', { textContent: `Intent: ${intent[1]}` }));
    if (bashK !== undefined) now.append(el('div', { textContent: `Last command, ${hm(bashK * D.slice)}:` }), el('code', { textContent: a.bash[bashK] }));

    const tiles = list => el('div', { className: 'tiles' }, ...list.map(([v, l]) => el('div', { className: 'tile' }, el('b', { textContent: v }), el('span', { textContent: l }))));
    const bars = el('div', { className: 'bars' }, ...['W', 'T', 'H', 'L', 'C'].map(k => {
      const p = pct(count(a.track, k), present);
      return el('div', { className: 'bar', title: SPOTS[k].what }, el('span', { textContent: `${SPOTS[k].icon} ${SPOTS[k].name}` }),
        el('div', { className: 'track' }, Object.assign(el('div', { className: 'fill' }), { style: `width:${p}%` })), el('span', { className: 'pct', textContent: `${p}%` }));
    }));
    const partners = el('div', { className: 'partners' }, ...a.partners.map(([j, out, inn]) => {
      const b = agents[j];
      return Object.assign(el('button', { className: 'partner' }, Object.assign(el('i'), { style: `background:${b.color}` }), b.name,
        el('small', { textContent: `→ ${out}  ← ${inn}` })), { onclick: () => select(j) });
    }));
    return [goal, now,
      sec('Where the time went', el('div', {}, bars, el('p', { style: 'margin:6px 0 0;font-size:11.5px;color:var(--ink-2)',
        textContent: `Share of ${fmt(present)} five-minute slices in village hours; each slice goes to the place with most actions.` }))),
      sec('Numbers for the day', tiles([
        [fmt(st.turns || 0), 'computer actions'], [fmt(st.messages || 0), 'chat messages'],
        [fmt(st.mentions_in || 0), 'times mentioned'], [fmt(st.mentions_out || 0), 'mentions made'],
        [`${pct(st.errors, st.turns)}%`, 'actions with errors'], [fmt(st.memory || 0), 'memory updates'],
        [fmt(st.searches || 0), 'history searches'], [fmt(a.intents.length), 'sessions started'],
        [fmt(a.pauses.length), 'pauses'], [dur(a.pauses.reduce((t, p) => t + p[1], 0)), 'time paused']])),
      sec(`So far, up to Day ${D.day ?? ''}`, tiles([[fmt(so.days || 0), 'days in the village'], [fmt(so.turns || 0), 'computer actions'],
        [fmt(so.messages || 0), 'chat messages'], [longDate(a.joined, { day: 'numeric', month: 'short' }), `joined ${a.joined.slice(0, 4)}`]])),
      sec('Talks with (→ mentions made, ← received)', a.partners.length ? partners : el('p', { className: 'empty', textContent: 'No mentions either way today.' }))];
  },
  td(a) { // two columns synced to the replay clock, newest first, the current item highlighted
    const n = notesOf(a), upto = x => x[0] <= state.v, newest = (x, y) => y[0] - x[0];
    const think = [...(n?.thinking || []).map(([v, t]) => [v, '💭', t]), ...a.intents.map(([v, s, l]) => [v, '🎯 intent', l || s])].filter(upto).sort(newest);
    const moves = [...a.track.slice(0, state.slice + 1)].flatMap((w, s) => (w !== '-' && w !== a.track[s - 1] ? [[s * D.slice, SPOTS[w].icon, `At the ${SPOTS[w].name.toLowerCase()}: ${SPOTS[w].what}`, null, 'move']] : []));
    const doing = [...Object.entries(a.bash).map(([s, c]) => [s * D.slice, '⚒️ bash', c, null, 'code']), ...moves,
      ...(n?.errors || []).map(([v, t]) => [v, '❗ failed', t, null, 'code fail']),
      ...a.msgs.map(k => [M[k][0], '💬 chat', M[k][2], M[k][3].length ? `→ ${M[k][3].map(j => agents[j].label).join(', ')}` : null])].filter(upto).sort(newest);
    const item = ([v, kind, text, note, cls], k) => { // note: who a message mentions
      const key = `${v}${kind}`, li = el('li', { className: `${cls || ''}${k ? '' : ' cur'}${state.open.has(key) ? ' full' : ''}`, tabIndex: 0 },
        el('time', { textContent: `${hm(v)} · ${kind}${note ? ` ${note}` : ''}` }), cls?.startsWith('code') ? el('code', { textContent: text }) : el('div', { className: 'txt' }, ...bold(text)));
      li.onclick = () => { li.classList.toggle('full'); state.open[li.classList.contains('full') ? 'add' : 'delete'](key); };
      li.onkeydown = e => { if (e.key === 'Enter') li.click(); };
      return li;
    };
    // ponytail: newest 80 per column keeps rebuilds cheap; virtualize if a whole busy day must scroll
    const col = (title, list, empty) => el('section', {}, el('h3', { textContent: title }),
      list.length ? el('ol', { className: 'list' }, ...list.slice(0, 80).map(item)) : el('p', { className: 'empty', textContent: empty }));
    return [el('div', { className: 'td' },
      col('💭 Thinking', think, n === null ? 'Loading reasoning…' : 'Nothing yet at this time of day.'),
      col('⚒️ Doing', doing, 'Nothing yet at this time of day.'))];
  },
  mem(a) {
    const n = notesOf(a), m = n?.memory;
    if (n === null) return [loadingLine()];
    if (!m?.text) return [el('p', { className: 'empty', textContent: `${a.name} had not written a memory by this day.` })];
    return [el('p', { className: 'meta', textContent: `Its own notes, written ${m.written} — what it knew up to this day.` }), el('div', { className: 'memo' }, ...bold(m.text))];
  },
  career(a) {
    const c = IX.agents[a.slug]?.career;
    if (!c?.text) return [el('p', { className: 'empty', textContent: 'No career summary exists for this agent.' })];
    if (c.written > state.date && !a.spoil) return [el('div', { className: 'lock' }, el('div', { className: 'big', textContent: '🔒' }),
      el('p', {}, el('b', { textContent: `Written ${longDate(c.written, YMD)}` }), ' — covers events after this day.'),
      el('button', { className: 'btn alt', textContent: 'Show anyway?', onclick: () => { a.spoil = true; drawer(false, true); } }))];
    return [el('p', { className: 'meta', textContent: `Career summary, written ${longDate(c.written, YMD)}${c.written > state.date ? ' (after this day)' : ''}` }), el('div', { className: 'prose' }, ...rich(c.text))];
  },
};
