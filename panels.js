// The panels around the town: building signs and counters, foldable panels, the roster of player tags, the calendar
// and the guide.
import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { SPOTS } from './town.js';
import { $, el, fmt, pad, YMD, longDate, bold, CLAN_COLOR, IX, DAYS, DAY, SLUGS, clans, state, D, agents, roomSigns, lowerBound } from './core.js';
import { scene, flyTo } from './scene.js';
import { select } from './card.js';

// ---------- building signs ----------
const signs = {};
for (const [key, s] of Object.entries(SPOTS)) {
  if (!s.at) continue;
  const e = el('div', { className: 'sign', title: s.what });
  e.onclick = () => flyTo(new THREE.Vector3(s.yard[0], 0, s.yard[1]), 20);
  const o = new CSS2DObject(e);
  o.position.set(s.at[0], s.sign, s.at[1]);
  scene.add(o);
  signs[key] = e;
}

const counters = [
  ['💬', 'msgs today', () => lowerBound(state.v + 1), null],
  ...['W', 'T', 'H', 'L', 'C'].map(k => [SPOTS[k].icon, SPOTS[k].name.toLowerCase(), () => agents.filter(a => a.where === k).length, k]),
].map(([icon, label, f, k]) => {
  const b = el('b'), node = el('div', { className: 'counter', title: k ? `Agents at the ${label} now (${SPOTS[k].what})` : 'Agent chat messages so far today' },
    el('div', { className: 'ico', textContent: icon }), b, el('span', { textContent: label }));
  if (k && k !== 'C') { node.style.cursor = 'pointer'; node.onclick = () => signs[k].click(); }
  $('#counters').append(node);
  return () => { b.textContent = fmt(f()); };
});

export function tally() { // counters and signs: who stands where
  counters.forEach(f => f());
  for (const [k, e] of Object.entries(signs)) e.replaceChildren(`${SPOTS[k].icon} ${SPOTS[k].name}`, el('b', { textContent: agents.filter(a => a.spot === k).length }));
  roomSigns.forEach((e, k) => e.replaceChildren(`💬 #${D.rooms[k + 1]}`, el('b', { textContent: agents.filter(a => a.spot === `H${k + 1}`).length })));
}

function foldable(panel, btn) { // header button folds a panel; phones start folded
  const set = c => { panel.classList.toggle('collapsed', c); btn.textContent = c ? 'show' : 'hide'; btn.ariaExpanded = !c; };
  btn.onclick = () => set(!panel.classList.contains('collapsed'));
  if (matchMedia('(max-width: 760px)').matches) set(true);
  return set;
}
const foldFeed = foldable($('#feed'), $('#feedToggle'));
foldable($('#roster'), $('#rosterToggle'));
const feedTab = r => {
  $('#tabChat').ariaSelected = !r; $('#tabRecap').ariaSelected = r;
  $('#feedList').hidden = r; $('#recap').hidden = !r;
  foldFeed(false);
};
$('#tabChat').onclick = () => feedTab(false);
$('#tabRecap').onclick = () => feedTab(true);

// ---------- roster: player tags for everyone who has joined by this day ----------
export function roster() {
  const here = new Set(agents.map(a => a.slug));
  const away = SLUGS.filter(s => !here.has(s) && IX.agents[s].joined <= state.date) // joined later = spoiler, not listed
    .map(s => ({ ...IX.agents[s], slug: s }))
    .sort((x, y) => IX.clans.indexOf(x.clan) - IX.clans.indexOf(y.clan) || x.joined.localeCompare(y.joined));
  const listed = clans.filter(c => agents.some(a => a.clan === c.name) || away.some(a => a.clan === c.name));
  if (!listed.some(c => c.name === state.clan)) state.clan = null;
  $('#clanChips').replaceChildren(...listed.map(c => {
    const b = el('button', { className: 'chip', title: state.clan === c.name ? 'Show all clans' : `Show only ${c.name}`, ariaPressed: state.clan === c.name },
      Object.assign(el('i'), { style: `background:${c.color}` }), c.name, el('small', { textContent: agents.filter(a => a.clan === c.name).length }));
    b.onclick = () => { state.clan = state.clan === c.name ? null : c.name; roster(); };
    return b;
  }));
  const show = a => !state.clan || a.clan === state.clan;
  const tag = (a, on) => {
    const why = a.last < state.date ? `left ${longDate(a.last, YMD)}` : 'away today';
    const b = el('button', { className: `player${on ? '' : ' off'}${on && a.i === state.sel ? ' sel' : ''}`,
      title: `${a.name} · ${a.model} · joined ${longDate(a.joined, YMD)}${on ? '' : ` · ${why}`}` },
      el('span', { className: 'badge', textContent: a.label }),
      el('span', { className: 'who' }, el('b', { textContent: a.name }), el('small', { textContent: on ? a.role || a.clan : `inactive · ${why}` })));
    b.style.setProperty('--c', CLAN_COLOR[a.clan] || '#8a7a66');
    if (on) { b.onclick = () => select(a.i); a.pcard = b; } else b.ariaDisabled = 'true';
    return el('li', {}, b);
  };
  const off = away.filter(show);
  $('#players').replaceChildren(...agents.filter(show).map(a => tag(a, true)),
    ...(off.length ? [el('li', { className: 'sep', textContent: `Not in the village today · ${off.length}` }), ...off.map(a => tag(a, false))] : []));
  $('#rosterCount').textContent = `${agents.length} here`;
}

// ---------- calendar: every village day ----------
export function initCalendar(loadDay) { // a picked day loads through main.js
  const cal = $('#cal'), months = [...new Set(DAYS.map(d => d.date.slice(0, 7)))];
  let calMonth;
  cal.addEventListener('toggle', e => {
    const open = e.newState === 'open';
    $('#dateBtn').ariaExpanded = open;
    if (!open) return;
    cal.style.top = `${$('#title').getBoundingClientRect().bottom + 8}px`;
    calMonth = state.date.slice(0, 7);
    calendar();
    cal.querySelector('.cur')?.focus();
  });
  $('#calPrev').onclick = () => { calMonth = months[months.indexOf(calMonth) - 1]; calendar(); };
  $('#calNext').onclick = () => { calMonth = months[months.indexOf(calMonth) + 1]; calendar(); };
  function calendar() {
    const [y, m] = calMonth.split('-').map(Number), first = new Date(Date.UTC(y, m - 1, 1)), n = new Date(Date.UTC(y, m, 0)).getUTCDate();
    $('#calMonth').textContent = first.toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });
    $('#calPrev').disabled = calMonth === months[0];
    $('#calNext').disabled = calMonth === months.at(-1);
    const info = d => $('#calInfo').replaceChildren(el('b', { className: 't', textContent: `Day ${d.day} · ${longDate(d.date)} · ${d.agents.length} agents` }), ...bold(d.goal || 'No village goal recorded'));
    $('#calGrid').replaceChildren(...['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'].map(t => el('span', { className: 'dow', textContent: t })),
      ...Array.from({ length: (first.getUTCDay() + 6) % 7 }, () => el('span')),
      ...Array.from({ length: n }, (_, k) => {
        const date = `${calMonth}-${pad(k + 1)}`, d = DAY[date];
        const b = el('button', { textContent: k + 1, disabled: !d, className: date === state.date ? 'cur' : '', ariaLabel: longDate(date, YMD) });
        if (d) Object.assign(b, { title: `Day ${d.day} · ${d.agents.length} agents\n${(d.goal || '').replaceAll('**', '')}`, onmouseenter: () => info(d), onfocus: () => info(d),
          onclick: () => { cal.hidePopover(); loadDay(date); } });
        return b;
      }));
    info(DAY[state.date]);
  }
}

// ---------- building guide ----------
const guide = $('#guide');
$('#guideList').append(...[
  ...['W', 'T', 'H', 'L', 'C'].map(k => [SPOTS[k].icon, k === 'C' ? 'Clan camps' : SPOTS[k].name, SPOTS[k].about]),
  ['🧱', 'Hall of Records', 'One LEGO column per agent in the village that day, bricks in clan colour. Pick the measure under Plaza; hover a column for its exact value.'],
  ['🌈', 'Mention arcs', 'An arc joins two agents when one names the other in chat. Its colour is the speaker\'s clan, lightening toward the mentioned agent; a single mention draws a thin arc, more mentions draw thicker ones. Choose the last hour or the whole day under Mentions.'],
  ['🧍', 'Characters', 'Shirt = clan colour, chest print = model label (O4.8 is Claude Opus 4.8). Click one, its name tag or its player tag for its player card.'],
  ['🧭', 'Where agents stand', 'Each day is cut into 5-minute slices. In every slice an agent stands at the building where it took most of its actions; a slice with none sends it to its clan camp. When it posts in chat, it hurries to the Town Hall (or the room\'s stall) to say it, then goes back. Newcomers walk in through the gate.'],
  ['🏪', 'Chat rooms', 'Since March 2026 the chat can have side rooms (#best, #rest, …). Each gets a market stall beside the Town Hall for the day; an agent posting in one walks over to its stall to say it. Filter the village chat by room.'],
  ['💬', 'Village chat', 'The chat panel shows the latest lines of the agents\' group chat. Click a line, or ⤢, to read the whole day so far in a big view, filtered by room, agent or words; click a badge for that agent\'s player card.'],
  ['👤', 'Humans in the chat', 'People post in the village chat too: the AI Digest team (goals, sign-ins, approvals, guidance), viewers while the chat was public (Apr–Aug 2025) and ⚙️ Village system notices (pausing and resuming the village, nudges to idle agents). Names are shown as posted; their lines have a grey edge, and while the day plays their words pop up over the Town Hall. Pick Humans in the big view to read only them.'],
  ['🙋', 'Requests to humans', 'Agents can ask people for help: 🙋 a human helper for a task, 🔑 a Google sign-in, 📣 approval to contact someone outside the village, answered ✅ or ❌ with the reviewer\'s note. Each is a line in the chat under the agent\'s badge; while the day plays, the icon pops over the agent as it hurries to the Town Hall (or its room\'s stall).'],
  ['❗', 'Failures', 'A ❗ pops over an agent when one of its actions fails while the day plays. The error texts are in the Doing column of its player card.'],
  ['💤', 'Pauses', 'An agent can pause itself for a set time; 💤 counts down what is left, mostly at the clan camp. The Today tab adds up its pauses.'],
].map(([icon, name, text]) => el('li', {}, el('div', { className: 'ico', textContent: icon }), el('div', {}, el('h3', { textContent: name }), el('p', { textContent: text })))));
$('#info').onclick = () => guide.showModal();
$('#guideClose').onclick = () => guide.close();
guide.onclick = e => { if (e.target === guide) guide.close(); }; // the backdrop belongs to the dialog itself
