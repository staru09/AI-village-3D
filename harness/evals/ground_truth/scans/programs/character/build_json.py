"""Assemble ../character.json from the CH1-CH6 programs (tables computed here; answers and findings written by hand from
their printed output)."""
import json, re
from collections import Counter, defaultdict
from chcommon import *
import ch1_table, ch1_self, ch2_peer, ch3_compare, ch4_signature, ch5_topics, ch6_addressed

c = con()
Q = []

# CH1
n1 = {a: Counter() for a in AGENTS}
for src, r, a, ts, x in ch1_self.matches(c):
    n1[a][src] += 1
rows1 = []
for a in AGENTS:
    kq = ch1_table.CARRIED[a]
    r, q = ch1_table.DURING[a]
    rows1.append([a, kq, mem_ref(c, a, kq), q, r, n1[a]['memory'] + n1[a]['intent'] + n1[a]['chat']])

# CH2
L2 = ch2_peer.labels(c)
by2, giv2, ex2 = defaultdict(Counter), defaultdict(set), {}
for r, s, a, lab, ts, x in L2:
    by2[a][lab] += 1
    giv2[a, lab].add(s)
    ex2.setdefault((a, lab), r)
L7 = {'Claude Opus 4.6': 'coordinator 8 by 4 others (L7 hand count)', 'GPT-5.4': 'study lead 7 by 2 others (L7 hand count)'}
rows2 = []
for a in AGENTS:
    t = by2[a].most_common(2)
    rows2.append([a, sum(by2[a].values()), f'{t[0][0]} {t[0][1]} ({len(giv2[a, t[0][0]])} givers)' if t else '-',
                  f'{t[1][0]} {t[1][1]}' if len(t) > 1 else '-', ex2.get((a, t[0][0])) if t else '-', L7.get(a, '')])

# CH3
rows3 = [[a, ', '.join(f'{w} {n}' for w, n in s) or '-', ', '.join(f'{w} {n}' for w, n in p) or '-', g, cm]
         for a, s, p, g, cm in ch3_compare.table(c)]

# CH4
sig, base = ch4_signature.signatures(c, top=1)
rows4 = [[a, sig[a][0][1] if sig[a] else '-', sig[a][0][0] if sig[a] else 0, base[a], sig[a][0][2] if sig[a] else '-'] for a in AGENTS]

# CH5
fav, _ = ch5_topics.favourites(c)
rows5 = []
for a in AGENTS:
    (p, s), (p2, s2) = fav[a][0], fav[a][1]
    rows5.append([a, p.replace('\\b', '').replace('?:', ''), ' '.join(f'{d}:{n}' for d, n in s['days'].items()), s['uses'],
                  len(s['unprompted']), f"{s['share']:.0%}", s['first'], f"{p2.replace(chr(92) + 'b', '').replace('?:', '')} ({len(s2['days'])} days, {s2['uses']} uses)"])

# CH6
L6 = ch6_addressed.links(c)
tot6, day6 = defaultdict(Counter), defaultdict(lambda: defaultdict(Counter))
for r, s, a, ts, x in L6:
    tot6[s][a] += 1
    day6[s][day(ts)][a] += 1
rows6 = []
for s in AGENTS:
    top = tot6[s].most_common(2)
    act = [d for d in DAYS if day6[s][d]]
    daily = []
    for d in DAYS:
        cc = day6[s][d]
        if cc:
            mx = max(cc.values())
            daily.append(f"{d[3:]}:{'/'.join(sorted(k.replace('Claude ', '') for k, n in cc.items() if n == mx))} {mx}")
        else:
            daily.append(f'{d[3:]}:-')
    same = sum(1 for d in act if top and day6[s][d][top[0][0]] == max(day6[s][d].values()))
    rows6.append([s, f'{top[0][0]} {top[0][1]}' if top else '-', f'{top[1][0]} {top[1][1]}' if len(top) > 1 else '-',
                  '; '.join(daily), f'{same} of {len(act)}'])

json.dump({'rows1': rows1, 'rows2': rows2, 'rows3': rows3, 'rows4': rows4, 'rows5': rows5, 'rows6': rows6,
           'n_links6': len(L6), 'n_labels2': len(L2)}, open('tables.json', 'w'), ensure_ascii=False, indent=1)
for k in ('rows1', 'rows2', 'rows3', 'rows4', 'rows5', 'rows6'):
    print(k)
    for r in locals()[k]:
        print('  ', r)
