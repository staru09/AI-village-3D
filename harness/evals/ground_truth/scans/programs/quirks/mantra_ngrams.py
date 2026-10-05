"""Per agent: word 5-grams in reasoning ranked by number of reasoning texts containing them, kept only if
used by at most 3 agents (agent-specific) and containing a self-instruction word. Also counts in memory snapshots."""
import re
from collections import Counter, defaultdict
from common import load, AGENTS
T = load()
W = re.compile(r"[a-z0-9'’\[\]-]+")
SELF = {'must', 'should', 'never', 'always', "don't", 'remember', 'keep', 'stay', 'avoid', 'protocol', 'rule', 'gotta',
        'need', 'idle', 'idling', 'proactive', 'waiting', 'passive', 'busy', 'precision', 'meticulous', 'hostile', 'critical', 'lesson', 'wants'}
N = 5
docs = {}; agents_of = defaultdict(set)
for a in AGENTS:
    C = Counter()
    for r, ts, txt, s in T[a]['reasoning']:
        w = W.findall(txt.lower().replace('’', "'")); seen = set(' '.join(w[i:i + N]) for i in range(len(w) - N + 1))
        for g in seen: C[g] += 1; agents_of[g].add(a)
    docs[a] = C
for a in AGENTS:
    print('=====', a, len(T[a]['reasoning']))
    k = 0
    for g, n in docs[a].most_common(4000):
        if len(agents_of[g]) > 3 or not (set(g.split()) & SELF): continue
        print(f'  {n:4d} {g}'); k += 1
        if k >= 15: break
