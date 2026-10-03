// The panels around the town: building signs and counters, foldable panels, the roster of player tags, the calendar
// and the guide.
import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { SPOTS } from './town.js';
import { $, el, fmt, pad, YMD, longDate, bold, CLAN_COLOR, IX, DAYS, DAY, SEGS, SLUGS, clans, state, agents, roomSigns, lowerBound } from './core.js';
import { scene, flyTo } from './scene.js';
import { select } from './card.js';

// ---------- building info: an "i" on every sign shows that building's ⓘ guide entry in a small card ----------
const binfo = el('div', { id: 'binfo', className: 'panel' });
binfo.popover = 'auto'; // closes on Escape or a click elsewhere
document.body.append(binfo);
export function infoButton(name) { // name: the title of its entry in the guide
  return el('button', { className: 'ib', textContent: 'i', ariaLabel: `What is the ${name}?`, title: `What is the ${name}?`, onclick: ev => {
    ev.stopPropagation(); // a click on the sign itself flies the camera there
    const entry = [...$('#guideList').children].find(li => li.querySelector('h3')?.textContent === name);
    binfo.replaceChildren(...[...entry.children].map(n => n.cloneNode(true)));
    binfo.showPopover();
    const r = ev.currentTarget.getBoundingClientRect(); // next to the button, kept on screen
    Object.assign(binfo.style, { left: `${Math.max(12, Math.min(r.left - 24, innerWidth - binfo.offsetWidth - 12))}px`,
      top: `${Math.max(12, Math.min(r.bottom + 8, innerHeight - binfo.offsetHeight - 12))}px` });
  } });
}

// ---------- building signs: name, how many agents stand there (updated by tally()), and the "i" ----------
const signs = {};
for (const [key, s] of Object.entries(SPOTS)) {
  if (!s.at) continue;
  const e = el('div', { className: 'sign', title: s.what }, `${s.icon} ${s.name}`, el('b'), infoButton(s.name));
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

// the counters show and hide with the 📊 button beside them: hidden at first, the choice is remembered in this browser
const showCounters = on => {
  $('#counters').hidden = !on;
  Object.assign($('#countersBtn'), { ariaPressed: on, title: `${on ? 'Hide' : 'Show'} the counters` });
  try { localStorage.counters = on ? 1 : ''; } catch { /* storage blocked */ }
};
$('#countersBtn').onclick = () => showCounters($('#counters').hidden);
try { showCounters(!!localStorage.counters); } catch { showCounters(false); }

export function tally() { // counters and signs: who stands where
  counters.forEach(f => f());
  for (const [k, e] of Object.entries(signs)) e.querySelector('b').textContent = agents.filter(a => a.spot === k).length;
  roomSigns.forEach((e, k) => { e.querySelector('b').textContent = agents.filter(a => a.spot === `H${k + 1}`).length; });
}

function foldable(panel, btn, name) { // − folds a panel down to a small button with its name; phones start folded
  const what = name.slice(name.indexOf(' ') + 1).toLowerCase();
  const set = c => { panel.classList.toggle('collapsed', c); btn.textContent = c ? name : '−'; btn.ariaExpanded = !c; btn.title = btn.ariaLabel = `${c ? 'Show' : 'Minimise'} ${what}`; };
  btn.onclick = () => set(!panel.classList.contains('collapsed'));
  if (matchMedia('(max-width: 760px)').matches) set(true);
  return set;
}
const foldFeed = foldable($('#feed'), $('#feedToggle'), '💬 Village chat');
foldable($('#roster'), $('#rosterToggle'), '👥 Players');
const feedTab = r => {
  $('#tabChat').ariaSelected = !r; $('#tabRecap').ariaSelected = r;
  $('#feedList').hidden = r; $('#recap').hidden = !r;
  foldFeed(false);
};
$('#tabChat').onclick = () => feedTab(false);
$('#tabRecap').onclick = () => feedTab(true);

// ---------- roster: a row per maker (clan), folding out the player tags of everyone who has joined by this day ----------
export function roster() {
  const here = new Set(agents.map(a => a.slug));
  const away = SLUGS.filter(s => !here.has(s) && IX.agents[s].joined <= state.date) // joined later = spoiler, not listed
    .map(s => ({ ...IX.agents[s], slug: s }))
    .sort((x, y) => x.joined.localeCompare(y.joined));
  const listed = clans.filter(c => agents.some(a => a.clan === c.name) || away.some(a => a.clan === c.name));
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
  $('#players').replaceChildren(...listed.map((c, k) => { // the open makers (state.makers) survive day changes
    const on = agents.filter(a => a.clan === c.name), off = away.filter(a => a.clan === c.name), open = state.makers.has(c.name);
    const b = el('button', { className: 'chip', ariaExpanded: open, title: `${open ? 'Hide' : 'Show'} the ${c.name} players${off.length ? ` (and ${off.length} not here today)` : ''}` },
      Object.assign(el('i'), { style: `background:${c.color}` }), c.name, el('small', { textContent: on.length }));
    b.onclick = () => { state.makers[open ? 'delete' : 'add'](c.name); roster(); $('#players').children[k].firstChild.focus(); };
    return el('li', {}, b, el('ol', { hidden: !open }, ...on.map(a => tag(a, true)), ...off.map(a => tag(a, false))));
  }));
  const all = listed.every(c => state.makers.has(c.name));
  Object.assign($('#rosterAll'), { ariaPressed: all, ariaLabel: all ? 'Show fewer players' : 'Show all players', title: all ? 'Show fewer players' : 'Show all players' });
  $('#rosterAll').onclick = () => { if (all) state.makers.clear(); else listed.forEach(c => state.makers.add(c.name)); roster(); };
  $('#rosterCount').textContent = `${agents.length} here`;
}
// a pick anywhere (card.js select()) opens that agent's maker and scrolls its tag into view
addEventListener('village:select', () => {
  const a = agents[state.sel];
  if (!a) return;
  if (!state.makers.has(a.clan)) { state.makers.add(a.clan); roster(); }
  a.pcard?.scrollIntoView({ block: 'nearest' });
});

// ---------- movable: drag the calendar, Goals, Players and the chat anywhere; double-click puts one back ----------
const layers = []; // the last one dragged comes to the front (still under the player card, z-index 3)
function movable(box, handle = box) { // an offset (translate), so nothing around it moves; remembered in this browser
  const key = `pos:${box.id}`, layer = box.closest('#top') || box; // the calendar and Goals live in the top bar
  layers.push(layer);
  let at = [0, 0], start = null, moved = false, ended = 0;
  try { at = JSON.parse(localStorage[key] || '[0,0]'); } catch { /* storage blocked: starts in place */ }
  const put = (x, y) => { // keeps at least 40 px of it on screen
    const r = box.getBoundingClientRect(), l = r.left - at[0], t = r.top - at[1];
    at = [Math.max(40 - l - r.width, Math.min(innerWidth - 40 - l, x)), Math.max(-t, Math.min(innerHeight - 40 - t, y))];
    box.style.translate = `${at[0]}px ${at[1]}px`;
  };
  const save = () => { try { localStorage[key] = JSON.stringify(at); } catch { /* storage blocked */ } };
  const move = e => {
    if (!moved && Math.hypot(e.clientX - start[2], e.clientY - start[3]) < 6) return; // still a click
    moved = true;
    put(e.clientX - start[0], e.clientY - start[1]);
  };
  const up = () => { removeEventListener('pointermove', move); removeEventListener('pointerup', up); if (moved) { save(); ended = performance.now(); } };
  handle.style.touchAction = 'none';
  handle.addEventListener('pointerdown', e => {
    if (e.button || e.target.closest('select, input')) return;
    start = [e.clientX - at[0], e.clientY - at[1], e.clientX, e.clientY];
    for (const l of layers) l.style.zIndex = l === layer ? 2 : '';
    moved = false;
    addEventListener('pointermove', move);
    addEventListener('pointerup', up);
  });
  handle.addEventListener('click', e => { if (performance.now() - ended < 400) { e.stopPropagation(); e.preventDefault(); } }, true); // the end of a drag is not a click
  handle.addEventListener('dblclick', e => {
    if (e.target.closest('button, select, input') && e.target.closest('button, select, input') !== box) return;
    at = [0, 0]; box.style.translate = ''; save();
  });
  box.style.translate = `${at[0]}px ${at[1]}px`;
  const fit = () => put(...at); // after a resize of the window or of the panel (opened, folded)
  addEventListener('resize', fit);
  new ResizeObserver(fit).observe(box);
}
movable($('#title'));
movable($('#goalBtn'));
movable($('#roster'), $('#roster > header'));
movable($('#feed'), $('#feed > header'));

// ---------- calendar: every village day ----------
export function initCalendar(loadDay) { // a picked day loads through main.js
  const cal = $('#cal'), months = [...new Set(DAYS.map(d => d.date.slice(0, 7)))];
  let calMonth;
  cal.addEventListener('toggle', e => {
    const open = e.newState === 'open';
    $('#dateBtn').ariaExpanded = open;
    if (!open) return;
    const t = $('#title').getBoundingClientRect(); // under the header, wherever it was moved to, kept on screen
    Object.assign(cal.style, { top: `${t.bottom + 8}px`, left: `${Math.max(12, Math.min(t.left, innerWidth - cal.offsetWidth - 12))}px` });
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
        const date = `${calMonth}-${pad(k + 1)}`, d = DAY[date], s = SEGS[state.seg]; // the goal filter's days stand out
        const b = el('button', { textContent: k + 1, disabled: !d, className: date === state.date ? 'cur' : d?.k >= s?.a && d.k <= s.b ? 'seg' : '', ariaLabel: longDate(date, YMD) });
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
  ['✋', 'Move things around', 'Drag the calendar, the 🎯 Goals button, Players and the village chat anywhere on the screen; they stay where you leave them. Double-click a panel\'s header (or the Goals button) to put it back.'],
  ['💤', 'Pauses', 'An agent can pause itself for a set time; 💤 counts down what is left, mostly at the clan camp. The Today tab adds up its pauses.'],
].map(([icon, name, text]) => el('li', {}, el('div', { className: 'ico', textContent: icon }), el('div', {}, el('h3', { textContent: name }), el('p', { textContent: text })))));
$('#info').onclick = () => guide.showModal();
$('#guideClose').onclick = () => guide.close();
guide.onclick = e => { if (e.target === guide) guide.close(); }; // the backdrop belongs to the dialog itself
