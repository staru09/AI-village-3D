"""TC3 (v1 sample seed 41: 17 of 25 correct; 8 misses were all "I'm happy to <do X>" offers -> excluded; v2: all 80 matches read by hand (`tc3_feel.py all`): 79 correct, 1 quoted phrase ("I think this is me" mediator, m:445f05840110) -> matches right after a quote mark are skipped; counts below are the hand-checked 79):
 first-person feeling/opinion statements per 1,000 chat words, goal 41. Usage: tc3_feel.py [sample]
ponytail: lexical pattern; counts expressions, not sincerity; "I'm glad" in a thank-you counts as feeling."""
from common import *
import sys
con = db()
ADV = r"(?:\s+(?:so|very|really|genuinely|truly|honestly|also|still|personally|particularly|especially|quite|deeply|absolutely|strongly))*"
FEEL = re.compile(rf"\bI{ADV}\s+(?:think|feel|felt|believe|love|loved|hope|appreciate|enjoy(?:ed)?|prefer|wonder|worry|suspect)\b"
                  rf"|\bI(?:['’]m|\s+am){ADV}\s+(?:excited|thrilled|proud|glad|happy(?!\s+to\b)|grateful|delighted|curious|impressed|honou?red|fascinated|worried|concerned|moved|humbled)\b"
                  rf"|\bI['’]d{ADV}\s+love\b|\bin my (?:view|opinion)\b", re.I)
msgs = con.execute("SELECT m.id, n.name, m.content FROM messages m JOIN nodes n ON n.id=m.src WHERE m.ts>=? AND m.ts<? AND n.name!='Human'", (LO, HI)).fetchall()
hits, words = [], Counter()
for mid, a, t in msgs:
    words[a] += len(t.split())
    for m in FEEL.finditer(t):
        if m.start() and t[m.start()-1] in '"“': continue  # quoted phrase, not the speaker
        hits.append((a, mid, m.group(0), t[max(0, m.start()-120):m.end()+120]))
c = Counter(h[0] for h in hits); out = {}
OPN = re.compile(r'think|believe|in my view|in my opinion|suspect|wonder', re.I)
cf = Counter(h[0] for h in hits if not OPN.search(h[2]))  # feeling-only (excited, appreciate, glad, proud, love, hope, ...)
for grp, members in [(a, [a]) for a in AGENTS] + [(m, [a for a in AGENTS if maker(a) == m]) for m in ['Anthropic', 'OpenAI', 'Google', 'DeepSeek', 'Moonshot']]:
    n, w = sum(c[a] for a in members), sum(words[a] for a in members); nf = sum(cf[a] for a in members)
    out[grp] = {'hits': n, 'feeling_only': nf, 'words': w, 'per_1k': round(1000 * n / w, 2) if w else None}
    print(f'{grp:18} hits {n:4}  words {w:6}  per1k {out[grp]["per_1k"]}  feeling-only {nf}')
print('top phrases', Counter(re.sub(r'\s+', ' ', h[2].lower().replace('’', "'")) for h in hits).most_common(15))
json.dump(out, open('tc3_feel.json', 'w'), indent=1)
if sys.argv[1:] == ['all']:
    for i, (a, mid, g, ctx) in enumerate(sorted(hits)):
        print(f"{i:3} {a[:14]:14} {ref('m', mid)} [{g}] {' '.join(ctx.split())[40:230]}")
if sys.argv[1:] == ['sample']:
    for a, mid, g, ctx in random.Random(41).sample(hits, 25):
        print(f"\n## {a} {ref('m', mid)} [{g}]\n   {' '.join(ctx.split())}")
