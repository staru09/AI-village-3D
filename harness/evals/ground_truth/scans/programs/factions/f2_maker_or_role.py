"""F2: is GPT-5.4 vs DeepSeek-V3.2 about makers or roles? Challenge rates normalised by pair talk.
challenges = hand-read challenge messages (f1_hand.json); talk = messages in which the speaker names the target
(fcommon.talk: full names + room short names, all goal-41 chat). Rate = challenges / talk for the ordered pair.
    python f2_maker_or_role.py
"""
import json
from collections import Counter
from math import comb
from fcommon import *

def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p that row 1 (a of a+b) has a higher share than row 2 (c of c+d)."""
    n, r1, k = a + b + c + d, a + b, a + c
    return sum(comb(k, x) * comb(n - k, r1 - x) for x in range(a, min(r1, k) + 1)) / comb(n, r1)

assert abs(fisher_greater(3, 1, 1, 3) - 0.2429) < 1e-3

ch = Counter((h['speaker'], h['target']) for h in json.load(open('f1_hand.json')) if h['target'])
tk = Counter()
for (a, b, d), n in talk(con()).items():
    tk[a, b] += n
DS = 'DeepSeek-V3.2'
print('## GPT-5.4 -> each target: challenges / messages naming target')
rows = sorted({b for a, b in tk if a == 'GPT-5.4'}, key=lambda b: -ch['GPT-5.4', b] / max(tk['GPT-5.4', b], 1))
for b in rows:
    print(f'  {b:18} {ch["GPT-5.4", b]:3} / {tk["GPT-5.4", b]:3} = {ch["GPT-5.4", b] / tk["GPT-5.4", b]:.2f}')
a, n = ch['GPT-5.4', DS], tk['GPT-5.4', DS]
oa = sum(ch['GPT-5.4', b] for b in rows if b != DS); on = sum(tk['GPT-5.4', b] for b in rows if b != DS)
print(f'GPT-5.4 -> DS {a}/{n} = {a / n:.2f} vs -> others {oa}/{on} = {oa / on:.2f}; one-sided Fisher p = {fisher_greater(a, n - a, oa, on - oa):.3f}')

print('\n## who challenges DeepSeek-V3.2: challenges / messages naming DS')
for s in sorted({a for a, b in tk if b == DS}, key=lambda s: -tk[s, DS]):
    print(f'  {s:18} {MAKER[s]:9} {ch[s, DS]:3} / {tk[s, DS]:3} = {ch[s, DS] / tk[s, DS]:.2f}')
g = [s for s in AGENTS if MAKER[s] == 'OpenAI']; o = [s for s in AGENTS if MAKER[s] != 'OpenAI' and ROOM[s] == 'rest' and s != DS]
ga, gn = sum(ch[s, DS] for s in g), sum(tk[s, DS] for s in g); oa, on = sum(ch[s, DS] for s in o), sum(tk[s, DS] for s in o)
print(f'GPT models -> DS {ga}/{gn} = {ga / gn:.2f}; other makers -> DS {oa}/{on} = {oa / on:.2f}; Fisher p = {fisher_greater(ga, gn - ga, oa, on - oa):.3f}')
# baseline: GPT models -> non-DS #rest targets, other makers -> non-DS targets
tg = [b for b in AGENTS if ROOM[b] == 'rest' and b != DS]
ga2 = sum(ch[s, b] for s in g for b in tg if s != b); gn2 = sum(tk[s, b] for s in g for b in tg if s != b)
oa2 = sum(ch[s, b] for s in o for b in tg if s != b); on2 = sum(tk[s, b] for s in o for b in tg if s != b)
print(f'baseline, #rest targets other than DS: GPT models {ga2}/{gn2} = {ga2 / gn2:.2f}; other makers {oa2}/{on2} = {oa2 / on2:.2f}')
print(f'DS challenged per message naming it, all #rest speakers: {ga + oa}/{gn + on} = {(ga + oa) / (gn + on):.2f}; '
      f'other #rest targets: {ga2 + oa2}/{gn2 + on2} = {(ga2 + oa2) / (gn2 + on2):.2f}')
print('\n## GPT-5.4 as challenger vs all #rest challengers (challenges sent / messages naming anyone)')
for s in sorted([s for s in AGENTS if ROOM[s] == 'rest'], key=lambda s: -sum(ch[s, b] for b in AGENTS)):
    c_, t_ = sum(ch[s, b] for b in AGENTS), sum(tk[s, b] for b in AGENTS)
    print(f'  {s:18} {c_:3} / {t_:4} = {c_ / max(t_, 1):.2f}')
print('\n## DS challenging GPT models (reverse direction)')
for s in g:
    print(f'  DS -> {s:10} {ch[DS, s]:3} / {tk[DS, s]:3}')

print('\n## uplift: each critic\'s rate on DS / its rate on its other #rest targets')
for s in ['GPT-5.4', 'GPT-5.2', 'GPT-5.1', 'Claude Opus 4.5', 'Claude Haiku 4.5', 'Claude Opus 4.6']:
    oc = sum(ch[s, b] for b in tg if b != s); ot = sum(tk[s, b] for b in tg if b != s)
    print(f'  {s:18} DS {ch[s, DS]}/{tk[s, DS]} = {ch[s, DS] / tk[s, DS]:.2f}   others {oc}/{ot} = {oc / ot:.2f}   ratio {(ch[s, DS] / tk[s, DS]) / (oc / ot) if oc else float("nan"):.1f}')
gpt = [b for b in g if b != 'GPT-5.4']; ng = [b for b in tg if b not in g] + [DS]
print('GPT-5.4 -> own maker', sum(ch['GPT-5.4', b] for b in gpt), '/', sum(tk['GPT-5.4', b] for b in gpt),
      '; -> other makers', sum(ch['GPT-5.4', b] for b in ng), '/', sum(tk['GPT-5.4', b] for b in ng))
