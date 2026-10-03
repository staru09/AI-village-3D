// Gallery: every link the agents shared in chat, up to the selected day, from data/gallery.json
// ([url, date first shared, slug of the first sharer], oldest first). A building in town (town.js GALLERY)
// with a sign that opens the #gallery dialog; main.js passes in its scene, state and helpers.
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { GALLERY } from './town.js';
import { infoButton } from './panels.js';

const PAGE = 300; // links a section renders at a time

export function gallery({ scene, state, IX, el, fmt, longDate, YMD, CLAN_COLOR }) {
  const $ = s => document.querySelector(s), dlg = $('#gallery'), list = $('#galleryList'), filter = $('#galleryFilter');
  let links, by = 'site';
  const runs = [], RUN = {}; // consecutive days with the same village goal; date -> run
  for (const d of IX.days) {
    if (runs.at(-1)?.goal !== d.goal) runs.push({ goal: d.goal, from: d.date });
    runs.at(-1).to = d.date;
    RUN[d.date] = runs.at(-1);
  }
  const badge = slug => {
    const a = IX.agents[slug], b = el('span', { className: 'badge', textContent: a.label, title: a.name });
    b.style.setProperty('--c', CLAN_COLOR[a.clan] || '#8a7a66');
    return b;
  };
  const host = u => u.hostname.replace(/^www\./, '');
  const row = ([url, date, slug]) => {
    const u = new URL(url);
    return el('li', {}, el('a', { href: url, target: '_blank', rel: 'noopener noreferrer', title: url },
      el('b', { textContent: host(u) }), (u.pathname + u.search + u.hash).replace(/\/$/, '')),
    badge(slug), el('time', { textContent: longDate(date, YMD) }));
  };
  const section = (summary, ls, open) => { // links render on first open, a page at a time
    const d = el('details', { open }, el('summary', {}, ...summary)), ol = el('ol'), more = el('button', { className: 'btn off', textContent: 'Show more' });
    let n = 0;
    const page = () => { ol.append(...ls.slice(n, (n += PAGE)).map(row)); more.hidden = n >= ls.length; };
    more.onclick = page;
    d.ontoggle = () => { if (d.open && !n) { d.append(ol, more); page(); } };
    if (open) d.ontoggle();
    return d;
  };
  const span = r => { // a goal's days so far; the run may go on past the selected day
    const to = r.to < state.date ? r.to : state.date;
    return ` · ${longDate(r.from, YMD)}${to > r.from ? ` – ${longDate(to, YMD)}` : ''}`;
  };

  function draw() {
    const q = filter.value.trim().toLowerCase(), all = links.filter(l => l[1] <= state.date); // no links from days not yet replayed
    const shown = q ? all.filter(([u, , s]) => u.toLowerCase().includes(q) || IX.agents[s].name.toLowerCase().includes(q)) : all;
    $('#galleryTitle').textContent = `Gallery · ${longDate(state.date, YMD)}`;
    $('#galleryNote').textContent = q ? `${fmt(shown.length)} of ${fmt(all.length)} links match` : `${fmt(all.length)} links the agents shared in chat up to this day`;
    const groups = new Map(); // newest link first, so goal runs come newest first too
    for (const l of shown.toReversed()) { const k = by === 'goal' ? RUN[l[1]] : by === 'site' ? host(new URL(l[0])) : l[2]; if (!groups.has(k)) groups.set(k, []); groups.get(k).push(l); }
    const secs = [...groups];
    if (by !== 'goal') secs.sort((x, y) => y[1].length - x[1].length);
    const count = n => ` · ${fmt(n)} link${n === 1 ? '' : 's'}`;
    const sharers = ls => { // a site's top sharers, most links first
      const n = {};
      for (const l of ls) n[l[2]] = (n[l[2]] || 0) + 1;
      return Object.keys(n).sort((x, y) => n[y] - n[x]).slice(0, 4).map(badge);
    };
    list.replaceChildren(...secs.map(([k, ls], i) => section(by === 'goal'
      ? [(k.goal || 'No village goal recorded').replaceAll('**', ''), el('small', { textContent: span(k) + count(ls.length) })]
      : by === 'site'
      ? [el('a', { href: `${new URL(ls[0][0]).origin}/`, target: '_blank', rel: 'noopener noreferrer', textContent: k }),
        el('small', { textContent: `${count(ls.length)}${span({ from: ls.at(-1)[1], to: ls[0][1] })}` }), ...sharers(ls)]
      : [badge(k), ` ${IX.agents[k].name}`, el('small', { textContent: count(ls.length) })], ls, !i)));
    if (!secs.length) list.append(el('p', { className: 'empty', textContent: q ? 'No links match.' : 'No links shared yet.' }));
  }

  async function open() {
    dlg.showModal();
    if (!links) {
      list.replaceChildren(el('p', { className: 'empty', textContent: 'Loading links…' }));
      try { // fetched on the first open, then kept; only web links become hrefs
        links = (await (await fetch('data/gallery.json')).json()).filter(([u]) => /^https?:\/\//.test(u) && URL.canParse(u));
      } catch {
        list.replaceChildren(el('p', { className: 'empty', textContent: "Couldn't load data/gallery.json." }));
        return;
      }
    }
    draw();
  }
  filter.oninput = () => links && draw();
  for (const b of $('#galleryBy').children) b.onclick = () => {
    by = b.dataset.by;
    for (const x of $('#galleryBy').children) x.ariaPressed = x === b;
    if (links) draw();
  };
  $('#galleryClose').onclick = () => dlg.close();
  dlg.onclick = e => { if (e.target === dlg) dlg.close(); }; // the backdrop belongs to the dialog itself

  const sign = el('div', { className: 'sign', title: 'Every link the agents shared in chat' }, '🖼️ Gallery', infoButton('Gallery'));
  sign.onclick = open;
  const o = new CSS2DObject(sign);
  o.position.set(GALLERY.at[0], GALLERY.sign, GALLERY.at[1]);
  scene.add(o);
  $('#guideList').append(el('li', {}, el('div', { className: 'ico', textContent: '🖼️' }), el('div', {}, el('h3', { textContent: 'Gallery' }),
    el('p', { textContent: 'What the village made: every link the agents shared in chat up to this day, by site, goal or agent, credited to whoever shared it first. Click its sign to browse.' }))));
}
