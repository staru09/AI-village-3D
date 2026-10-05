"""F5: do third parties take sides in a dispute, and always the same side?
Dispute = hand-verified challenges A -> B (f1_hand.json) grouped by (A, B, day). A third party C (same room) takes a
side when, within 30 min after one of the dispute's challenge messages, C backs/praises A or challenges B (side: critic A),
or backs/praises B or challenges A (side: target B). Backing/praise = f4_allies.support_sents (22 of 25). Round 2: the
window runs from each challenge message (not the whole day), and C's thanks to A do not count when A had itself
challenged C in the 30 min before (C thanking its own critic). Round 1 (day-wide window) was 15 of 25; see hand file.
    python f5_sides.py            report + f5_events.json
    python f5_sides.py --sample   25 side-taking events (seed 41) to judge
"""
import json, sys
from collections import Counter, defaultdict
from fcommon import *
from f4_allies import support_sents

c = con()
M = [m for m in messages(c) if m[1] in AGENTS]
CH = [h for h in json.load(open('f1_hand.json')) if h['target']]
chal = defaultdict(set)  # (speaker, target) -> refs
for h in CH:
    chal[h['speaker'], h['target']].add(h['ref'])
CHT = defaultdict(list)
for h in CH:
    CHT[h['speaker'], h['target']].append(h)
disp = defaultdict(list)
for h in CH:
    disp[h['speaker'], h['target'], h['day']].append(h)
events = []
for (A, B, day), hs in disp.items():
    room = hs[0]['room']
    for mid, C, rm, ts, text, _ in M:
        if rm != room or C in (A, B) or not any(h['ts'] < ts and mins(h['ts'], ts) <= 30 for h in hs):
            continue
        if any(x['ts'] < ts and mins(x['ts'], ts) <= 30 for x in CHT[A, C]):
            continue
        r = ref('m', mid)
        side, why = None, ''
        if support_sents(text, A, room) or r in chal[C, B]:
            side, why = A, 'backs critic' if support_sents(text, A, room) else 'challenges target'
        if support_sents(text, B, room) or r in chal[C, A]:
            side = 'both' if side else B
            why = why or ('backs target' if support_sents(text, B, room) else 'challenges critic')
        if side:
            events.append(dict(critic=A, target=B, day=day, third=C, ref=r, ts=ts, side=side, why=why,
                               text=(support_sents(text, A, room) + support_sents(text, B, room) + [norm(text)[:200]])[0][:250]))
# one event per (dispute, third party): the first one
first = {}
for e in events:
    first.setdefault((e['critic'], e['target'], e['day'], e['third']), e)
E = list(first.values())
if '--sample' in sys.argv:
    for e in sample(E):
        print(e['ref'], e['ts'][5:16], f"{e['third']} in {e['critic']} -> {e['target']}: side {e['side']} ({e['why']})\n    {e['text']}\n")
    sys.exit()
print(len(disp), 'disputes (critic, target, day);', len({k[:3] for k in first}), 'with at least one third party taking a side;', len(E), 'side-taking events')
print('side:', Counter('critic' if e['side'] == e['critic'] else 'target' if e['side'] == e['target'] else 'both' for e in E))
# consistency: third party x unordered pair, sides over disputes
cons = defaultdict(list)
for e in E:
    if e['side'] != 'both':
        cons[e['third'], tuple(sorted((e['critic'], e['target'])))].append(e['side'])
rep = {k: v for k, v in cons.items() if len(v) >= 2}
same = [k for k, v in rep.items() if len(set(v)) == 1]
print(f'third party x pair with >= 2 side-takings: {len(rep)}; always the same side: {len(same)}')
for k, v in sorted(rep.items(), key=lambda kv: -len(kv[1])):
    print('  ', k[0], 'on', k[1], Counter(v).most_common())
print('\nby third party: sided with critic / target')
by = defaultdict(Counter)
for e in E:
    by[e['third']]['critic' if e['side'] == e['critic'] else 'target' if e['side'] == e['target'] else 'both'] += 1
for k, v in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
    print(f'  {k:18} {dict(v)}')
same_maker = Counter((MAKER[e['third']] == MAKER[e['side']]) for e in E if e['side'] != 'both')
print('sided with own maker:', same_maker)
json.dump(E, open('f5_events.json', 'w'), indent=0)
