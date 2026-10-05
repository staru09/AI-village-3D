"""P2, P3, P6 from matrix_out.json (run matrix.py first).

P3 one-sided: A->B mentions >= 15 and B->A mentions <= A->B / 5, or A->B praise >= 5 and B->A praise <= 1.
P6 trend: pairs with >= 30 mentions; net = praise - criticism messages per day (11-15 May); slope = least-squares
           net per day over the days the pair is active (>= 3 days), plus first-active-day vs last-active-day net.
"""
import json
from collections import Counter

D = json.load(open('matrix_out.json'))
P = {(p['src'], p['dst']): p for p in D['pairs']}
g = lambda s, d, k: P.get((s, d), {}).get(k, 0)
DAYS = ['05-11', '05-12', '05-13', '05-14', '05-15']

print('## P2 received (praise, criticism) per 100 mentions received')
R = D['received']
for a in sorted(R, key=lambda a: -R[a].get('praise', 0)):
    r = R[a]; m = r.get('mention', 0) or 1
    print(f"{a:18} mentions {r.get('mention',0):4} praise {r.get('praise',0):3} ({100*r.get('praise',0)/m:4.1f}) "
          f"crit {r.get('criticism',0):3} ({100*r.get('criticism',0)/m:4.1f}) | gives praise {D['given'][a].get('praise',0)}")

print('\n## P3 one-sided pairs')
for (s, d), p in sorted(P.items(), key=lambda x: -x[1]['mention']):
    back_m, back_p = g(d, s, 'mention'), g(d, s, 'praise')
    if (p['mention'] >= 15 and back_m * 5 <= p['mention']) or (p['praise'] >= 5 and back_p <= 1):
        print(f"{s:18} -> {d:18} mentions {p['mention']:3} back {back_m:3} | praise {p['praise']:2} back {back_p:2}"
              f" | crit {p['criticism']:2} back {g(d, s, 'criticism'):2}")

print('\n## P6 daily net (praise - criticism), pairs with >= 30 mentions')
rows = []
for k, v in D['daily'].items():
    s, d = k.split('|')
    if g(s, d, 'mention') < 30:
        continue
    act = [x for x in DAYS if v.get('m' + x, 0) or v.get(x, 0)]
    if len(act) < 3:
        continue
    xs = [DAYS.index(x) for x in act]; ys = [v.get(x, 0) for x in act]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    rows.append((slope, s, d, [v.get(x, 0) if x in act else None for x in DAYS],
                 [v.get('m' + x, 0) for x in DAYS]))
rows.sort()
for slope, s, d, net, men in rows:
    print(f'{s:18} -> {d:18} slope {slope:+.2f}  net {net}  mentions {men}')
tot = Counter()
for k, v in D['daily'].items():
    for x in DAYS:
        tot[x] += v.get(x, 0)
print('all pairs, net per day:', [tot[x] for x in DAYS])
