// The Hall of Records: one LEGO brick column per agent, for the measure picked under "Plaza".
import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { PLAZA } from './town.js';
import { $, el, pct, count, fmt, SLUGS, clans, agents, dayGroup, SLICES } from './core.js';
import { scene, gltf, flyTo } from './scene.js';

// ---------- stats plaza: one LEGO brick column per agent ----------
export const METRICS = [
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
export const plaza = { cols: [] };
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
export function buildColumns() { // per day; risers and labels live in dayGroup
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
export function buildPlaza() {
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
$('#metric').onchange = buildPlaza;
$('#plazaBtn').onclick = () => flyTo(new THREE.Vector3(PLAZA[0], 0, PLAZA[1]), 22);
