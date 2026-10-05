"""L1/L5: who assigns tasks to whom, per room and day, from the stored `delegation` labels (label 'directs').
Addressees = @-mention edges + short names in address position (common.addressees)."""
import json, collections, sys
from common import con, messages, addressees, ROOM, sample

c = con()
msgs = {m['ref']: m for m in messages(c)}
lab = dict(c.execute("select ref,label from L.labels where rubric='delegation'"))
directs = [msgs[r] for r, l in lab.items() if l == 'directs' and r in msgs]
pairs = [(m, a) for m in directs for a in sorted(addressees(c, m))]

sent = collections.Counter(m['src'] for m in directs)
recv = collections.Counter()           # directs messages received (one per message per addressee)
for m, a in pairs:
    recv[a] += 1
links = collections.Counter((m['src'], a) for m, a in pairs)
byday = collections.Counter((m['room'], m['day'], m['src']) for m in directs)

if __name__ == '__main__':
    print('directs messages', len(directs), 'addressee links', len(pairs), 'labelled msgs', len(lab))
    print('\nAgent | room | assigned(msgs) | received(msgs) | net')
    for a in sorted(ROOM, key=lambda a: -(sent[a] - recv[a])):
        print(f'{a} | {ROOM[a]} | {sent[a]} | {recv[a]} | {sent[a]-recv[a]:+d}')
    print('\ntop links', links.most_common(15))
    print('\nPer room/day (assigner counts; top first)')
    for room in ('best', 'rest'):
        for d in ['2026-05-1%d' % i for i in range(1, 6)]:
            row = sorted(((n, a) for (r, dd, a), n in byday.items() if r == room and dd == d), reverse=True)
            print(room, d, 'total', sum(n for n, _ in row), row)
    if 'sample' in sys.argv:   # validation of addressee resolution: 25 links, seed 41
        for m, a in sample(pairs):
            print('=====', m['ref'], m['room'], m['src'], '->', a, '| all:', sorted(addressees(c, m)))
            print(m['content'][:700])
