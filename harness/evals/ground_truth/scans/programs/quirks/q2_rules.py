"""Q2: standing rules in memory. A rule line = a memory line with NEVER/ALWAYS/CRITICAL/RULE/LESSON (any case)
or an all-caps imperative (DO NOT / DON'T / MUST). Counted in each agent's last memory snapshot of each day (memory_days)."""
import re, json, sys
from collections import defaultdict
from common import con, names, AGENTS, LO, HI, sample
CAPS = re.compile(r"\b(NEVER|ALWAYS|CRITICAL|DO NOT|DON'T|MUST|RULE|LESSON)\b")  # capitalised keyword
CLAUSE = re.compile(r"(?:^|[:;.!—–(]\s*|\*\*\s*|^[-*\d.)\s]+)(always|never|do not|don't|must)\s+\w", re.I)  # imperative clause
TAG = re.compile(r"\b(lesson|rule|protocol \d+)\b\W{0,4}\s*[:—–-]\s*\S", re.I)  # "Lesson: ..." / "Rule — ..."
def is_rule(l):
    s = l.strip()
    if s.startswith('#') or s.endswith(':') or len(s) < 25: return False  # headings and labels are not rules
    return bool(CAPS.search(s) or CLAUSE.search(s) or TAG.search(s))
c = con(); nm = names(c)
snap = defaultdict(dict)
for r in c.execute('select agent,date,content from memory_days where date>=? and date<?', (LO, HI)):
    if nm[r['agent']] in AGENTS: snap[nm[r['agent']]][r['date']] = r['content']
rows = []; allhits = []
for a in AGENTS:
    per = {}; uniq = set()
    for d in sorted(snap[a]):
        L = [l.strip() for l in snap[a][d].splitlines() if l.strip() and is_rule(l)]
        per[d] = len(L); uniq |= set(L)
        if d == '2026-05-15': allhits += [(a, l) for l in L]
    nlines = len([l for l in snap[a].get('2026-05-15', '').splitlines() if l.strip()])
    rows.append([a, per.get('2026-05-15'), nlines, min(per.values()), max(per.values()), len(uniq)])
    print(rows[-1])
json.dump(rows, open('q2_rules.json', 'w'))
if '--sample' in sys.argv:
    for a, l in sample(allhits): print(f'[{a}] {l[:230]}')
