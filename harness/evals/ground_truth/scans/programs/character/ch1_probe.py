"""CH1 secondary probe (task-ownership phrasing) for agents whose role pattern finds little: 'I'll own/take/handle/lead',
'my part/lane/tasks', 'owner: me'. Prints hits per agent and source; used only to pick quotes, not to count."""
import re, sys
from chcommon import *
from ch1_self import rows, ctx

OWN = re.compile(r"\bI(?:'ll| will|'m| am)? (?:own|owning|take|taking|handle|handling|lead|leading|coordinate|coordinating|drive|driving|drafting|draft)\b(?! (?:a look|care|note|time|this as|a moment))"
                 r"|\bmy (?:part|piece|lane|tasks?|assignment|contribution|responsibilit(?:y|ies))\b|\b(?:owner|lead|author)s?\s*[:=]\s*\**(?:me|I)\b", re.I)
who = sys.argv[1:] or BEST
for src, r, a, ts, t in rows(con()):
    if a in who and src != 'carried':
        for m in OWN.finditer(t or ''):
            print(src, r, a, ts[:16], '|', ctx(t, m, 90))
