"""W5: which agents reported their own errors before anyone else found them?

Self-correction expression (SELF) over goal-41 chat (sentence level, first person, quoted code removed). A match counts as
unprompted when no other agent's challenge (W1: label calls_out_other) that targets the speaker, or names it, was sent
in the same room in the 60 minutes before.

    python w5_selfcorrect.py            per-agent counts + w5_hits.json
    python w5_selfcorrect.py --sample   25 unprompted matches, seed 41
"""
import json, re, sys
from collections import Counter
from datetime import datetime, timedelta
from common import *

SELF = re.compile(r"(" + "|".join([
    r"\b(my|our) (own )?(mistake|error|bad|oversight)\b", r"\bI made (a|an|another|one) (small |real )?(mistake|error)\b",
    r"\b(I|I've|I had) (accidentally|mistakenly|incorrectly|wrongly|erroneously|inadvertently)\b",
    r"\bI (was|had been) (wrong|checking the wrong|looking at the wrong|using (a|an|the) (stale|old|wrong))\b",
    r"\bI (misread|miscounted|misstated|mislabell?ed|misreported|misunderstood|misattributed|overstated|overclaimed)\b",
    r"\bI stand corrected\b", r"\bapologi(es|ze|se)\b", r"\bretract\w*|\berratum\b",
    r"\bcorrection (to|of) my\b|\bcorrecting my\b|\bto correct my\b",
    r"\bmy (earlier|previous|prior|last|initial|first) [\w-]+( [\w-]+)?\b[^.!?\n]{0,80}"
    r"\b(wrong|incorrect|inaccurate|overstated|stale|mistaken|obsolete|off|mixed|superseded|premature)\b",
    r"\b(caught|found|noticed|fixed) (a|an|one) [\w -]{0,20}(bug|error|mistake|typo|inconsistency) in my (own )?",
    r"\bI (should not|shouldn't) have\b", r"\bthat was (my|a) (mistake|error)\b",
]) + r")", re.I)
SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
QUOTED = re.compile(r'`[^`\n]*`|"[^"\n]*"|“[^”\n]*”')


# All 24 matches read by hand (fewer than 25 unprompted, so no sample): (is it an own-error report?, the earlier
# challenge of THAT error by another agent, or None). The program's 60-minute test was wrong on 11 of 24
# (unrelated messages counted as challenges, one real challenge missed), so the hand flags are the answer.
HAND = {
    'm:b059b618616e': (False, None), 'm:24212fb7d193': (True, 'm:8e82493c27f1'), 'm:2e1eae2f9b0d': (True, 'm:58a931f82057'),
    'm:70efe24a96f6': (True, None), 'm:6c3759148b03': (True, None), 'm:44388ba4a66f': (True, None),
    'm:5205752fa04e': (True, None), 'm:eef7d1f05e34': (True, None), 'm:fc79eb69bfa7': (True, 'm:3d73a13b5719'),
    'm:e77d56c9d28c': (True, 'm:07c13f5f1472'), 'm:bb4c9284c5dc': (True, None), 'm:32c2a0c16f64': (True, None),
    'm:702db80cde08': (False, None), 'm:23bccf41164a': (True, 'm:b1cf1b7af997'), 'm:e1661b9736db': (False, None),
    'm:4bcb3f4e2e87': (True, None), 'm:c074b260e62a': (True, 'm:3962b3fca414'), 'm:cfe97e87fc9a': (True, 'm:2250b3ddf5a2'),
    'm:ab106ae88f80': (True, None), 'm:5302a4629855': (True, 'm:7dfa22fcd139'), 'm:443ebaa6a48b': (True, None),
    'm:9d470f8cbfbd': (True, 'm:c55364df79ec'), 'm:5e125ea24846': (True, None), 'm:63dae0cfcdb8': (True, None),
}
# Found by W2, missed by the expression ("Fixed syntax error" has no first-person error word).
EXTRA = [('m:64bf37b58067', 'Claude Sonnet 4.5')]


def hits(c):
    W1 = json.load(open('w1_hits.json'))
    out = []
    for mid, who, room, ts, text, _ in messages(c):
        if who not in AGENTS:
            continue
        t = QUOTED.sub(' ', (text or '').translate(HYPHENS))
        s = next((s for s in SPLIT.split(t) if SELF.search(s)), None)
        if not s:
            continue
        t0 = str(datetime.fromisoformat(ts[:19]) - timedelta(minutes=60))
        prior = [h['ref'] for h in W1 if h['room'] == room and t0 <= h['ts'] < ts and h['speaker'] != who
                 and (who in h['targets'] or name_rx(who, room).search(h.get('quote', '')))]
        out.append(dict(ref=ref('m', mid), ts=ts, speaker=who, room=room, sentence=s.strip()[:300],
                        prior_challenge=prior[-1] if prior else None))
    return out


if __name__ == '__main__':
    c = con()
    H = hits(c)
    U = [h for h in H if not h['prior_challenge']]
    if '--sample' in sys.argv:
        for h in sample(U):
            print(h['ref'], h['ts'][:16], h['speaker'], '\n   ', h['sentence'], '\n')
        sys.exit()
    print(f'{len(H)} self-correction matches, program: {len(U)} with no challenge of the speaker in the hour before')
    real = [h for h in H if HAND[h['ref']][0]]
    hand_u = [h['speaker'] for h in real if not HAND[h['ref']][1]] + [a for _, a in EXTRA]
    hand_p = [h['speaker'] for h in real if HAND[h['ref']][1]]
    print(f'hand: {len(real)} of {len(H)} are own-error reports; unprompted {len(hand_u)} (incl. {len(EXTRA)} from W2), '
          f'after a challenge {len(hand_p)}')
    prog_ok = sum((not h['prior_challenge']) == (HAND[h['ref']][0] and not HAND[h['ref']][1]) for h in H)
    print(f'program unprompted flag agrees with hand on {prog_ok} of {len(H)}')
    u, p = Counter(hand_u), Counter(hand_p)
    for a in sorted(set(u) | set(p), key=lambda a: (-u[a], a)):
        print(f'  {a:18} unprompted {u[a]}  after challenge {p[a]}')
    json.dump(H, open('w5_hits.json', 'w'), indent=0)
