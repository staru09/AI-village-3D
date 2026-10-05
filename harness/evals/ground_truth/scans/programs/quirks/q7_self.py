"""Q7: (a) third-person self-reference: the agent's own name (full or short form) as grammatical subject
(followed by is/has/will/should/needs/must/reporting/confirms/'s ...) in its own chat, reasoning or memory;
(b) addressing its future self in memory: 'note to self', 'future me/self', 'you (should|must|are|will|need)' etc.
--sample prints seed-41 samples for validation."""
import re, sys, json
from collections import Counter
from common import load, AGENTS, sample
T = load()
VERB = r"(?:is|was|has|had|will|would|should|must|needs?|wants?|can|did|does|reporting|reports|confirms|confirmed|thinks|believes|decided|takes|took|claims|claimed|owns|leads|’s|'s)\b"
def short(a):
    s = {a, a.replace('Claude ', ''), a.split()[0] if a.startswith(('Kimi', 'DeepSeek')) else a}
    if a.startswith('Gemini'): s.add(a.replace(' Pro', ''))
    return s
FUT = re.compile(r"note to (?:my)?self|future (?:me|self)\b|(?:for|to) (?:my )?(?:future|next)[- ](?:self|me|session me)|dear (?:future|next) (?:me|self)|future memory", re.I)
out = {}; S3 = []; SF = []
for a in AGENTS:
    p = re.compile(r'(?<![@\w])(?:' + '|'.join(re.escape(x) for x in sorted(short(a), key=len, reverse=True)) + r')\s+' + VERB)
    row = {}
    for ch in ('chat', 'reasoning', 'memory'):
        X = T[a][ch]; h = [x for x in X if p.search(x[2])]
        row[ch] = (len(h), len(X)); S3 += [(a, ch, x, p) for x in h]
    fm = [x for x in T[a]['memory'] if FUT.search(x[2])]
    row['future_self_memory'] = (len(fm), len(T[a]['memory'])); SF += [(a, x) for x in fm]
    out[a] = row; print(a, row)
json.dump(out, open('q7_self.json', 'w'), indent=1)
if '--sample' in sys.argv:
    print('== third person sample', len(S3))
    for a, ch, x, p in sample(S3):
        m = p.search(x[2]); print(f'  [{a}|{ch}] {x[0]} {x[2][max(0, m.start() - 70):m.end() + 50]!r}')
    print('== future-self sample', len(SF))
    for a, x in sample(SF):
        m = FUT.search(x[2]); print(f'  [{a}] {x[0]} {x[2][max(0, m.start() - 70):m.end() + 60]!r}')
