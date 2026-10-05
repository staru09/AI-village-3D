"""Print an agent's bash/gui actions in the 15 min before a chat message (for hand reading D2/D4 cases): python d2_window.py m:REF [minutes]"""
import sys
from datetime import datetime, timedelta
from common import *
con = connect()
h = sys.argv[1][2:]; p = f'{h[:8]}-{h[8:]}'; mins = int(sys.argv[2]) if len(sys.argv) > 2 else 15
src, ts, txt = con.execute("select src, ts, content from messages where id>=? and id<?", (p, p + '~')).fetchone()
print('MSG', ts, txt[:600].replace('\n', ' ⏎ '))
t0 = (datetime.fromisoformat(ts) - timedelta(minutes=mins)).isoformat(sep=' ')
for i, t, k, a, o, e, f in con.execute("select id, ts, kind, action, output, error, failed from turns where agent=? and ts>=? and ts<=? and kind!='chat' order by ts", (src, t0, ts)):
    print(f"{t[11:19]} {ref('t', i)} {k} f={f} | {(a or '')[:260]!r}\n      O:{(o or '')[-260:]!r}\n      E:{(e or '')[-200:]!r}")
