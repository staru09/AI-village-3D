// AI Village 3D: replays any day of the AI Village as a walkable toy town.
// Data: data/index.json and data/days/<date>.json from extract.py; player-card notes load lazily from
// data/days/<date>/<agent>.json. Scenery: town.js. Models: Kenney CC0 kits in assets/.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MapControls } from 'three/addons/controls/MapControls.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { buildTown, camps, SPOTS, PLAZA, WALL, ROOMS } from './town.js';
import { gallery } from './gallery.js';

// Validated categorical palette (dataviz reference, slot order); colour follows the clan, never its rank.
const CLAN_COLOR = { Google: '#2a78d6', Anthropic: '#eb6834', OpenAI: '#1baf7a', Zhipu: '#eda100',
  Moonshot: '#e87ba4', xAI: '#008300', DeepSeek: '#4a3aa7', Meta: '#e34948' };
const ANIM = { W: 'interact-right', T: 'interact-left', H: 'emote-yes', L: 'pick-up', C: 'sit' };
const SKINS = 'abcdefghijklmnopqr';
const CH = 0.38; // character scale: 2.7-unit Kenney figures become ~1 unit, toy-sized next to the houses
const GATE = new THREE.Vector3(0, 0, WALL + 3);

const $ = s => document.querySelector(s);
const el = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); e.append(...kids); return e; };
const pct = (a, b) => (b ? Math.round(100 * (a || 0) / b) : 0);
const count = (s, ch) => s.split(ch).length - 1;
const fmt = n => n.toLocaleString('en-US');
const dur = s => (s < 60 ? `${Math.ceil(s)} s` : s < 3600 ? `${Math.round(s / 60)} min` : `${+(s / 3600).toFixed(1)} h`);
const pad = n => String(n).padStart(2, '0');
const YMD = { day: 'numeric', month: 'short', year: 'numeric' };
const longDate = (d, o = { weekday: 'short', day: 'numeric', month: 'short' }) => new Date(`${d.slice(0, 10)}T12:00:00Z`).toLocaleDateString('en-US', { ...o, timeZone: 'UTC' });
// Dataset text stays text: **bold** becomes <b> by splitting, never through innerHTML.
const bold = t => t.split('**').map((s, k) => (k % 2 ? el('b', { textContent: s }) : s));
const rich = t => t.split(/\n\s*\n/).map(p => el('p', {}, ...bold(p)));

// ---------- loading ----------
const manager = new THREE.LoadingManager();
manager.onProgress = (_, done, total) => { const bar = $('#loadbar i'); if (bar) bar.style.width = `${(100 * done) / total}%`; };
const loader = new GLTFLoader(manager);
const gltfs = new Map();
const gltf = url => { if (!gltfs.has(url)) gltfs.set(url, loader.loadAsync(url)); return gltfs.get(url); };
const shade = o => { if (o.isMesh) o.castShadow = o.receiveShadow = true; };
function lib(name, fix) { // a placeholder group that fills in when the model arrives
  const g = new THREE.Group();
  gltf(`assets/${name}.glb`).then(m => { const o = m.scene.clone(); o.traverse(shade); fix?.(o); g.add(o); });
  return g;
}

let IX;
try {
  IX = await (await fetch('data/index.json')).json();
} catch {
  $('#loadmsg').replaceChildren('No data/index.json yet. Build it from the AI Village dataset, then serve this folder:',
    el('pre', { textContent: 'cd village-3d\npython3 extract.py\npython3 -m http.server 8000\n# open http://localhost:8000' }));
  throw new Error('data/index.json missing');
}
await document.fonts.load('28px "Lilita One"');

const DAYS = IX.days, DAY = Object.fromEntries(DAYS.map((d, k) => [d.date, { ...d, k }]));
const SLUGS = Object.keys(IX.agents);
const clans = IX.clans.map(name => ({ name, color: CLAN_COLOR[name] || '#8a7a66' }));
// The loaded day; everything below that reads these is rebuilt by loadDay(). M: agent messages [v, agent, text, mentioned, room];
// C: what the chat shows, M plus human messages and requests to humans, [v, agent or HUMAN, text, mentioned, room, name or icon].
const HUMAN = -2; // a human line's sender, and the #chat filter's "Humans" option (-1 is everyone)
let D, M = [], C = [], agents = [], END = 1, SLICES = 1, dayPairs = new Map(), dayGroup = null, gaps = [], roomSigns = [];

// ---------- scene ----------
const canvas = $('#stage');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
const css = new CSS2DRenderer({ element: $('#labels') });
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xcdeeff, 90, 200);
scene.add(new THREE.HemisphereLight(0xeaf6ff, 0x5b7d31, 1.7));
const sun = new THREE.DirectionalLight(0xfff0d8, 2.9);
sun.position.set(-30, 52, 34);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -44, right: 44, top: 44, bottom: -44, near: 1, far: 150 });
sun.shadow.bias = -0.0005;
sun.shadow.normalBias = 0.03;
scene.add(sun);

const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 600);
const HOME = { pos: new THREE.Vector3(24, 36, 64), target: new THREE.Vector3(0, 0, 4) };
camera.position.copy(HOME.pos);
const controls = new MapControls(camera, canvas);
controls.target.copy(HOME.target);
Object.assign(controls, { enableDamping: true, maxPolarAngle: 1.3, minDistance: 5, maxDistance: 140, zoomToCursor: true });

const town = buildTown(scene, lib, clans); // built once, with a camp for every clan of the whole run
const campFire = Object.fromEntries(camps(clans.length).map(([x, z], i) => [clans[i].name, new THREE.Vector3(x, 0, z + 0.4)]));

// ---------- characters ----------
function paintSkin(orig, color, text) {
  // Kenney blocky skins share one UV layout: torso cross bottom-left, sleeves top of each arm block.
  // The repainted texture clones the original to keep its glTF sampler settings, with its own image source.
  const img = orig.image, c = el('canvas', { width: 512, height: 512 }), g = c.getContext('2d'), k = 0.5;
  g.drawImage(img, 0, 0, 512, 512);
  const shirt = [[0, 688, 448, 336], [480, 534, 64, 64], [480, 598, 256, 107], [768, 534, 64, 64], [768, 598, 256, 107]];
  g.fillStyle = color;
  for (const r of shirt) g.fillRect(...r.map(v => v * k));
  g.globalAlpha = 0.28;
  g.globalCompositeOperation = 'luminosity'; // keep a hint of the original pockets and belts
  for (const r of shirt) g.drawImage(img, ...r, ...r.map(v => v * k));
  g.globalAlpha = 1;
  g.globalCompositeOperation = 'source-over';
  g.font = `${text.length > 3 ? 21 : 27}px "Lilita One"`; // chest print on the torso front face
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineWidth = 5; g.strokeStyle = 'rgba(40,20,5,.7)'; g.fillStyle = '#fff';
  g.strokeText(text, 80, 420); g.fillText(text, 80, 420);
  const t = orig.clone();
  t.source = new THREE.TextureSource(c);
  t.needsUpdate = true;
  return t;
}

const pickables = [];
function spawn(a) {
  a.root = new THREE.Group();
  a.root.visible = false;
  dayGroup.add(a.root);
  gltf(`assets/characters/character-${SKINS[a.skin]}.glb`).then(m => {
    if (a.gone) return; // the day changed while the model loaded
    const body = m.scene.clone();
    let orig;
    body.traverse(o => { if (o.isMesh) orig ||= o.material.map; });
    a.mat = new THREE.MeshStandardMaterial({ map: paintSkin(orig, a.color, a.label), roughness: 0.42 }); // shiny toy plastic
    body.traverse(o => { if (o.isMesh) { o.material = a.mat; o.castShadow = true; o.userData.agent = a.i; pickables.push(o); } });
    body.scale.setScalar(CH);
    a.root.add(body);
    a.mixer = new THREE.AnimationMixer(body);
    a.clips = Object.fromEntries(m.animations.map(c => [c.name, a.mixer.clipAction(c)]));
    a.anim = null;
    play(a, a.want || 'idle');
  });
  const tag = el('div', { className: 'tag', textContent: a.label, title: `${a.name} · ${a.role || a.clan}` });
  tag.style.background = a.color;
  tag.onclick = () => select(a.i);
  a.tag = tag;
  a.tagObj = new CSS2DObject(tag);
  a.tagObj.position.y = 1.2;
  a.bubble = el('div'); // inside the label, so it can pop without fighting CSS2D's transform
  a.bubble.onclick = () => select(a.i);
  a.bubbleObj = new CSS2DObject(el('div', { className: 'bubble' }, a.bubble));
  a.bubbleObj.position.y = 1.2;
  a.bubbleObj.visible = false;
  a.puff = el('b'); // ❗ a failed action, or the icon of a request to humans
  a.puffObj = new CSS2DObject(el('div', { className: 'puff' }, a.puff));
  a.zzz = el('div', { className: 'zzz' }); // pause timer
  a.zzzObj = new CSS2DObject(a.zzz);
  a.puffObj.position.y = a.zzzObj.position.y = 1.2;
  a.puffObj.visible = a.zzzObj.visible = false;
  a.root.add(a.tagObj, a.bubbleObj, a.puffObj, a.zzzObj);
  a.yaw = 0;
}

function play(a, name) {
  a.want = name;
  if (!a.clips || a.anim === name) return;
  a.clips[name].reset().fadeIn(0.25).play();
  a.clips[a.anim]?.fadeOut(0.25);
  a.anim = name;
}

// Agents at the same place stand in a sunflower spiral in the building's yard (or their chat room's), or sit in a ring at their clan's fire.
function slotOf(a, k, n) {
  if (a.where === 'C') {
    const f = campFire[a.clan], th = -2.2 + (4.4 * (k + 0.5)) / n, r = 1.35 + n * 0.06;
    return { pos: new THREE.Vector3(f.x + Math.sin(th) * r, 0, f.z + Math.cos(th) * r), look: f };
  }
  const s = (a.where === 'H' && ROOMS[a.room - 1]) || SPOTS[a.where], r = 0.95 * Math.sqrt(k + 0.5), th = k * 2.39996;
  return { pos: new THREE.Vector3(s.yard[0] + Math.cos(th) * r, 0, s.yard[1] + Math.sin(th) * r), look: new THREE.Vector3(s.at[0], 0, s.at[1]) };
}

function place(slice, jump) {
  const groups = {}, end = (slice + 1) * D.slice, now = performance.now();
  for (const a of agents) {
    const talk = a.talk?.until > now && a.track[slice] !== '-'; // just posted: over at the Town Hall or its room's stall
    a.where = talk ? 'H' : a.track[slice] || '-';
    a.room = talk ? a.talk.room : a.chats.findLast(e => e[0] < end)?.[1] || 0; // else its latest message or room move in this slice
    a.spot = a.where === 'H' && a.room ? `H${a.room}` : a.where;
    if (a.where === '-') { a.root.visible = false; a.target = null; continue; }
    if (!a.root.visible) { a.root.visible = true; a.root.position.copy(GATE); } // newcomers walk in through the gate
    (groups[a.where === 'C' ? `C${a.clan}` : a.spot] ||= []).push(a);
  }
  for (const list of Object.values(groups)) list.forEach((a, k) => { a.target = slotOf(a, k, list.length); });
  if (jump) for (const a of agents) if (a.target) a.root.position.copy(a.target.pos);
}

// ---------- mention arcs ----------
const beamMats = [2, 3.5, 6].map(w => new LineMaterial({ linewidth: w, vertexColors: true, transparent: true, opacity: 0.92, depthWrite: false }));
const beams = beamMats.map(m => { const l = new LineSegments2(new LineSegmentsGeometry(), m); l.frustumCulled = false; l.renderOrder = 2; scene.add(l); return l; });
let livePairs = new Map();
function computeLive(v) { // mentions in the last village hour
  livePairs = new Map();
  for (let k = lowerBound(v - 3600); k < M.length && M[k][0] <= v; k++)
    for (const d of M[k][3]) livePairs.set(M[k][1] * 64 + d, (livePairs.get(M[k][1] * 64 + d) || 0) + 1);
}
const cA = new THREE.Color(), cB = new THREE.Color(), white = new THREE.Color('#fff'), P0 = new THREE.Vector3(), P1 = new THREE.Vector3(), Q = new THREE.Vector3();
function drawBeams() {
  const mode = +$('#beams').value;
  const pairs = mode === 1 ? livePairs : mode === 2 ? dayPairs : new Map();
  const cut = mode === 1 ? [1, 2, 4] : [1, 6, 20]; // mention-count buckets -> line width
  const buf = [[], [], []], col = [[], [], []];
  for (const [key, n] of pairs) {
    const s = agents[Math.floor(key / 64)], d = agents[key % 64];
    if (state.sel !== null && s.i !== state.sel && d.i !== state.sel) continue;
    if (!s.root.visible || !d.root.visible) continue;
    const b = n >= cut[2] ? 2 : n >= cut[1] ? 1 : 0;
    P0.copy(s.root.position).setY(1.05); P1.copy(d.root.position).setY(1.05);
    const lift = 1.2 + P0.distanceTo(P1) * 0.28;
    cA.set(s.color); cB.copy(cA).lerp(white, 0.55); // lightens toward the mentioned agent: direction
    let prev = P0.clone();
    for (let t = 1; t <= 14; t++) {
      const u = t / 14;
      Q.lerpVectors(P0, P1, u).setY(Q.y + Math.sin(Math.PI * u) * lift);
      buf[b].push(prev.x, prev.y, prev.z, Q.x, Q.y, Q.z);
      const c0 = cA.clone().lerp(cB, (t - 1) / 14), c1 = cA.clone().lerp(cB, u);
      col[b].push(c0.r, c0.g, c0.b, c1.r, c1.g, c1.b);
      prev = Q.clone();
    }
  }
  beams.forEach((l, b) => {
    l.visible = buf[b].length > 0;
    if (!l.visible) return;
    l.geometry.dispose();
    l.geometry = new LineSegmentsGeometry().setPositions(buf[b]).setColors(col[b]);
  });
}

// ---------- stats plaza: one LEGO brick column per agent ----------
const METRICS = [
  ['Computer actions', a => a.stats.turns || 0],
  ['Chat messages', a => a.stats.messages || 0],
  ['Times mentioned by others', a => a.stats.mentions_in || 0],
  ['Mentions of others', a => a.stats.mentions_out || 0],
  ['Bash share of actions (%)', a => pct(a.stats.W, a.stats.turns)],
  ['Actions with errors (%)', a => pct(a.stats.errors, a.stats.turns)],
  ['Time idle at camp (%)', a => pct(count(a.track, 'C'), SLICES - count(a.track, '-'))],
  ['Memory consolidations', a => a.stats.memory || 0],
];
$('#metric').append(...METRICS.map(([n], i) => el('option', { value: i, textContent: n })));
const MAXB = 12, BS = 5.2; // bricks per full column, brick scale
const plaza = { cols: [] };
const riserMat = new THREE.MeshStandardMaterial({ color: 0xcfc3a8, roughness: 0.95 });
{
  const sign = el('div', { className: 'sign', textContent: '🧱 Hall of Records', title: 'One LEGO column per agent; pick the measure under "Plaza"' });
  sign.onclick = () => flyTo(new THREE.Vector3(PLAZA[0], 0, PLAZA[1]), 22);
  plaza.sign = new CSS2DObject(sign);
  plaza.sign.position.set(PLAZA[0] - 3, 8, PLAZA[1] - 5.5);
  scene.add(plaza.sign);
  gltf('assets/bricks/bevel-hq-brick-2x2.glb').then(m => {
    let geo;
    m.scene.traverse(o => { if (o.isMesh) geo = o.geometry; });
    geo.computeBoundingBox();
    plaza.step = (geo.boundingBox.max.y - geo.boundingBox.min.y) * BS * 0.84; // studs nest into the brick above
    plaza.mesh = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ roughness: 0.3 }), SLUGS.length * MAXB); // room for every agent of the run
    plaza.mesh.castShadow = plaza.mesh.receiveShadow = true;
    scene.add(plaza.mesh);
    buildPlaza();
  });
}
function buildColumns() { // per day; risers and labels live in dayGroup
  plaza.cols = [];
  // rows: clans by size, next-fit so a clan never splits across rows
  const bySize = clans.map(c => ({ ...c, list: agents.filter(a => a.clan === c.name) })).filter(c => c.list.length).sort((x, y) => y.list.length - x.list.length);
  const rows = [[]];
  for (const c of bySize) {
    if (rows.at(-1).length && rows.at(-1).reduce((n, g) => n + g.list.length, 0) + c.list.length > 12) rows.push([]);
    rows.at(-1).push(c);
  }
  rows.forEach((row, r) => {
    const z = PLAZA[1] + 3.3 - r * 3.3, y = r * 0.75;
    const n = row.reduce((s, g) => s + g.list.length, 0), w = n * 1.1 + (row.length - 1) * 0.5;
    const riser = new THREE.Mesh(new THREE.BoxGeometry(w + 1.2, y + 0.16, 2.4), riserMat);
    riser.position.set(PLAZA[0], (y + 0.16) / 2, z);
    riser.castShadow = riser.receiveShadow = true;
    riser.userData.own = true;
    dayGroup.add(riser);
    let x = PLAZA[0] - w / 2 + 0.55;
    for (const g of row) {
      for (const a of g.list) {
        const lab = el('div', { className: 'col-label' });
        const obj = new CSS2DObject(lab);
        dayGroup.add(obj);
        plaza.cols.push({ a, x, z, y: y + 0.16, lab, obj });
        x += 1.1;
      }
      x += 0.5;
    }
  });
  buildPlaza();
}
function buildPlaza() {
  if (!plaza.mesh) return;
  const [name, f] = METRICS[+$('#metric').value];
  const vals = plaza.cols.map(c => f(c.a)), max = Math.max(1, ...vals);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(BS, BS, BS), p = new THREE.Vector3(), col = new THREE.Color();
  let n = 0;
  plaza.inst = [];
  plaza.cols.forEach((c, i) => {
    const bricks = vals[i] ? Math.max(1, Math.round((vals[i] / max) * MAXB)) : 0;
    for (let b = 0; b < bricks; b++, n++) {
      plaza.mesh.setMatrixAt(n, m4.compose(p.set(c.x, c.y + b * plaza.step, c.z), q, s));
      plaza.mesh.setColorAt(n, col.set(c.a.color).offsetHSL(0, 0, b % 2 ? 0.035 : 0));
      plaza.inst[n] = i;
    }
    c.value = vals[i];
    c.lab.replaceChildren(c.a.label, el('small', { textContent: fmt(vals[i]) + (name.includes('%') ? '%' : '') }));
    c.obj.position.set(c.x, c.y + bricks * plaza.step + 0.55, c.z);
  });
  plaza.mesh.count = n;
  plaza.mesh.instanceMatrix.needsUpdate = true;
  if (plaza.mesh.instanceColor) plaza.mesh.instanceColor.needsUpdate = true;
  plaza.mesh.computeBoundingSphere();
}

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
// humans have no character in town: their messages pop up over the Town Hall's sign
const hallSay = el('div', { onclick: () => openChat() }), hallObj = new CSS2DObject(el('div', { className: 'bubble' }, hallSay));
hallObj.position.set(SPOTS.H.at[0], SPOTS.H.sign, SPOTS.H.at[1]);
hallObj.visible = false;
scene.add(hallObj);

// ---------- UI ----------
const state = { v: 0, slice: -1, playing: true, speed: 300, sel: null, mp: 0, fly: null, names: true, tab: 'today', clan: null, open: new Set() };
const hm = v => { const m = Math.round(D.open * 60) + Math.floor(v / 60); return `${pad(Math.floor(m / 60) % 24)}:${pad(m % 60)}`; };
function lowerBound(v, A = M) { let lo = 0, hi = A.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (A[mid][0] < v) lo = mid + 1; else hi = mid; } return lo; }

const time = $('#time');
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

const playBtn = $('#play');
const setPlaying = p => { state.playing = p; playBtn.textContent = p ? '❚❚ Pause' : '▶ Play'; };
playBtn.onclick = () => { if (state.v >= END - 1) setV(0, true); setPlaying(!state.playing); };
$('#speed').onchange = e => { state.speed = +e.target.value; };
time.oninput = () => setV(+time.value, true);
$('#beams').onchange = () => computeLive(state.v);
$('#metric').onchange = buildPlaza;
$('#plazaBtn').onclick = () => flyTo(new THREE.Vector3(PLAZA[0], 0, PLAZA[1]), 22);
$('#names').onclick = e => { state.names = !state.names; e.currentTarget.setAttribute('aria-pressed', state.names); };
const stepDay = k => { const d = DAYS[DAY[state.date].k + k]; if (d) loadDay(d.date); };
$('#prevDay').onclick = () => stepDay(-1);
$('#nextDay').onclick = () => stepDay(1);
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
addEventListener('keydown', e => {
  if (e.target.closest?.('input, select, button, dialog, [popover]') || walker.isLocked) return; // buttons handle Space themselves
  if (e.code === 'Space') { e.preventDefault(); playBtn.click(); }
  if (e.code === 'ArrowRight' || e.code === 'ArrowLeft') setV(state.v + (e.code === 'ArrowRight' ? 900 : -900), true);
  if (e.code === 'Escape') select(null);
});

function setV(v, jump) {
  state.v = Math.max(0, Math.min(END - 1, v));
  if (state.v >= END - 1) setPlaying(false);
  const s = Math.min(SLICES - 1, Math.floor(state.v / D.slice));
  if (jump) {
    state.mp = lowerBound(state.v + 1, C);
    hallUntil = 0;
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
  if (fresh || jump) { feed(); chatSync(); }
  $('#clock').textContent = `${longDate(state.date)} · ${hm(state.v)} PT`;
  if (!time.matches(':active')) time.value = Math.floor(state.v);
}

// Posting a message sends the agent to the Town Hall (or the message's room stall) for as long as its bubble shows,
// then back to the slice's place: chat rarely wins a whole 5-minute slice against dozens of commands.
// A request to humans pops its icon instead of a bubble; a human's message shows over the Town Hall.
const TALK = 3200;
let regroup = false, hallUntil = 0;
const sender = name => (name === 'automated' ? '⚙️ Village system' : `👤 ${name}`); // humans as posted, the village's notices as itself
function say(m) {
  const a = agents[m[1]], t = m[2].replaceAll('**', ''), now = performance.now();
  const short = t.length > 120 ? `${t.slice(0, 118)}…` : t;
  if (!a) { hallSay.textContent = `${sender(m[5])}: ${short}`; hallUntil = now + TALK; return; }
  if (m[5]) { a.puff.textContent = m[5]; a.puffUntil = now + 1200; } else { a.bubble.textContent = short; a.bubbleUntil = now + TALK; }
  a.talk = { room: m[4], until: now + TALK };
  regroup = true;
}

// ---------- village chat: the latest lines in the panel, the whole day so far in the #chat dialog ----------
const chat = $('#chat'), chatList = $('#chatList'), chatQ = $('#chatQ'), chatWho = $('#chatWho');
let chatM, chatN = 0; // the day the dialog shows and how many of its lines it has gone through
const inRoom = m => state.room < 0 || m[4] === state.room;
function from(a, named = true) { // badge (and name) that opens the player card
  const b = el('button', { className: 'from', title: named ? `${a.name}'s player card` : `Mentions ${a.name}` },
    el('span', { className: 'badge', textContent: a.label }), ...(named ? [el('b', { textContent: a.name })] : []));
  b.style.setProperty('--c', a.color);
  b.onclick = e => { e.stopPropagation(); chat.close(); select(a.i); };
  return b;
}
function line(k, full) { // full: the dialog's row, with all the text and the agents it mentions
  const m = C[k], a = agents[m[1]], to = full ? m[3].map(j => from(agents[j], false)) : [];
  const li = el('li', { className: a ? (m[5] ? 'ask' : '') : 'human' }, el('div', { className: 'meta' }, el('time', { textContent: hm(m[0]) }),
    a ? from(a) : el('b', { className: 'from', textContent: sender(m[5]) }), // a human: no player card
    ...(D.rooms.length > 1 ? [el('small', { textContent: `#${D.rooms[m[4]]}` })] : []), ...(to.length ? ['→', ...to] : [])),
  el('div', { className: 'txt' }, ...bold(full ? m[2] : m[2].slice(0, 300))));
  if (a) li.style.borderLeftColor = a.color;
  li.dataset.k = k;
  if (!full) li.onclick = () => openChat(k);
  return li;
}

function feed() {
  const ks = [];
  for (let k = state.mp - 1; k >= 0 && ks.length < 6; k--) if (inRoom(C[k])) ks.unshift(k);
  $('#feedList').replaceChildren(...(ks.length ? ks.map(k => line(k)) : [el('li', { className: 'empty', textContent: 'No chat yet today.' })]));
}

function chatSync(redraw) { // lines up to the replay clock, never later ones; follows new ones only from the bottom
  if (!chat.open) return;
  if (redraw || chatM !== C || state.mp < chatN) { chatList.replaceChildren(); chatM = C; chatN = 0; }
  const q = chatQ.value.trim().toLowerCase(), end = chatList.scrollHeight - chatList.scrollTop - chatList.clientHeight < 30, rows = [], n = agents.map(() => 0);
  for (; chatN < state.mp; chatN++) {
    const m = C[chatN];
    if (inRoom(m) && (state.who === -1 || m[1] === state.who) && (!q || m[2].toLowerCase().includes(q))) rows.push(line(chatN, true));
  }
  chatList.append(...rows);
  if (end) chatList.scrollTop = chatList.scrollHeight;
  n[HUMAN] = 0;
  for (let k = 0; k < state.mp; k++) n[C[k][1]]++;
  if (document.activeElement !== chatWho) { // counts so far; left alone while someone is picking
    chatWho.replaceChildren(el('option', { value: -1, textContent: 'Everyone' }),
      ...(n[HUMAN] || state.who === HUMAN ? [el('option', { value: HUMAN, textContent: `👤 Humans (${fmt(n[HUMAN])})` })] : []),
      ...agents.filter(a => n[a.i] || a.i === state.who).sort((x, y) => n[y.i] - n[x.i])
        .map(a => el('option', { value: a.i, textContent: `${a.name} (${fmt(n[a.i])})` })));
    chatWho.value = state.who;
  }
  const shown = chatList.childElementCount;
  $('#chatNote').textContent = `${longDate(state.date)}, up to ${hm(state.v)} PT · ${state.room < 0 && state.who === -1 && !q
    ? `${fmt(shown)} message${shown === 1 ? '' : 's'}` : `${fmt(shown)} of ${fmt(state.mp)} match`}`;
}
function openChat(k) { // k: a message to scroll to and highlight
  if (k !== undefined) { chatQ.value = ''; state.who = -1; }
  chat.showModal();
  chatSync(true);
  const li = chatList.querySelector(`[data-k="${k}"]`);
  if (li) { li.classList.add('hit'); li.scrollIntoView({ block: 'center' }); }
}
$('#chatBtn').onclick = () => openChat();
$('#chatClose').onclick = () => chat.close();
chat.onclick = e => { if (e.target === chat) chat.close(); }; // the backdrop belongs to the dialog itself
chatQ.oninput = chatWho.onchange = () => { state.who = +chatWho.value; chatSync(true); };
$('#roomPick').onchange = $('#chatRoom').onchange = e => { // one room filter for the panel and the dialog
  state.room = +e.target.value;
  $('#roomPick').value = $('#chatRoom').value = state.room;
  feed(); chatSync(true);
};

function tally() { // counters and signs: who stands where
  counters.forEach(f => f());
  for (const [k, e] of Object.entries(signs)) e.replaceChildren(`${SPOTS[k].icon} ${SPOTS[k].name}`, el('b', { textContent: agents.filter(a => a.spot === k).length }));
  roomSigns.forEach((e, k) => e.replaceChildren(`💬 #${D.rooms[k + 1]}`, el('b', { textContent: agents.filter(a => a.spot === `H${k + 1}`).length })));
}
function slowUi() { // once per slice
  tally();
  if (state.sel !== null && (state.tab === 'today' || state.tab === 'td')) drawer(false);
}

// ---------- roster: player tags for everyone who has joined by this day ----------
function roster() {
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
gallery({ scene, state, IX, el, fmt, longDate, YMD, CLAN_COLOR });

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
  D = nd; M = D.messages; state.date = date;
  END = D.hours * 3600; SLICES = Math.ceil(END / D.slice);
  dayGroup = new THREE.Group();
  scene.add(dayGroup);
  agents = D.agents.map((a, i) => ({ ...a, i, joined: IX.agents[a.slug]?.joined || a.joined || date, color: CLAN_COLOR[a.clan] || '#8a7a66', msgs: [], skin: (SLUGS.indexOf(a.slug) + SKINS.length) % SKINS.length,
    bashAt: Object.keys(a.bash).map(Number).sort((x, y) => x - y) }));
  M.forEach((m, k) => agents[m[1]].msgs.push(k));
  for (const a of agents) a.chats = [...a.enter, ...a.msgs.map(k => [M[k][0], M[k][4]])].sort((x, y) => x[0] - y[0]); // [v, room]
  C = [...M, ...(D.human || []).map(([v, name, text, to, room]) => [v, HUMAN, text, to, room, name]), // see C at the top
    ...(D.asks || []).map(([v, i, icon, text, room]) => [v, i, `${icon} ${text}`, [], room, icon])].sort((x, y) => x[0] - y[0]);
  // quiet stretches (>= 30 min with no action and no chat, e.g. between two sessions) are skipped while playing
  const lively = Array.from({ length: SLICES }, (_, s) => agents.some(a => 'WTHL'.includes(a.track[s] || '-')));
  for (const m of M) lively[Math.floor(m[0] / D.slice)] = true;
  gaps = [];
  for (let s = 0, q = -1; s <= SLICES; s++) {
    if (s < SLICES && !lively[s]) { if (q < 0) q = s; continue; }
    if (q >= 0 && s - q >= 6) gaps.push([q, s]);
    q = -1;
  }
  dayPairs = new Map();
  for (const [, s, , to] of M) for (const d of to) dayPairs.set(s * 64 + d, (dayPairs.get(s * 64 + d) || 0) + 1);
  agents.forEach(spawn);
  buildColumns();
  roomSigns = D.rooms.slice(1, ROOMS.length + 1).map((name, k) => { // a market stall per side chat room, gone with the day
    const r = ROOMS[k], ry = Math.atan2(r.yard[0] - r.at[0], r.yard[1] - r.at[1]); // the stall faces its yard
    for (const [m, dx, s] of [[k % 2 ? 'town/stall-red' : 'town/stall-green', 0, 1.8], ['town/stall-bench', -1.9, 1.8], ['town/lantern', 1.7, 1.6]]) {
      const o = lib(m);
      o.position.set(r.at[0] + Math.cos(ry) * dx, 0, r.at[1] - Math.sin(ry) * dx);
      o.rotation.y = ry; o.scale.setScalar(s);
      dayGroup.add(o);
    }
    const e = el('div', { className: 'sign', title: `Chat room #${name}` });
    e.onclick = () => flyTo(new THREE.Vector3(r.yard[0], 0, r.yard[1]), 16);
    const o = new CSS2DObject(e);
    o.position.set(r.at[0], r.sign, r.at[1]);
    dayGroup.add(o);
    return e;
  });
  for (const s of [$('#roomPick'), $('#chatRoom')]) {
    s.disabled = D.rooms.length < 2; // always there, greyed out on days with only #general
    s.title = s.disabled ? 'Only #general this day' : 'Filter the chat by room';
    s.replaceChildren(...['All rooms', ...D.rooms.map(r => `#${r}`)].map((t, k) => el('option', { value: k - 1, textContent: t })));
  }
  state.room = state.who = -1;

  const n = DAY[date]?.day ?? D.day;
  $('#range').textContent = `Day ${n}`;
  document.title = `AI Village · Day ${n} · ${longDate(date, YMD)}`;
  $('#prevDay').disabled = !(DAY[date]?.k > 0);
  $('#nextDay').disabled = !(DAY[date]?.k < DAYS.length - 1);
  time.max = END - 1;
  $('#ticks').replaceChildren(...Array.from({ length: Math.ceil(D.hours) }, (_, h) =>
    Object.assign(el('span', { textContent: hm(h * 3600) }), { style: `left:${(100 * h * 3600) / END}%` })));
  $('#recap').replaceChildren(el('div', { className: 'goal' }, el('b', { textContent: 'Village goal: ' }), ...bold(D.goal || DAY[date]?.goal || 'none recorded')),
    ...(D.recap ? rich(D.recap) : [el('p', { className: 'empty', textContent: 'No recap was written for this day.' })]));
  const u = new URL(location);
  u.searchParams.set('date', date);
  history.replaceState(null, '', u);

  state.slice = -1; state.sel = null; state.open.clear();
  roster();
  setV(0, true);
  select(agents.find(a => a.slug === keep)?.i ?? null); // follow the same player across days
  return true;
}

// ---------- player card ----------
function select(i) {
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

function drawer(fly, top = fly) { // fly: new agent (fly there); top: new agent or tab, so head and tabs rebuild too
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

function flyTo(p, dist) {
  if (walker.isLocked) return;
  const dir = camera.position.clone().sub(controls.target).setY(0).normalize().multiplyScalar(0.6).setY(0.8); // ~53° down, clears walls
  state.fly = { t: 0, t0: controls.target.clone(), c0: camera.position.clone(), t1: p.clone(), c1: p.clone().add(dir.multiplyScalar(dist)) };
}

const walker = new PointerLockControls(camera, document.body);
const keys = new Set(), saved = {};
$('#walk').onclick = () => walker.lock();
$('#walk').hidden = matchMedia('(pointer: coarse)').matches; // pointer lock needs a mouse
walker.addEventListener('lock', () => {
  saved.pos = camera.position.clone(); saved.target = controls.target.clone();
  controls.enabled = false;
  camera.position.set(0, 1.5, WALL - 3);
  camera.lookAt(0, 1.5, 0);
  $('#cross').style.display = $('#walkhelp').style.display = 'block';
});
walker.addEventListener('unlock', () => {
  controls.enabled = true;
  camera.position.copy(saved.pos); controls.target.copy(saved.target);
  $('#cross').style.display = $('#walkhelp').style.display = 'none';
});
addEventListener('keydown', e => keys.add(e.code));
addEventListener('keyup', e => keys.delete(e.code));
document.addEventListener('mousedown', () => {
  if (!walker.isLocked) return;
  const h = pick(innerWidth / 2, innerHeight / 2);
  if (h) select((h.agent || h.col.a).i);
});

function resize() {
  renderer.setSize(innerWidth, innerHeight);
  css.setSize(innerWidth, innerHeight);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize);
resize();

// ---------- first day, then the main loop ----------
const want = new URLSearchParams(location.search).get('date');
if (!(await loadDay(DAY[want] ? want : DAYS.at(-1).date))) {
  $('#loadmsg').textContent = $('#busy').textContent;
  throw new Error('first day failed to load');
}
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
  for (const a of agents) if (a.talk?.until <= now) { a.talk = null; regroup = true; } // said its line: back to work
  if (regroup) { regroup = false; place(state.slice, false); tally(); }

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
  hallObj.visible = state.names && now < hallUntil; // from any distance: humans have no other sign in town
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
