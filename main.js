// AI Village 3D: replays any day of the AI Village as a walkable toy town.
// Data: data/index.json and data/days/<date>.json from extract.py; player-card notes load lazily from
// data/days/<date>/<agent>.json. Scenery: town.js. Models: Kenney CC0 kits in assets/.
// Modules: core.js (helpers, index, replay state, the loaded day) · scene.js (3D stage, camera, walk mode) · characters.js
// · arcs.js (mention arcs) · plaza.js (Hall of Records) · chat.js · card.js (player card) · portrait.js (its picture)
// · panels.js · town.js · gallery.js.
import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { PLAZA, ROOMS, SPOTS, WALL } from './town.js';
import { gallery } from './gallery.js';
import { $, el, fmt, dur, YMD, longDate, bold, rich, CLAN_COLOR, HUMAN, IX, DAYS, DAY, SEGS, SLUGS, state, keep, setDay, D, M, C, agents,
  END, SLICES, dayGroup, dayPairs, gaps, hm, lowerBound } from './core.js';
import { manager, canvas, renderer, css, scene, camera, controls, HOME, town, flyTo, walker, lib } from './scene.js';
import { ANIM, SKINS, pickables, spawn, play, place } from './characters.js';
import { computeLive, drawBeams } from './arcs.js';
import { METRICS, plaza, buildColumns } from './plaza.js';
import { talk, hallObj, say, feed, chatSync } from './chat.js';
import { select, drawer } from './card.js';
import { tally, roster, initCalendar, infoButton } from './panels.js';

// ---------- controls ----------
const time = $('#time');
const playBtn = $('#play');
const setPlaying = p => { state.playing = p; playBtn.textContent = p ? '❚❚ Pause' : '▶ Play'; };
playBtn.onclick = () => { if (state.v >= END - 1) setV(0, true); setPlaying(!state.playing); };
$('#speed').value = state.speed; // speed and Names are kept across a refresh (core.js state)
$('#speed').onchange = e => { state.speed = +e.target.value; keep('speed', state.speed); };
time.oninput = () => setV(+time.value, true);
$('#names').setAttribute('aria-pressed', state.names);
$('#names').onclick = e => { state.names = !state.names; e.currentTarget.setAttribute('aria-pressed', state.names); keep('names', state.names); };
const stepDay = k => { const d = DAYS[DAY[state.date].k + k]; if (d) loadDay(d.date); };
$('#prevDay').onclick = () => stepDay(-1);
$('#nextDay').onclick = () => stepDay(1);
// browse by goal (the 🎯 Goals button beside the header): while a goal is picked, ◀ ▶ step through its days only
const goals = $('#goals'), span = new Intl.DateTimeFormat('en-US', { ...YMD, timeZone: 'UTC' }), noon = k => new Date(`${DAYS[k].date}T12:00:00Z`);
const pickGoal = k => { state.seg = k; goals.hidePopover(); if (k >= 0) loadDay(DAYS[SEGS[k].a].date); else nav(); };
$('#goalList').append(el('li', {}, el('button', { value: -1, textContent: 'All days', onclick: () => pickGoal(-1) })),
  ...SEGS.map((s, k) => el('li', {}, el('button', { value: k, title: s.goal, onclick: () => pickGoal(k) },
    el('small', { textContent: `${span.formatRange(noon(s.a), noon(s.b))} · ${s.b - s.a + 1} day${s.b > s.a ? 's' : ''}` }), s.goal))));
goals.addEventListener('toggle', e => { // opens under the header like the calendar, at the picked goal
  $('#goalBtn').ariaExpanded = e.newState === 'open';
  if (e.newState !== 'open') return;
  const r = $('#goalBtn').getBoundingClientRect(); // under its button, kept on screen
  Object.assign(goals.style, { top: `${r.bottom + 8}px`, left: `${Math.max(12, Math.min(r.left, innerWidth - goals.offsetWidth - 12))}px` });
  goals.querySelector('[aria-current]')?.scrollIntoView({ block: 'center' });
});
// goal stories (data/goals.json, fetched after the first day: [goal segment, written, 'goal' | 'checkpoint', readable from, text]):
// a hover on a goal shows how its story starts; 📖 in Goals, or a click on the goal under the header or atop the Day recap,
// opens it whole. Like the Career tab, a story is locked before the day it is readable from (a checkpoint: the day it covers up to).
const STORY = {}, spoiled = new Set(), story = $('#story'), daySeg = () => SEGS.findIndex(s => s.a <= DAY[state.date]?.k && DAY[state.date].k <= s.b);
const preview = k => { // undefined: no story
  const e = STORY[k]?.find(e => e[3] <= state.date);
  return STORY[k] && (e ? `📖 ${e[4].replaceAll('**', '').replace(/\s+/g, ' ').slice(0, 300).replace(/\s\S*$/, '…')}` : `📖 🔒 Its story was written ${longDate(STORY[k][0][1], YMD)}, after this day`);
};
function openStory(k) {
  const s = SEGS[k], list = STORY[k];
  if (!list) return;
  $('#storyTitle').textContent = `📖 ${s.goal.replaceAll('**', '')}`;
  $('#storyNote').textContent = `${span.formatRange(noon(s.a), noon(s.b))} · story written ${longDate(list[0][1], YMD)}`;
  $('#storyText').replaceChildren(...list.flatMap(e => [ // the story, then its checkpoints
    ...(e[2] === 'checkpoint' ? [el('h3', { textContent: `📍 Checkpoint: the story up to ${longDate(e[3], YMD)}` })] : []),
    ...(e[3] > state.date && !spoiled.has(e) ? [el('div', { className: 'lock' }, el('div', { className: 'big', textContent: '🔒' }),
      el('p', {}, el('b', { textContent: `Written ${longDate(e[1], YMD)}` }), ', after this day.'),
      el('button', { className: 'btn alt', textContent: 'Show anyway?', onclick: () => { spoiled.add(e); openStory(k); } }))] : rich(e[4]))]));
  if (!story.open) story.showModal();
}
$('#storyClose').onclick = () => story.close();
story.onclick = e => { if (e.target === story) story.close(); }; // the backdrop belongs to the dialog itself
$('#goalNow').onclick = () => openStory(state.seg);
$('#recap').onclick = e => { if (e.target.closest('.goal')) openStory(daySeg()); };
function nav() { // ◀ ▶, the goal picker, goal story previews and the URL follow the loaded day and the goal filter
  const k = DAY[state.date]?.k, s = SEGS[state.seg], g = $('#recap .goal');
  $('#prevDay').disabled = !(k > (s ? s.a : 0));
  $('#nextDay').disabled = !(k < (s ? s.b : DAYS.length - 1));
  for (const b of $('#goalList').querySelectorAll('button[value]')) Object.assign(b, { ariaCurrent: +b.value === state.seg ? 'true' : null, title: preview(+b.value) || SEGS[b.value]?.goal || '' });
  Object.assign($('#goalBtn'), { ariaPressed: !!s, title: s ? `Goal: ${s.goal}` : 'Browse the village by goal' });
  Object.assign($('#goalNow'), { textContent: s ? `🎯 ${s.goal}` : '', title: s ? preview(state.seg) || s.goal : '', className: STORY[state.seg] ? 'story' : '' });
  if (g) Object.assign(g, { title: preview(daySeg()) || '', className: STORY[daySeg()] ? 'goal story' : 'goal' });
  const u = new URL(location);
  u.searchParams.set('date', state.date);
  if (s) u.searchParams.set('goal', state.seg); else u.searchParams.delete('goal');
  history.replaceState(null, '', u);
}
addEventListener('keydown', e => {
  if (e.target.closest?.('input, select, button, dialog, [popover]') || walker.isLocked) return; // buttons handle Space themselves
  if (e.code === 'Space') { e.preventDefault(); playBtn.click(); }
  if (e.code === 'ArrowRight' || e.code === 'ArrowLeft') setV(state.v + (e.code === 'ArrowRight' ? 900 : -900), true);
  if (e.code === 'Escape') select(null);
});

// ---------- the clock ----------
function setV(v, jump) {
  state.v = Math.max(0, Math.min(END - 1, v));
  if (state.v >= END - 1) setPlaying(false);
  const s = Math.min(SLICES - 1, Math.floor(state.v / D.slice));
  if (jump) {
    state.mp = lowerBound(state.v + 1, C);
    talk.hallUntil = 0;
    for (const a of agents) { a.bubbleObj.visible = false; a.fp = 0; a.puffUntil = 0; a.talk = null; }
  }
  for (const a of agents) { // ❗ when the playing clock passes failed actions, one puff per frame; jumps only move the pointer
    const k = a.fp;
    while (a.fp < a.fails.length && a.fails[a.fp] <= state.v) a.fp++;
    if (a.fp > k && !jump) { a.puff.textContent = '❗'; a.puffUntil = performance.now() + 1200; }
  }
  if (s !== state.slice || jump) {
    state.slice = s;
    place(s, jump);
    computeLive(state.v);
    slowUi();
  }
  let fresh = false;
  while (state.mp < C.length && C[state.mp][0] <= state.v) { say(C[state.mp]); state.mp++; fresh = true; }
  if (fresh || jump) { computeLive(state.v); feed(); chatSync(); } // arcs appear the moment a mention is made
  $('#clock').textContent = `${longDate(state.date)} · ${hm(state.v)} PT`;
  if (!time.matches(':active')) time.value = Math.floor(state.v);
}

function slowUi() { // once per slice
  tally();
  if (state.sel !== null && (state.tab === 'today' || state.tab === 'td')) drawer(false);
}

gallery({ scene, state, IX, el, fmt, longDate, YMD, CLAN_COLOR });
initCalendar(loadDay);

// ---------- day loading ----------
let loadTok = 0;
function unloadDay() {
  if (!dayGroup) return;
  scene.remove(dayGroup);
  dayGroup.traverse(o => { o.element?.remove(); if (o.userData.own) o.geometry.dispose(); }); // CSS2D labels leave the DOM
  for (const a of agents) { a.gone = true; a.mixer?.stopAllAction(); a.mat?.map.dispose(); a.mat?.dispose(); } // model geometry is shared, kept
  pickables.length = 0;
}
async function loadDay(date) {
  const tok = ++loadTok, busy = $('#busy');
  busy.replaceChildren(`Loading ${longDate(date, YMD)}…`, el('i'));
  busy.hidden = false;
  let nd;
  try {
    const r = await fetch(`data/days/${date}.json`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    nd = await r.json();
  } catch (err) {
    if (tok === loadTok) {
      busy.textContent = `Couldn't load ${date} (${err.message})`;
      setTimeout(() => { if (tok === loadTok) busy.hidden = true; }, 4000);
    }
    return false;
  }
  if (tok !== loadTok) return false; // a newer pick won
  busy.hidden = true;
  const keep = agents[state.sel]?.slug;
  unloadDay();
  setDay({ D: nd, M: nd.messages, END: nd.hours * 3600, SLICES: Math.ceil(nd.hours * 3600 / nd.slice), dayGroup: new THREE.Group() });
  state.date = date;
  scene.add(dayGroup);
  setDay({ agents: D.agents.map((a, i) => ({ ...a, i, joined: IX.agents[a.slug]?.joined || a.joined || date, color: CLAN_COLOR[a.clan] || '#8a7a66', msgs: [], skin: (SLUGS.indexOf(a.slug) + SKINS.length) % SKINS.length,
    bashAt: Object.keys(a.bash).map(Number).sort((x, y) => x - y) })) });
  M.forEach((m, k) => agents[m[1]].msgs.push(k));
  for (const a of agents) a.chats = [...a.enter, ...a.msgs.map(k => [M[k][0], M[k][4]])].sort((x, y) => x[0] - y[0]); // [v, room]
  setDay({ C: [...M, ...(D.human || []).map(([v, name, text, to, room]) => [v, HUMAN, text, to, room, name]), // see C at the top
    ...(D.asks || []).map(([v, i, icon, text, room]) => [v, i, `${icon} ${text}`, [], room, icon])].sort((x, y) => x[0] - y[0]) });
  // quiet stretches (>= 30 min with no action and no chat, e.g. between two sessions) are skipped while playing
  const lively = Array.from({ length: SLICES }, (_, s) => agents.some(a => 'WTHL'.includes(a.track[s] || '-')));
  for (const m of M) lively[Math.floor(m[0] / D.slice)] = true;
  setDay({ gaps: [] });
  for (let s = 0, q = -1; s <= SLICES; s++) {
    if (s < SLICES && !lively[s]) { if (q < 0) q = s; continue; }
    if (q >= 0 && s - q >= 6) gaps.push([q, s]);
    q = -1;
  }
  setDay({ dayPairs: new Map() });
  for (const [, s, , to] of M) for (const d of to) dayPairs.set(s * 64 + d, (dayPairs.get(s * 64 + d) || 0) + 1);
  agents.forEach(spawn);
  buildColumns();
  setDay({ roomSigns: D.rooms.slice(1, ROOMS.length + 1).map((name, k) => { // a market stall per side chat room, gone with the day
    const r = ROOMS[k], ry = Math.atan2(r.yard[0] - r.at[0], r.yard[1] - r.at[1]); // the stall faces its yard
    for (const [m, dx, s] of [[k % 2 ? 'town/stall-red' : 'town/stall-green', 0, 1.8], ['town/stall-bench', -1.9, 1.8], ['town/lantern', 1.7, 1.6]]) {
      const o = lib(m);
      o.position.set(r.at[0] + Math.cos(ry) * dx, 0, r.at[1] - Math.sin(ry) * dx);
      o.rotation.y = ry; o.scale.setScalar(s);
      dayGroup.add(o);
    }
    const e = el('div', { className: 'sign', title: `Chat room #${name}` }, `💬 #${name}`, el('b'), infoButton('Chat rooms'));
    e.onclick = () => flyTo(new THREE.Vector3(r.yard[0], 0, r.yard[1]), 16);
    const o = new CSS2DObject(e);
    o.position.set(r.at[0], r.sign, r.at[1]);
    dayGroup.add(o);
    return e;
  }) });
  for (const s of [$('#roomPick'), $('#chatRoom')]) {
    s.disabled = D.rooms.length < 2; // always there, greyed out on days with only #general
    s.title = s.disabled ? 'Only #general this day' : 'Filter the chat by room';
    s.replaceChildren(...['All rooms', ...D.rooms.map(r => `#${r}`)].map((t, k) => el('option', { value: k - 1, textContent: t })));
  }
  state.room = state.who = -1;

  const n = DAY[date]?.day ?? D.day;
  $('#dayNo').textContent = `Day ${n} · `;
  document.title = `AI Village · Day ${n} · ${longDate(date, YMD)}`;
  $('#recap').replaceChildren(el('div', { className: 'goal' }, el('b', { textContent: 'Village goal: ' }), ...bold(D.goal || DAY[date]?.goal || 'none recorded')),
    ...(D.recap ? rich(D.recap) : [el('p', { className: 'empty', textContent: 'No recap was written for this day.' })]));
  if (state.seg >= 0) state.seg = daySeg(); // a day outside the goal filter switches to its goal
  nav();
  time.max = END - 1;
  $('#ticks').replaceChildren(...Array.from({ length: Math.ceil(D.hours) }, (_, h) =>
    Object.assign(el('span', { textContent: hm(h * 3600) }), { style: `left:${(100 * h * 3600) / END}%` })));

  state.slice = -1; state.sel = null; state.open.clear();
  roster();
  setV(0, true);
  select(agents.find(a => a.slug === keep)?.i ?? null); // follow the same player across days
  return true;
}

// ---------- picking, hover, camera ----------
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), tip = $('#tip');
function pick(x, y) {
  ndc.set((x / innerWidth) * 2 - 1, -(y / innerHeight) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObjects([...pickables.filter(o => agents[o.userData.agent].root.visible), ...(plaza.mesh ? [plaza.mesh] : [])], false)[0];
  if (!hit) return null;
  return hit.object === plaza.mesh ? { col: plaza.cols[plaza.inst[hit.instanceId]] } : { agent: agents[hit.object.userData.agent] };
}
let down = null;
canvas.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
canvas.addEventListener('pointerup', e => {
  if (walker.isLocked || !down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
  const h = pick(e.clientX, e.clientY);
  select(h ? (h.agent || h.col.a).i : null);
});
canvas.addEventListener('pointermove', e => {
  if (walker.isLocked || e.buttons) { tip.style.display = 'none'; return; }
  const h = pick(e.clientX, e.clientY);
  canvas.style.cursor = h ? 'pointer' : '';
  if (!h) { tip.style.display = 'none'; return; }
  const a = h.agent || h.col.a;
  tip.replaceChildren(el('b', { textContent: a.name }), el('br'),
    h.col ? `${METRICS[+$('#metric').value][0]}: ${fmt(h.col.value)}` : `${a.role || a.clan} · ${a.where === '-' ? '' : SPOTS[a.where].name}`);
  Object.assign(tip.style, { display: 'block', left: `${e.clientX + 14}px`, top: `${e.clientY + 14}px` });
});

const keys = new Set();
addEventListener('keydown', e => keys.add(e.code));
addEventListener('keyup', e => keys.delete(e.code));
document.addEventListener('mousedown', () => {
  if (!walker.isLocked) return;
  const h = pick(innerWidth / 2, innerHeight / 2);
  if (h) select((h.agent || h.col.a).i);
});

// ---------- first day, then the main loop ----------
const q = new URLSearchParams(location.search), want = q.get('date');
if (SEGS[q.get('goal')]) state.seg = +q.get('goal'); // ?goal= alone opens the goal's first day; with a date, the date wins
if (!(await loadDay(DAY[want] ? want : state.seg >= 0 ? DAYS[SEGS[state.seg].a].date : DAYS.at(-1).date))) {
  $('#loadmsg').textContent = $('#busy').textContent;
  throw new Error('first day failed to load');
}
fetch('data/goals.json').then(r => r.json()).then(rows => { // the goal stories, then 📖 on each goal in Goals that has one
  for (const e of rows) (STORY[e[0]] ||= []).push(e);
  for (const k in STORY) $('#goalList').children[+k + 1].append(el('button', { className: 'read', textContent: '📖', title: 'Read the story of this goal', ariaLabel: `Read the story of: ${SEGS[k].goal}`, onclick: () => openStory(+k) }));
  nav();
}).catch(() => {}); // none built yet: goals without stories
const timer = new THREE.Timer();
const face = new THREE.Vector3();
renderer.setAnimationLoop(t => {
  timer.update(t);
  const dt = Math.min(timer.getDelta(), 0.1), now = performance.now();
  if (state.playing) setV(state.v + dt * state.speed, false);
  const gap = state.playing && gaps.find(([a, b]) => state.slice >= a && state.slice < b);
  if (gap) {
    setV(gap[1] * D.slice, true);
    const b = $('#busy');
    b.textContent = `Skipped a quiet stretch, ${hm(gap[0] * D.slice)}–${hm(gap[1] * D.slice)} PT`;
    b.hidden = false;
    setTimeout(() => { if (b.textContent.startsWith('Skipped')) b.hidden = true; }, 2500);
  }
  const left = state.playing ? ((state.slice + 1) * D.slice - state.v) / state.speed : 1.5; // real seconds to the next slice
  for (const a of agents) if (a.talk?.until <= now) { a.talk = null; talk.regroup = true; } // said its line: back to work
  if (talk.regroup) { talk.regroup = false; place(state.slice, false); tally(); }

  for (const a of agents) {
    if (!a.target) { a.mixer?.update(dt); continue; }
    const p = a.root.position, dx = a.target.pos.x - p.x, dz = a.target.pos.z - p.z, d = Math.hypot(dx, dz);
    let yaw;
    if (d > 0.04) {
      const speed = Math.max(2.4, d / Math.max(0.25, (a.talk ? Math.min(left, 0.8) : left) * 0.8)); // talkers hurry over
      const step = Math.min(d, speed * dt);
      p.x += (dx / d) * step; p.z += (dz / d) * step;
      yaw = Math.atan2(dx, dz);
      play(a, speed > 7 ? 'sprint' : 'walk');
    } else {
      face.copy(a.target.look).sub(p);
      yaw = Math.atan2(face.x, face.z);
      play(a, ANIM[a.where]);
    }
    a.yaw += Math.atan2(Math.sin(yaw - a.yaw), Math.cos(yaw - a.yaw)) * Math.min(1, dt * 10);
    a.root.rotation.y = a.yaw;
    a.mixer?.update(dt);
    // bubbles and the 💤 countdown only up close (or for the selected agent), the overview stays readable;
    // ❗ and a bare 💤 show from any distance, like the name tags
    const close = state.names && (a.i === state.sel || camera.position.distanceTo(a.root.position) < 26);
    a.bubbleObj.visible = close && now < (a.bubbleUntil || 0);
    a.puffObj.visible = state.names && now < a.puffUntil;
    const pz = state.names && a.pauses.findLast(x => x[0] <= state.v), due = pz && pz[0] + pz[1] - state.v;
    a.zzzObj.visible = due > 0;
    if (due > 0) a.zzz.textContent = close ? dur(due) : ''; // 💤 is its ::before
    a.tagObj.visible = state.names;
  }
  hallObj.visible = state.names && now < talk.hallUntil; // from any distance: humans have no other sign in town
  town.tick(now / 1000, agents.filter(a => a.where === 'W').length);
  drawBeams();

  const near = camera.position.distanceTo(new THREE.Vector3(PLAZA[0], 0, PLAZA[1])) < 48;
  for (const c of plaza.cols) c.obj.visible = near;

  if (walker.isLocked) {
    const run = keys.has('ShiftLeft') || keys.has('ShiftRight') ? 14 : 6;
    const f = (keys.has('KeyW') || keys.has('ArrowUp')) - (keys.has('KeyS') || keys.has('ArrowDown'));
    const r = (keys.has('KeyD') || keys.has('ArrowRight')) - (keys.has('KeyA') || keys.has('ArrowLeft'));
    walker.moveForward(f * run * dt);
    walker.moveRight(r * run * dt);
    camera.position.clamp(new THREE.Vector3(-WALL - 25, 1.5, -WALL - 25), new THREE.Vector3(WALL + 25, 1.5, WALL + 25));
  } else {
    if (state.fly) {
      const u = Math.min(1, (state.fly.t += dt / 0.9)), e = u * u * (3 - 2 * u);
      controls.target.lerpVectors(state.fly.t0, state.fly.t1, e);
      camera.position.lerpVectors(state.fly.c0, state.fly.c1, e);
      if (u === 1) state.fly = null;
    }
    controls.update(dt);
  }
  renderer.render(scene, camera);
  css.render(scene, camera);
});

manager.onLoad = () => $('#loading')?.remove();
setPlaying(true);
window.village = { state, get agents() { return agents; }, setV, select, flyTo, loadDay, camera, controls, HOME }; // handy from the console
