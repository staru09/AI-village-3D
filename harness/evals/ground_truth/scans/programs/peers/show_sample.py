"""Print a matrix.py sample (seed 41) with message context, for hand validation: python show_sample.py CLASS"""
import sys
from matrix import *
c = con()
M, H = build()
T = {ref('m', m[0]): m for m in M}
W = {r: w for r, w in c.execute("select ref, why from L.labels where rubric='callout'")}
k = sys.argv[1]
for h in sample([h for h in H if h[k]]):
    print('##', h['ref'], h['src'], '->', h['dst'], h['form'])
    print('   ', ' | '.join(h[k])[:400] if k in RX else clean(T[h['ref']][4])[:600].replace('\n', ' '))
    if k == 'criticism':
        print('   WHY:', (W.get(h['ref']) or '')[:250])
