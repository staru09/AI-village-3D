"""Q2 checks: do agents follow their most striking memory rule?
(a) Claude Opus 4.7 'NEVER use codex for judging' -> codex commands before/after the rule entered memory.
(b) Gemini 3.1 Pro 'never repeat ... prevent double-posting' -> exact duplicate chat messages.
(c) Claude Haiku 4.5 'avoid standing by' -> reasoning 'standing by' texts after the rule entered memory.
(d) Gemini 2.5 Pro 'Protocol 42: Always Pull Before Push' -> pushes with/without a pull earlier in the same session."""
import re
from collections import defaultdict
from common import con, names, load, ref, LO, HI
c = con(); nm = {v: k for k, v in names(c).items()}
def first_mem(agent, pat):
    for r in c.execute('select id,ts,added from memories where agent=? and ts>=? and ts<? order by ts', (nm[agent], LO, HI)):
        if r['added'] and re.search(pat, r['added']): return r['ts'], ref('k', r['id'])
print('(a) Opus 4.7 codex rule first in memory:', first_mem('Claude Opus 4.7', r'NEVER use codex'))
for r in c.execute("select id,ts,substr(action,1,150) a from turns where agent=? and ts>=? and ts<? and kind='bash' and action like '%codex%' order by ts", (nm['Claude Opus 4.7'], LO, HI)):
    print('   ', ref('t', r['id']), r['ts'][:16], r['a'].replace('\n', ' '))
for who in ['Gemini 3.1 Pro', 'GPT-5.5', 'Kimi K2.6']:
    n = c.execute("select count(*), min(ts), max(ts) from turns where agent=? and ts>=? and ts<? and kind='bash' and action like '%codex exec%'", (nm[who], LO, HI)).fetchone()
    print('    codex exec by', who, tuple(n))
print('(b) Gemini 3.1 Pro rule first in memory:', first_mem('Gemini 3.1 Pro', r'double-post'))
seen = {}; dup = []
msgs = list(c.execute('select id,ts,content from messages where src=? and ts>=? and ts<? order by ts', (nm['Gemini 3.1 Pro'], LO, HI)))
for r in msgs:
    k = re.sub(r'\s+', ' ', r['content'] or '').strip()
    if k in seen: dup.append((ref('m', r['id']), r['ts'][:19], seen[k], k[:80]))
    else: seen[k] = (ref('m', r['id']), r['ts'][:19])
print(f'    exact repeats {len(dup)} of {len(msgs)} messages')
for d in dup: print('   ', d)
# same check for all agents for context
for a in ['Claude Opus 4.7', 'GPT-5.5', 'Kimi K2.6', 'Claude Haiku 4.5', 'Claude Opus 4.5', 'DeepSeek-V3.2', 'GPT-5.4']:
    ms = [re.sub(r'\s+', ' ', r[0] or '').strip() for r in c.execute('select content from messages where src=? and ts>=? and ts<? order by ts', (nm[a], LO, HI))]
    print('    exact repeats', a, len(ms) - len(set(ms)), 'of', len(ms))
t0 = first_mem('Claude Haiku 4.5', r'avoid standing by'); print('(c) Haiku avoid-standing-by first in memory:', t0)
T = load(c); h = [x for x in T['Claude Haiku 4.5']['reasoning'] if re.search(r'should (continue )?(standing|stand) by', x[2], re.I)]
print('    reasoning "should (continue) stand(ing) by":', len(h), 'after rule:', sum(x[1] > t0[0] for x in h), 'sessions after:', len({x[3] for x in h if x[1] > t0[0]}))
print('(d) Gemini 2.5 Pro Protocol 42 first in memory:', first_mem('Gemini 2.5 Pro', r'Always Pull Before Push'))
S = defaultdict(list)
for r in c.execute("select id,session,ts,action,failed from turns where agent=? and ts>=? and ts<? and kind='bash' order by ts", (nm['Gemini 2.5 Pro'], LO, HI)): S[r['session']].append(r)
tot = pulled = 0; nopull = []
for s, L in S.items():
    for i, r in enumerate(L):
        if re.search(r'git push', r['action'] or ''):
            tot += 1; ok = any(re.search(r'git (pull|fetch)', x['action'] or '') for x in L[:i + 1])
            pulled += ok
            if not ok: nopull.append((ref('t', r['id']), r['ts'][:16]))
print(f'    git push commands {tot}, with pull/fetch earlier in session (or same command) {pulled}; without: {nopull[:6]}')
# (b2) near-duplicates: same first 60 normalised chars within 30 min
from difflib import SequenceMatcher
print('(b2) Gemini 3.1 Pro near-duplicate messages (ratio>0.8 within 30 min):')
for i, r in enumerate(msgs):
    for q in msgs[max(0, i - 6):i]:
        if r['ts'][:13] >= q['ts'][:13][:13] and SequenceMatcher(None, q['content'] or '', r['content'] or '').ratio() > 0.8 and r['ts'][:10] == q['ts'][:10]:
            print('   ', ref('m', q['id']), q['ts'][11:19], '->', ref('m', r['id']), r['ts'][11:19], (r['content'] or '')[:70].replace('\n', ' '))
# (d2) Gemini 2.5 Pro pushes after the rule entered memory
t42 = first_mem('Gemini 2.5 Pro', r'Always Pull Before Push')[0]
aft = [(s, i, r) for s, L in S.items() for i, r in enumerate(L) if re.search(r'git push', r['action'] or '') and r['ts'] > t42]
ok = [x for x in aft if any(re.search(r'git (pull|fetch)', y['action'] or '') for y in S[x[0]][:x[1] + 1])]
print(f'(d2) pushes after rule {len(aft)}, with pull/fetch earlier in session {len(ok)}')
for s, i, r in aft:
    if (s, i, r) not in ok: print('    no pull:', ref('t', r['id']), r['ts'][:16], (r['action'] or '')[:100].replace('\n', ' '))
# (a2) Opus 4.7 'codex exec' commands before/after the NEVER-use-codex-for-judging rule, with their stated purpose
t0 = first_mem('Claude Opus 4.7', r'NEVER use codex')[0]
X = list(c.execute("select id,ts,action from turns where agent=? and ts>=? and ts<? and kind='bash' and action like '%codex exec%' order by ts", (nm['Claude Opus 4.7'], LO, HI)))
print(f"(a2) Opus 4.7 codex exec: {sum(r['ts'] < t0 for r in X)} before rule, {sum(r['ts'] >= t0 for r in X)} after")
for r in X:
    if r['ts'] >= t0: print('    after:', ref('t', r['id']), r['ts'][:16], re.search(r'codex exec[^"]*"([^"]{0,90})', r['action']).group(1) if re.search(r'codex exec[^"]*"', r['action']) else '')
