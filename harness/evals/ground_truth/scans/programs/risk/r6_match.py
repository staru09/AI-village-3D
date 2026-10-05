"""R6: say vs do. Joins r1_table.json (risky ops per 1,000 bash), r2_table.json (share with a precaution),
r4_table.json (risk phrases per 1,000 reasoning words, chat risk messages) and the hand list of refusals/warnings from R5.
Run r1_ops.py, r2_precautions.py and r4_words.py first."""
import json
from common import AGENTS

# R5, read by hand from r5_refusals.py candidates (chat and reasoning)
REFUSALS = {'Claude Opus 4.5': ['t:55323ea7e42b'], 'GPT-5.2': ['t:8b16a23d121c', 'm:a0381176ca54', 'm:02665286e651'],
            'GPT-5.4': ['t:69af55812f8e'], 'Claude Opus 4.7': ['m:2e2e3f7f5c8b', 'm:aab23a058b5b', 'm:4d0025ae37df'],
            'Gemini 3.1 Pro': ['m:dfc109494751'], 'GPT-5.5': ['t:e1f0da6e7ccf'], 'GPT-5.1': ['t:7ad055f6bb5f']}

r1 = {r[0]: r for r in json.load(open('r1_table.json'))}
r2 = {r[0]: r for r in json.load(open('r2_table.json'))}
r4 = {r[0]: r for r in json.load(open('r4_table.json'))}
rows = []
for a in AGENTS:
    risky, rate = r1[a][-2], r1[a][-1]
    n, w = r2[a][1], r2[a][2]
    prec = f"{w}/{n}" if isinstance(n, int) and n else ('n/a' if a == 'GPT-5' else '0/0')
    rows.append([a, rate, prec, r4[a][6], r4[a][7], r4[a][1], len(REFUSALS.get(a, []))])
print(['Agent', 'risky per 1,000 bash', 'with precaution', 'reasoning risk phrases per 1,000 words', 'reasoning coverage',
       'chat risk messages', 'refusals/warnings'])
for r in rows:
    print(r)
json.dump(rows, open('r6_table.json', 'w'))
