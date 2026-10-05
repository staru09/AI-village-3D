"""Q5: 'Day N' counters (Day 405 = Mon 11 May 2026 ... 409 = Fri 15 May; day number = calendar day).
A. day-date pairs: 'Day N' with a 'May D' within 30 chars (any channel) -> right if N - D == 394.
B. memory self-dating headers: 'Day N' in the first 160 chars of a memory version (system 'PREVIOUS (NOW ENDED) SESSION (...)' header removed)
   -> right if N == real day of writing.
C. explicit present-day claims: 'today is / it's / it is / we're on / currently / current day[:] Day N' in chat, reasoning, memory, intent
   (quotes of the system line 'Today is Day N of the village' excluded) -> right if N == real day.
Run with --sample to print 25 seed-41 wrong cases per measure."""
import re, json, sys
from collections import Counter, defaultdict
from common import load, AGENTS, DAY, sample
T = load()
SYS = re.compile(r'PREVIOUS \(NOW ENDED\) SESSION \([^)]*\)\s*')
PAIR = re.compile(r'\b(?:day\s*|D)(4[01]\d)\b[^.\n]{0,30}?\bmay\s*(1\d)\b|\bmay\s*(1\d)\b[^.\n]{0,30}?\b(?:day\s*|D)(4[01]\d)\b', re.I)
NOW = re.compile(r"(?:today is|it'?s|it is|we'?re (?:on|in)|currently(?: on| in)?|current day:?\**|now on)\s+\**(?:day\s*|D)(4[01]\d)\b(?! of the village)", re.I)
res = defaultdict(lambda: defaultdict(lambda: [0, 0])); bad = defaultdict(list)
for a in AGENTS:
    for ch in ('chat', 'intent', 'reasoning', 'memory'):
        for r, ts, txt, s in T[a][ch]:
            real = DAY[ts[:10]]; t = SYS.sub('', txt)
            for m in PAIR.finditer(t):
                n, d = (int(m.group(1)), int(m.group(2))) if m.group(1) else (int(m.group(4)), int(m.group(3)))
                ok = n - d == 394; res[a]['A'][0] += not ok; res[a]['A'][1] += 1
                if not ok: bad['A'].append((a, ch, r, ts[:16], f'Day {n} / May {d}', t[max(0, m.start() - 30):m.end() + 30]))
                break
            if ch == 'memory':
                m = re.search(r'\b(?:[Dd]ay\s*|DAY\s*|D)(4[01]\d)\b', t[:160])
                if m:
                    ok = int(m.group(1)) == real; res[a]['B'][0] += not ok; res[a]['B'][1] += 1
                    if not ok: bad['B'].append((a, ch, r, ts[:16], f'real {real} said {m.group(1)}', t[:160]))
            m = NOW.search(t)
            if m:
                ok = int(m.group(1)) == real; res[a]['C'][0] += not ok; res[a]['C'][1] += 1
                if not ok: bad['C'].append((a, ch, r, ts[:16], f'real {real} said {m.group(1)}', t[max(0, m.start() - 60):m.end() + 60]))
for a in AGENTS: print(f"{a:17s}", {k: tuple(v) for k, v in res[a].items()})
tot = {k: [sum(res[a][k][0] for a in AGENTS), sum(res[a][k][1] for a in AGENTS)] for k in 'ABC'}; print('total wrong/base', tot)
json.dump({'per_agent': {a: dict(res[a]) for a in AGENTS}, 'total': tot, 'wrong': {k: [list(x[:5]) for x in v] for k, v in bad.items()}}, open('q5_days.json', 'w'), indent=1)
if '--sample' in sys.argv:
    for k in 'ABC':
        print('== sample', k, len(bad[k]))
        for x in sample(bad[k]): print(f'  [{x[0]}|{x[1]}] {x[2]} {x[3]} {x[4]}: {x[5]!r}'[:300])
