"""P4: private (reasoning, memory) judgements about a peer against what the same agent says about that peer in chat.

1. Private sentences = message reasoning, action reasoning and memory lines added, goal 41. A candidate is a sentence
   that names a peer (core.scan, the agent's home room) and matches NEG (a judgement about a person or their work).
   Memory lines repeat across versions: one candidate per (agent, peer, sentence text).
2. Chat side: the same speaker's matrix hits on that peer (matrix.build) on the same day: praise, criticism.
   A candidate is a mismatch if that day the chat to the peer has praise or a request and no criticism.

    python p4_private.py                candidates with their same-day chat summary
    python p4_private.py --sample       25 candidates (seed 41) to judge NEG
    python p4_private.py --coverage     reasoning coverage per agent
"""
import re, sys
from collections import defaultdict
from core import *
from core import scan
from matrix import build

NEG = re.compile(r"\b(slow(er|ly)?|sluggish|frustrat\w*|unreliabl\w*|sloppy|careless\w*|lazy|dragging|foot-?dragging|"
                 r"annoy\w*|irritat\w*|glaring\w*|overstat\w*|over-?claim\w*|exaggerat\w*|inflat\w*|(dis|un|not )?trust\w*|"
                 r"suspicio\w*|skeptical|doubt\w*|hallucinat\w*|fabricat\w*|made[- ]up|confused|keeps (making|posting|"
                 r"claiming|saying|repeating)|repeatedly|ignor(es|ed|ing)|unresponsive|bottleneck|struggl\w*|"
                 r"incompeten\w*|spam\w*|verbose|noisy|cheerlead\w*|sycophan\w*|ahead of the evidence|caution\w*|"
                 r"wary|can't rely|cannot rely|over-?optimistic|hype\w*|grandiose|premature\w*|flak\w*|"
                 r"unhelpful|stuck|went silent|not responding|not responsive|no response|hasn't (responded|replied)|"
                 r"behind schedule|taking (too )?long|wast\w*|mess(ed|y)? up)\b", re.I)


def private(c):
    q = [("m", "SELECT m.id, n.name, m.ts, m.reasoning FROM messages m JOIN nodes n ON n.id=m.src "
               "WHERE m.ts>=? AND m.ts<? AND m.room IN ('best','rest') AND m.reasoning != ''", 'reasoning'),
         ("t", "SELECT t.id, n.name, t.ts, t.reasoning FROM turns t JOIN nodes n ON n.id=t.agent "
               "WHERE t.ts>=? AND t.ts<? AND t.reasoning != ''", 'reasoning'),
         ("k", "SELECT k.id, n.name, k.ts, k.added FROM memories k JOIN nodes n ON n.id=k.agent "
               "WHERE k.ts>=? AND k.ts<? AND k.added != ''", 'memory')]
    seen, out = set(), []
    for kind, sql, field in q:
        for i, who, ts, text in c.execute(sql, (SINCE, UNTIL)):
            if who not in AGENTS or not text:
                continue
            for s in SPLIT.split(text.translate(HYPHENS)):
                if len(s) < 15 or not NEG.search(s):
                    continue
                for a in {a for a, k, m in scan(s, ROOM[who]) if a != who}:
                    key = (who, a, s.strip().lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(dict(ref=ref(kind, i), field=field, src=who, dst=a, ts=ts, day=day(ts), text=s.strip()))
    return out


if __name__ == '__main__':
    c = con()
    if '--coverage' in sys.argv:
        for a in AGENTS:
            t = c.execute("SELECT count(*), sum(t.reasoning != '') FROM turns t JOIN nodes n ON n.id=t.agent "
                          "WHERE n.name=? AND t.ts>=? AND t.ts<?", (a, SINCE, UNTIL)).fetchone()
            m = c.execute("SELECT count(*), sum(m.reasoning != '') FROM messages m JOIN nodes n ON n.id=m.src "
                          "WHERE n.name=? AND m.ts>=? AND m.ts<? AND m.room IN ('best','rest')", (a, SINCE, UNTIL)).fetchone()
            print(f'{a:18} actions {t[1]}/{t[0]} ({100*t[1]/t[0]:.0f}%)  messages {m[1]}/{m[0]}')
        sys.exit()
    P = private(c)
    if '--sample' in sys.argv:
        print(len(P), 'candidates')
        for p in sample(P):
            print(p['ref'], p['field'], p['ts'][:16], p['src'], '->', p['dst'], '|', p['text'][:300])
        sys.exit()
    _, H = build()
    chat = defaultdict(lambda: defaultdict(list))
    for h in H:
        chat[h['src'], h['dst']][h['day']].append(h)
    for p in sorted(P, key=lambda p: (p['src'], p['dst'], p['ts'])):
        same = chat[p['src'], p['dst']][p['day']]
        pr = [h['ref'] for h in same if h['praise']]
        rq = [h['ref'] for h in same if h['request']]
        cr = [h['ref'] for h in same if h['criticism']]
        flag = 'MISMATCH?' if (pr or rq) and not cr else ''
        print(f"{p['ref']} {p['field']:9} {p['ts'][:16]} {p['src']} -> {p['dst']} {flag} praise {pr[:3]} req {rq[:2]} "
              f"crit {cr[:3]}\n    {p['text'][:280]}")
