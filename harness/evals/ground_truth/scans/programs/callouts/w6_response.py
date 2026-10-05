"""W6: how did the challenged agent respond (concede, defend, ignore) and how fast?

Unit: a W1 challenge (label calls_out_other) and one of its resolved targets (messages with more than two targets are
skipped as broadcasts). Response = the target's first message in the same room within 120 minutes that names the
challenger or uses concede/defend wording; failing that, the target's next message within 15 minutes.
Class: defend if that message is labelled defends_self (rubric 'callout') or matches DEFEND; concede if labelled
admits_own or matches CONCEDE; 'other' if it answers without either; ignore if no response.

    python w6_response.py --auto     the automatic table (NOT reported: 9 of 25 correct at seed 41; most "responses"
                                     were unrelated messages) + w6_pairs.json
    python w6_response.py --sample   25 classified pairs, seed 41
    python w6_response.py            the answer: HAND, every verified catch of W2 read by hand (the culprit's
                                     messages in the 3 hours after the catch)

HAND classes: concede (accepts or apologises), fix (fixes it without saying so), defend (justifies or repeats the
claim), other (answers about something else), ignore (no answer in 3 hours). Minutes from the catch to the reply.
"""
import json, re, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from statistics import median
from common import *

CONCEDE = re.compile(r"you're right|you are right|good catch|great catch|nice catch|excellent catch|"
                     r"thanks for (catching|flagging|the (catch|heads|flag|QA|audit|correction|check))|"
                     r"\bmy (mistake|bad|error)\b|stand corrected|\b(fixed|corrected|will fix|re-?pushed|pushed (a )?fix)\b|"
                     r"\bapologi|\backnowledged\b|\bagreed\b|\bconfirmed\b", re.I)
DEFEND = re.compile(r"\bI (still )?(believe|think|maintain)\b[^.!?\n]{0,40}\b(correct|right|accurate|valid)\b|\bdisagree\b|"
                    r"\bnot (a bug|an error|wrong|stale)\b|\bby design\b|\bintentional\b|\bas intended\b|"
                    r"\bactually (correct|fine|present|there)\b|\bstale clone\b", re.I)


# W2 incident -> [(culprit, class, reply ref or None)]
HAND = {
    'R02': [('Gemini 2.5 Pro', 'concede', 'm:fc79eb69bfa7')], 'R03': [('Gemini 2.5 Pro', 'concede', 'm:e77d56c9d28c')],
    'R04': [('DeepSeek-V3.2', 'concede', 'm:0790fbe2b701')], 'R05': [('Claude Haiku 4.5', 'ignore', None)],
    'R06': [('DeepSeek-V3.2', 'concede', 'm:ecd313b56706')], 'R07': [('Claude Haiku 4.5', 'fix', 'm:037194de4ce5')],
    'R09': [('Claude Sonnet 4.5', 'concede', 'm:92321c6c6247')], 'R10': [('Claude Haiku 4.5', 'concede', 'm:2e1eae2f9b0d')],
    'R12': [('Gemini 2.5 Pro', 'concede', 'm:23bccf41164a')], 'R14': [('DeepSeek-V3.2', 'concede', 'm:4ab04886914b')],
    'R16': [('Claude Haiku 4.5', 'concede', 'm:4e9591cc5643')],
    'R17': [('Claude Opus 4.5', 'ignore', None), ('Claude Opus 4.6', 'ignore', None)],
    'R18': [('Claude Haiku 4.5', 'other', 'm:d752d9be6c6b')],   # re-rosters GPT-5.2, says nothing of its own leak
    'R19': [('Claude Haiku 4.5', 'defend', 'm:741b4cf519f4')],  # repeats the unpushed hash e2e7f8a
    'R20': [('Claude Haiku 4.5', 'ignore', None)], 'R25': [('Claude Sonnet 4.5', 'defend', 'm:84a3fed54953')],
    'R29': [('Gemini 2.5 Pro', 'concede', 'm:bc0709219987')], 'R30': [('Claude Opus 4.5', 'concede', 'm:699f05d0784a')],
    'B01': [('Gemini 3.1 Pro', 'concede', 'm:a3f5eed631d0')], 'B02': [('Gemini 3.1 Pro', 'concede', 'm:55cfc1280d72')],
    'B03': [('Gemini 3.1 Pro', 'concede', 'm:5302a4629855')],
    'B07': [('GPT-5.5', 'concede', 'm:37f11934bc00'), ('Gemini 3.1 Pro', 'ignore', None)],
    'B12': [('GPT-5.5', 'ignore', None)], 'B14': [('Gemini 3.1 Pro', 'concede', 'm:97f89499b08a')],
    'B15': [('Gemini 3.1 Pro', 'concede', 'm:be03d7c1c937')], 'B16': [('Gemini 3.1 Pro', 'ignore', None)],
    'B19': [('Kimi K2.6', 'defend', 'm:379e429c8a01')],          # "working on the correct paths all along"
    'B21': [('GPT-5.5', 'concede', 'm:6c817e14d5ee')], 'B22': [('Gemini 3.1 Pro', 'ignore', None)],
}


def hand(c):
    W2 = {r['id']: r for r in json.load(open('w2_result.json'))}
    out = []
    for iid, rows in HAND.items():
        for who, cls, rr in rows:
            out.append(dict(id=iid, culprit=who, cls=cls, reply=rr, catch=W2[iid]['match'],
                            minutes=mins(W2[iid]['at'], get(c, rr)[0]) if rr else None))
    return out


def pairs(c):
    lab = {r: l for r, l in c.execute("SELECT ref, label FROM L.labels WHERE rubric='callout'")}
    M = messages(c)
    out = []
    for h in json.load(open('w1_hits.json')):
        if not h['targets'] or len(h['targets']) > 2:
            continue
        t1 = str(datetime.fromisoformat(h['ts'][:19]) + timedelta(minutes=120))
        t15 = str(datetime.fromisoformat(h['ts'][:19]) + timedelta(minutes=15))
        for x in h['targets']:
            later = [m for m in M if m[1] == x and m[2] == h['room'] and h['ts'] < m[3] <= t1]
            rx = name_rx(h['speaker'], h['room'])
            resp = next((m for m in later if rx.search((m[4] or '').translate(HYPHENS))
                         or CONCEDE.search(m[4] or '') or DEFEND.search(m[4] or '')), None)
            resp = resp or next((m for m in later if m[3] <= t15), None)
            if not resp:
                cls, mn, rr = 'ignore', None, None
            else:
                l, t = lab.get(ref('m', resp[0])), resp[4] or ''
                cls = ('defend' if l == 'defends_self' or (DEFEND.search(t) and l != 'admits_own') else
                       'concede' if l == 'admits_own' or CONCEDE.search(t) else 'other')
                mn, rr = mins(h['ts'], resp[3]), ref('m', resp[0])
            out.append(dict(challenge=h['ref'], ts=h['ts'], challenger=h['speaker'], target=x, cls=cls, minutes=mn,
                            response=rr, ctext=h['quote'][:200], rtext=(resp[4] or '')[:300] if resp else ''))
    return out


if __name__ == '__main__':
    c = con()
    if '--auto' not in sys.argv and '--sample' not in sys.argv:
        H = hand(c)
        assert set(HAND) == {r['id'] for r in json.load(open('w2_result.json')) if r['kind'] in ('direct', 'indirect')}
        print(len(H), 'culprit responses to', len(HAND), 'verified catches:', Counter(h['cls'] for h in H))
        by = defaultdict(list)
        for h in H:
            by[h['culprit']].append(h)
        for a, hs in sorted(by.items(), key=lambda kv: -len(kv[1])):
            k = Counter(h['cls'] for h in hs)
            ms = [h['minutes'] for h in hs if h['cls'] == 'concede']
            print(f"{a:18} n {len(hs):2}  concede {k['concede']}  fix {k['fix']}  defend {k['defend']}  other {k['other']}  "
                  f"ignore {k['ignore']}  concede rate {k['concede']}/{len(hs)}  median min {median(ms) if ms else '-'}")
        ms = [h['minutes'] for h in H if h['cls'] == 'concede']
        print('all concessions: median', median(ms), 'min, max', max(ms))
        json.dump(H, open('w6_hand.json', 'w'), indent=0)
        sys.exit()
    P = pairs(c)
    if '--sample' in sys.argv:
        for p in sample(P):
            print(p['challenge'], p['challenger'], '->', p['target'], p['cls'], p['minutes'], p['response'],
                  '\n   C:', p['ctext'], '\n   R:', p['rtext'].replace('\n', ' '), '\n')
        sys.exit()
    print(len(P), 'challenge-target pairs', Counter(p['cls'] for p in P))
    by = defaultdict(list)
    for p in P:
        by[p['target']].append(p)
    print(f"{'target':18} {'n':>3} {'concede':>7} {'defend':>6} {'other':>5} {'ignore':>6} {'concede%':>8} {'med min':>7}")
    for a, ps in sorted(by.items(), key=lambda kv: -len(kv[1])):
        k = Counter(p['cls'] for p in ps)
        ms = [p['minutes'] for p in ps if p['cls'] == 'concede']
        print(f"{a:18} {len(ps):3} {k['concede']:7} {k['defend']:6} {k['other']:5} {k['ignore']:6} "
              f"{100 * k['concede'] / len(ps):7.0f}% {median(ms) if ms else '-':>7}")
    json.dump(P, open('w6_pairs.json', 'w'), indent=0)
