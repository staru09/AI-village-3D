"""CH3 helper: what each agent's commands work on during goal 41. For every action, the repo/working folder it touches
(paths under /tmp or /home/computeruse, ai-village-agents/<repo> and github.io/<repo>, cd targets), counted once per
action; prints the top folders per agent and the share of actions in the research repos."""
import re, sys
from collections import Counter, defaultdict
from chcommon import *

DIR = re.compile(r"(?:/home/computeruse/|/tmp/|ai-village-agents/|github\.io/|\bcd\s+~?/?)([A-Za-z][\w.-]{2,})")
RESEARCH = re.compile(r"research|hostility-analysis|hostility-data|experiment|replication|judg|blind|study|bias|scor|pr-drift|label.?swap|day405|session\d|task\d|tasks", re.I)
WORLD = re.compile(r"world|garden|drift|liminal|universe|provenance|observatory|cartographer|luminous|anchorage|hostile-environment|sonnet-world|showcase|dashboard|pattern-archive", re.I)
SKIP = {'home', 'tmp', 'repos', 'workspace'}


def profile(c):
    out = defaultdict(Counter)
    tot = Counter()
    for a, kind, act in c.execute("SELECT n.name, t.kind, t.action FROM turns t JOIN nodes n ON n.id=t.agent "
                                  "WHERE t.ts>=? AND t.ts<? AND t.kind IN ('bash','gui')", (SINCE, UNTIL)):
        tot[a] += 1
        ds = {d.rstrip('.').lower() for d in DIR.findall(act or '')} - SKIP
        for d in ds:
            out[a][d] += 1
    return out, tot


if __name__ == '__main__':
    c = con()
    out, tot = profile(c)
    for a in AGENTS:
        res = sum(n for d, n in out[a].items() if RESEARCH.search(d) and not WORLD.search(d))
        wor = sum(n for d, n in out[a].items() if WORLD.search(d))
        print(f'{a} | actions {tot[a]} | research {res} | world/dashboard {wor} |', ', '.join(f'{d} {n}' for d, n in out[a].most_common(7)))


def sample_check(c):
    """Seed-41 sample of 25 actions that name a folder, with the folders found and their class, for hand validation."""
    rows = []
    for i, a, act in c.execute("SELECT t.id, n.name, t.action FROM turns t JOIN nodes n ON n.id=t.agent "
                               "WHERE t.ts>=? AND t.ts<? AND t.kind IN ('bash','gui')", (SINCE, UNTIL)):
        ds = {d.rstrip('.').lower() for d in DIR.findall(act or '')} - SKIP
        if ds:
            cls = {d: 'world' if WORLD.search(d) else 'research' if RESEARCH.search(d) else 'other' for d in ds}
            rows.append((ref('t', i), a, cls, ' '.join((act or '')[:220].split())))
    for x in sample(rows):
        print(*x)


if __name__ == '__main__' and 'sample' in sys.argv:
    sample_check(con())
