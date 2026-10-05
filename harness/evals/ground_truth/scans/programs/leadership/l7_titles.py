"""L7: leadership titles. Matches 'lead/leader/leadership/coordinator/manager' (not 'lead to') and case-sensitive 'PI'.
Auto-attribution: the room member named nearest the word (+-80 chars); first-person ('I'll act as', 'my ... as', 'me')
next to the word = the sender. Self-claim if titled agent == sender, recognised if another agent applies it.
Hand labels for all matches are in l7_hand.json (run with 'all' to print every match for reading)."""
import re, sys, json, collections, os
from common import con, messages, alias_re, ROOM, BEST, REST

P = re.compile(r'(?i:\b(?:co-?)?lead(?:er|ership)?\b(?! to\b)|\bcoordinator\b|\bmanager\b)|\bPI\b')
FIRST = re.compile(r"\b(?:I['’]ll|I am|I['’]m|I will|my|me|I)\b")

c = con()
M = messages(c)
hits = []
for m in M:
    for x in P.finditer(m['content']):
        lo = max(0, x.start() - 80)
        win = m['content'][lo: x.end() + 80]
        pos = x.start() - lo
        near = sorted((abs(y.start() - pos), a) for a in (BEST if m['room'] == 'best' else REST)
                      for y in re.finditer(alias_re(a, m['room']), win))
        fp = [abs(y.start() - pos) for y in FIRST.finditer(win)]
        who = m['src'] if fp and (not near or min(fp) < near[0][0]) else (near[0][1] if near else None)
        hits.append(dict(ref=m['ref'], src=m['src'], room=m['room'], ts=m['ts'], word=x.group(0), auto=who,
                         ctx=win.replace('\n', ' ')))

hand = {}
if os.path.exists(os.path.join(os.path.dirname(__file__) or '.', 'l7_hand.json')):
    for h in json.load(open(os.path.join(os.path.dirname(__file__) or '.', 'l7_hand.json'))):
        hand[(h['ref'], h['i'])] = h

if __name__ == '__main__':
    print('matches', len(hits), collections.Counter(h['word'].lower() for h in hits))
    seen = collections.Counter()
    by = collections.defaultdict(set)
    claimed, recog, ok = collections.Counter(), collections.Counter(), 0
    for h in hits:
        i = seen[h['ref']]; seen[h['ref']] += 1
        lab = hand.get((h['ref'], i))
        if 'all' in sys.argv:
            print(h['ref'], i, h['src'], h['ts'][5:16], '| auto:', h['auto'], '|', h['ctx'])
        if lab:
            ok += (lab['agent'] == h['auto']) if lab['kind'] != 'none' else (h['auto'] is None)
            for ag, kind in [[lab['agent'], lab['kind']]] + lab['also']:
                if kind == 'self':
                    claimed[ag] += 1
                elif kind == 'other':
                    recog[ag] += 1
                    by[ag].add(h['src'])
    if hand:
        print(f'auto attribution agrees with hand on {ok} of {len(hits)}')
        print('Agent | self-claims | applied by others | distinct others')
        for a in sorted(ROOM, key=lambda a: -(claimed[a] + recog[a])):
            if claimed[a] or recog[a]:
                print(f'{a} | {claimed[a]} | {recog[a]} | {sorted(by[a])}')
