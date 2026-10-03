// The player card's portrait: the agent's own character (same model and painted skin), standing, facing the viewer.
import * as THREE from 'three';

let r; // one small offscreen renderer, made on the first card
const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 1, 0.1, 20);
cam.position.set(0, 1.5, 4.5); // at chest height, mid-thigh to just over the head in frame
cam.lookAt(0, 1.75, 0);
const sun = new THREE.DirectionalLight(0xfff0d8, 2.9); // the town's lights, the sun from the front
sun.position.set(-1, 2, 3);
scene.add(new THREE.HemisphereLight(0xeaf6ff, 0x5b7d31, 1.7), sun);

export function portrait(a) { // a PNG data URL (null if the day changed first), rendered once per agent and day
  return (a.portrait ||= a.ready.then(model => {
    if (!model) return null;
    if (!r) { r = new THREE.WebGLRenderer({ alpha: true, antialias: true }); r.setSize(192, 192, false); r.toneMapping = THREE.ACESFilmicToneMapping; }
    const body = model.clone(); // shares geometry and a.mat (freed with the day), so nothing of its own to dispose
    body.traverse(o => { if (o.isMesh) o.material = a.mat; });
    scene.add(body);
    r.render(scene, cam);
    scene.remove(body);
    return r.domElement.toDataURL();
  }));
}
