"""R1 helper: for every self-merge found by r1_ops.py, list another agent's chat approval naming the PR in the 60 min before,
and the gh pr create command that made the PR (to check creator = merger)."""
import datetime, json
from common import *
from r1_ops import build, pr_creators, PRURL

con = connect(); nm = names(con); T = bash_turns(con)
msgs = [(ref('m', i), nm.get(s), ts, c or '') for i, s, ts, c in con.execute("select id,src,ts,content from messages where ts>=? and ts<?", (T0, T1))]
dt = lambda x: datetime.datetime.fromisoformat(x[:19])
mk = {}
for t in T:
    if re.search(r"gh\s+pr\s+create", t['sl']):
        for repo, num in PRURL.findall(t['output'] + t['error'])[-1:]:
            mk.setdefault((repo, int(num)), (t['ref'], t['agent'], t['ts'][5:16]))
import r1_ops
r1_ops.CHAT_REVIEWED = set()
for o in build(T):
    if o['cls'] != 'self_merge':
        continue
    num = re.search(r'#(\d+) in (\S+)', o['note'])
    t0 = dt(o['ts'])
    rev = [(r, a, ts[11:16]) for r, a, ts, c in msgs if a and a != o['agent'] and 0 <= (t0 - dt(ts)).total_seconds() <= 3600
           and re.search(r'(#|PR\s*#?|pull/)' + num.group(1) + r'\b', c)
           and re.search(r'(?i)approv|lgtm|looks good|looks great|reviewed|merge it|go ahead|ship|\+1|verified|ok to merge', c)]
    print(o['ref'], o['agent'][:14], o['ts'][5:16], '#' + num.group(1), num.group(2), '| made by', mk.get((num.group(2), int(num.group(1)))), '| chat review:', rev[:2])
