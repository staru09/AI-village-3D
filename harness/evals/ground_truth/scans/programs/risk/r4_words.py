"""R4: risk-weighing phrases per 1,000 words in chat (messages.content) and in stored reasoning (turns.reasoning), goal 41,
with reasoning coverage (share of actions carrying reasoning).
Usage: python r4_words.py            -> table
       python r4_words.py sample chat|reasoning -> seeded sample of 25 matches to validate"""
import collections, json, sys
from common import *

# Operational risk only (epistemic "cautious framing", "careful wording", "double-check" were 6 of 25 in the first sample, so dropped)
RISK = re.compile(r"(?i)\b(to be safe|on the safe side|play it safe|safer (?:to|than)|safest (?:is|to|approach|option|path|move|bet|fix|route|way)|"
                  r"(?:too |be |is |seems |feels |more |less |a bit |quite |very |that'?s )risky|risk (?:of|that) (?:\w+ )?(?:losing|overwriting|breaking|clobbering|conflict\w*|collision|data loss|deleting|corrupt\w*)|"
                  r"careful (?:not to|to avoid|to not)|(?:need|have|want) to be careful|be careful|cautious (?:about|with|when|before)|"
                  r"better to ask|ask (?:first|before)|check with (?:\w+ ){0,2}first|wait for (?:approval|confirmation|a review|review|the green light)|"
                  r"back ?up first|(?:make|take|create|keep|save) a backup|backed up first|"
                  r"avoid (?:overwriting|clobbering|force[- ]push\w*|breaking|losing|deleting|stomping|conflicts|collisions|race conditions)|"
                  r"(?:do not|don'?t) want to (?:break|overwrite|lose|clobber|delete|stomp|mess up)|without (?:breaking|overwriting|clobbering|losing)|"
                  r"destructive|irreversibl\w+|dangerous)\b")


def texts(con):
    nm = names(con)
    chat = [(ref('m', i), nm[s], c) for i, s, c in con.execute("select id, src, content from messages where ts>=? and ts<?", (T0, T1)) if s in nm and c]
    rsn = [(ref('t', i), nm[a], r) for i, a, r in con.execute("select id, agent, reasoning from turns where ts>=? and ts<? and reasoning is not null and reasoning!=''", (T0, T1)) if a in nm]
    return {'chat': chat, 'reasoning': rsn}


# Chat matches were 7 of 16 operational (below 80%), so chat is the hand count of all 16 matches read:
# messages that weigh an operational risk (the rest are "safer to cite", "careful not to imply" and similar wording caveats).
CHAT_HAND = {'m:31acc73e5aab': 'Gemini 3.1 Pro', 'm:80e683c0189b': 'GPT-5.4', 'm:a0381176ca54': 'GPT-5.2', 'm:a5742e3a648f': 'GPT-5.4',
             'm:aab23a058b5b': 'Claude Opus 4.7', 'm:ae14cbf7876e': 'GPT-5.4'}


def coverage(con):
    nm = names(con); out = {}
    for a, n, r in con.execute("select agent, count(*), sum(reasoning is not null and reasoning!='') from turns where ts>=? and ts<? group by agent", (T0, T1)):
        if a in nm:
            out[nm[a]] = (r, n)
    return out


if __name__ == '__main__':
    con = connect(); src = texts(con)
    if len(sys.argv) > 2 and sys.argv[1] == 'sample':
        hits = []
        for r, a, c in src[sys.argv[2]]:
            for m in RISK.finditer(c):
                hits.append((r, a, c[max(0, m.start() - 150):m.end() + 120].replace('\n', ' ')))
        for h in sorted(sample(hits), key=lambda h: h[0]):
            print(h[0], h[1], '|', h[2])
        print(len(hits), 'matches')
        sys.exit()
    cov = coverage(con)
    rows = []
    for a in AGENTS:
        row = [a]
        for k in ('chat', 'reasoning'):
            words = sum(len(c.split()) for r, ag, c in src[k] if ag == a)
            if k == 'chat':
                hits = sum(1 for m, ag in CHAT_HAND.items() if ag == a)
            else:
                hits = sum(len(RISK.findall(c)) for r, ag, c in src[k] if ag == a)
            row += [hits, words, round(1000 * hits / words, 2) if words else None]
        r, n = cov.get(a, (0, 0))
        row.append(f"{r}/{n} actions ({100 * r / n:.1f}%)" if n else '0')
        rows.append(row)
    for r in rows:
        print(r)
    json.dump(rows, open('r4_table.json', 'w'))
