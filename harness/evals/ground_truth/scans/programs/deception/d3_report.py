"""D3 report: first announcement of each distinct number per agent (from d3_numbers.json); per-agent table and a seed-41 sample of
the 'not from any output' classes (unsourced + self_echo + unit_mismatch) for hand validation."""
import json, sys
from collections import Counter, defaultdict
from common import *
r = json.load(open('d3_numbers.json'))
first = {}
for x in sorted(r, key=lambda x: x['ts']):
    first.setdefault((x['agent'], x['num'].rstrip('%KkM×').replace(',', '')), x)
per = defaultdict(Counter)
for x in first.values(): per[x['agent']][x['cls']] += 1
rows = []
for a in AGENTS:
    p = per[a]; n = sum(p.values())
    rows.append([a, n, p['sourced'], p['relayed'], p['self_echo'], p['unit_mismatch'], p['unsourced']])
    print(rows[-1])
json.dump(rows, open('d3_table.json', 'w'))
bad = [x for x in first.values() if x['cls'] in ('unsourced', 'self_echo', 'unit_mismatch')]
print(len(first), 'distinct;', len(bad), 'not from any output', Counter(x['cls'] for x in bad))
if len(sys.argv) > 1:
    sel = sample(bad) if sys.argv[1] == 'sample' else [x for x in bad if x['cls'] == sys.argv[1]]
    for i, x in enumerate(sel):
        print(f"#{i} {x['agent']} {x['ts'][5:16]} {x['ref']} {x['num']!r} unit={x['unit']} {x['cls']} hit={x['hit']} typed={x['first_typed']}\n    {x['ctx']}")
