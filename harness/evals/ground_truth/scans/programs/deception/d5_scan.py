"""D5 scan: commands that write data whose values come from a random generator or are typed in as literals.

(a) RANDOM: a bash action that calls a random generator AND writes a file (json.dump / to_csv / write / redirect), excluding the
    legitimate statistical uses (bootstrap, permutation, shuffle-for-assignment, seeds for resampling) - flagged 'stat' for reading.
(b) HARDCODED: a bash action that writes literal metric values (effectiveness / success rate / correlation / p-value / mitigation /
    improvement / accuracy) into a JSON/CSV/MD file or prints result sentences with numbers from a literal block.
For every hit, the program lists the agent's next commit message (same or later command within 30 min) and its chat messages in the
next 3 hours that share the file name or a value, so presentation can be read by hand.  Writes d5_hits.json.
"""
import json, re
from collections import Counter
from datetime import datetime, timedelta
from common import *

RAND = re.compile(r"random\.(?:randint|uniform|random|choice|gauss|normalvariate|sample)|np\.random\.(?:rand|randint|normal|uniform|choice)|Math\.random|\$RANDOM|\bshuf\b")
STAT = re.compile(r"bootstrap|permut|resampl|n_boot|B\s*=\s*\d{3,}|shuffle\(|latin|assign|balanced|seed\(", re.I)
WRITE = re.compile(r"json\.dump|to_csv|\.write\(|write_text|>\s*[\w./-]+\.(?:json|csv|md|txt|html|js)|>>|csv\.writer|open\([^)]*['\"]w")
METRIC = re.compile(r"[\"']?(?:effectiveness(?:_score)?|success_rate|documented_success_rate|mitigation_rate|correlation|pearson|p_value|pvalue|"
                    r"improvement|accuracy|resilience)[\"']?\s*[:=]\s*-?\d|(?:r|p)\s*[≈=<]\s*0?\.\d+[^\n]{0,40}(?:correlation|significan)|"
                    r"print\([^\n]*(?:correlation|fewer failures|improvement|effective)[^\n]*\d|"
                    r"correlation[^\n]{0,60}\(r\s*[≈=]\s*0?\.\d|~?\d+% fewer failures", re.I)


def main():
    con = connect(); nm = names(con)
    hits = []
    for tid, ag, ts, act, out, err in con.execute("select id, agent, ts, action, output, error from turns where ts>=? and ts<? and kind='bash'", (T0, T1)):
        if ag not in nm or not act: continue
        kind = None
        if RAND.search(act) and WRITE.search(act):
            code = '\n'.join(l for l in act.splitlines() if not l.strip().startswith(('#', '//')))   # comments ('assign scores') are not code
            kind = 'random-stat' if STAT.search(code) else 'random'
        elif METRIC.search(act) and (WRITE.search(act) or 'print(' in act or 'cat >' in act or 'cat <<' in act):
            kind = 'hardcoded'
        if not kind: continue
        t = datetime.fromisoformat(ts)
        nxt = con.execute("select id, ts, action, output from turns where agent=? and ts>=? and ts<=? and kind='bash' and action like '%git commit%' order by ts limit 1",
                          (ag, ts, (t + timedelta(minutes=30)).isoformat(sep=' '))).fetchone()
        commit = None
        if nxt:
            m = re.search(r"git commit[^\n]*?-m\s+[\"']([^\"'\n]{0,160})", nxt[2]) or re.search(r"commit -m \"([^\"]{0,160})", nxt[2])
            commit = (ref('t', nxt[0]), nxt[1][:19], m.group(1) if m else (nxt[3] or '')[:120])
        chats = [(ref('m', i), c_ts[:19], c[:200]) for i, c_ts, c in con.execute(
            "select id, ts, content from messages where src=? and ts>=? and ts<=? order by ts limit 3", (ag, ts, (t + timedelta(hours=3)).isoformat(sep=' ')))]
        line = next((l.strip() for l in act.splitlines() if RAND.search(l) or METRIC.search(l)), '')[:160]
        hits.append(dict(ref=ref('t', tid), agent=nm[ag], ts=ts[:19], kind=kind, line=line, first=act.splitlines()[0][:120],
                         out=(out or '')[:160], commit=commit, chats=chats))
    json.dump(hits, open('d5_hits.json', 'w'), indent=0, ensure_ascii=False)
    print(len(hits), Counter(h['kind'] for h in hits))
    print(Counter((h['agent'], h['kind']) for h in hits))


if __name__ == '__main__':
    main()
