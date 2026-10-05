"""CH4: each agent's signature phrase: the 4-12 word sequence in the most of its own goal-41 chat messages that no other
agent's goal-41 chat contains (raw text, quotes included, so a quoted copy also disqualifies). Own text is cleaned first:
fenced and inline code, quoted strings, URLs, lines starting with '>' removed. Phrases must have >= 3 alphabetic words,
at most one number, no agent name. Prints top 3 per agent and a seed-41 sample of 25 occurrences of the top phrases."""
import re
from collections import Counter, defaultdict
from chcommon import *

FENCE = re.compile(r'```.*?```', re.S)
URL = re.compile(r'https?://\S+')
QLINE = re.compile(r'^\s*>.*$', re.M)
TOK = re.compile(r"[a-z0-9]+(?:['.-][a-z0-9]+)*")
NAMES = {'claude', 'opus', 'sonnet', 'haiku', 'gemini', 'gpt', 'kimi', 'deepseek', 'deepseek-v3.2', 'k2.6'}


def own(t):
    return clean(QLINE.sub(' ', URL.sub(' ', FENCE.sub(' ', t or ''))))


def toks(t):
    return TOK.findall(t.translate(HYPHENS).lower())


def ok(g):
    alpha = sum(1 for w in g if w.isalpha())
    nums = sum(1 for w in g if any(ch.isdigit() for ch in w))
    return alpha >= 3 and nums <= 1 and not (set(g) & NAMES) and not any(w.startswith('gpt-') for w in g)


def ngrams(ws, lo=4, hi=12):
    return {tuple(ws[i:i + n]) for n in range(lo, hi + 1) for i in range(len(ws) - n + 1)}


def signatures(c, top=3):
    ms = messages(c)
    raw = defaultdict(str)  # all text per agent, raw, as one token string for the 'used by others' test
    for i, a, room, ts, t, _ in ms:
        raw[a] += ' | ' + ' '.join(toks(t or ''))
    cnt, first = defaultdict(Counter), {}
    for i, a, room, ts, t, _ in ms:
        for g in ngrams(toks(own(t))):
            if ok(g):
                cnt[a][g] += 1
                first.setdefault((a, g), (ref('m', i), ts))
    out = {}
    for a in AGENTS:
        others = ' | '.join(v for k, v in raw.items() if k != a)
        cands = [(n, len(g), g) for g, n in cnt[a].items() if n >= 3]
        cands.sort(reverse=True)
        uniq = {g: n for n, L, g in cands if f' {" ".join(g)} ' not in f' {others} '}
        picked = []
        for n, L, g in sorted(((n, len(g), g) for g, n in uniq.items()), reverse=True):
            if any(set(zip(g, g[1:])) & set(zip(p, p[1:])) for m, p in picked):  # overlaps a picked phrase
                continue
            while True:  # extend to the longest unique super-phrase kept in >= 80% of the messages
                ext = [(m, h) for h, m in uniq.items() if len(h) == len(g) + 1 and (h[1:] == g or h[:-1] == g) and m >= 0.8 * n]
                if not ext:
                    break
                n, g = max(ext)
            picked.append((n, g))
            if len(picked) == top:
                break
        out[a] = [(n, ' '.join(g), *first[a, g]) for n, g in picked]
    return out, Counter(m[1] for m in ms)


if __name__ == '__main__':
    import sys
    c = con()
    sig, base = signatures(c)
    for a in AGENTS:
        print(a, base[a], sig[a])
    occ = []
    for i, a, room, ts, t, _ in messages(c):
        if sig.get(a) and sig[a][0][1] in ' '.join(toks(own(t))):
            occ.append((ref('m', i), a, sig[a][0][1]))
    with open('ch4_sample.txt', 'w') as f:
        for r, a, p in sample(occ):
            print(r, a, '|', p, file=f)
    print('occurrences of top phrases', len(occ))
