"""How did the agents' goals evolve over time? -> goals_over_time.png

Every village goal (village_goals) as a bar from its start to its end date, coloured by theme, under a small panel
with the number of agents active each day (data/index.json from extract.py).
Run: VILLAGE_DATA=/data/ai-village-tables uv run --no-project --with matplotlib python dataset-exploration/goals_over_time.py
"""
import gzip, json, os
from datetime import date, timedelta
from pathlib import Path
from statistics import median

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
TABLES = Path(os.environ.get('VILLAGE_DATA', '/data/ai-village-tables'))
INK, INK2, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#8a8984', '#e7e6e2', '#fcfcfb'
# themes in the validated categorical order (slots 1-6); free choice and holidays stay neutral grey
THEMES = {'Do good': '#2a78d6', 'Make & publish': '#eb6834', 'Compete & play': '#1baf7a',
          'Study themselves & AI': '#eda100', 'Lead & coordinate': '#e87ba4', 'Each agent its own goal': '#008300',
          'Free choice / holiday': '#b9b8b2'}
THEME = {  # goal start date -> theme, read off the 51 goal texts
    '2025-04-02': 'Do good', '2025-05-10': 'Study themselves & AI', '2025-05-12': 'Free choice / holiday',
    '2025-05-15': 'Make & publish', '2025-06-19': 'Free choice / holiday', '2025-06-26': 'Make & publish',
    '2025-07-16': 'Free choice / holiday', '2025-07-18': 'Study themselves & AI', '2025-08-13': 'Free choice / holiday',
    '2025-08-18': 'Compete & play', '2025-08-25': 'Free choice / holiday', '2025-09-01': 'Compete & play',
    '2025-09-08': 'Study themselves & AI', '2025-09-22': 'Study themselves & AI', '2025-09-29': 'Study themselves & AI',
    '2025-10-06': 'Free choice / holiday', '2025-10-13': 'Make & publish', '2025-10-20': 'Do good',
    '2025-11-03': 'Make & publish', '2025-11-17': 'Make & publish', '2025-12-01': 'Study themselves & AI',
    '2025-12-08': 'Free choice / holiday', '2025-12-15': 'Compete & play', '2025-12-22': 'Do good',
    '2025-12-29': 'Make & publish', '2026-01-05': 'Lead & coordinate', '2026-01-12': 'Compete & play',
    '2026-01-26': 'Make & publish', '2026-02-02': 'Compete & play', '2026-02-09': 'Do good',
    '2026-02-16': 'Free choice / holiday', '2026-02-23': 'Compete & play', '2026-03-02': 'Lead & coordinate',
    '2026-03-05': 'Make & publish', '2026-03-16': 'Make & publish', '2026-03-23': 'Lead & coordinate',
    '2026-03-30': 'Free choice / holiday', '2026-04-02': 'Do good', '2026-04-27': 'Make & publish',
    '2026-05-04': 'Make & publish', '2026-05-11': 'Study themselves & AI', '2026-05-18': 'Make & publish',
    '2026-05-25': 'Study themselves & AI', '2026-05-26': 'Study themselves & AI', '2026-06-01': 'Lead & coordinate',
    '2026-06-08': 'Lead & coordinate', '2026-06-15': 'Do good', '2026-06-22': 'Lead & coordinate',
    '2026-06-23': 'Compete & play', '2026-06-29': 'Compete & play', '2026-07-06': 'Each agent its own goal',
}

day = lambda ts: date.fromisoformat(ts[:10])
goals = sorted((json.loads(l) for l in gzip.open(TABLES / 'village_goals.jsonl.gz', 'rt')), key=lambda g: g['start_time'])
idx = json.loads((HERE.parent / 'data' / 'index.json').read_text())
days = [(date.fromisoformat(d['date']), len(d['agents'])) for d in idx['days']]
last = days[-1][0] + timedelta(days=1)  # the open-ended last goal runs to the latest exported day
rows = [(day(g['start_time']), day(g['end_time']) if g['end_time'] else last, g['goal'].strip(), THEME[g['start_time'][:10]]) for g in goals]
assert len(THEME) == len(rows)

fig, (top, gantt) = plt.subplots(2, 1, figsize=(13, 17.5), sharex=True, gridspec_kw={'height_ratios': [1, 9], 'hspace': 0.04, 'top': 0.955},
                                 facecolor=SURFACE)
for ax in (top, gantt):
    ax.set_facecolor(SURFACE)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis='x', color=GRID, lw=0.8)
    ax.set_axisbelow(True)

top.plot([d for d, _ in days], [n for _, n in days], color=INK2, lw=1.6, marker='o', ms=2.2)
top.set_ylim(0, 36)
top.set_yticks([0, 10, 20, 30])
top.grid(axis='y', color=GRID, lw=0.8)
top.set_title('Agents active each day', loc='left', fontsize=10, color=INK2, pad=4)

for k, (a, b, text, theme) in enumerate(rows):
    gantt.barh(k, max((b - a).days, 1.5), left=a, height=0.66, color=THEMES[theme], edgecolor=SURFACE, lw=1)
    label = f'{text if len(text) <= 78 else text[:76] + "…"}  ({(b - a).days} d)'
    if a < date(2026, 3, 1): gantt.text(b + timedelta(days=3), k, label, va='center', fontsize=8.6, color=INK)
    else: gantt.text(a - timedelta(days=3), k, label, va='center', ha='right', fontsize=8.6, color=INK)  # late rows: left of the bar
gantt.set_ylim(len(rows) - 0.4, -0.6)
gantt.set_yticks([])
gantt.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
gantt.xaxis.set_minor_locator(mdates.MonthLocator())
gantt.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
gantt.grid(axis='x', which='minor', color=GRID, lw=0.5)
gantt.set_xlim(rows[0][0] - timedelta(days=6), last + timedelta(days=12))

# the two shifts: weekly cadence from mid-Aug 2025, individual goals from 6 Jul 2026
for when, note in [(date(2025, 8, 18), 'Mid-Aug 2025: from multi-week goals\nwith holidays to one goal a week'),
                   (date(2026, 7, 6), '6 Jul 2026: no more shared goals,\neach agent maximizes its own')]:
    for ax in (top, gantt): ax.axvline(when, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=0)
    early = when.year == 2025
    top.text(when + timedelta(days=4 if early else -4), 33, note, fontsize=9, color=INK2, va='top', ha='left' if early else 'right')

gantt.legend(handles=[Patch(color=c, label=t) for t, c in THEMES.items()], loc='upper right', frameon=False, fontsize=9.5,
             labelcolor=INK, title='Theme', title_fontsize=9.5, alignment='left', bbox_to_anchor=(1.0, 0.985))
fig.suptitle('How the AI Village\'s goals evolved, Apr 2025 – Sep 2026', x=0.125, ha='left', y=0.993, fontsize=17,
             fontweight='bold', color=INK)
fig.text(0.125, 0.972, f'{len(rows)} village goals, one row each from start to end; colour = theme. Data: aidigestorg/ai-village '
         f'(export {idx["export"]}).', fontsize=10, color=INK2)
fig.savefig(HERE / 'goals_over_time.png', dpi=130, bbox_inches='tight', facecolor=SURFACE)

# the numbers behind the answer
work = [(a, (b - a).days) for a, b, _, t in rows[:-1] if t != 'Free choice / holiday']  # shared goals, holidays aside
early, late = [n for a, n in work if a < date(2025, 8, 18)], [n for a, n in work if a >= date(2025, 8, 18)]
print(f'goals {len(rows)}; median shared-goal length before mid-Aug 2025 {median(early)} d {sorted(early)}, after {median(late)} d ({len(late)} goals)')
for t in THEMES:
    rs = [r for r in rows if r[3] == t]
    print(f'{t:26} {len(rs):2} goals {sum((b - a).days for a, b, *_ in rs):4} days')
print('agents per day: first', days[0], 'max', max(days, key=lambda x: x[1]), 'last', days[-1])
