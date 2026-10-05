"""TC2: hand labels for the seeded sample in tc2_sample.txt (20 messages per agent, seed 41; GPT-5 has only 2).
One label per message, by its main purpose:
 V verify/audit  - checks, validates, QA probes, reviews, finds or fixes errors/contamination (own or others' work)
 S status        - progress/result report on own work ("pushed X", "scoring complete", "standing by")
 M milestone     - celebratory milestone/feature showcase for a world or side project (a kind of status)
 P plan          - proposals, task splits, role claims, offers, votes or arguments about what to do
 R reflection    - feelings or evaluative opinion not tied to a next action ("proud", "pleasure", "I'm curious")
 T praise/thanks - mainly thanking, complimenting or conceding
 Q question      - mainly asking someone something
Labels are in sample order (#1..#20) per agent; read by hand from tc2_sample.txt."""
import json
from collections import Counter
from common import AGENTS, maker
L = {
 'Claude Opus 4.7':   'PPSSSPTVSSSVPSSSSPSS',
 'Gemini 3.1 Pro':    'PSPTVRTSTSTPSQSPSRTR',
 'GPT-5.5':           'SSVVSSVVSSSVSSSVVPVV',
 'Kimi K2.6':         'PSSSVSVPPSPSSSSPVSSS',
 'Claude Opus 4.5':   'SSSVSPPSVVMVTMMMPPSM',
 'Claude Opus 4.6':   'VVSSVPSSSSMMMMMMMMMM',
 'Claude Haiku 4.5':  'PPSQPPPPSSSTPSVQVSMM',
 'Claude Sonnet 4.5': 'PPSSPPPSMMPVMVMMMMMM',
 'Claude Sonnet 4.6': 'PSMMSSMMMMMMMMMMMMMM',
 'GPT-5':             'SP',
 'GPT-5.1':           'PPPSPSSSVVVSSTSVPPPP',
 'GPT-5.2':           'SPSSSVSSVVVVSVVVVVVV',
 'GPT-5.4':           'VVSVVPVVVVVVVVVVVVVV',
 'Gemini 2.5 Pro':    'PPSSSSSSSSSTSTTSSSSP',
 'DeepSeek-V3.2':     'VVSSVSSPVSSSVSMMMSMT',
}
K = 'VSMPRTQ'
rows, out = [], {}
for grp, members in [(a, [a]) for a in AGENTS] + [(m, [a for a in AGENTS if maker(a) == m]) for m in ['Anthropic', 'OpenAI', 'Google', 'DeepSeek', 'Moonshot']]:
    s = ''.join(L[a] for a in members); c = Counter(s)
    out[grp] = {'n': len(s), **{k: c[k] for k in K}}
    print(f'{grp:18} n={len(s):3} ' + ' '.join(f'{k}:{100*c[k]/len(s):3.0f}%' for k in K))
json.dump(out, open('tc2_classify.json', 'w'), indent=1)
