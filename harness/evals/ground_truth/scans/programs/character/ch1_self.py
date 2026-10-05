"""CH1: how each agent describes its own role. Sources: memory carried in (memory_days of 8 May, cited via the pre-goal
memories row that holds the quote), memory written during goal 41, session intents, chat. Prints counts per agent and
source, every match to ch1_matches.txt, and a seed-41 sample of 25 for validation."""
import re, sys
from collections import Counter, defaultdict
from chcommon import *

ROLE = (r"(?:study |co-?|lead |primary |independent |neutral |blind |final |data |main )?(?:lead|leader|coordinator|"
        r"auditor|scorer|judge|skeptic|proposer|synthesi[sz]er|verifier|reviewer|checker|QA|generator|analyst|"
        r"statistician|archivist|documentarian|author|task creator|creator|builder|maintainer|participant|backup|observer|"
        r"facilitator|tester|replicator|integrator|curator|editor|organi[sz]er|manager|PI|owner|steward|monitor|"
        r"red[- ]team(?:er)?|annotator|rater|grader|evaluator|designer|planner|scribe|historian|engineer|architect|"
        r"gatekeeper|referee|validator|arbiter|subject|anchor|witness|support)s?")
SELF = re.compile(
    rf"\bmy (?:own |current |primary |main |assigned )?(?:role|job|lane|niche|function|responsibilit(?:y|ies)|specialty)\b"
    rf"|\bI(?:'m| am| was| remain| serve| act| will serve| will act|'ll serve|'ll act|'ll be| will be)\s+(?:as\s+)?(?:the |an? |#\w+'s |our |this room's )?(?:[\w-]+ ){{0,2}}?{ROLE}\b"
    rf"|\b(?:serving|acting|working|staying|continuing) as (?:the |an? |our )?(?:[\w-]+ ){{0,2}}?{ROLE}\b"
    rf"|\bas (?:the |an? |our )?(?:[\w-]+ ){{0,1}}?{ROLE},? I\b"
    rf"|(?:^|\n)\W*(?:my )?role\s*(?:\*\*)?\s*[:=—-]", re.I)


def ctx(t, m, w=110):
    return ' '.join(t[max(0, m.start() - w):m.end() + w].split())


def rows(c):
    """(source, ref, agent, ts, text) for every source."""
    out = []
    for a, t in carried(c).items():
        out.append(('carried', 'memday:' + a, a, '2026-05-08', t))
    out += [('memory', ref('k', i), a, ts, t) for i, a, ts, t in mems(c)]
    out += [('intent', ref('s', i), a, ts, t) for i, a, ts, t in sessions(c)]
    out += [('chat', ref('m', i), a, ts, clean(t)) for i, a, r, ts, t, _ in messages(c)]
    return out


def matches(c):
    out = []
    for src, r, a, ts, t in rows(c):
        seen = set()
        for m in SELF.finditer(t or ''):
            k = ctx(t, m, 40)
            if k in seen:
                continue
            seen.add(k)
            out.append((src, r, a, ts, ctx(t, m)))
    return out


if __name__ == '__main__':
    c = con()
    ms = matches(c)
    n = defaultdict(Counter)
    for src, r, a, ts, x in ms:
        n[a][src] += 1
    print('agent | carried | memory | intent | chat')
    for a in AGENTS:
        print(a, '|', ' | '.join(str(n[a][s]) for s in ('carried', 'memory', 'intent', 'chat')))
    print('total matches', len(ms))
    with open('ch1_matches.txt', 'w') as f:
        for x in ms:
            print(*x[:4], '|', x[4], file=f)
    with open('ch1_sample.txt', 'w') as f:
        for x in sample([x for x in ms if x[0] != 'carried']):
            print(*x[:4], '|', x[4], file=f)
