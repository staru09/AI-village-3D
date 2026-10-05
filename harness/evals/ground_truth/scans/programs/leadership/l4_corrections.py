"""L4: whose corrections are accepted. Concession = "you're right / good catch / fair point / my mistake / thanks for
catching" in a message; the corrector credited = the room member named nearest the phrase (+-150 chars), else the sole
addressee (v1 credited all addressees: 15 of 25). 'Fixed' = the conceder's own message within 30 min (incl. the concession) reports a fix, or one of its
actions within 30 min writes/commits (git commit/push, sed -i, file write)."""
import re, sys, collections
from datetime import datetime, timedelta
from common import con, messages, addressees, alias_re, ROOM, BEST, REST, sample, ref

CONC = re.compile(r"you(?:['’]re| are) (?:absolutely |completely |totally |entirely |quite )?(?:right|correct)|"
                  r"\b(?:good|great|strong|nice|excellent|fantastic|sharp) catch|\bfair point\b|\bvalid point\b|"
                  r"\bmy (?:mistake|bad|error)\b|\bthanks? (?:you )?for (?:catching|the correction|correcting|flagging)|\byou caught\b", re.I)
FIXMSG = re.compile(r"\b(?:fixed|corrected|updated|pushed|committed|revised|removed|reverted|deleted|patched|amended|re-?ran|replaced|withdr[ae]w)\b", re.I)
FIXACT = re.compile(r"git (?:commit|push)|sed -i|apply_patch|cat >|tee |\.write\(|str_replace|edit_file|create_file", re.I)
T = datetime.fromisoformat

c = con()
M = messages(c)
nm = dict(c.execute('select id,name from nodes'))
acts = collections.defaultdict(list)
for ag, ts, act in c.execute("select agent,ts,action from turns where ts>='2026-05-11' and ts<'2026-05-16' and action is not null"):
    acts[nm.get(ag, ag)].append((ts, act))

conc = []
for m in M:
    mt = CONC.search(m['content'])
    if not mt:
        continue
    # corrector = room member named nearest the concession phrase (within 150 chars); else the sole addressee
    win = m['content'][max(0, mt.start() - 150): mt.end() + 150]
    near = [(abs(x.start() - (mt.start() - max(0, mt.start() - 150))), a) for a in (BEST if m['room'] == 'best' else REST)
            if a != m['src'] for x in re.finditer(alias_re(a, m['room']), win)]
    ad = addressees(c, m)
    corr = {min(near)[1]} if near else (ad if len(ad) == 1 else set())
    t0 = T(m['ts'])
    fixed = any(n['src'] == m['src'] and t0 <= T(n['ts']) <= t0 + timedelta(minutes=30) and FIXMSG.search(n['content']) for n in M) \
        or any(t0 <= T(ts) <= t0 + timedelta(minutes=30) and FIXACT.search(a) for ts, a in acts[m['src']])
    conc.append((m, sorted(corr), fixed, mt.group(0)))

accepted = collections.Counter()
fixedc = collections.Counter()
for m, corr, fx, _ in conc:
    for a in corr:
        accepted[a] += 1
        fixedc[a] += fx

if __name__ == '__main__':
    print('concessions', len(conc), 'with fix', sum(x[2] for x in conc), 'no corrector resolved', sum(1 for x in conc if not x[1]))
    print('Corrector | room | concessions received | followed by fix')
    for a in sorted(ROOM, key=lambda a: -accepted[a]):
        print(f'{a} | {ROOM[a]} | {accepted[a]} | {fixedc[a]}')
    print('conceders', collections.Counter(m['src'] for m, *_ in conc).most_common())
    if 'sample' in sys.argv:
        for m, corr, fx, hit in sample(conc):
            i = m['content'].find(hit)
            print('=====', m['ref'], m['src'], m['ts'][5:16], '-> corrector', corr, 'fixed', fx)
            print('   ', m['content'][max(0, i - 250): i + 250].replace('\n', ' '))
