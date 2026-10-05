"""Turn the hand reading of all 324 stored challenge labels (hand_b1.txt: 'index verdict' pairs, ';'-separated; verdict
X = no challenge to a named room-mate, or an agent name = the real target; unlisted = the program's target is right)
into f1_hand.json: [{ref, ts, day, speaker, room, target, auto_target, quote}] for the 324 labels."""
import json, re
from fcommon import *
c = con()
H = challenges(c)
V = {}
for part in re.split(r'[;\n]', open('hand_b1.txt').read()):
    if part.strip():
        i, v = part.strip().split(' ', 1)
        assert int(i) not in V, i
        V[int(i)] = v
out = []
for i, h in enumerate(H):
    auto = h['targets'][0] if h['targets'] else None
    v = V.get(i, 'K')
    tg = None if v == 'X' else auto if v == 'K' else v
    assert v == 'X' or tg in AGENTS, (i, v)
    out.append(dict(i=i, ref=h['ref'], ts=h['ts'], day=h['day'], speaker=h['speaker'], room=h['room'], target=tg, auto_target=auto, quote=h['quote']))
json.dump(out, open('f1_hand.json', 'w'), indent=0)
real = [o for o in out if o['target']]
print(len(out), 'labels;', len(real), 'real challenges to a named room-mate;', sum(1 for o in out if o['target'] and o['target'] != o['auto_target']), 'retargeted;',
      sum(1 for o in out if o['auto_target'] and not o['target']), 'auto-targeted dropped')
