"""F3: do clashes end or come back? Tabulates the hand-coded episodes of the 16 recurring pairs (f3_episodes.json,
read from f3_dump.txt which f3_dump.py prints) and checks every episode ref is a hand-verified challenge of that pair."""
import json
from collections import Counter
E = json.load(open('f3_episodes.json'))
H = {h['ref']: h for h in json.load(open('f1_hand.json'))}
P = {(p['speaker'], p['target']): set(p['refs']) for p in json.load(open('f1_pairs.json')) if p['days'] >= 3}
seen = set()
for a, b, days, issue, out, refs in E['episodes']:
    for r in refs.split():
        assert r in P[a, b], (a, b, r)
        seen.add((a, b, r))
assert seen == {(a, b, r) for (a, b), rs in P.items() for r in rs}, 'every challenge of a recurring pair is in one episode'
ep = E['episodes']
print(len(ep), 'episodes (issues) in', len(P), 'recurring pairs, covering', len(seen), 'challenge messages')
print('outcomes:', Counter(e[4] for e in ep).most_common())
multi = [e for e in ep if len(e[2]) > 1]
print('issues raised on more than one day by the same pair:', len(multi))
for e in multi:
    print('  ', e[0], '->', e[1], e[2], e[3], e[4], len(e[5].split()), 'msgs')
print('repeated within one day (>= 2 messages):', sum(1 for e in ep if len(e[2]) == 1 and len(e[5].split()) >= 2))
milestone = [e for e in ep if 'milestone' in e[3] or 'not public' in e[3] or 'stat mixed' in e[3]]
print('status/milestone episodes:', len(milestone), Counter(e[4] for e in milestone), '| others:', Counter(e[4] for e in ep if e not in milestone))
tab = {}
for a, b, days, issue, out, refs in ep:
    t = tab.setdefault((a, b), Counter())
    t[out] += 1
    t['multi'] += len(days) > 1
print('\npair | episodes | conceded partial defended ignored yielded | issue on >1 day')
for (a, b), t in tab.items():
    print(f'{a} -> {b} | {sum(t[k] for k in ("conceded", "partial", "defended", "ignored", "yielded"))} | {t["conceded"]} {t["partial"]} {t["defended"]} {t["ignored"]} {t["yielded"]} | {t["multi"]}')
