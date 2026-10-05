"""W7: do call-outs go to the agents who assign tasks, or only to those who receive them?

Assigning = messages with the stored label rubric 'delegation' = 'directs' (one label per @-message); the
assignee(s) = room-mates named in that message (short names resolved). Call-outs = W1 (label calls_out_other,
resolved targets). For every ordered pair where A directed B at least once: call-outs B->A (up) vs A->B (down).
Per agent: directs sent, directs received, call-outs received.

    python w7_direction.py
    python w7_direction.py --sample    25 'directs' messages with their assignees, seed 41
"""
import json
from collections import Counter
from common import *

if __name__ == '__main__':
    c = con()
    M = {ref('m', m[0]): m for m in messages(c)}
    D = Counter()                      # (director, assignee) -> directs messages
    refs = [r for r, in c.execute("SELECT ref FROM L.labels WHERE rubric='delegation' AND label='directs'")]
    for r in refs:
        _, who, room, ts, text, _ = M[r]
        for x in named(text or '', who, room):
            D[who, x] += 1
    if '--sample' in __import__('sys').argv:
        for r in sample(refs):
            _, who, room, ts, text, _ = M[r]
            print(r, who, '->', named(text or '', who, room), '|', (text or '')[:250].replace('\n', ' '), '\n')
        raise SystemExit
    W1 = [h for h in json.load(open('w1_hits.json')) if h['targets']]
    C = Counter((h['speaker'], t) for h in W1 for t in h['targets'])
    sent, recv = Counter(), Counter()
    for (a, b), n in D.items():
        sent[a] += n; recv[b] += n
    crecv = Counter(t for (_, t), n in C.items() for _ in range(n))
    print(f'{sum(D.values())} director->assignee links from {len(refs)} directs messages; {sum(C.values())} call-out links')
    print(f"{'agent':18} {'directs sent':>12} {'directs recv':>12} {'call-outs recv':>14} {'call-outs sent':>14}")
    csent = Counter(a for (a, _), n in C.items() for _ in range(n))
    for a in sorted(AGENTS, key=lambda a: -sent[a]):
        print(f'{a:18} {sent[a]:12} {recv[a]:12} {crecv[a]:14} {csent[a]:14}')
    up = sum(C[b, a] for (a, b) in D)
    down = sum(C[a, b] for (a, b) in D)
    print(f'\npairs where A directed B: {len(D)}; call-outs B->A (assignee to director) {up}, A->B (director to assignee) {down}')
    one = [(a, b) for (a, b) in D if (b, a) not in D]
    print(f'one-way pairs (B never directed A): {len(one)}; call-outs up {sum(C[b, a] for a, b in one)}, '
          f'down {sum(C[a, b] for a, b in one)}')
    for (a, b), n in sorted(D.items(), key=lambda kv: -kv[1])[:15]:
        print(f'  {a:18} directs {b:18} x{n:2}   up {C[b, a]}  down {C[a, b]}')
    top = [a for a, _ in sent.most_common(5)]
    print('\ntop-5 directors', top, 'receive', sum(crecv[a] for a in top), 'of', sum(crecv.values()), 'call-out links')
