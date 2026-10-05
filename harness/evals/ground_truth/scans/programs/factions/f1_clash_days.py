"""F1: challenge messages per ordered pair per day; a recurring clash = ordered pair with challenges on >= 3 of the 5 days.
Source: stored 'callout' labels (calls_out_other, 324). The automatic target rule (fcommon.challenges) was right on
18 of 25 links (seed 41, below 80%), so the answer uses the hand reading of all 324 labels (f1_hand.json, build_hand.py).
    python f1_clash_days.py            report (hand count) + f1_pairs.json
    python f1_clash_days.py --auto     same table from the automatic rule (not reported)
    python f1_clash_days.py --sample   the 25 automatic links judged (seed 41)
"""
import json, sys
from collections import Counter, defaultdict
from fcommon import *

if '--sample' in sys.argv or '--auto' in sys.argv:
    H = challenges(con())
    links = [(h['ref'], h['ts'], h['speaker'], t, h['quote'], h['why']) for h in H for t in h['targets']]
    if '--sample' in sys.argv:
        for r, ts, a, b, q, w in sample(links):
            print(r, ts[:16], a, '->', b, '\n   Q:', q[:300], '\n   W:', w[:250], '\n')
        sys.exit()
    links = [(r, ts, a, b) for r, ts, a, b, q, w in links]
else:
    links = [(h['ref'], h['ts'], h['speaker'], h['target']) for h in json.load(open('f1_hand.json')) if h['target']]
pd = defaultdict(Counter)
for r, ts, a, b in links:
    pd[a, b][ts[:10]] += 1
rows = sorted(pd, key=lambda k: (-len(pd[k]), -sum(pd[k].values())))
print(f'{len(links)} challenge links, {len(pd)} ordered pairs')
print(f'{"speaker":18} {"target":18} days total ' + ' '.join(d[5:] for d in DAYS))
for k in rows:
    if len(pd[k]) >= 2:
        print(f'{k[0]:18} {k[1]:18} {len(pd[k]):4} {sum(pd[k].values()):5} ' + ' '.join(f'{pd[k][d]:5}' for d in DAYS))
rec = [k for k in rows if len(pd[k]) >= 3]
print('recurring (>=3 days):', len(rec), '| their messages:', sum(sum(pd[k].values()) for k in rec), 'of', len(links))
und = Counter()
for (a, b), cn in pd.items():
    und[tuple(sorted((a, b)))] += 0
both = [k for k in und if pd.get(k) and pd.get(k[::-1])]
print('pairs challenging both ways:', [(a, b, len(pd[a, b]), len(pd[b, a])) for a, b in both])
if '--auto' not in sys.argv:
    json.dump([dict(speaker=a, target=b, days=len(pd[a, b]), total=sum(pd[a, b].values()), per_day=[pd[a, b][d] for d in DAYS],
                    refs=[r for r, ts, x, y in links if (x, y) == (a, b)]) for a, b in rows], open('f1_pairs.json', 'w'), indent=0)
