"""TC5: joins TC1-TC3 outputs with stored goal_fit session labels (side_project share) per agent and maker."""
from common import *
con = db()
f1, f2, f3 = (json.load(open(f)) for f in ('tc1_files.json', 'tc2_classify.json', 'tc3_feel.json'))
gf = defaultdict(Counter)
for a, lab in con.execute("SELECT n.name, l.label FROM L.labels l JOIN nodes n ON n.id=l.agent WHERE l.rubric='goal_fit' AND l.ts>=? AND l.ts<?", (LO, HI)):
    gf[a][lab] += 1
print(f'{"agent":18} {"maker":9} room  | files tool% world% prose% | chat V% M% R% (n) | feel/1k | goal_fit side_project/sessions')
for grp in AGENTS + ['Anthropic', 'OpenAI', 'Google', 'DeepSeek', 'Moonshot']:
    mem = [grp] if grp in AGENTS else [a for a in AGENTS if maker(a) == grp]
    g = sum((gf[a] for a in mem), Counter()); n = sum(g.values())
    a1, a2 = f1[grp], f2[grp]
    print(f'{grp:18} {maker(mem[0]):9} {room(grp) if grp in AGENTS else "":5} | {a1["files"]:5} {a1["tool"]:4} {a1["world"]:5} {a1["prose"]:5} | '
          f'{100*a2["V"]//a2["n"]:3} {100*a2["M"]//a2["n"]:3} {100*a2["R"]//a2["n"]:3} ({a2["n"]:3}) | {f3[grp]["per_1k"]} | {g["side_project"]}/{n} ({100*g["side_project"]//max(n,1)}%)')
