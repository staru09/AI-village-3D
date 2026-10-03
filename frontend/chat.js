// The village chat: speech bubbles in town, the latest lines in the panel, the whole day so far in the #chat dialog.
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { SPOTS } from './town.js';
import { $, el, fmt, longDate, bold, HUMAN, state, D, C, agents, hm } from './core.js';
import { scene } from './scene.js';
import { select } from './card.js';

// humans have no character in town: their messages pop up over the Town Hall's sign
export const hallSay = el('div', { onclick: () => openChat() }), hallObj = new CSS2DObject(el('div', { className: 'bubble' }, hallSay));
hallObj.position.set(SPOTS.H.at[0], SPOTS.H.sign, SPOTS.H.at[1]);
hallObj.visible = false;
scene.add(hallObj);

// Posting a message sends the agent to the Town Hall (or the message's room stall) for as long as its bubble shows,
// then back to the slice's place: chat rarely wins a whole 5-minute slice against dozens of commands.
// A request to humans pops its icon instead of a bubble; a human's message shows over the Town Hall.
const TALK = 3200;
export const talk = { regroup: false, hallUntil: 0 }; // read by the clock and the main loop
const sender = name => (name === 'automated' ? '⚙️ Village system' : `👤 ${name}`); // humans as posted, the village's notices as itself
export function say(m) {
  const a = agents[m[1]], t = m[2].replaceAll('**', ''), now = performance.now();
  const short = t.length > 120 ? `${t.slice(0, 118)}…` : t;
  if (!a) { hallSay.textContent = `${sender(m[5])}: ${short}`; talk.hallUntil = now + TALK; return; }
  if (m[5]) { a.puff.textContent = m[5]; a.puffUntil = now + 1200; } else { a.bubble.textContent = short; a.bubbleUntil = now + TALK; }
  a.talk = { room: m[4], until: now + TALK };
  talk.regroup = true;
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

export function feed() {
  const ks = [];
  for (let k = state.mp - 1; k >= 0 && ks.length < 6; k--) if (inRoom(C[k])) ks.unshift(k);
  $('#feedList').replaceChildren(...(ks.length ? ks.map(k => line(k)) : [el('li', { className: 'empty', textContent: 'No chat yet today.' })]));
}

export function chatSync(redraw) { // lines up to the replay clock, never later ones; follows new ones only from the bottom
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
export function openChat(k) { // k: a message to scroll to and highlight
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
