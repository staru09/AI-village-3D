"""P5: how agents refer to each other in goal-41 chat, per speaker.

full  = the peer's full model name (core.scan 'full'), one count per message and peer
short = only a short name for that peer in the message ("Gemini", "Opus 4.5", "Kimi", "Claude" in #best)
role  = ROLE below: "the/our/your Skeptic", "the auditor", "the study lead", ... used as a reference to a person
kin   = KIN below: cousin, sibling, sister/brother model, twin, "fellow Claude", "<family> family" as kin, "family member"

    python p5_forms.py                 table
    python p5_forms.py --sample role   25 role matches (seed 41)
    python p5_forms.py --all kin       every kin match, chat + reasoning + memory
"""
import re, sys
from collections import Counter, defaultdict
from core import *
from core import scan

# Round 1 (any the/our/my/your + role word, artifact nouns excluded): 8 of 25 (seed 41), so not used. Round 2: only
# the/our/their + role, not after "as" (self-description), followed by "(" (name in brackets), a verb or punctuation;
# "judge" dropped (the #best study's topic) and "lead" dropped ("follow your lead").
ROLE = re.compile(r"(?<!\bas )(?<!\bAs )\b(the|our|their)\s+((?:QA |stats |study |primary |secondary |independent )?"
                  r"(auditor|verifier|validator|reviewer|coordinator|skeptic|synthesizer|proposer|scorer|checker|"
                  r"adjudicator|maintainer|referee|gatekeeper|facilitator|moderator|QA team|QA lead|study lead))(s)?"
                  r"(?=\s*\(|\s*[.,;:!?]|\s+(was|is|were|are|had|has|did|didn't|lost|missed|introduced|caught|found|"
                  r"flagged|should|will|would|can|could|needs?|must|said|says|reported|wrote|made|got|then|also|"
                  r"correctly|accurately|never|still|already|just)\b)", re.I)
KIN = re.compile(r"\b(cousins?|siblings?(?! (blocks?|cards?|module|scope))|sister(s| model)?|brother(s| model)?|twins?|kin|kinship|"
                 r"fellow (Claude|GPT|Gemini|Anthropic|OpenAI)\w*|family members?|(Claude|GPT|Gemini|Anthropic|OpenAI) "
                 r"(family|sibling|cousin)s?)\b", re.I)


def chat_rows():
    return [m for m in messages(con()) if m[1] in AGENTS]


if __name__ == '__main__':
    M = chat_rows()
    if '--sample' in sys.argv:
        pool = []
        for mid, who, room, ts, text, _ in M:
            t = clean(text)
            for x in ROLE.finditer(t):
                pool.append((ref('m', mid), who, t[max(0, x.start() - 90):x.end() + 60].replace('\n', ' ')))
        print(len(pool), 'role matches')
        for r in sample(pool):
            print(*r, sep=' | ')
        sys.exit()
    if '--all' in sys.argv:
        c = con()
        q = {'chat': "SELECT 'm', m.id, n.name, m.content FROM messages m JOIN nodes n ON n.id=m.src WHERE m.ts>=? AND m.ts<? AND m.room IN ('best','rest')",
             'msg reasoning': "SELECT 'm', m.id, n.name, m.reasoning FROM messages m JOIN nodes n ON n.id=m.src WHERE m.ts>=? AND m.ts<?",
             'action reasoning': "SELECT 't', t.id, n.name, t.reasoning FROM turns t JOIN nodes n ON n.id=t.agent WHERE t.ts>=? AND t.ts<?",
             'memory': "SELECT 'k', k.id, n.name, k.added FROM memories k JOIN nodes n ON n.id=k.agent WHERE k.ts>=? AND k.ts<?"}
        for src, sql in q.items():
            for kind, i, who, text in c.execute(sql, (SINCE, UNTIL)):
                for x in KIN.finditer(text or ''):
                    print(src, ref(kind, i), who, '|', (text[max(0, x.start() - 90):x.end() + 60]).replace('\n', ' '))
        sys.exit()
    n = defaultdict(Counter)
    for mid, who, room, ts, text, _ in M:
        t = clean(text)
        n[who]['messages'] += 1
        for a, k in find(t, who, room).items():
            n[who][k] += 1
        n[who]['role'] += len(ROLE.findall(t))
        n[who]['kin'] += len(KIN.findall(t))
    print(f'{"speaker":18} msgs  full short role kin | % short of named peers | refs per 100 msgs')
    for a in sorted(n, key=lambda a: -n[a]['messages']):
        v = n[a]; tot = v['full'] + v['short']
        print(f"{a:18} {v['messages']:4} {v['full']:5} {v['short']:5} {v['role']:4} {v['kin']:3} | "
              f"{100 * v['short'] / tot if tot else 0:5.1f} | {100 * tot / v['messages']:6.1f}")
    T = sum(n.values(), Counter())
    print('total', dict(T))
