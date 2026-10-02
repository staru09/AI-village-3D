"""How much is each agent involved in the village, and where do human messages come in?
-> agent_involvement.png, human_messages.png

Agents: days present, computer actions and chat messages per agent, from the built day files (data/, extract.py).
Humans: USER_TALK events (chat messages by people, with their names) and the requests agents make to humans.
Run: VILLAGE_DATA=/data/ai-village-tables uv run --no-project --with matplotlib python dataset-exploration/agents_and_humans.py
"""
import gzip, json, os
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
DATA, TABLES = HERE.parent / 'data', Path(os.environ.get('VILLAGE_DATA', '/data/ai-village-tables'))
INK, INK2, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#8a8984', '#e7e6e2', '#fcfcfb'
SLOTS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']  # validated order
CLAN = dict(zip(['Google', 'Anthropic', 'OpenAI', 'Zhipu', 'Moonshot', 'xAI', 'DeepSeek', 'Meta'], SLOTS))  # as in the village
CLOSED = date(2025, 9, 1)  # the public chat had closed by then; later human senders are the AI Digest team


def style(ax, grid='x'):
    ax.set_facecolor(SURFACE)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis=grid, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


# ---------- agents ----------
ix = json.loads((DATA / 'index.json').read_text())
present, turns, msgs = defaultdict(list), Counter(), Counter()
for d in ix['days']:
    for a in json.loads((DATA / 'days' / f'{d["date"]}.json').read_text())['agents']:
        present[a['slug']].append(date.fromisoformat(d['date']))
        turns[a['slug']] += a['stats'].get('turns', 0)
        msgs[a['slug']] += a['stats'].get('messages', 0)
A = ix['agents']
order = sorted(present, key=lambda s: (present[s][0], A[s]['name']))  # by join date, earliest on top
end = date.fromisoformat(ix['days'][-1]['date'])

fig = plt.figure(figsize=(16, 15), facecolor=SURFACE)
gs = fig.add_gridspec(1, 4, width_ratios=[5, 1.3, 1.3, 1.3], wspace=0.09, top=0.9)
lane = fig.add_subplot(gs[0])
bars = [fig.add_subplot(gs[k], sharey=lane) for k in (1, 2, 3)]
for k, s in enumerate(order):
    c = CLAN[A[s]['clan']]
    lane.plot([present[s][0], present[s][-1]], [k, k], color=GRID, lw=5, solid_capstyle='round', zorder=1)  # tenure
    lane.scatter(present[s], [k] * len(present[s]), marker='|', s=46, color=c, lw=1.3, zorder=2)  # each day present
style(lane)
lane.set_yticks(range(len(order)), [f'{A[s]["name"]}' for s in order], fontsize=9, color=INK)
lane.set_ylim(len(order) - 0.4, -0.6)
lane.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
lane.set_xlim(date(2025, 3, 20), end + timedelta(days=8))  # ends before Oct 2026: its label ran into the next panel
lane.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
lane.set_title('Days in the village (one tick per day, grey = first to last day)', loc='left', fontsize=10, color=INK2)
for ax, (title, val, fmt) in zip(bars, [('Days present', lambda s: len(present[s]), '{:,}'),
                                         ('Computer actions', lambda s: turns[s], '{:,.0f}'),
                                         ('Chat messages', lambda s: msgs[s], '{:,}')]):
    vs = [val(s) for s in order]
    ax.barh(range(len(order)), vs, height=0.68, color=[CLAN[A[s]['clan']] for s in order], edgecolor=SURFACE, lw=1)
    for k in sorted(range(len(vs)), key=lambda i: -vs[i])[:3]:  # label the top three only
        ax.text(vs[k], k, ' ' + fmt.format(vs[k]), va='center', fontsize=8, color=INK)
    style(ax)
    ax.tick_params(labelleft=False)
    ax.set_xlim(0, max(vs) * 1.32)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x / 1000:.0f}k' if x >= 1000 else f'{x:.0f}'))
    ax.set_title(title, loc='left', fontsize=10, color=INK2)
present_clans = [c for c in CLAN if any(A[s]['clan'] == c for s in order)]
fig.legend(handles=[Patch(color=CLAN[c], label=c) for c in present_clans], loc='upper left', ncol=len(present_clans),
           frameon=False, fontsize=9.5, bbox_to_anchor=(0.125, 0.935), handlelength=1.2, columnspacing=1.4)
fig.suptitle('How involved is each agent? 46 agents, Apr 2025 – Sep 2026', x=0.125, ha='left', y=0.985, fontsize=17,
             fontweight='bold', color=INK)
fig.text(0.125, 0.958, 'Sorted by first day in the village; colour = model maker. Actions = computer and tool actions; '
         f'data: aidigestorg/ai-village (export {ix["export"]}).', fontsize=10, color=INK2)
fig.savefig(HERE / 'agent_involvement.png', dpi=120, bbox_inches='tight', facecolor=SURFACE)

tot_t, tot_m = sum(turns.values()), sum(msgs.values())
top5 = sum(v for _, v in turns.most_common(5))
print(f'agents {len(order)}; actions {tot_t:,} (top 5 agents {top5 / tot_t:.0%}); messages {tot_m:,}')
for name, f in [('days', lambda s: len(present[s])), ('actions', lambda s: turns[s]), ('messages', lambda s: msgs[s])]:
    print(f'top {name}:', [(A[s]['name'], f(s)) for s in sorted(order, key=f, reverse=True)[:5]])
print('still there on the last day:', sum(present[s][-1] == end for s in order), '| left:',
      [(A[s]['name'], present[s][-1].isoformat()) for s in order if present[s][-1] < end - timedelta(days=30)][:12])

# ---------- humans ----------
week = lambda ts: (d := date.fromisoformat(ts[:10])) - timedelta(days=d.weekday())
talk, asks, last = [], [], {}
with gzip.open(TABLES / 'events.jsonl.gz', 'rt') as f:
    for line in f:
        e = json.loads(line)
        kind = e['data'].get('actionType')
        if kind == 'USER_TALK':
            s, c = e['data'].get('speakerName'), e['data'].get('content') or ''
            talk.append((e['created_at'], s, c))
            last[s] = max(last.get(s, ''), e['created_at'])
        elif kind in ('REQUEST_HUMAN_HELPER', 'REQUEST_GOOGLE_SIGN_IN', 'OUTREACH_APPROVAL_REQUEST'):
            asks.append((e['created_at'], kind))
team = {s for s, t in last.items() if t >= CLOSED.isoformat() and s != 'automated'}
def who(s, c):
    if s == 'automated': return 'Automated: daily pause/resume' if 'the village for today' in c else 'Automated: nudges to idle agents'
    return 'AI Digest team' if s in team else 'Public viewers'
KINDS = ['Public viewers', 'AI Digest team', 'Automated: daily pause/resume', 'Automated: nudges to idle agents']
ASKS = {'REQUEST_HUMAN_HELPER': 'Asked for a human helper', 'REQUEST_GOOGLE_SIGN_IN': 'Asked for a Google sign-in',
        'OUTREACH_APPROVAL_REQUEST': 'Asked approval to contact someone'}
hw, aw, agent_w = defaultdict(Counter), defaultdict(Counter), Counter()
for t, s, c in talk: hw[week(t)][who(s, c)] += 1
for t, k in asks: aw[week(t)][ASKS[k]] += 1
for l in gzip.open(TABLES / 'chat_messages.jsonl.gz', 'rt'):
    m = json.loads(l)
    if m['speaker_type'] == 'agent': agent_w[week(m['created_at'])] += 1
weeks = sorted(set(hw) | set(agent_w))

fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(14, 11), sharex=True, facecolor=SURFACE,
                                 gridspec_kw={'height_ratios': [3, 1.6, 2], 'hspace': 0.28, 'top': 0.88})
def stack(ax, series, counts, colors, where='upper right'):
    base = [0] * len(weeks)
    for name, c in zip(series, colors):
        v = [counts[w][name] for w in weeks]
        ax.bar(weeks, v, bottom=base, width=6, color=c, edgecolor=SURFACE, lw=0.6, label=name)
        base = [b + x for b, x in zip(base, v)]
    ax.legend(loc=where, frameon=False, fontsize=9, labelcolor=INK)
stack(a1, KINDS, hw, SLOTS[:4])
a1.set_title('Human messages in the chat, per week', loc='left', fontsize=11, color=INK)
share = [100 * sum(hw[w].values()) / ((sum(hw[w].values()) + agent_w[w]) or 1) for w in weeks]
a2.plot(weeks, share, color=INK2, lw=1.8)
a2.set_ylim(0, 100)
a2.set_title('Share of all chat messages written by humans (%)', loc='left', fontsize=11, color=INK)
stack(a3, list(ASKS.values()), aw, SLOTS[4:7], 'upper left')  # the Jul 2026 peak sits top right
a3.set_title('Times agents asked humans for something, per week', loc='left', fontsize=11, color=INK)
for ax in (a1, a2, a3):
    style(ax, 'y')
    ax.axvline(CLOSED - timedelta(days=17), color=MUTED, lw=1, ls=(0, (3, 3)))
a1.text(CLOSED - timedelta(days=12), a1.get_ylim()[1] * 0.92, 'Mid-Aug 2025: chat closed to the public;\nonly the team '
        'and the system post after this', fontsize=9, color=INK2, va='top')
a3.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
a3.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
fig.suptitle('Where do humans come into the village?', x=0.125, ha='left', y=0.975, fontsize=17, fontweight='bold', color=INK)
fig.text(0.125, 0.935, f'{len(talk):,} human messages from {len(last)} names: {len(last) - len(team) - 1} public viewers, '
         f'the AI Digest team ({", ".join(sorted(team))}) and an automated system account.', fontsize=10, color=INK2)
fig.savefig(HERE / 'human_messages.png', dpi=120, bbox_inches='tight', facecolor=SURFACE)

kc = Counter(who(s, c) for _, s, c in talk)
print('human messages by kind:', kc.most_common())
print('share of all chat by humans:', f'{len(talk) / (len(talk) + sum(agent_w.values())):.1%}',
      '| before close', f'{sum(sum(hw[w].values()) for w in weeks if w < CLOSED) / max(1, sum(sum(hw[w].values()) + agent_w[w] for w in weeks if w < CLOSED)):.1%}',
      '| after', f'{sum(sum(hw[w].values()) for w in weeks if w >= CLOSED) / sum(sum(hw[w].values()) + agent_w[w] for w in weeks if w >= CLOSED):.1%}')
print('asks:', Counter(k for _, k in asks), '| team names:', sorted(team))
