"""L3: whom agents ask for permission/approval. A permission request = a sentence ending in '?' that contains
"can I / should I / OK to / may I / shall I / want me to / go ahead", or any sentence with "approve/approval/sign-off"
that is a question or a request ('please'). Asked-of = addressees (common.addressees); none = whole room."""
import re, sys, collections
from common import con, messages, addressees, ROOM, sample

ASK = re.compile(r"\b(?:can|could|should|may|shall) I\b|\bOK(?:ay)? (?:to|if I)\b|\bwant me to\b|\bgo ahead\b|\bgreen ?light\b", re.I)
APP = re.compile(r"\bapprov(?:e|al)\b|\bsign[- ]off\b", re.I)
SENT = re.compile(r'[^.!?\n]*[.!?\n]?')


def is_request(t):
    for s in SENT.findall(t):
        if s.rstrip().endswith('?') and (ASK.search(s) or APP.search(s)):
            return True
        if APP.search(s) and re.search(r'\bplease\b|\bneed (?:your|an?)\b|\bawait', s, re.I):
            return True
    return False


c = con()
M = messages(c)
reqs = [m for m in M if is_request(m['content'])]
asked = collections.Counter()
askers = collections.Counter(m['src'] for m in reqs)
pairs = []
for m in reqs:
    ad = addressees(c, m)
    for a in (ad or ['(room)']):
        asked[(m['room'], a)] += 1
        pairs.append((m, a))

if __name__ == '__main__':
    print('requests', len(reqs), 'of', len(M), 'messages; asker->addressee pairs', len(pairs))
    for room in ('best', 'rest'):
        print(room, sorted(((n, a) for (r, a), n in asked.items() if r == room), reverse=True))
    print('askers', askers.most_common())
    if 'sample' in sys.argv:
        for m in sample(reqs):
            hits = [s.strip()[:250] for s in SENT.findall(m['content']) if (s.rstrip().endswith('?') and (ASK.search(s) or APP.search(s))) or (APP.search(s) and re.search(r'please|need|await', s, re.I))]
            print('=====', m['ref'], m['src'], '->', sorted(addressees(c, m)) or '(room)'); print('  HIT:', hits[:3])

# Who answered: first message by another agent within 15 min that addresses/names the asker and says yes/go ahead/approve.
from datetime import datetime, timedelta
from common import alias_re
YES = re.compile(r"\b(?:yes|yep|go ahead|approved?|please do|agreed?|sounds good|confirmed?|green ?light|do it|proceed)\b", re.I)
T = datetime.fromisoformat
answers = {}
for m in reqs:
    for n in M:
        if n['room'] == m['room'] and n['src'] != m['src'] and T(m['ts']) < T(n['ts']) <= T(m['ts']) + timedelta(minutes=15) \
           and (m['src'] in addressees(c, n) or re.search(alias_re(m['src'], m['room']), n['content'])) and YES.search(n['content']):
            answers[m['ref']] = n
            break
granted = collections.Counter((m['room'], answers[m['ref']]['src']) for m in reqs if m['ref'] in answers)
if __name__ == '__main__':
    print('answered with yes/go-ahead within 15 min:', len(answers), 'of', len(reqs))
    for room in ('best', 'rest'):
        print(' granted by', room, sorted(((n, a) for (r, a), n in granted.items() if r == room), reverse=True))
    if 'answers' in sys.argv:
        for m in reqs:
            n = answers.get(m['ref'])
            print(m['ref'], m['src'], '->', n and (n['ref'], n['src'], n['ts'][11:19], n['content'][:200].replace('\n', ' ')))
