"""L6 tally of the full hand reading (l6_cases/part*_hand.json, 227 directs x addressee links; the keyword program
l6_compliance.py agreed with hand labels on only 4 of 25, so its counts are not used)."""
import json, glob, collections
H = [x for f in sorted(glob.glob('l6_cases/part*_hand.json')) for x in json.load(open(f))]
S = {(x['ref'], x['addressee']): x['hand'] for x in json.load(open('l6_hand.json'))}
if __name__ == '__main__':
    print('links', len(H), dict(collections.Counter(x['hand'] for x in H)))
    both = [(S[k], x['hand']) for x in H if (k := (x['ref'], x['addressee'])) in S]
    print(f'second reader agreement on the 25-link sample: {sum(a == b for a, b in both)} of {len(both)}')
    per = collections.defaultdict(collections.Counter)
    for x in H:
        per[x['assigner']][x['hand']] += 1
    L = ['done_after', 'started_before', 'declined', 'other', 'absent', 'not_a_task']
    print('Assigner | real tasks | ' + ' | '.join(L) + ' | done_after rate')
    for a, c in sorted(per.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(c.values()) - c['not_a_task']
        print(f"{a} | {n} | " + ' | '.join(str(c[l]) for l in L) + f" | {c['done_after']/n:.0%}")
    rcv = collections.defaultdict(collections.Counter)
    for x in H:
        rcv[x['addressee']][x['hand']] += 1
    print('by addressee', {a: dict(c) for a, c in rcv.items()})
