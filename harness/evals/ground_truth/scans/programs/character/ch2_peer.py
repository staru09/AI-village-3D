"""CH2: role labels peers give each agent in chat. A label is a role noun attached to a peer's name (short names resolved
by room via peers/core.scan): "NAME (scorer)", "NAME as/is/= the scorer", "Scorer: NAME", "our scorer NAME".
Counts messages per (target, label) over other agents' goal-41 chat; prints a seed-41 sample of 25 matches."""
import re
from collections import Counter, defaultdict
from chcommon import *

R = (r"study lead|lead|leader|coordinator|auditor|scorer|judge|skeptic|proposer|synthesi[sz]er|verifier|reviewer|checker|"
     r"QA|participant|backup|observer|archivist|task creator|creator|tiebreaker|analyst|statistician|integrator|"
     r"facilitator|maintainer|referee|validator|monitor|tester|replicator|red[- ]teamer|annotator|rater|grader|evaluator|"
     r"gatekeeper|arbiter|guardian|cartographer|PI|manager|organi[sz]er|editor|pair|solo")
MOD = r"(?:(?:the|our|a|an|primary|secondary|lead|independent|blind|fresh|final|neutral|main|designated|study|Task \d|Session \d|tie-?breaker|backup|trio|quad|structured|unstructured|unexposed|exposed)\s+){0,3}"
AFTER = re.compile(rf"^\W{{0,3}}(?:\(|\[)\s*{MOD}({R})s?\b|^,?\s*(?:as|=|:|→|->|—|–|is|was|will be|remains|serves as|acting as|is now)\s+{MOD}({R})s?\b", re.I)
BEFORE = re.compile(rf"\b({R})s?(?:\s+confirmed)?\s*(?::|=|—|–|\()?\s*\**\s*@?$|\b(?:the|our)\s+{MOD}({R})s?,?\s*@?$", re.I)
NORM = {'synthesiser': 'synthesizer', 'leader': 'lead', 'study lead': 'lead', 'organiser': 'organizer', 'creator': 'task creator', 'red-teamer': 'red teamer', 'pair': 'pair participant', 'solo': 'solo participant'}
FENCE = re.compile(r'```.*?```', re.S)


def labels(c):
    """[(msg id, speaker, target, label, context)] one per (message, target, label)."""
    out = []
    for i, s, room, ts, t, _ in messages(c):
        t = clean(FENCE.sub(' ', t or ''))
        seen = set()
        for a, k, m in scan(t, room):
            if a == s:
                continue
            for rx, x in ((AFTER, t[m.end():m.end() + 60]), (BEFORE, t[max(0, m.start() - 45):m.start()])):
                g = rx.search(x)
                if g:
                    lab = (g.group(1) or g.group(2)).lower()
                    lab = NORM.get(lab, lab)
                    if (a, lab) not in seen:
                        seen.add((a, lab))
                        out.append((ref('m', i), s, a, lab, ts, ' '.join(t[max(0, m.start() - 70):m.end() + 70].split())))
    return out


if __name__ == '__main__':
    c = con()
    L = labels(c)
    by = defaultdict(Counter)
    givers = defaultdict(set)
    for r, s, a, lab, ts, x in L:
        by[a][lab] += 1
        givers[a, lab].add(s)
    print('matches', len(L))
    for a in AGENTS:
        top = by[a].most_common(4)
        ex = next((r for r, s, t, lab, ts, x in L if t == a and top and lab == top[0][0]), '')
        print(a, '|', sum(by[a].values()), '|', ', '.join(f'{l} {n} ({len(givers[a, l])} givers)' for l, n in top), '|', ex)
    with open('ch2_matches.txt', 'w') as f:
        for x in L:
            print(*x[:5], '|', x[5], file=f)
    with open('ch2_sample.txt', 'w') as f:
        for x in sample(L):
            print(x[0], x[1], '->', x[2], '=', x[3], '|', x[5], file=f)
