"""F5 answer: tabulates the hand-coded side-taking (f5_sides_hand.json) over the 19 two-sided disputes (f5_disputes.json).
Checks each ref is a message by that third party inside the dispute window. The automatic detector
f5_sides.py was right on 15 of 25 events (seed 41) and is not used for counts."""
import json
from collections import Counter, defaultdict
from fcommon import *
c = con()
D = {d[0]: d for d in json.load(open('f5_disputes.json'))}
E = json.load(open('f5_sides_hand.json'))['events']
for d, who, side, r in E:
    ts, name, _ = get(c, r)
    assert name == who and D[d][3] <= ts[:16] <= D[d][4], (d, who, r, ts, name)
print(len(D), 'disputes;', len({e[0] for e in E}), 'with a third party taking a side;', len(E), 'side-taking messages by',
      len({(e[0], e[1]) for e in E}), 'third parties')
print('side:', Counter(e[2] for e in E))
print('no third party took a side in:', [k for k in D if k not in {e[0] for e in E}])
for k in D:
    ev = [e for e in E if e[0] == k]
    if ev:
        print(f'  {k} {D[k][1]} vs {D[k][2]} ({D[k][5]}): ' + '; '.join(f'{e[1]} -> {D[k][1] if e[2] == "critic" else D[k][2]}' for e in ev))
# same side each time? third party x unordered pair, and third party x named agent across disputes
side_of = lambda e: D[e[0]][1] if e[2] == 'critic' else D[e[0]][2]
other = lambda e: D[e[0]][2] if e[2] == 'critic' else D[e[0]][1]
per = defaultdict(list)
for e in E:
    per[e[1], frozenset((D[e[0]][1], D[e[0]][2]))].append((e[0], side_of(e)))
print('\nthird party on the same pair more than once:')
for (t, p), v in per.items():
    if len({x[0] for x in v}) > 1:
        print('  ', t, sorted(p), v)
print('\nthird party with an agent of its own maker on exactly one side:')
own = Counter()
for e in E:
    s, o = side_of(e), other(e)
    if (MAKER[s] == MAKER[e[1]]) != (MAKER[o] == MAKER[e[1]]):
        own['with own maker' if MAKER[s] == MAKER[e[1]] else 'against own maker'] += 1
        print('  ', e[0], e[1], 'sided with', s, 'against', o)
print(own)
