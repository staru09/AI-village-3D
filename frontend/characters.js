// The agents as LEGO-like characters: skins in clan colour, labels over their heads, and where each one stands.
import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { SPOTS, ROOMS, WALL } from './town.js';
import { el, D, agents, dayGroup } from './core.js';
import { gltf, campFire } from './scene.js';
import { select } from './card.js';

export const ANIM = { W: 'interact-right', T: 'interact-left', H: 'emote-yes', L: 'pick-up', C: 'sit' };
export const SKINS = 'abcdefghijklmnopqr';
const CH = 0.38; // character scale: 2.7-unit Kenney figures become ~1 unit, toy-sized next to the houses
const GATE = new THREE.Vector3(0, 0, WALL + 3);

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

export const pickables = [];
export function spawn(a) {
  a.root = new THREE.Group();
  a.root.visible = false;
  dayGroup.add(a.root);
  a.ready = gltf(`assets/characters/character-${SKINS[a.skin]}.glb`).then(m => {
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
    return m.scene; // never animated: the standing pose, for the card portrait
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

export function play(a, name) {
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

export function place(slice, jump) {
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
