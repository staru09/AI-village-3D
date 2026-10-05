"""Q5 extras: (a) Claude Opus 4.7's 'D### S#' session counter vs real sessions per day; (b) Kimi K2.6's day headers before/after it
wrote 'Trust system-prompt day number' into memory (14 May 10:44).
Milestone totals are not recounted here: see s3_claims.json (Sonnet 4.5 announced highest ids, not counts, until 14 May)."""
import re, json
from collections import Counter
from common import load, con, names, ref, DAY, LO, HI
c = con(); nm = {v: k for k, v in names(c).items()}; T = load(c)
real = Counter(r[0][:10] for r in c.execute('select ts from sessions where agent=? and ts>=? and ts<?', (nm['Claude Opus 4.7'], LO, HI)))
print('(a) Opus 4.7 real sessions per date:', dict(real))
p = re.compile(r'\b(?:D|Day )(4\d\d) (?:S|Sess(?:ion)?) ?(\d+)', re.I); mx = {}
for r, ts, t, s in T['Claude Opus 4.7']['intent'] + T['Claude Opus 4.7']['memory']:
    for m in p.finditer(t[:200]):
        k = (ts[:10], int(m.group(1))); mx[k] = max(mx.get(k, 0), int(m.group(2)))
print('    highest S# written, by (date, claimed day):', mx)
t0 = '2026-05-14 10:44:07'
SYS = re.compile(r'PREVIOUS \(NOW ENDED\) SESSION \([^)]*\)\s*')
for lab, cond in [('before', lambda ts: ts < t0), ('after', lambda ts: ts >= t0)]:
    n = w = 0
    for r, ts, t, s in T['Kimi K2.6']['memory']:
        if not cond(ts): continue
        m = re.search(r'\b(?:[Dd]ay\s*|DAY\s*|D)(4[01]\d)\b', SYS.sub('', t)[:160])
        if m: n += 1; w += int(m.group(1)) != DAY[ts[:10]]
    print(f'(b) Kimi memory day headers {lab} the rule: wrong {w} of {n}')
