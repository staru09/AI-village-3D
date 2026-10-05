"""Q6 columns: agent, messages, emoji msgs, emoji per msg, check-mark msgs, bold/heading-start msgs, emoji-start msgs, @-start msgs,
'Conservative QA' openers, link-line endings, sign-offs, commonest opening, median chars.
Q6: formatting tics per agent over its goal-41 chat messages (base = messages sent).
emoji: any char in emoji ranges (check marks excluded); check: ✅ ✓ ✔ ☑ ✔️; bold head: message starts with ** or # (after emoji);
sign-off: last line names the agent ('— Name' / '-Name' / 'Name' alone) or a closing formula; opening: commonest first 3 words;
length: median characters. --sample prints 25 seed-41 messages flagged emoji / sign-off for validation."""
import re, json, sys, statistics
from collections import Counter
from common import load, AGENTS, sample
T = load()
EMO = re.compile('[\U0001F300-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF\U0001F000-\U0001F2FF⭐⬆⬇⤴⤵‼⁉]')
CHECK = re.compile('[✅✓✔☑]')
HEAD = re.compile(r'^\W{0,4}(\*\*|#)')
def signoff(a, t):
    last = t.strip().splitlines()[-1].strip() if t.strip() else ''
    short = a.replace('Claude ', '')
    return bool(re.match(r'^[—–\-~*_ ]*(' + re.escape(a) + '|' + re.escape(short) + r')[\s*_.!]*$', last)) or bool(re.match(r'^[—–-]\s*\w', last) and (a in last or short in last))
rows = []; flagged = {'emoji': [], 'signoff': []}
for a in AGENTS:
    M = T[a]['chat']; n = len(M)
    if not n: continue
    emo = [m for m in M if EMO.search(CHECK.sub('', m[2]))]; chk = [m for m in M if CHECK.search(m[2])]
    head = [m for m in M if HEAD.match(m[2])]; so = [m for m in M if signoff(a, m[2])]
    ops = Counter(' '.join(re.findall(r"[A-Za-z0-9'’.#@-]+", m[2])[:3]) for m in M).most_common(1)[0]
    emo_per = sum(len(EMO.findall(CHECK.sub('', m[2]))) for m in M) / n
    med = int(statistics.median(len(m[2]) for m in M))
    e0 = sum(bool(EMO.match(m[2].strip())) for m in M)  # opens with an emoji
    at = sum(m[2].strip().startswith('@') for m in M)  # opens by @-addressing a peer
    cq = sum(bool(re.match(r'\W*conservative qa', m[2].strip(), re.I)) for m in M)  # 'Conservative QA ...' opener
    live = sum(bool(re.search(r'(live|url|repo(sitory)?)\W{0,4}:?\W*\s*https?://\S+\W*$|^\W*https?://\S+\W*$', m[2].strip().splitlines()[-1].strip(), re.I)) for m in M if m[2].strip())  # ends on a link line
    rows.append([a, n, len(emo), round(emo_per, 1), len(chk), len(head), e0, at, cq, live, len(so), f'"{ops[0]}" {ops[1]}', med])
    flagged['emoji'] += [(a, m) for m in emo]; flagged['signoff'] += [(a, m) for m in so]
    print(rows[-1])
json.dump(rows, open('q6_tics.json', 'w'), indent=1)
if '--sample' in sys.argv:
    for k in flagged:
        print('== sample', k, len(flagged[k]))
        for a, m in sample(flagged[k]):
            t = m[2]; x = (EMO.search(CHECK.sub('', t)).group(0) if k == 'emoji' else t.strip().splitlines()[-1][:60])
            print(f'  [{a}] {m[0]} {x!r}')
if '--sample2' in sys.argv:  # validation of the heading-start and link-ending columns
    H = [(a, m) for a in AGENTS for m in T[a]['chat'] if HEAD.match(m[2])]
    Lk = [(a, m) for a in AGENTS for m in T[a]['chat'] if m[2].strip() and re.search(r'(live|url|repo(sitory)?)\W{0,4}:?\W*\s*https?://\S+\W*$|^\W*https?://\S+\W*$', m[2].strip().splitlines()[-1].strip(), re.I)]
    for lab, X, f in [('heading', H, lambda t: t[:50]), ('link end', Lk, lambda t: t.strip().splitlines()[-1][:80])]:
        print('== sample', lab, len(X))
        for a, m in sample(X): print(f'  [{a}] {m[0]} {f(m[2])!r}')
