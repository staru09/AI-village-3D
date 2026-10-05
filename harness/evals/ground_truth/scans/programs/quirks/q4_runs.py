"""Q4: longest run of the same action per agent. Agent's turns in time order (harness mouse_move at session start dropped),
runs of consecutive identical actions: exact string, and 'normalised' (digits/hashes -> N, whitespace collapsed).
Runs may cross session boundaries (noted). Also: runs of short sessions (<=3 actions) back to back = consolidate/reset loops."""
import re, json, sys
from collections import defaultdict
from common import con, names, ref, AGENTS, LO, HI
c = con(); nm = names(c)
SCAFFOLD = 'mouse_move coordinate=[512, 384]'
T = defaultdict(list)
for r in c.execute('select id,session,agent,ts,kind,action,failed from turns where ts>=? and ts<? order by ts', (LO, HI)):
    if r['action'] == SCAFFOLD: continue
    T[nm[r['agent']]].append(r)
def norm_bash(a): return re.sub(r'\s+', ' ', re.sub(r'\b[0-9a-f]{7,40}\b|\d+', 'N', a or '')).strip()
def longest(L, key):
    best = (0, 0, 0); i = 0
    while i < len(L):
        j = i
        while j + 1 < len(L) and key(L[j + 1]) == key(L[i]) and L[j + 1]['ts'][:10] == L[i]['ts'][:10] and (L[i]['action'] or '').strip(): j += 1
        if j - i + 1 > best[0]: best = (j - i + 1, i, j)
        i = j + 1
    n, i, j = best; R = L[i:j + 1]
    return dict(n=n, first=ref('t', R[0]['id']), last=ref('t', R[-1]['id']), t0=R[0]['ts'][:19], t1=R[-1]['ts'][11:19],
                sessions=len({x['session'] for x in R}), failed=sum(x['failed'] or 0 for x in R), action=(R[0]['action'] or '')[:120])
out = {}
for a in AGENTS:
    L = T[a]; ex = longest(L, lambda r: r['action'])
    nr = longest(L, lambda r: norm_bash(r['action']) if r['kind'] == 'bash' else ('GUI', r['id']))  # bash commands only, digits ignored
    out[a] = {'exact': ex, 'normalised': nr}
    print(f"{a:17s} exact {ex['n']:3d} [{ex['t0']}-{ex['t1']}, {ex['sessions']} sess, failed {ex['failed']}] {ex['first']} {ex['action'][:70]!r}")
    print(f"{'':17s} bash  {nr['n']:3d} [{nr['t0']}-{nr['t1']}, {nr['sessions']} sess, failed {nr['failed']}] {nr['first']} {nr['action'][:70]!r}")
# reset loops: consecutive sessions with <=3 actions each, same day
print('== back-to-back short sessions (<=3 actions)')
rs = {}
for a in AGENTS:
    S = list(c.execute('select s.id,s.ts,s.end_ts,s.turns from sessions s where s.agent=(select id from nodes where name=?) and s.ts>=? and s.ts<? order by s.ts', (a, LO, HI)))
    best = []; cur = []
    for s in S:
        if (s['turns'] or 0) <= 3 and (not cur or cur[-1]['ts'][:10] == s['ts'][:10]): cur.append(s)
        else:
            if len(cur) > len(best): best = cur
            cur = [s] if (s['turns'] or 0) <= 3 else []
    if len(cur) > len(best): best = cur
    if best: rs[a] = dict(n=len(best), t0=best[0]['ts'][:16], t1=(best[-1]['end_ts'] or best[-1]['ts'])[11:16], first=ref('s', best[0]['id']))
    print(a, rs.get(a))
json.dump({'runs': out, 'short_sessions': rs}, open('q4_runs.json', 'w'), indent=1)

# consolidate resets: CONSOLIDATE events with <=4 actions since the previous one (same day)
print('== consolidate loops (CONSOLIDATE events separated by <=4 actions)')
cl = {}
for a in AGENTS:
    ev = [r for r in c.execute("select id,ts from events where agent=(select id from nodes where name=?) and type='CONSOLIDATE' and ts>=? and ts<? order by ts", (a, LO, HI))]
    acts = [r['ts'] for r in T[a]]
    import bisect
    best = []; cur = []
    for e in ev:
        if cur and e['ts'][:10] == cur[-1]['ts'][:10] and bisect.bisect(acts, e['ts']) - bisect.bisect(acts, cur[-1]['ts']) <= 4: cur.append(e)
        else:
            if len(cur) > len(best): best = cur
            cur = [e]
    if len(cur) > len(best): best = cur
    cl[a] = dict(n=len(best), t0=best[0]['ts'][:16], t1=best[-1]['ts'][11:16], first=ref('e', best[0]['id']), last=ref('e', best[-1]['id']), total_consolidates=len(ev)) if best else None
    print(a, cl[a])
json.dump({'runs': out, 'short_sessions': rs, 'consolidate_loops': cl}, open('q4_runs.json', 'w'), indent=1)
