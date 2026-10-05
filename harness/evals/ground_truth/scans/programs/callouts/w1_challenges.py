"""W1: who challenges whose work, goal 41 chat.

Round 1, a challenge expression (CHALLENGE below, sentence level, target = room-mate named in the sentence or the
addressee): 14 of 25 correct at seed 41 (admissions, thanks-for-the-catch replies, status notes), so its counts are not
reported (`--regex` prints them; `--regex --sample` the sample).
Round 2 (the answer): challenge = stored label rubric 'callout' = calls_out_other (one label per goal-41 message);
21 of 25 correct at seed 41 as challenges; it also covers 18 of the 21 regex matches judged real. Target = room-mates
named in the label's quote, else in the label's reason, else the addressee (named in the first 80 characters), else
'unnamed'.

    python w1_challenges.py            report + w1_hits.json (used by W2, W5, W6, W7)
    python w1_challenges.py --sample   25 challenges with targets, seed 41
"""
import json, re, sys
from collections import Counter
from common import *

CHALLENGE = re.compile(r"(" + "|".join([
    r"\bhow\b[^.?!\n]{0,50}\b(were|was)\b[^.?!\n]{0,30}\b(produced|generated|computed|derived|made|created|scored)\b",
    r"\b(does(n't| not)|do(n't| not)|did(n't| not)) match\b", r"\bmismatch\w*", r"\bdiscrepanc\w*", r"\binconsisten\w*",
    r"\b(could(n't| not)|can't|cannot|unable to) (reproduce|replicate|verify|confirm)\b",
    r"\bplease (verify|double-check|re-?check|re-?run|document|remove|revert|correct|fix|re-?push)\b",
    r"\b(one|small|quick|minor|a) correction\b|\bcorrection:", r"\b(should|needs? to) be (corrected|fixed|removed|reverted|excluded|relabell?ed)\b",
    r"\b(is|are|was|were|looks|seems|remains?|still) (stale|wrong|incorrect|inaccurate|overstated|misleading|premature|"
    r"not accurate|not correct|contaminated|empty|broken|unsupported|not supported|aspirational)\b",
    r"\bnot (actually|yet) (pushed|on main|landed|merged|present|there|in the repo|in `?main)",
    r"\b(n't|not) actually\b", r"\boverstat\w*|\bover-?claim\w*",
    r"\b(synthetic|random\w*|heuristic|hard-?coded|fabricat\w*|placeholder)\b[^.?!\n]{0,20}\b(rows|scores|data|numbers|values|judg\w+)\b",
    r"\b(I|we) (disagree|don't agree|do not agree)\b",
    r"\b(I|we) (don't|do not|can't|cannot|couldn't|could not) (see|find)\b",
    r"\b(does(n't| not)|do(n't| not)) exist\b",
    r"\b(caught|spotted|found|noticed) (a|an|one|two|three|the|another|several)? ?(real |small |minor |critical )?"
    r"(bug|error|issue|problem|mistake|discrepanc\w*|inconsistenc\w*|mismatch)",
    r"\bwrong[- ](task|file|dir\w*|branch|number|count|score|condition)\b",
    r"\b(audit|QA|hygiene|risk) note\b", r"\bheads[- ]up\b",
]) + r")", re.I)
SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
QUOTED = re.compile(r'`[^`\n]*`')
LEAD = re.compile(r"^(\W*@?(Claude |Gemini )?[\w.-]+( [\d.]+)?\W*(,|:|—|-)?\s*)?")
OWN = re.compile(r"\b(my|mine|I've|I'm|I was|I had|we've|our own)\b", re.I)  # own work: an admission, not a challenge
YOU = re.compile(r"\b(you|your|you're|you've)\b", re.I)
# acknowledging someone else's catch ("thanks for the heads-up", "X flagged a ...") is not a challenge by the speaker
ACK = re.compile(r"\b(thanks|thank you|appreciate\w*|excellent|great|good|nice|fair) (catch|point|for|the|on)\b|\bflagged by\b|"
                 r"\b(flagged|identified|caught|noted|spotted|raised|found)\b|\back\b|\byou're right\b|\bagreed\b|\bfixed\b", re.I)
PLAN = re.compile(r"^\W*(-|\*|\d+\.)\s|\bif\b", re.I)  # plan bullets and conditionals ("adjudicate if >50 pt discrepancy")


def regex_hits(c):
    out = []
    for mid, who, room, ts, text, _ in messages(c):
        if who not in AGENTS:
            continue
        t = QUOTED.sub(' ', (text or '').translate(HYPHENS))
        addr = named(t[:80], who, room)
        sents, tg = [], set()
        for s in SPLIT.split(t):
            if not CHALLENGE.search(s) or (OWN.search(s) and not YOU.search(s)) or PLAN.search(s) or ACK.search(s):
                continue
            who_s = named(s, who, room) or addr
            if who_s:
                sents.append(s); tg |= set(who_s)
        if not sents:
            continue
        tg = sorted(tg)
        out.append(dict(ref=ref('m', mid), id=mid, ts=ts, speaker=who, room=room, targets=tg,
                        match=CHALLENGE.search(sents[0]).group(0), sentence=sents[0][:300]))
    return out



def hits(c):
    out = []
    M = {ref('m', m[0]): m for m in messages(c)}
    for r, quote, why in c.execute("SELECT ref, quote, why FROM L.labels WHERE rubric='callout' AND label='calls_out_other' "
                                   "ORDER BY ts"):
        mid, who, room, ts, text, _ = M[r]
        t = (text or '').translate(HYPHENS)
        tg = named(quote or '', who, room) or named(why or '', who, room) or named(t[:80], who, room)
        out.append(dict(ref=r, id=mid, ts=ts, speaker=who, room=room, targets=tg, quote=(quote or '')[:300], why=why))
    return out


if __name__ == '__main__':
    c = con()
    H = regex_hits(c) if '--regex' in sys.argv else hits(c)
    if '--sample' in sys.argv:
        for h in sample(H):
            print(h['ref'], h['ts'][:16], h['speaker'], '->', h['targets'], '|', h.get('match', ''), '\n   ',
                  h.get('sentence') or h['quote'], '\n   why:', (h.get('why') or '')[:300], '\n')
        sys.exit()
    T = [h for h in H if h['targets']]
    pair = Counter((h['speaker'], t) for h in T for t in h['targets'])
    print(f'{len(H)} challenge messages, {len(T)} with a resolved room-mate target, {len(H) - len(T)} unnamed')
    print('by speaker (all):', Counter(h['speaker'] for h in H).most_common())
    print('by speaker (targeted):', Counter(h['speaker'] for h in T).most_common())
    print('by target :', Counter(t for h in T for t in h['targets']).most_common())
    for (a, b), n in pair.most_common():
        print(f'  {a:18} -> {b:18} {n}')
    if '--regex' not in sys.argv:
        json.dump(H, open('w1_hits.json', 'w'), indent=0)
