"""TC4: long-form prose for an audience. Lists every blog/essay/paper file each agent wrote (from tc1_files.pkl) with the
title line of what it wrote, plus chat messages announcing a published post/paper/gist. Pieces are then grouped by hand
(drafts v2..v9, _CORRECTED, copies = one piece) in tc4_pieces below."""
from common import *
import pickle
con = db()
rows = pickle.load(open('tc1_files.pkl', 'rb'))
act = {}
for a, tid, ts, r, p, k in rows:
    if k in ('blog', 'essay'): act.setdefault((a, r, p), []).append((ts, tid))
for (a, r, p), ev in sorted(act.items()):
    ts, tid = min(ev)
    text = con.execute('SELECT action FROM turns WHERE id=?', (tid,)).fetchone()[0]
    i = text.find(p.rsplit('/', 1)[-1]); title = re.search(r'\n(#+ [^\n]{0,90}|<title>[^<]{0,90})', text[i:])
    print(f"{a:18} {len(ev):3}w {ts[5:16]} {ref('t', tid)} {r}/{p}  | {title.group(1) if title else ''}")
print('\n--- chat announcements')
PUB = re.compile(r'(blog ?post|paper|essay|write-?up|gist|substack|article)[^.\n]{0,80}(published|live|deployed|now available|read it|here:)|(published|deployed|live)[^.\n]{0,60}(blog ?post|paper|essay|write-?up|gist|article)', re.I)
for mid, a, ts, t in con.execute("SELECT m.id, n.name, m.ts, m.content FROM messages m JOIN nodes n ON n.id=m.src WHERE m.ts>=? AND m.ts<? ORDER BY m.ts", (LO, HI)):
    m = PUB.search(t)
    if m: print(f"{a:18} {ts[5:16]} {ref('m', mid)} {' '.join(t[max(0, m.start()-60):m.end()+100].split())}")
