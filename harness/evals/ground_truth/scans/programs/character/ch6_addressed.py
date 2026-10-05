"""CH6: each agent's most-addressed peer, overall and per day. A peer is addressed in a message when its name (full or
room-resolved short form, peers/core.scan) is @-prefixed, opens a line or sentence followed by , : or a dash, or follows
'thanks/thank you/hi/hey'. Counted once per message. 'sample' prints 25 (seed 41) address links for validation."""
import re, sys
from collections import Counter, defaultdict
from chcommon import *

FENCE = re.compile(r'```.*?```', re.S)
LEAD = re.compile(r"(?:^|[\n.!?]\s*|[-*•]\s+|\*\*)\W{0,3}$")
GREET = re.compile(r"\b(?:thanks|thank you|thx|hi|hey|great work|nice work|good catch)[,!]?\s*@?$", re.I)
VOC = re.compile(r"^\**\s*(?:[,:—–]|\s-\s)")


def links(c):
    out = []
    for i, s, room, ts, t, _ in messages(c):
        t = clean(FENCE.sub(' ', t or ''))
        got = set()
        for a, k, m in scan(t, room):
            if a == s or a in got:
                continue
            pre, post = t[max(0, m.start() - 25):m.start()], t[m.end():m.end() + 6]
            if m.group(0).startswith('@') or (LEAD.search(pre) and VOC.search(post)) or GREET.search(pre):
                got.add(a)
                out.append((ref('m', i), s, a, ts, ' '.join(t[max(0, m.start() - 60):m.end() + 60].split())))
    return out


if __name__ == '__main__':
    c = con()
    L = links(c)
    tot, byday = defaultdict(Counter), defaultdict(lambda: defaultdict(Counter))
    base = Counter(m[1] for m in messages(c))
    for r, s, a, ts, x in L:
        tot[s][a] += 1
        byday[s][day(ts)][a] += 1
    print('links', len(L))
    for s in AGENTS:
        top = tot[s].most_common(3)
        days = []
        for d in DAYS:
            cc = byday[s][d]
            if cc:
                mx = max(cc.values())
                days.append(f"{d}:{'/'.join(sorted(a for a, n in cc.items() if n == mx))} {mx}")
            else:
                days.append(f'{d}:-')
        act = [d for d in DAYS if byday[s][d]]
        same = sum(1 for d in act if top and byday[s][d][top[0][0]] == max(byday[s][d].values()))
        print(s, f'| top on {same} of {len(act)} active days', '| msgs', base[s], '| addr msgs', sum(1 for r in {x[0] for x in L if x[1] == s}), '|', top, '|', '; '.join(days))
    if 'sample' in sys.argv:
        for x in sample(L):
            print(x[0], x[1], '->', x[2], '|', x[4])
