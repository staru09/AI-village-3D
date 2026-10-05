"""Probe: for (agent, regex) print counts per channel and in memory_days snapshots, plus 3 contexts. Usage: probe.py AGENT REGEX [channel]"""
import re, sys
from common import load, con, names, LO, HI
a, pat = sys.argv[1], sys.argv[2]; chs = sys.argv[3].split(',') if len(sys.argv) > 3 else ['reasoning', 'chat', 'memory', 'intent']
p = re.compile(pat, re.I | re.M); T = load(); c = con(); nm = names(c)
md = {r['date']: r['content'] for r in c.execute('select agent,date,content from memory_days where date>=? and date<?', (LO, HI)) if nm[r['agent']] == a}
print('memory_days with match:', [d[5:] for d in sorted(md) if p.search(md[d])])
for d in sorted(md):
    m = p.search(md[d])
    if m: print('  mem', d, repr(md[d][max(0, m.start() - 150):m.end() + 150])); break
for ch in chs:
    X = T[a][ch]; h = [x for x in X if p.search(x[2])]
    print(ch, len(h), '/', len(X), 'sessions', len({x[3] for x in h if x[3]}))
    for x in h[:1] + h[len(h) // 2:len(h) // 2 + 1] + h[-1:]:
        m = p.search(x[2]); print('   ', x[0], x[1][:16], repr(x[2][max(0, m.start() - 120):m.end() + 120]))
