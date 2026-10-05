"""F5 reading aid: for each two-sided dispute in f5_disputes.json (picked from challenges answered with a stored
'defends_self' label within 30 min, plus the m2 score disputes), print every third-party message in the window that
names either party, so sides can be coded by hand (f5_sides_hand.json)."""
import json
from fcommon import *
M = [m for m in messages(con()) if m[1] in AGENTS]
for d, A, B, t0, t1, topic in json.load(open('f5_disputes.json')):
    print(f'\n### {d} {A} vs {B}: {topic} ({t0[5:]}-{t1[11:]})')
    for mid, C, room, ts, text, _ in M:
        if t0 <= ts[:16] <= t1 and C not in (A, B) and ROOM[C] == ROOM[A]:
            n = [x for x in named2(text, C, room) if x in (A, B)]
            if n:
                print(f'  {ref("m", mid)} {ts[11:16]} {C} names {n}: {norm(text)[:330]!r}'.replace('\\n', ' '))
