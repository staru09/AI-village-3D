"""TC2: 20 random chat messages per agent (seed 41; all if fewer), goal 41, for hand classification (labels in tc2_classify.py)."""
from common import *
import json
con = db(); N = dict(con.execute('SELECT id,name FROM nodes'))
out = []
for a in AGENTS:
    rows = con.execute("SELECT m.id, m.ts, m.content FROM messages m JOIN nodes n ON n.id=m.src WHERE n.name=? AND m.ts>=? AND m.ts<? ORDER BY m.id", (a, LO, HI)).fetchall()
    samp = sorted(random.Random(41).sample(rows, min(20, len(rows))), key=lambda r: r[1])
    for i, (mid, ts, text) in enumerate(samp, 1):
        out.append((a, i, ref('m', mid), ts[5:16], len(text.split()), text))
json.dump(out, open('tc2_sample.json', 'w'))
with open('tc2_sample.txt', 'w') as f:
    for a, i, r, ts, n, text in out:
        t = ' '.join(text.split())
        f.write(f"[{a} #{i}] {r} {ts} ({n}w) {t[:600]}\n")
print(len(out))
