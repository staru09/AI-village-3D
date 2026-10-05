"""Find word 8-grams that appear in the reasoning of many agents: candidates for system-injected text the agents quote."""
import re
from collections import defaultdict, Counter
from common import load, AGENTS
T = load()
W = re.compile(r"[a-z0-9\[\]-]+")
ng_agents = defaultdict(set); ng_docs = Counter()
for a in AGENTS:
    for ch in ('reasoning',):
        for r, ts, txt, s in T[a][ch]:
            w = W.findall(txt.lower()); seen = set()
            for i in range(len(w) - 7):
                g = ' '.join(w[i:i + 8])
                if g not in seen: seen.add(g); ng_agents[g].add(a); ng_docs[g] += 1
top = sorted((g for g in ng_agents if len(ng_agents[g]) >= 4), key=lambda g: (-len(ng_agents[g]), -ng_docs[g]))
for g in top[:80]: print(len(ng_agents[g]), ng_docs[g], g)
