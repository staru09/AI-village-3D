"""Swarm analysis: who mentions whom in the AI Village (data/mentions.csv and data/index.json from extract.py).

  uv run --no-project --with networkx --with scipy python analysis/swarm.py [--since YYYY-MM-DD] [--until YYYY-MM-DD]

Prints a Markdown report: the most mentioned agents (in total and per day present), the most active mentioners, the
strongest ties and how reciprocal they are, hubs and bridges, groups (Louvain communities over the whole run, with
ties scaled by the days two agents were both present, and per quarter), and how much agents stay within their maker.
"""
import argparse, csv, json
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

DATA = Path(__file__).resolve().parent.parent / 'data'


def table(head, rows):
    return '\n'.join(['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)] + ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows])


def groups(G, seed=1):  # Louvain communities of 2+ agents, largest first, and the partition's modularity
    parts = nx.community.louvain_communities(G, weight='weight', seed=seed)
    return [c for c in sorted(parts, key=len, reverse=True) if len(c) > 1], nx.community.modularity(G, parts, weight='weight')


def main():
    ap = argparse.ArgumentParser(description='Swarm analysis of agent-to-agent mentions.')
    ap.add_argument('--since', default='0000')
    ap.add_argument('--until', default='9999')
    a = ap.parse_args()
    ix = json.loads((DATA / 'index.json').read_text())
    A = ix['agents']
    name, maker = (lambda s: A[s]['name']), (lambda s: A[s]['clan'])
    present = defaultdict(set)  # agent -> days in the village
    for d in ix['days']:
        if a.since <= d['date'] <= a.until:
            for s in d['agents']:
                present[s].add(d['date'])
    rows = [r for r in csv.DictReader(open(DATA / 'mentions.csv', encoding='utf-8'))
            if a.since <= r['date_pt'] <= a.until and r['from'] != r['to']]
    E = Counter((r['from'], r['to']) for r in rows)
    # interactions: the mentioned agent was in the village that day (the rest refer back to agents who left or had not come)
    L = Counter((r['from'], r['to']) for r in rows if r['date_pt'] in present[r['to']])
    got, made = Counter(), Counter()
    by, to = defaultdict(set), defaultdict(set)
    for (s, t), n in E.items():
        got[t] += n; made[s] += n; by[t].add(s); to[s].add(t)
    total = sum(E.values())
    assert total == len(rows)
    out = [f'# Swarm analysis: who mentions whom\n',
           f'{total:,} mentions between {len(set(got) | set(made))} agents, {len(E):,} directed pairs, '
           f'{rows[0]["date_pt"]} to {rows[-1]["date_pt"]}. {1 - sum(L.values()) / total:.1%} of the mentions ({total - sum(L.values()):,}) name an agent '
           'who was not in the village that day (a reference to its past work). Hubs and groups count only the rest.\n']

    out += ['## Most mentioned agents\n', table(
        ['Agent', 'Maker', 'Mentions received', 'Share', 'By how many agents', 'Days present', 'Per day present'],
        [[name(s), maker(s), f'{n:,}', f'{n / total:.1%}', len(by[s]), len(present[s]), f'{n / max(1, len(present[s])):.0f}']
         for s, n in got.most_common(12)]), '']
    rate = sorted((s for s in got if len(present[s]) >= 20), key=lambda s: -got[s] / len(present[s]))
    out += ['## Most mentioned per day present (agents present 20+ days)\n', table(
        ['Agent', 'Per day present', 'Days present'], [[name(s), f'{got[s] / len(present[s]):.0f}', len(present[s])] for s in rate[:10]]), '']
    out += ['## Who mentions others most\n', table(
        ['Agent', 'Mentions made', 'Distinct agents mentioned', 'Made / received'],
        [[name(s), f'{n:,}', len(to[s]), f'{n / max(1, got[s]):.1f}'] for s, n in made.most_common(10)]), '']

    pair = Counter()
    for (s, t), n in E.items():
        pair[tuple(sorted((s, t)))] += n
    both = sum(2 * min(E[s, t], E[t, s]) for s, t in pair)
    out += ['## Strongest ties\n',
            f'Reciprocity: {both / total:.0%} of all mentions are matched by a mention in the other direction.\n',
            table(['Pair', 'Total', 'A → B', 'B → A', 'Balance'],
                  [[f'{name(x)} ↔ {name(y)}', f'{n:,}', f'{E[x, y]:,}', f'{E[y, x]:,}', f'{min(E[x, y], E[y, x]) / max(E[x, y], E[y, x]):.0%}']
                   for (x, y), n in pair.most_common(12)]), '']

    D = nx.DiGraph()
    D.add_weighted_edges_from((s, t, n) for (s, t), n in L.items())
    live = Counter()
    for (s, t), n in L.items():
        live[tuple(sorted((s, t)))] += n
    U = nx.Graph()
    for (x, y), n in live.items():  # ties scaled by the days both agents were present, so long stays do not dominate
        U.add_edge(x, y, weight=n / max(1, len(present[x] & present[y])), n=n, distance=1 / n)
    pr = nx.pagerank(D, weight='weight')
    btw = nx.betweenness_centrality(U, weight='distance')
    out += ['## Hubs and bridges\n',
            'PageRank: mentioned by agents who are themselves mentioned a lot. Betweenness: on the shortest paths between '
            'other agents (a bridge between groups).\n',
            table(['Rank', 'PageRank', 'Score', 'Betweenness', 'Score'],
                  [[k + 1, name(p), f'{pr[p]:.3f}', name(b), f'{btw[b]:.3f}']
                   for k, (p, b) in enumerate(zip(sorted(pr, key=pr.get, reverse=True)[:8], sorted(btw, key=btw.get, reverse=True)[:8]))]), '']

    G, Q = groups(U)
    inside = lambda c: sum(n for (s, t), n in L.items() if s in c and t in c)
    out += [f'## Groups over the whole run (Louvain, modularity {Q:.2f})\n',
            'Ties are mentions per day both agents were present. Members are listed by mentions received.\n',
            table(['Group', 'Members', 'Makers', 'First joined', 'Mentions inside the group'],
                  [[k + 1, ', '.join(name(s) for s in sorted(c, key=lambda s: -got[s])),
                    ', '.join(f'{m} {n}' for m, n in Counter(maker(s) for s in c).most_common()),
                    min(A[s]['joined'] for s in c), f'{inside(c):,} ({inside(c) / max(1, sum(n for (s, _), n in L.items() if s in c)):.0%} of theirs)']
                   for k, c in enumerate(G)]), '']

    quarter = lambda d: f'{d[:4]}-Q{(int(d[5:7]) - 1) // 3 + 1}'
    out += ['## Groups by quarter\n', 'Each line is one group of agents who mention each other most in that quarter.\n']
    for q in sorted({quarter(r['date_pt']) for r in rows}):
        Gq = nx.Graph()
        for r in rows:
            if quarter(r['date_pt']) == q and r['date_pt'] in present[r['to']]:
                x, y = sorted((r['from'], r['to']))
                Gq.add_edge(x, y, weight=Gq.get_edge_data(x, y, {'weight': 0})['weight'] + 1)
        cs, mq = groups(Gq)
        out.append(f'- **{q}** ({Gq.size(weight="weight"):,.0f} mentions, modularity {mq:.2f}): ' +
                   ' · '.join('[' + ', '.join(name(s) for s in sorted(c, key=lambda s: -Gq.degree(s, weight='weight'))) + ']' for c in cs))
    out.append('')

    same = sum(n for (s, t), n in E.items() if maker(s) == maker(t))
    rowsm = []
    for m in sorted({maker(s) for s in made}, key=lambda m: -sum(made[s] for s in made if maker(s) == m)):
        sent = Counter()
        for (s, t), n in E.items():
            if maker(s) == m:
                sent[maker(t)] += n
        k = sum(sent.values())
        top = [(mm, n) for mm, n in sent.most_common() if mm != m][:1]
        rowsm.append([m, f'{k:,}', f'{sent[m] / k:.0%}', f'{top[0][0]} ({top[0][1] / k:.0%})' if top else '-'])
    out += ['## Makers: do agents stay within their own maker?\n',
            f'{same / total:.0%} of all mentions go to an agent from the same maker.\n',
            table(['Maker', 'Mentions made', 'To the same maker', 'Most mentioned other maker'], rowsm), '']
    rooms = Counter(r['room'] for r in rows)
    out += ['## Rooms\n', ', '.join(f'#{r} {n:,} ({n / total:.0%})' for r, n in rooms.most_common()), '']
    print('\n'.join(out))


if __name__ == '__main__':
    main()
