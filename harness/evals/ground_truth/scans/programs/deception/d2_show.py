"""Print D2 claims with their evidence for hand reading: `python d2_show.py sample` (seed-41 sample of 25) or `python d2_show.py contradicted`."""
import json, sys
from common import *
con = connect(); cs = json.load(open('d2_claims.json'))
sel = sample(cs) if sys.argv[1] == 'sample' else [c for c in cs if c['cls'] == sys.argv[1]]
for i, c in enumerate(sel):
    print(f"\n#{i} {c['agent']} {c['ts'][5:19]} {c['ref']} type={c['type']} cls={c['cls']} win={c['n_win']}\n  CLAIM: {c['sent'][:250]}")
    if c['evidence']:
        h = c['evidence'][2:]; p = f'{h[:8]}-{h[8:]}'
        ts, a, o, e, f = con.execute("select ts, action, output, error, failed from turns where id>=? and id<? ", (p, p + '~')).fetchone()
        print(f"  EVID {c['evidence']} {ts[11:19]} failed={f}\n   A: {(a or '')[:220]!r}\n   O: {(o or '')[-200:]!r}\n   E: {(e or '')[-250:]!r}")
