"""L2: whose plans get adopted. Plan-like message = 'proposal' / 'plan:' in text, or >=2 numbered items plus a
forward-looking word. Adopted = another agent in the same room posts a claim ("I'll take", "on it", "claiming", ...)
within 10 minutes; the claim is credited to the latest plan in that window, preferring a plan whose author it names."""
import re, sys, collections
from datetime import datetime, timedelta
from common import con, messages, alias_re, ROOM, sample

NUM = re.compile(r'(?m)^\s*(?:[-*]\s*)?(?:\*\*)?(?:#?\d+[.)]|\(\d+\)|#\d+\b)')
FWD = re.compile(r'\bI(?:[\'’]d)? propose\b|\bproposed roles\b|\bnext steps\b|\baction (?:items|plan)\b|\bvolunteers?\b|\bwho wants\b|\bclaim\b|\bpriorities\b|\b(?:role|task) assignments\b', re.I)
PLAN = re.compile(r'\bproposal\b|\bplan\s*\**:', re.I)
CLAIM = re.compile(r'''\bI(?:['’]ll| will) (?:take|claim|grab|own|handle|pick up)\b|\bclaiming\b|\bon it\b|\bI can take\b|\bI accept the role\b|\bI['’]m taking\b|\bI take\b''', re.I)
T = lambda s: datetime.fromisoformat(s)


def is_plan(t):
    return len(NUM.findall(t)) >= 2 and bool(PLAN.search(t) or FWD.search(t))  # ponytail: v1 (any numbered list + 'plan'/'let's') was 11 of 25


c = con()
M = messages(c)
plans = [m for m in M if is_plan(m['content'])]
claims = [m for m in M if CLAIM.search(m['content'])]
adopt = []   # (claim, plan)
for cm in claims:
    win = [p for p in plans if p['room'] == cm['room'] and p['src'] != cm['src']
           and T(cm['ts']) - timedelta(minutes=10) <= T(p['ts']) < T(cm['ts'])]
    if not win:
        continue
    named = [p for p in win if re.search(alias_re(p['src'], p['room']), cm['content'])]
    adopt.append((cm, (named or win)[-1]))

proposed = collections.Counter(p['src'] for p in plans)
adopted_plans = {p['ref']: p for _, p in adopt}
adopted = collections.Counter(p['src'] for p in adopted_plans.values())
claimers = collections.defaultdict(set)
for cm, p in adopt:
    claimers[p['src']].add(cm['src'])

if __name__ == '__main__':
    print('plans', len(plans), 'claims', len(claims), 'claim->plan pairs', len(adopt), 'plans adopted', len(adopted_plans))
    print('Agent | room | plans | adopted | distinct claimers')
    for a in sorted(ROOM, key=lambda a: (-adopted[a], -proposed[a])):
        print(f'{a} | {ROOM[a]} | {proposed[a]} | {adopted[a]} | {sorted(claimers[a])}')
    if 'plans' in sys.argv:
        for p in sample(plans):
            print('=====', p['ref'], p['src'], p['ts']); print(p['content'][:900])
    if 'pairs' in sys.argv:
        for cm, p in adopt:
            print('=====', cm['ref'], cm['src'], cm['ts'], '<- plan', p['ref'], p['src'], p['ts'])
            print('CLAIM:', cm['content'][:600]); print('PLAN:', p['content'][:600])
    if 'unpaired' in sys.argv:
        for cm in claims:
            if cm not in [x for x, _ in adopt]:
                print('=====', cm['ref'], cm['src'], cm['ts']); print(cm['content'][:500])
