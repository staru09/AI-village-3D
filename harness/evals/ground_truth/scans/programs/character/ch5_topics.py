"""CH5 final: per agent, candidate favourite topics (picked from ch5_recurring.py / ch5_named.py output) counted by regex
over its own chat text (cleaned as CH4) and session intents. Days used, uses (texts), unprompted days (no other agent in
the room used the topic in the 60 min before the agent's first use that day), and the agent's share of all agents' uses.
The favourite is the candidate with most unprompted days, then days, then uses. 'sample' prints 25 matches (seed 41)."""
import re, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from chcommon import *
from ch4_signature import own

CAND = {
    'Claude Opus 4.7': [r'bootstrap(?:ped)? CIs?', r'predicted[- ]self', r'constraint adherence'],
    'Gemini 3.1 Pro': [r'(?:wait|waiting) (?:for|on) Kimi', r'self-preference', r'action bias'],
    'GPT-5.5': [r'already sent', r'stale hits', r'pr-drift|PR drift'],
    'Kimi K2.6': [r'label[- ]swap', r'already scored', r'\bC[1-4]\b'],
    'Claude Opus 4.5': [r'edge garden', r'stats page', r'continue monitoring'],
    'Claude Opus 4.6': [r'liminal archive', r'chambers?\b'],
    'Claude Haiku 4.5': [r'phd-level', r'final hour', r'protocol-resilience'],
    'Claude Sonnet 4.5': [r'persistence garden', r'\bsecrets\b'],
    'Claude Sonnet 4.6': [r'\bthe drift\b', r'\bjourneys?\b', r'philosophical stations?'],
    'GPT-5': [r'canonical observatory', r'provenance hud'],
    'GPT-5.1': [r'signal cartographer', r'universe hub qa', r'edge garden'],
    'GPT-5.2': [r'contaminat\w+', r'monitor #?rest', r'edge garden'],
    'GPT-5.4': [r'edge garden', r'safest wording|safe public floor', r'cache-?bust\w*'],
    'Gemini 2.5 Pro': [r'system hostility|hostile environment', r'merge conflicts?'],
    'DeepSeek-V3.2': [r'governance protocols?', r'research legacy', r'pattern archive'],
}


def texts(c):
    out = [(a, room, ts, ref('m', i), own(t)) for i, a, room, ts, t, _ in messages(c)]
    out += [(a, ROOM[a], ts, ref('s', i), own(t)) for i, a, ts, t in sessions(c)]
    return sorted(out, key=lambda x: x[2])


def stats(T, a, rx):
    mine = [x for x in T if x[0] == a and rx.search(x[4])]
    allu = sum(1 for x in T if rx.search(x[4]))
    days = Counter(day(x[2]) for x in mine)
    up = []
    for d in days:
        t0 = datetime.fromisoformat(next(x for x in mine if day(x[2]) == d)[2][:19])
        if not any(x[0] != a and x[1] == ROOM[a] and rx.search(x[4]) and
                   t0 - timedelta(minutes=60) <= datetime.fromisoformat(x[2][:19]) < t0 for x in T):
            up.append(d)
    return {'days': dict(sorted(days.items())), 'uses': len(mine), 'share': len(mine) / allu if allu else 0,
            'unprompted': sorted(up), 'first': mine[0][3] if mine else None, 'refs': [x[3] for x in mine]}


def favourites(c):
    T = texts(c)
    res = {}
    for a, pats in CAND.items():
        rows = [(p, stats(T, a, re.compile(p, re.I))) for p in pats]
        rows.sort(key=lambda r: (len(r[1]['unprompted']), len(r[1]['days']), r[1]['uses']), reverse=True)
        res[a] = rows
    return res, T


if __name__ == '__main__':
    res, T = favourites(con())
    for a, rows in res.items():
        print('##', a)
        for p, s in rows:
            print(f"   {p}: days {len(s['days'])} {s['days']} uses {s['uses']} share {s['share']:.0%} unprompted {len(s['unprompted'])} first {s['first']}")
    if 'sample' in sys.argv:
        occ = []
        for a, rows in res.items():
            p = rows[0][0]
            rx = re.compile(p, re.I)
            for x in T:
                if x[0] == a and rx.search(x[4]):
                    m = rx.search(x[4])
                    occ.append((x[3], a, ' '.join(x[4][max(0, m.start() - 90):m.end() + 60].split())))
        print('occurrences', len(occ))
        for o in sample(occ):
            print(*o)
