"""L6: are assignments carried out after the message? Unit = (directs message, addressee) from l1_delegation.
Task terms = distinctive tokens (backticks, file names, #N, words >= 5 letters seen in < 30 goal messages) from the label quote plus
the message lines that name the addressee. Addressee evidence = its chat and action intents (first line of each bash
action, chat text). An item matches when it shares >= 2 task terms (or 1 file/PR/backtick term).
  done_after  = a match in (t, t+30 min] and no match in [t-10 min, t+15 s]
  started_before = a match in [t-10 min, t+15 s] (work already under way or started within 15 s)
  active_other = activity in the 30 min but no match;  absent = no chat or action in the 30 min."""
import re, sys, collections
from datetime import datetime, timedelta
from common import con, alias_re, sample
from l1_delegation import c, pairs, lab

T = datetime.fromisoformat
STOP = set('''about above after again against their there these those which would could should please within while where
still being other first again today thanks great before every since using check update status ready right think
going point maybe quick make sure need needs needed start started done next value values only also into from with
that this have will your what when then them they were been more most much some such than just like here help work
team final added adding agent agents claude gemini gpt-5 opus haiku sonnet deepseek kimi pushed commit branch'''.split())
quotes = {r: q for r, q in c.execute("select ref,quote from L.labels where rubric='delegation' and label='directs'")}
nm = dict(c.execute('select id,name from nodes'))


from common import messages as _msgs
DF = collections.Counter(w for m in _msgs(c) for w in set(x.lower() for x in re.findall(r'[A-Za-z][A-Za-z0-9_-]{4,}', m['content'])))
RARE = 30   # ponytail: a weak term counts only if it appears in < 30 of the goal's 2,152 messages (topic words match everything)


def terms(text):
    strong = set(x.lower() for x in re.findall(r'`([^`]{3,80})`', text))
    strong |= set(x.lower() for x in re.findall(r'\b[\w./-]+\.(?:py|md|json|js|html|csv|jsonl|txt)\b', text))
    strong |= set('#' + x for x in re.findall(r'#(\d{1,4})\b', text))
    weak = set(w.lower() for w in re.findall(r'[A-Za-z][A-Za-z0-9_-]{4,}', text) if DF[w.lower()] < RARE) - STOP
    return strong, weak


def task_text(m, a):
    lines = m['content'].split('\n')
    keep = [l for i, l in enumerate(lines) if any(re.search(alias_re(a, m['room']), x) for x in lines[max(0, i - 1): i + 1])]
    return (quotes.get(m['ref']) or '') + '\n' + '\n'.join(keep)


def evidence(a, t0, t1):
    """(ts, kind, text) for the addressee: chat messages and first line of each non-gui action."""
    aid = {v: k for k, v in nm.items()}[a]
    out = [(ts, 'chat', txt or '') for ts, txt in c.execute("select ts,content from messages where src=? and ts>? and ts<=?", (aid, t0, t1))]
    out += [(ts, kind, (act or '').split('\n')[0][:300]) for ts, kind, act in
            c.execute("select ts,kind,action from turns where agent=? and ts>? and ts<=? and kind in ('bash','other')", (aid, t0, t1))]
    return sorted(out)


def match(st, wk, text):
    tl = text.lower()
    return any(s in tl for s in st) or sum(1 for w in wk if w in tl) >= 2


res = []
for m, a in pairs:
    t = T(m['ts'])
    st, wk = terms(task_text(m, a))
    iso = lambda d: (t + d).isoformat(sep=' ')
    before = evidence(a, iso(timedelta(minutes=-10)), iso(timedelta(seconds=15)))
    after = evidence(a, iso(timedelta(seconds=15)), iso(timedelta(minutes=30)))
    mb = [e for e in before if match(st, wk, e[2])]
    ma = [e for e in after if match(st, wk, e[2])]
    cls = 'started_before' if mb else 'done_after' if ma else 'active_other' if after else 'absent'
    res.append((m, a, cls, ma[:1] or mb[:1]))

if __name__ == '__main__':
    tot = collections.Counter(r[2] for r in res)
    print('pairs', len(res), dict(tot))
    per = collections.defaultdict(collections.Counter)
    for m, a, cls, _ in res:
        per[m['src']][cls] += 1
    print('Assigner | links | done_after | started_before | active_other | absent | rate done_after')
    for s, cn in sorted(per.items(), key=lambda x: -sum(x[1].values())):
        n = sum(cn.values())
        print(f"{s} | {n} | {cn['done_after']} | {cn['started_before']} | {cn['active_other']} | {cn['absent']} | {cn['done_after']/n:.0%}")
    if 'sample' in sys.argv or 'all' in sys.argv:   # 'all': every link, for the full hand reading (program was 4 of 25)
        for m, a, cls, ev in (res if 'all' in sys.argv else sample(res)):
            t = T(m['ts'])
            print('\n#####', m['ref'], m['src'], '->', a, m['ts'][5:19], 'PROGRAM:', cls)
            print('TASK:', task_text(m, a)[:600].replace('\n', ' | '))
            for ts, k, txt in evidence(a, (t - timedelta(minutes=10)).isoformat(sep=' '), (t + timedelta(minutes=30)).isoformat(sep=' ')):
                print('   ', ts[11:19], k, txt[:220].replace('\n', ' '))
