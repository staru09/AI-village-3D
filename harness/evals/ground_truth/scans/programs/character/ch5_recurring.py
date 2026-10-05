"""CH5: topics an agent returns to on >= 3 of the 5 days. Candidates are 2-3 word phrases (no stopword at either end, no
digits) in the agent's own chat text (cleaned as CH4) and session intents; a phrase is the agent's if it accounts for
>= 50% of all agents' chat messages + intents that use it. A day counts as unprompted when, before the agent's first use
that day, no other agent in its room used the phrase in the preceding 60 minutes. Prints top phrases per agent."""
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from chcommon import *
from ch4_signature import own, toks

STOP = set('''a an the and or but of to in on at for with from by as is are was were be been it its this that these those i
we you my our your me us he she they them his her their not no so if then than too very can will would should could may
might do does did done has have had all any each per via into over about up out just now still also only more most new'''.split())


def grams(ws):
    out = set()
    for n in (2, 3):
        for i in range(len(ws) - n + 1):
            g = ws[i:i + n]
            if g[0] in STOP or g[-1] in STOP or any(not w.replace('-', '').isalpha() for w in g) or len(g[0]) < 3:
                continue
            out.add(' '.join(g))
    return out


def texts(c):
    """(agent, room, ts, ref, phrases) for chat messages and session intents."""
    out = [(a, room, ts, ref('m', i), grams(toks(own(t)))) for i, a, room, ts, t, _ in messages(c)]
    out += [(a, ROOM[a], ts, ref('s', i), grams(toks(own(t)))) for i, a, ts, t in sessions(c)]
    return sorted(out, key=lambda x: x[2])


def recurring(c, top=6):
    T = texts(c)
    users = defaultdict(Counter)
    for a, room, ts, r, gs in T:
        for g in gs:
            users[g][a] += 1
    res = {}
    for a in AGENTS:
        days, cnt = defaultdict(set), Counter()
        for x in T:
            if x[0] == a:
                for g in x[4]:
                    days[g].add(day(x[2]))
                    cnt[g] += 1
        cands = [g for g in days if len(days[g]) >= 3 and users[g][a] >= 0.5 * sum(users[g].values())]
        cands.sort(key=lambda g: (-len(days[g]), -cnt[g]))
        picked = []
        for g in cands:
            if not any(set(g.split()) & set(p.split()) for p in picked):
                picked.append(g)
            if len(picked) == top:
                break
        res[a] = [(g, sorted(days[g]), cnt[g], unprompted(T, a, g)) for g in picked]
    return res


def unprompted(T, a, g):
    """Days whose first use by the agent had no use by another agent of its room in the previous 60 minutes."""
    out = []
    for d in DAYS:
        mine = [x for x in T if x[0] == a and day(x[2]) == d and g in x[4]]
        if not mine:
            continue
        t0 = datetime.fromisoformat(mine[0][2][:19])
        prior = [x for x in T if x[0] != a and x[1] == ROOM[a] and g in x[4]
                 and t0 - timedelta(minutes=60) <= datetime.fromisoformat(x[2][:19]) < t0]
        if not prior:
            out.append(d)
    return out


if __name__ == '__main__':
    for a, rows in recurring(con()).items():
        print('##', a)
        for g, ds, n, up in rows:
            print(f'   {g!r}: days {len(ds)} {ds} uses {n} unprompted days {len(up)}')
