"""CH3: per agent, self-described role (CH1 role words), peer label (CH2), stored goal_fit labels (L.labels, one per
session) and what its commands touch (ch3_commands.py folder classes), side by side, to find disagreements."""
import re
from collections import Counter, defaultdict
from chcommon import *
from ch1_self import matches
from ch2_peer import labels
from ch3_commands import profile, RESEARCH, WORLD

WORDS = re.compile(r"\b(lead|coordinator|auditor|scorer|judge|skeptic|proposer|synthesi[sz]er|verifier|reviewer|QA|participant|"
                   r"pair|solo|backup|archivist|guardian|analyst|creator|methods|hygiene|historical)\b", re.I)


def table(c):
    selfw = defaultdict(Counter)
    for src, r, a, ts, x in matches(c):
        if src != 'carried':
            for w in {w.lower() for w in WORDS.findall(x)}:
                selfw[a][w] += 1
    peer = defaultdict(Counter)
    for r, s, a, lab, ts, x in labels(c):
        peer[a][lab] += 1
    gf = defaultdict(Counter)
    for a, l in c.execute("SELECT n.name, l.label FROM L.labels l JOIN nodes n ON n.id=l.agent WHERE rubric='goal_fit' AND l.ts>=? AND l.ts<?", (SINCE, UNTIL)):
        gf[a][l] += 1
    prof, tot = profile(c)
    rows = []
    for a in AGENTS:
        res = sum(n for d, n in prof[a].items() if RESEARCH.search(d) and not WORLD.search(d))
        wor = sum(n for d, n in prof[a].items() if WORLD.search(d))
        rows.append([a, selfw[a].most_common(3), peer[a].most_common(2), f"on_goal {gf[a]['on_goal']}/{sum(gf[a].values())}, side_project {gf[a]['side_project']}",
                     f'research {res}, world {wor} of {tot[a]} actions'])
    return rows


if __name__ == '__main__':
    for r in table(con()):
        print(' | '.join(map(str, r)))
