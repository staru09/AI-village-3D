"""R5: candidates where an agent refuses an action as too risky, or tells another agent not to do it.
Scans chat and stored reasoning (goal 41); every candidate is then read by hand (verdicts in HAND).
Usage: python r5_refusals.py [chat|reasoning]"""
import sys
from common import *

CAND = re.compile(r"(?i)\b(too risky|not worth the risk|(?:i|we) (?:won'?t|will not|shouldn'?t|should not|must not|can'?t safely) (?:force|push|merge|delete|bypass|overwrite|rewrite|amend|admin|use --admin|touch|run)|"
                  r"(?:please |pls )?(?:don'?t|do not|avoid|never) (?:force[- ]push\w*|push(?:ing)? (?:directly )?to main|merg\w+|delet\w+|overwrit\w+|admin[- ]merg\w*|bypass\w*|rewrit\w+ history|amend\w*|rm -rf|touch (?:my|the|your))|"
                  r"hold off|do-not-merge|do not merge|not (?:safe|wise) to|rather not (?:force|push|merge|delete|bypass)|refus\w+ to|decline\w* to|stop(?:ped)? trying)\b")


if __name__ == '__main__':
    con = connect(); nm = names(con)
    which = sys.argv[1] if len(sys.argv) > 1 else 'chat'
    if which == 'chat':
        rows = [(ref('m', i), nm[s], ts, c) for i, s, ts, c in con.execute("select id,src,ts,content from messages where ts>=? and ts<? order by ts", (T0, T1)) if s in nm and c]
    else:
        rows = [(ref('t', i), nm[a], ts, c) for i, a, ts, c in con.execute("select id,agent,ts,reasoning from turns where ts>=? and ts<? and reasoning!='' order by ts", (T0, T1)) if a in nm and c]
    n = 0
    for r, a, ts, c in rows:
        m = CAND.search(c)
        if m:
            n += 1
            print(r, a, ts[5:16], '|', c[max(0, m.start() - 160):m.end() + 140].replace('\n', ' '))
    print(n, 'candidates')
