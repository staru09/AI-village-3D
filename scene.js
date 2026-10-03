// The 3D stage: model loading, renderer, lights, the town, the camera with its map controls, fly-to and walk mode.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MapControls } from 'three/addons/controls/MapControls.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';
import { buildTown, camps, WALL } from './town.js';
import { $, clans, state } from './core.js';

// ---------- loading ----------
export const manager = new THREE.LoadingManager();
manager.onProgress = (_, done, total) => { const bar = $('#loadbar i'); if (bar) bar.style.width = `${(100 * done) / total}%`; };
const loader = new GLTFLoader(manager);
const gltfs = new Map();
export const gltf = url => { if (!gltfs.has(url)) gltfs.set(url, loader.loadAsync(url)); return gltfs.get(url); };
const shade = o => { if (o.isMesh) o.castShadow = o.receiveShadow = true; };
export function lib(name, fix) { // a placeholder group that fills in when the model arrives
  const g = new THREE.Group();
  gltf(`assets/${name}.glb`).then(m => { const o = m.scene.clone(); o.traverse(shade); fix?.(o); g.add(o); });
  return g;
}

// ---------- scene ----------
export const canvas = $('#stage');
export const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
export const css = new CSS2DRenderer({ element: $('#labels') });
export const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xcdeeff, 90, 200);
const sky = new THREE.HemisphereLight(0xeaf6ff, 0x5b7d31, 1.7);
scene.add(sky);
const sun = new THREE.DirectionalLight(0xfff0d8, 2.9);
sun.position.set(-30, 52, 34);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -44, right: 44, top: 44, bottom: -44, near: 1, far: 150 });
sun.shadow.bias = -0.0005;
sun.shadow.normalBias = 0.03;
scene.add(sun);

// Daylight follows the replay clock: the sun over San Francisco for the date and the Pacific hour. North is -z.
const LAT = 37.77 * Math.PI / 180, LON = -122.42;
const zone = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', timeZoneName: 'short' });
export function sunAt(date, hour) { // -> [altitude, azimuth clockwise from north], radians
  const n = (Date.parse(date) - Date.UTC(+date.slice(0, 4), 0, 0)) / 864e5;
  const dec = 23.44 * Math.PI / 180 * Math.sin(2 * Math.PI * (284 + n) / 365);
  const dst = zone.format(new Date(`${date}T20:00Z`)).endsWith('PDT') ? 1 : 0;
  const h = (hour - dst + (LON + 120) / 15 - 12) * Math.PI / 12; // hour angle; ponytail: no equation of time (±16 min)
  const alt = Math.asin(Math.sin(LAT) * Math.sin(dec) + Math.cos(LAT) * Math.cos(dec) * Math.cos(h));
  return [alt, Math.PI + Math.atan2(Math.sin(h), Math.cos(h) * Math.sin(LAT) - Math.tan(dec) * Math.cos(LAT))];
}
const LOOK = { night: ['#0e1a3a', '#2c3d6b', '#8fa8ff'], low: ['#5d86c9', '#ffc690', '#ffa860'], day: ['#5fb8f5', '#cdeeff', '#fff0d8'] }; // sky top, sky bottom and fog, sunlight
const ramp = (x, a, b) => Math.min(1, Math.max(0, (x - a) / (b - a)));
const tint = new THREE.Color(), to = new THREE.Color();
let lit = '';
export function daylight(date, hour) {
  if (lit === (lit = `${date} ${Math.round(hour * 60)}`)) return; // once per village minute
  const [alt, az] = sunAt(date, hour), deg = alt * 180 / Math.PI, up = Math.max(alt, 0.17); // shadows from at least 10° up
  const night = ramp(deg, -8, 2), day = ramp(deg, 2, 20); // night -> sunrise/sunset colours -> day
  const look = i => (night < 1 ? tint.set(LOOK.night[i]).lerp(to.set(LOOK.low[i]), night) : tint.set(LOOK.low[i]).lerp(to.set(LOOK.day[i]), day));
  document.documentElement.style.setProperty('--sky-1', look(0).getStyle());
  scene.fog.color.copy(look(1));
  document.documentElement.style.setProperty('--sky-2', tint.getStyle());
  sun.color.copy(look(2));
  sun.intensity = 0.3 + 2.6 * ramp(deg, -4, 20);
  sky.intensity = 0.5 + 1.2 * ramp(deg, -8, 15);
  sun.position.set(Math.sin(az) * Math.cos(up), Math.sin(up), -Math.cos(az) * Math.cos(up)).multiplyScalar(70);
}

export const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 600);
export const HOME = { pos: new THREE.Vector3(24, 36, 64), target: new THREE.Vector3(0, 0, 4) };
camera.position.copy(HOME.pos);
export const controls = new MapControls(camera, canvas);
controls.target.copy(HOME.target);
Object.assign(controls, { enableDamping: true, maxPolarAngle: 1.3, minDistance: 5, maxDistance: 140, zoomToCursor: true });

export const town = buildTown(scene, lib, clans); // built once, with a camp for every clan of the whole run
export const campFire = Object.fromEntries(camps(clans.length).map(([x, z], i) => [clans[i].name, new THREE.Vector3(x, 0, z + 0.4)]));

export function flyTo(p, dist) {
  if (walker.isLocked) return;
  const dir = camera.position.clone().sub(controls.target).setY(0).normalize().multiplyScalar(0.6).setY(0.8); // ~53° down, clears walls
  state.fly = { t: 0, t0: controls.target.clone(), c0: camera.position.clone(), t1: p.clone(), c1: p.clone().add(dir.multiplyScalar(dist)) };
}

export const walker = new PointerLockControls(camera, document.body);
const saved = {};
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

function resize() {
  renderer.setSize(innerWidth, innerHeight);
  css.setSize(innerWidth, innerHeight);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize);
resize();
