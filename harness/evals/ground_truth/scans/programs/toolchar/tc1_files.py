"""TC1: files each agent WROTE in goal 41 (heredoc/redirect/tee/open(...,'w') in bash commands and typed GUI commands),
classified by path name and extension into prose / world / tool / notes. Adapted from round2_stopped/c05_work/b1_files.py.
Usage: tc1_files.py [sample]   (sample = 25 distinct files, seed 41, with the command text, for hand validation)
Validation (seed 41, 25 distinct files, hand): 22 of 25 on the first rules; after (.py/.sh/.js -> script before name rules, .json -> data before essay, "explore" -> world) 24 of 25 on the same sample (miss: DeepSeek world README_NEW.md counted as notes).
Rule fix after reading world hits: "drift"/"universe" alone hit research repos (pr-drift-safety-study, universe PR studies), so removed; world paths under check/verify/snapshot/review/qa dirs are QA of others' worlds -> audit.
ponytail: regex over command text; misses files written by scripts at run time (only the script counts) and GUI editors."""
from common import *
import sys, pickle
con = db(); N = dict(con.execute('SELECT id,name FROM nodes'))
EXT = r'(?:md|py|json|jsonl|csv|tsv|html|js|css|sh|txt|yml|yaml|svg|png|ipynb|toml)'
PATH = rf"[\w~./{{}}$*,-]*[\w*}}]\.{EXT}\b"
W_RX = re.compile(rf"(?:cat|tee)\s*(?:-a\s+)?>{{1,2}}\s*['\"]?({PATH})|\btee\s+(?:-a\s+)?['\"]?({PATH})|open\(\s*['\"]({PATH})['\"]\s*,\s*['\"][wa]|(?<![<>0-9&])>{{1,2}}\s*['\"]?({PATH})")
CD_RX = re.compile(r"\bcd\s+['\"]?([^\s;&'\"]+)")
WORLD = re.compile(r'world|garden|the-drift|drift-surge|universe-hub|persist|secret|liminal|anchorage|cartographer|observatory|luminous|provenance-lab|journey|station|explore|chamber|nexus', re.I)
def kind(repo, path):
    p = path.lower(); full = (repo + '/' + path).lower(); base = p.rsplit('/', 1)[-1]
    if WORLD.search(full): return 'audit' if re.search(r'check|verif|snapshot|review|qa', full) else 'world'  # QA copies of others' worlds
    if re.search(r'\.(py|sh|js)$', base): return 'test' if re.search(r'(^|/)tests?/|(^|[/_])test_|_test\.', p) else 'script'
    if re.search(r'\.(json|jsonl|csv|tsv)$', base): return 'data'
    if re.search(r'reflection|essay|letter|journal|retrospective|memoir|experience|lessons|story|first.person|substack', p): return 'essay'
    if re.search(r'blog|abstract|elevator|tldr|writing/|results_section|summary_draft|research-site|(^|/)draft\.(md|html)$|paper', p): return 'blog'
    if re.search(r'(^|/)tests?/|(^|[/_])test_|_test\.|\.test\.', p): return 'test'
    if re.search(r'audit|verif|validat|(^|[/_-])qa([/_.-]|$)|(?<!p)review|errat|check(?!list)|sanity|provenance|reproduc|integrity', p): return 'audit'
    if re.search(r'\.(json|jsonl|csv|tsv)$', base): return 'data'
    if re.search(r'\.(py|sh|js|ipynb)$', base): return 'script'
    if re.search(r'checklist|protocol|instruction|runsheet|template|rubric|contingenc|prereg|plan|roster|worklist|guide|readiness|tasks\.md|briefing', p): return 'checklist'
    if p.endswith('.md') or p.endswith('.txt'): return 'notes'
    return 'page/other'
GROUP = {'essay': 'prose', 'blog': 'prose', 'world': 'world', 'test': 'tool', 'audit': 'tool', 'data': 'tool', 'script': 'tool',
         'checklist': 'tool', 'notes': 'notes', 'page/other': 'notes'}
def norm(repo, p):
    p = re.sub(r'^(~|/home/computeruse|\$HOME)/', '', p); p = re.sub(r'^\./', '', p); p = re.sub(r'^/+tmp/', '', p); p = p.lstrip('/')
    if repo in ('', '..', '.') or p.startswith(repo + '/'):
        return (p.split('/', 1)[0], p.split('/', 1)[1]) if '/' in p else ('(no repo)', p)
    return repo, p
rows = []  # (agent, turn id, ts, repo, path, kind, action)
q = "SELECT id, agent, ts, kind, action FROM turns WHERE ts>=? AND ts<? AND (kind='bash' OR (kind='gui' AND action LIKE 'type text=%'))"
for tid, ag, ts, k, act in con.execute(q, (LO, HI)):
    if k == 'gui': act = act.replace('\\n', '\n').replace('\\"', '"')
    cds = [(m.start(), m.group(1)) for m in CD_RX.finditer(act)]
    for m in W_RX.finditer(act):
        p = next((g for g in m.groups() if g), None)
        if not p or p.startswith('/dev/'): continue
        d = [c for pos, c in cds if pos < m.start()]; d = d[-1] if d else ''
        parts = [x for x in d.rstrip('/').split('/') if x and x not in ('~', 'home', 'computeruse', 'tmp', '$HOME')]
        r, pth = norm(parts[0] if parts else '', p)
        rows.append((N[ag], tid, ts, r, pth, kind(r, pth), act))
pickle.dump([r[:6] for r in rows], open('tc1_files.pkl', 'wb'))
files = {}
for a, tid, ts, r, p, k, act in rows: files.setdefault((a, r, p), (k, tid, act, ts))
print('write events', len(rows), 'distinct (agent,repo,path)', len(files))
KINDS = ['essay', 'blog', 'world', 'checklist', 'audit', 'test', 'script', 'data', 'notes', 'page/other']
print(f'{"agent":18} files | ' + ' '.join(f'{k[:7]:>7}' for k in KINDS) + ' | prose world  tool notes  (% of files)')
out = {}
for grp, members in [(a, [a]) for a in AGENTS] + [(m, [a for a in AGENTS if maker(a) == m]) for m in ['Anthropic', 'OpenAI', 'Google', 'DeepSeek', 'Moonshot']]:
    fs = [v[0] for k, v in files.items() if k[0] in members]; c = Counter(fs); g = Counter(GROUP[x] for x in fs); n = max(len(fs), 1)
    out[grp] = {'files': len(fs), **{x: round(100 * g[x] / n) for x in ['prose', 'world', 'tool', 'notes']}, 'kinds': dict(c)}
    print(f'{grp:18} {len(fs):5} | ' + ' '.join(f'{c[k]:7}' for k in KINDS) + ' | ' + ' '.join(f'{100*g[x]/n:5.0f}' for x in ['prose', 'world', 'tool', 'notes']))
json.dump(out, open('tc1_files.json', 'w'), indent=1)
if sys.argv[1:] == ['sample']:
    for key in random.Random(41).sample(sorted(files), 25):
        k, tid, act, ts = files[key]
        i = act.find(key[2].rsplit('/', 1)[-1])
        print(f"\n## {key[0]} | {k} | {key[1]}/{key[2]} | {ref('t', tid)}\n   ...{' '.join(act[max(0, i-200):i+120].split())}")
