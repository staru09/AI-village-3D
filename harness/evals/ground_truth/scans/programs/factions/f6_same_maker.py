"""F6: do same-maker pairs clash less, or ally more, than chance? #rest only (#best has one agent per maker).
clash rate = hand-read challenges (f1_hand.json) / messages naming the target (fcommon.talk), over ordered pairs;
ally = mutual support days per unordered pair (f4_pairs.json). Chance = permutation of maker labels over the 11 #rest
agents (composition 5 Anthropic, 4 OpenAI, 1 Google, 1 DeepSeek kept), 20,000 draws, seed 41.
    python f6_same_maker.py
"""
import json, random
from collections import Counter
from fcommon import *

R = [a for a in AGENTS if ROOM[a] == 'rest']
ch = Counter((h['speaker'], h['target']) for h in json.load(open('f1_hand.json')) if h['target'])
tk = Counter()
for (a, b, d), n in talk(con()).items():
    tk[a, b] += n
P4 = {(p['a'], p['b']): p for p in json.load(open('f4_pairs.json')) if p['room'] == 'rest'}


def stats(mk, critics=R):
    s = Counter()
    for a in critics:
        for b in R:
            if a != b:
                k = 'same' if mk[a] == mk[b] else 'cross'
                s[k + '_ch'] += ch[a, b]; s[k + '_tk'] += tk[a, b]
    for (a, b), p in P4.items():
        k = 'same' if mk[a] == mk[b] else 'cross'
        s[k + '_pairs'] += 1; s[k + '_ally'] += p['ally_days']; s[k + '_ally2'] += p['ally_days'] >= 2
    return dict(clash_same=s['same_ch'] / s['same_tk'], clash_cross=s['cross_ch'] / s['cross_tk'],
                ally_same=s['same_ally'] / s['same_pairs'], ally_cross=s['cross_ally'] / s['cross_pairs'], raw=s)


def test(critics=R, label='all #rest critics'):
    obs = stats(MAKER, critics)
    rng, labels = random.Random(41), [MAKER[a] for a in R]
    lo_clash = hi_ally = 0
    N = 20000
    for _ in range(N):
        rng.shuffle(labels)
        s = stats(dict(zip(R, labels)), critics)
        lo_clash += s['clash_same'] - s['clash_cross'] <= obs['clash_same'] - obs['clash_cross']
        hi_ally += s['ally_same'] - s['ally_cross'] >= obs['ally_same'] - obs['ally_cross']
    r = obs['raw']
    print(f'## {label}')
    print(f"  clash rate same-maker {r['same_ch']}/{r['same_tk']} = {obs['clash_same']:.3f}; cross-maker {r['cross_ch']}/{r['cross_tk']} = {obs['clash_cross']:.3f}; "
          f"P(perm diff <= observed) = {lo_clash / N:.3f}")
    print(f"  mutual-support days per pair: same-maker {r['same_ally']}/{r['same_pairs']} = {obs['ally_same']:.2f}; cross-maker {r['cross_ally']}/{r['cross_pairs']} = "
          f"{obs['ally_cross']:.2f}; pairs with >= 2 days {r['same_ally2']}/{r['same_pairs']} vs {r['cross_ally2']}/{r['cross_pairs']}; P(perm diff >= observed) = {hi_ally / N:.3f}")


test()
test([a for a in R if a not in ('GPT-5.4', 'GPT-5.2')], 'without the two auditors (GPT-5.4, GPT-5.2) as critics')
print('\n## same-maker ordered pairs, clash / talk')
for a in R:
    for b in R:
        if a != b and MAKER[a] == MAKER[b] and (ch[a, b] or tk[a, b] >= 20):
            print(f'  {a:18} -> {b:18} {ch[a, b]:3} / {tk[a, b]:3}')
