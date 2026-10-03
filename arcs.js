// Mention arcs: a line from a speaker to each agent it names, over the last village hour or the whole day.
import * as THREE from 'three';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { $, state, M, agents, dayPairs, lowerBound } from './core.js';
import { scene } from './scene.js';

// ---------- mention arcs ----------
const beamMats = [2, 3.5, 6].map(w => new LineMaterial({ linewidth: w, vertexColors: true, transparent: true, opacity: 0.92, depthWrite: false }));
const beams = beamMats.map(m => { const l = new LineSegments2(new LineSegmentsGeometry(), m); l.frustumCulled = false; l.renderOrder = 2; scene.add(l); return l; });
let livePairs = new Map();
export function computeLive(v) { // mentions in the last village hour
  livePairs = new Map();
  for (let k = lowerBound(v - 3600); k < M.length && M[k][0] <= v; k++)
    for (const d of M[k][3]) livePairs.set(M[k][1] * 64 + d, (livePairs.get(M[k][1] * 64 + d) || 0) + 1);
}
const cA = new THREE.Color(), cB = new THREE.Color(), white = new THREE.Color('#fff'), P0 = new THREE.Vector3(), P1 = new THREE.Vector3(), Q = new THREE.Vector3();
export function drawBeams() {
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
$('#beams').onchange = () => computeLive(state.v);
