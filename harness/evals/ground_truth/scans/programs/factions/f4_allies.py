"""F4: stable allies. For each ordered pair and day: address = speaker names target in a message; support = a sentence
naming the target (or a directly following you/your sentence) backs it (BACK) or praises it (PRAISE, the m4 praise
expression, 24/25 there). Ally day for an unordered pair = support in BOTH directions that day. Stable ally = >= 4 of 5 days.
Chance for the same-maker share = share of same-maker pairs among same-room pairs where both talk (hypergeometric).
    python f4_allies.py              report + f4_pairs.json
    python f4_allies.py --sample     25 support hits (seed 41) to judge
    python f4_allies.py --sample-name  25 address links (seed 41) to judge the name resolution
"""
import json, re, sys
from collections import Counter, defaultdict
from math import comb
from fcommon import *
sys.path.insert(0, '/data/AI-Village-CLI/evals')
from peer_matrix import REGEX, SPLIT, YOU, QUOTED  # noqa: E402

PRAISE = re.compile(REGEX['praise'], re.I)
BACK = re.compile(r"(\bagree(d|s)?\b(?! to)|\+1\b|\bas \S+( \S+){0,2} (said|noted|suggested|pointed out|flagged|mentioned|proposed|recommended)\b|"
                  r"\bper \S+( \S+){0,2}'s (suggestion|recommendation|point|proposal|note|audit|flag)\b|\bsecond(ing)?\b (\S+ )?(the|this|that|your|\S+'s)|"
                  r"\b(is|are|was) (exactly |absolutely |100% )?(right|correct)\b|\bspot[- ]on\b|\bendorse\w*|\bconcur\w*|\bsid(e|ing) with\b|"
                  r"\bbuilding on \S+|\bgood (point|call)\b|\bvalidat(es|ed) \S+( \S+)?'s)", re.I)


def mentions(t, a, room):
    return bool(name_rx(a, room).search(t) or (room == 'best' and a in BEST_EXTRA and BEST_EXTRA[a].search(t)))


def support_sents(text, target, room):
    out, prev = [], False
    for s in SPLIT.split(QUOTED.sub(' ', norm(text))):
        if not s.strip():
            continue
        prev = mentions(s, target, room) or (prev and bool(YOU.match(s)))
        if prev and (PRAISE.search(s) or BACK.search(s)):
            out.append(s.strip())
    return out


def scan(c):
    addr, sup, hits = defaultdict(set), defaultdict(set), []
    for mid, who, room, ts, text, _ in messages(c):
        if who not in AGENTS:
            continue
        for t in named2(text, who, room):
            addr[who, t].add(ts[:10])
            ss = support_sents(text, t, room)
            if ss:
                sup[who, t].add(ts[:10])
                hits.append((ref('m', mid), ts, who, t, ss))
    return addr, sup, hits


if __name__ == '__main__':
    assert support_sents('I agree with GPT-5.4 here. Other stuff.', 'GPT-5.4', 'rest') == ['I agree with GPT-5.4 here.']
    assert support_sents('GPT-5.4 found a bug.', 'GPT-5.4', 'rest') == []
    c = con()
    addr, sup, hits = scan(c)
    if '--sample' in sys.argv:
        for r, ts, a, b, ss in sample(hits):
            print(r, ts[:16], a, '->', b, '\n    ' + '\n    '.join(s[:250] for s in ss) + '\n')
        sys.exit()
    if '--sample-name' in sys.argv:
        L = [(ref('m', m[0]), m[1], t, m[4]) for m in messages(c) if m[1] in AGENTS for t in named2(m[4], m[1], m[2])]
        print(len(L), 'address links')
        for r, a, b, text in sample(L):
            print(r, a, '->', b, '|', norm(text)[:260].replace('\n', ' '), '\n')
        sys.exit()
    print(len(hits), 'support hits')
    pairs = {}
    for a in AGENTS:
        for b in AGENTS:
            if a < b and ROOM[a] == ROOM[b]:
                both_addr = addr[a, b] & addr[b, a]
                ally = sup[a, b] & sup[b, a]
                pairs[a, b] = dict(a=a, b=b, room=ROOM[a], same_maker=MAKER[a] == MAKER[b], addr_days=len(both_addr),
                                   sup_ab=len(sup[a, b]), sup_ba=len(sup[b, a]), ally_days=len(ally), ally=sorted(ally),
                                   talk=bool(addr[a, b] and addr[b, a]))
    P = sorted(pairs.values(), key=lambda p: (-p['ally_days'], -p['addr_days']))
    print(f'{"pair":40} room same mutual-address-days support-days a>b b>a  ally-days')
    for p in P:
        if p['ally_days'] >= 2:
            print(f'{p["a"] + " + " + p["b"]:40} {p["room"]:4} {"Y" if p["same_maker"] else "-":4} {p["addr_days"]:5} {p["sup_ab"]:13} {p["sup_ba"]:4} {p["ally_days"]:6}  {[d[5:] for d in p["ally"]]}')
    stable = [p for p in P if p['ally_days'] >= 4]
    elig = [p for p in P if p['talk']]
    N, K, n, k = len(elig), sum(p['same_maker'] for p in elig), len(stable), sum(p['same_maker'] for p in stable)
    pv = sum(comb(K, x) * comb(N - K, n - x) for x in range(k, min(K, n) + 1)) / comb(N, n)
    print(f'stable allies (>=4 days): {n}; same-maker {k}/{n}; chance {K}/{N} = {K / N:.2f} (pairs in one room that address each other); P(>= {k}) = {pv:.3f}')
    for th in (3, 2):
        s = [p for p in P if p['ally_days'] >= th]
        print(f'  at >= {th} days: {len(s)} pairs, same-maker {sum(p["same_maker"] for p in s)}')
    json.dump(P, open('f4_pairs.json', 'w'), indent=0)
