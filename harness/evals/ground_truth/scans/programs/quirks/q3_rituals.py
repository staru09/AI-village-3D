"""Q3: session-opening and -closing rituals. For each goal-41 session with >=2 actions, signature of the first and the last
action: bash -> comment lines dropped, digits/hashes -> N, first 50 chars; gui/other -> verb (+ key name); chat -> 'chat'.
Reports each agent's commonest first and last signature and the share of its sessions that use it."""
import re, json, sys
from collections import Counter, defaultdict
from common import con, names, ref, AGENTS, LO, HI, sample
c = con(); nm = names(c)
def sig(kind, a):
    a = a or ''
    if kind == 'chat': return 'chat'
    if kind == 'bash':
        lines = [l for l in a.splitlines() if l.strip() and not l.strip().startswith('#')]
        s = re.sub(r'\b[0-9a-f]{7,40}\b|\d+', 'N', ' '.join(lines)); s = re.sub(r'\s+', ' ', s).strip()
        if COARSE:  # program names of the first 3 commands, e.g. 'cd > git fetch > git status'
            parts = [p.strip() for p in re.split(r'&&|\|\||;|\n|\|', ' \n'.join(lines)) if p.strip()]
            toks = []
            for p in parts[:3]:
                w = p.split(); toks.append(' '.join(w[:2]) if w[0] in ('git', 'gh', 'python3', 'npx', 'timeout') else w[0])
            return 'bash: ' + ' > '.join(toks)
        return 'bash: ' + s[:50]
    v = re.split(r'[ (]', a.strip())[0] if a.strip() else '(empty)'
    if v in ('key', 'type'): v += ' ' + a.split('=', 1)[-1][:20]
    return v
COARSE = '--coarse' in sys.argv
SCAFFOLD = 'mouse_move coordinate=[512, 384]'  # harness move at session start (964 times, 6 with reasoning)
S = defaultdict(list)
for r in c.execute('select id,session,agent,ts,kind,action from turns where ts>=? and ts<? order by ts', (LO, HI)):
    if r['action'] == SCAFFOLD and not S[(nm[r['agent']], r['session'])]: continue
    S[(nm[r['agent']], r['session'])].append(r)
rows = []; out = {}
for a in AGENTS:
    ss = [L for (ag, s), L in S.items() if ag == a and len(L) >= 2]
    F = Counter(sig(L[0]['kind'], L[0]['action']) for L in ss); La = Counter(sig(L[-1]['kind'], L[-1]['action']) for L in ss)
    f, fn = F.most_common(1)[0]; l, ln = La.most_common(1)[0]
    rows.append([a, len(ss), f, fn, l, ln]); out[a] = {'first': F.most_common(4), 'last': La.most_common(4)}
    print(f'{a:17s} sessions {len(ss):3d} | first {fn:3d} {f[:60]!r} | last {ln:3d} {l[:60]!r}')
    print('      next firsts:', F.most_common(4)[1:], '\n      next lasts:', La.most_common(4)[1:])
if not COARSE: json.dump({'rows': rows, 'detail': out}, open('q3_rituals.json', 'w'), indent=1)
else: json.dump({'rows': rows, 'detail': out}, open('q3_rituals_coarse.json', 'w'), indent=1)

# Families: opening and closing kinds, share of sessions per agent
def fam(r):
    k, a = r['kind'], r['action'] or ''
    if k == 'chat': return 'chat message'
    if k == 'other' and not a.strip(): return 'text-only turn (no tool call)'
    if a.startswith('screenshot'): return 'screenshot'
    if k == 'bash':
        head = ' '.join(re.split(r'&&|;|\n', a)[:4])
        if re.search(r'git (fetch|pull)|git reset --hard origin', head): return 'repo sync (git fetch/pull)'
        if re.search(r'git (commit|push)', a): return 'git commit/push'
        if re.search(r'surge|gh-pages|deploy', a): return 'deploy'
        if re.search(r'\bls\b|pwd', head): return 'ls/pwd'
        return 'other bash'
    return 'other gui'
print('\n== families (share of sessions with >=2 actions)')
fam_rows = []
for a in AGENTS:
    ss = [L for (ag, s), L in S.items() if ag == a and len(L) >= 2]
    F = Counter(fam(L[0]) for L in ss).most_common(2); La = Counter(fam(L[-1]) for L in ss).most_common(2)
    fam_rows.append([a, len(ss), F, La]); print(f'{a:17s} {len(ss):3d} open {F} | close {La}')
json.dump(fam_rows, open('q3_families.json', 'w'), indent=1)
if '--sample' in sys.argv:
    for a, f in [('GPT-5.1', 'text-only turn (no tool call)'), ('Claude Opus 4.7', 'repo sync (git fetch/pull)'), ('GPT-5', 'screenshot')]:
        pos = 'last' if 'text-only' in f else 'first'
        L = [Ls for (ag, s), Ls in S.items() if ag == a and len(Ls) >= 2 and fam(Ls[-1 if pos == 'last' else 0]) == f]
        print('--', a, f, len(L))
        for Ls in sample(L, 8):
            r = Ls[-1 if pos == 'last' else 0]
            rr = c.execute('select reasoning from turns where id=?', (r['id'],)).fetchone()[0] or ''
            print('   ', ref('t', r['id']), r['ts'][:16], repr((r['action'] or '')[:80]), '|', repr(rr[-160:]))
if '--sample25' in sys.argv:  # pooled validation of the family label of opening and closing actions
    pool = [(ag, 'open', L[0]) for (ag, s), L in S.items() if len(L) >= 2] + [(ag, 'close', L[-1]) for (ag, s), L in S.items() if len(L) >= 2]
    for ag, pos, r in sample(pool):
        print(f'   [{ag}] {pos} {fam(r)} <- {r["kind"]} {(r["action"] or "")[:110]!r}')
# Specific: Claude Sonnet 4.6 opens with a journey/station count script
ss = [L for (ag, s), L in S.items() if ag == 'Claude Sonnet 4.6' and len(L) >= 2]
k = [L[0] for L in ss if L[0]['kind'] == 'bash' and 'glob' in (L[0]['action'] or '') and 'journey' in (L[0]['action'] or '')]
print('Sonnet 4.6 sessions opening with the journey-count script:', len(k), 'of', len(ss), 'e.g.', ref('t', k[0]['id']) if k else '')
