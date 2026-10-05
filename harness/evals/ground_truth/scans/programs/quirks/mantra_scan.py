"""Scan: per agent, most repeated normalised sentences in reasoning that read as self-instructions
(must/should/need to/never/always/don't/remember/keep/stay/no ...). Prints top candidates with doc counts."""
import re, sys
from collections import Counter, defaultdict
from common import load, AGENTS
T = load()
SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
SELF = re.compile(r"\b(must|should|need to|never|always|don'?t|do not|remember|keep|stay|no more|avoid|protocol|rule|lesson|can'?t afford|gotta|have to)\b", re.I)
def norm(s): return re.sub(r'\s+', ' ', re.sub(r"[^a-z' ]", ' ', s.lower())).strip()
for a in AGENTS:
    C = Counter(); ex = {}
    for r, ts, txt, s in T[a]['reasoning']:
        seen = set()
        for sent in SPLIT.split(txt):
            n = norm(sent)
            if len(n.split()) < 4 or not SELF.search(sent) or n in seen: continue
            seen.add(n); C[n] += 1; ex.setdefault(n, (r, ts[:16], sent.strip()[:160]))
    print('=====', a, len(T[a]['reasoning']))
    for n, k in C.most_common(12):
        if k >= 3: print(f'  {k:4d} {ex[n][1]} {ex[n][0]} | {ex[n][2]}')
