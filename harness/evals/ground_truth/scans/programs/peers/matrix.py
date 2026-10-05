"""P1, P2, P3, P6: speaker x target matrix of goal-41 chat with short names resolved (core.find).

mention   = the message names the target (full or resolved short name)
praise, request, deference = m4 expressions (peer_matrix.REGEX) on the sentences about the target (core.target_sentences)
criticism = stored label rubric 'callout' = calls_out_other; target = agents named in the label's reason (the
            labeller says whose work is challenged), else in its quote, else in the first 80 characters (the addressee).
            Within the reason, agents in a possessive or right after a call-out verb win (culprits()). Rounds: quote first (as
            w1) and reason first both put the target wrong when several agents are named (19 of 25); culprits() fixed it.

    python matrix.py                 report, writes matrix_out.json
    python matrix.py --sample CLASS  25 hits (seed 41); CLASS in shortonly praise criticism request deference
"""
import json, sys
from collections import Counter, defaultdict
from core import *
from core import scan

CLS = ['praise', 'criticism', 'request', 'deference']
VERB = re.compile(r"\b(call(s|ed|ing)? out|challeng\w*|correct(s|ed|ing)?|disput\w*|question(s|ed|ing)|criticiz\w*|"
                  r"disagree\w* with|tells?|telling)\b", re.I)


def culprits(why, who, room):
    """Agents the labeller's reason names as at fault: named in a possessive ("Gemini's work") or within 30
    characters after a call-out verb ("calls out Claude and Kimi"); else everyone it names."""
    w = why.translate(HYPHENS)
    ends = [m.end() for m in VERB.finditer(w)]
    found = [(a, m) for a, k, m in scan(w, room) if a != who]
    strong = {a for a, m in found if w[m.end():m.end() + 2] == "'s" or any(0 <= m.start() - e <= 30 for e in ends)}
    return strong or {a for a, m in found}


def build():
    c = con()
    M = [m for m in messages(c) if m[1] in AGENTS]
    lab = {r: (q or '', w or '') for r, q, w in c.execute(
        "SELECT ref, quote, why FROM L.labels WHERE rubric='callout' AND label='calls_out_other'")}
    hits = []  # dict per (message, target)
    for mid, who, room, ts, text, _ in M:
        t = clean(text)
        named = find(t, who, room)
        r = ref('m', mid)
        crit = set()
        if r in lab:
            q, w = lab[r]
            crit = set(culprits(w, who, room) or find(q.translate(HYPHENS), who, room)
                       or find(t[:80], who, room))
        for a in sorted(set(named) | crit):
            sents = target_sentences(t, a, room) if a in named else []
            h = dict(ref=r, ts=ts, day=day(ts), room=room, src=who, dst=a, form=named.get(a), mention=a in named,
                     criticism=a in crit, crit_quote=lab.get(r, ('', ''))[0][:200] if a in crit else '')
            for k, rx in RX.items():
                h[k] = [s for s in sents if rx.search(s)]
            hits.append(h)
    return M, hits


if __name__ == '__main__':
    M, H = build()
    if '--sample' in sys.argv:
        k = sys.argv[sys.argv.index('--sample') + 1]
        pool = [h for h in H if (h['form'] == 'short' if k == 'shortonly' else h[k])]
        print(len(pool), 'hits')
        for h in sample(pool):
            print(h['ref'], h['ts'][:16], h['room'], h['src'], '->', h['dst'], h['form'])
            print('   ', (h['crit_quote'] if k == 'criticism' else ' | '.join(h[k]) if k in RX else '')[:400])
        sys.exit()
    n = defaultdict(Counter)
    daily = defaultdict(Counter)
    for h in H:
        k = (h['src'], h['dst'])
        n[k]['mention'] += h['mention']
        for c in CLS:
            n[k][c] += bool(h[c])
        daily[k][h['day']] += bool(h['praise']) - bool(h['criticism'])
        daily[k]['m' + h['day']] += h['mention']
    short_only = sum(1 for m in {h['ref'] for h in H if h['form'] == 'short'}
                     if not any(x['ref'] == m and x['form'] == 'full' for x in H))
    print(len(M), 'messages;', len({h['ref'] for h in H if h['mention']}), 'name a peer;',
          sum(h['mention'] for h in H), 'mention pairs;', sum(h['form'] == 'short' for h in H), 'by short name only;',
          short_only, 'messages name peers only by short name')
    pairs = sorted(n, key=lambda k: -n[k]['mention'])
    for k in pairs:
        if n[k]['mention'] >= 5:
            print(f'{k[0]:18} -> {k[1]:18}', ' '.join(f'{c[:4]} {n[k][c]:3}' for c in ['mention'] + CLS))
    recv = {a: Counter() for a in AGENTS}
    give = {a: Counter() for a in AGENTS}
    for (s, d), v in n.items():
        recv[d].update(v); give[s].update(v)
    print('\nper agent received: mention praise crit (per 100 mentions) | given')
    for a in sorted(AGENTS, key=lambda a: -recv[a]['praise']):
        r = recv[a]; m = r['mention'] or 1
        print(f'{a:18} {r["mention"]:4} {r["praise"]:4} ({100*r["praise"]/m:5.1f}) {r["criticism"]:4} ({100*r["criticism"]/m:5.1f})'
              f' | {give[a]["mention"]:4} {give[a]["praise"]:4} {give[a]["criticism"]:4}')
    json.dump(dict(pairs=[dict(src=s, dst=d, **n[s, d]) for s, d in pairs],
                   daily={f'{s}|{d}': dict(daily[s, d]) for s, d in daily},
                   received={a: dict(recv[a]) for a in AGENTS}, given={a: dict(give[a]) for a in AGENTS}),
              open('matrix_out.json', 'w'), indent=0)
