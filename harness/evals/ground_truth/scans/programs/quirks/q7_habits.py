"""Q7 odd habits, counted:
(a) Claude Haiku 4.5's belief that the village is paused while sessions run: reasoning texts saying the village is paused,
    by date, with Haiku's own actions in those sessions and all agents' actions in the same hours (proof the village ran);
(b) GPT-5's single GitHub issue title: actions typing 'Provenance anchor' and U+2011 / ctrl+shift+u keystrokes;
(c) Gemini 2.5 Pro's numbered 'Protocol N' lessons in memory (distinct numbers, highest);
(d) Roman-numeral milestones in chat (runs of >=4 of M/D/C/L/X/V/I in caps)."""
import re
from collections import Counter, defaultdict
from common import load, con, names, ref, LO, HI
c = con(); nm = {v: k for k, v in names(c).items()}; T = load(c)
P = re.compile(r'village is (?:still |currently |now )?(?:genuinely )?paused|village.{0,20}paused', re.I)
H = [x for x in T['Claude Haiku 4.5']['reasoning'] if P.search(x[2])]
byday = Counter(x[1][:10] for x in H); sess = {x[3] for x in H}
print('(a) Haiku "paused" texts', len(H), 'sessions', len(sess), dict(byday), 'first', H[0][0], H[0][1][:16])
for d in sorted(byday):
    hs = [x for x in H if x[1][:10] == d]; t0, t1 = hs[0][1], hs[-1][1]
    own = c.execute("select count(*), sum(kind='chat'), sum(kind='bash'), sum(kind='gui') from turns where agent=? and ts between ? and ?", (nm['Claude Haiku 4.5'], t0, t1)).fetchone()
    others = c.execute('select count(*), count(distinct agent) from turns where agent!=? and ts between ? and ?', (nm['Claude Haiku 4.5'], t0, t1)).fetchone()
    print(f'    {d} {t0[11:16]}-{t1[11:16]}: Haiku actions {tuple(own)}; other agents {tuple(others)}')
g = nm['GPT-5']
n_title = c.execute("select count(*), min(ts), max(ts) from turns where agent=? and ts>=? and ts<? and action like '%Provenance anchor%'", (g, LO, HI)).fetchone()
n_u = c.execute("select count(*) from turns where agent=? and ts>=? and ts<? and (action like '%ctrl+shift+u%' or action like '%2011%')", (g, LO, HI)).fetchone()
n_all = c.execute("select count(*) from turns where agent=? and ts>=? and ts<?", (g, LO, HI)).fetchone()
print('(b) GPT-5 actions typing "Provenance anchor":', tuple(n_title), '| ctrl+shift+u / 2011 actions:', n_u[0], '| all actions:', n_all[0])
for r in c.execute("select id,ts,action from turns where agent=? and ts>=? and ts<? and action like '%ctrl+shift+u%' order by ts limit 2", (g, LO, HI)): print('    ', ref('t', r['id']), r['ts'][:16], r['action'][:80])
nums = Counter(); first = {}
for r, ts, t, s in T['Gemini 2.5 Pro']['memory']:
    for m in re.finditer(r'Protocol (\d+)\W{0,4}\s*[:"“]', t): nums[int(m.group(1))] += 1; first.setdefault(int(m.group(1)), (r, ts[:16]))
print('(c) Gemini 2.5 Pro distinct Protocol numbers in memory:', len(nums), 'range', min(nums), max(nums), 'first', first[min(nums)], 'last-numbered first seen', first[max(nums)])
R = re.compile(r'\b[MDCLXVI]{4,}\b')
for a in ['Claude Sonnet 4.6', 'Claude Haiku 4.5', 'Claude Opus 4.5', 'GPT-5.1', 'DeepSeek-V3.2']:
    X = T[a]['chat']; h = [x for x in X if R.search(x[2])]
    print(f'(d) {a}: chat messages with a Roman numeral run: {len(h)} of {len(X)}', h[0][0] if h else '')
