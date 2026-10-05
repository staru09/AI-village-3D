"""CH5 (named topics): Title-Case 2-3 word names (projects, worlds, constructs) in the agent's own chat text (cleaned as
CH4) and session intents, used on >= 3 of the 5 days; agent names, weekdays, months, Day/Session/Task labels excluded.
Ranks by days then uses; 'unprompted' days as in ch5_recurring. The agent's share of all uses is shown."""
import re
from collections import Counter, defaultdict
from chcommon import *
from ch4_signature import own
from ch5_recurring import unprompted

NAME = re.compile(r"\b(?:[A-Z][a-z][\w'-]*|HUD|RCT|QA|PR)(?:\s+(?:[A-Z][a-z][\w'-]*|HUD|RCT|QA|of|the)){1,3}\b")
BAD = re.compile(r"\b(Claude|Opus|Sonnet|Haiku|Gemini|GPT|Kimi|DeepSeek|Monday|Tuesday|Wednesday|Thursday|Friday|May|Day|Session|Task|PT|AM|PM|"
                 r"Shoshannah|Adam|Zak|I|The|This|That|My|Our|We|All|Next|Current|Final|Status|Update|Key|New|Ready|Confirmed|Done)\b")


def names(t):
    out = set()
    for m in NAME.finditer(t):
        w = re.sub(r'(\s+(of|the))+$', '', m.group(0))
        w = re.sub(r"^(The|A|An)\s+", '', w)
        if len(w.split()) >= 2 and not BAD.search(w):
            out.add(w.lower())
    return out


def texts(c):
    out = [(a, room, ts, ref('m', i), names(own(t))) for i, a, room, ts, t, _ in messages(c)]
    out += [(a, ROOM[a], ts, ref('s', i), names(own(t))) for i, a, ts, t in sessions(c)]
    return sorted(out, key=lambda x: x[2])


if __name__ == '__main__':
    import sys
    T = texts(con())
    users = defaultdict(Counter)
    for x in T:
        for g in x[4]:
            users[g][x[0]] += 1
    for a in AGENTS:
        days, cnt, first = defaultdict(set), Counter(), {}
        for x in T:
            if x[0] == a:
                for g in x[4]:
                    days[g].add(day(x[2])); cnt[g] += 1; first.setdefault(g, x[3])
        cands = sorted((g for g in days if len(days[g]) >= 3), key=lambda g: (-len(days[g]), -cnt[g]))[:6]
        print('##', a)
        for g in cands:
            share = cnt[g] / sum(users[g].values())
            print(f'   {g!r}: days {len(days[g])} uses {cnt[g]} share {share:.0%} unprompted {len(unprompted(T, a, g))} first {first[g]}')
