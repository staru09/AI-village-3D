"""F3 reading aid: for every recurring pair (F1, >= 3 days), each challenge with the target's next message within
30 min (its stored callout label) to judge by hand whether the clash ended and whether the issue came back."""
import json
from fcommon import *
c = con()
M = messages(c)
lab = dict(c.execute("SELECT ref, label FROM L.labels WHERE rubric='callout'"))
P = [p for p in json.load(open('f1_pairs.json')) if p['days'] >= 3]
H = {h['ref']: h for h in json.load(open('f1_hand.json'))}
for p in P:
    print(f"\n### {p['speaker']} -> {p['target']} ({p['days']} days, {p['total']})")
    for r in p['refs']:
        h = H[r]
        nxt = next((m for m in M if m[1] == p['target'] and m[3] > h['ts'] and mins(h['ts'], m[3]) <= 30), None)
        print(f" {r} {h['ts'][5:16]} Q: {h['quote'][:170]!r}".replace('\\n', ' '))
        if nxt:
            print(f"     -> {ref('m', nxt[0])} +{mins(h['ts'], nxt[3])}m [{lab.get(ref('m', nxt[0]))}] {norm(nxt[4])[:170]!r}".replace('\\n', ' '))
        else:
            print('     -> no reply within 30 min')
