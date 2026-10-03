"""Export one village goal as a folder thimble can analyse: python3 thimble/export.py [goal words] -> thimble/<slug>/

    corpus/  README.md, chat.jsonl, sessions.jsonl, actions.jsonl, memory/<agent>.md   (what thimble reads)
    reference/  AI Digest's goal stories and daily recaps for those days                (kept out, to check against)

Chat, sessions and memory come from frontend/data (extract.py's output); every computer action, with its full reasoning
and error, comes from the raw computer_use_turns table. Both folders quote the gated dataset: git-ignored.
"""
import gzip, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from extract import pt, recent, slugify, snapshot, thought, untag  # noqa: E402

DATA = ROOT / 'frontend' / 'data'


def hms(s):
    return f'{s // 3600:02}:{s % 3600 // 60:02}:{s % 60:02}'


def main():
    words = ' '.join(sys.argv[1:]) or 'Complete as many games as you can in a week'
    ix = json.loads((DATA / 'index.json').read_text())
    days = [d for d in ix['days'] if words.lower() in d['goal'].lower()]
    if not days:
        sys.exit(f'no village goal contains "{words}"')
    goal, dates = days[0]['goal'], [d['date'] for d in days]
    out = Path(__file__).resolve().parent / slugify(goal)
    (out / 'corpus' / 'memory').mkdir(parents=True, exist_ok=True)
    (out / 'reference').mkdir(exist_ok=True)
    names, chat, sessions, memory = {}, [], [], {}
    for d in days:
        D = json.loads((DATA / 'days' / f"{d['date']}.json").read_text())
        at = lambda v: hms(D['open'] * 3600 + v)
        for a in D['agents']:
            names[a['slug']] = a['name']
        idx = [a['name'] for a in D['agents']]
        chat += [{'date': d['date'], 'time_pt': at(v), 'speaker': idx[i], 'speaker_type': 'agent', 'text': text,
                  'mentions': [idx[j] for j in to], 'room': D['rooms'][r]} for v, i, text, to, r in D['messages']]
        chat += [{'date': d['date'], 'time_pt': at(v), 'speaker': who, 'speaker_type': 'human', 'text': text,
                  'mentions': [idx[j] for j in to], 'room': D['rooms'][r]} for v, who, text, to, r in D['human']]
        for a in D['agents']:
            n = json.loads((DATA / 'days' / d['date'] / f"{a['slug']}.json").read_text())
            reports = sorted(n.get('reports', []))
            for k, (v, short, long_goal) in enumerate(a['intents']):  # a session's report: the first one after it started
                end = a['intents'][k + 1][0] if k + 1 < len(a['intents']) else float('inf')
                rep = next((r for r in reports if v <= r[0] < end), None)
                sessions.append({'agent': a['name'], 'date': d['date'], 'start_pt': at(v), 'short_goal': short, 'goal': long_goal,
                                 'end_pt': at(rep[0]) if rep else None, 'report': rep[1] if rep else None})
            if (m := n.get('memory')) and m.get('text'):
                memory.setdefault(a['name'], []).append((d['date'], m['written'], m['text']))
    chat.sort(key=lambda x: (x['date'], x['time_pt']))

    snap = snapshot()  # every action of these agents on these days, with its whole reasoning
    agent_ids = {r['id']: r['name'] for r in map(json.loads, gzip.open(snap / 'agents.jsonl.gz')) if r['name'] in names.values()}
    sess = {r['id']: agent_ids[r['agent_id']] for r in map(json.loads, gzip.open(snap / 'computer_use_sessions.jsonl.gz'))
            if r['agent_id'] in agent_ids}
    actions = []
    for t in recent(snap, 'computer_use_turns.jsonl.gz', dates[0]):
        if t['session_id'] not in sess or (when := pt(t['created_at']))[0] not in dates:
            continue
        a = t['agent_action'] or {}
        actions.append({'agent': sess[t['session_id']], 'date': when[0], 'time_pt': hms(when[1]), 'session': t['session_id'][:8],
                        'action': a.get('action') or ('bash' if 'command' in a else None),
                        **{k: v for k, v in a.items() if k != 'action' and v not in (None, '', [], False)},
                        'reasoning': thought(t['agent_messages'], None) or None, 'error': (t['error'] or '').strip() or None,
                        'output': (t['output'] or '').strip()[:2000] or None})
    actions.sort(key=lambda x: (x['date'], x['time_pt']))

    write = lambda name, rows: (out / 'corpus' / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    write('chat.jsonl', chat)
    write('sessions.jsonl', sessions)
    write('actions.jsonl', actions)
    for name, versions in memory.items():
        (out / 'corpus' / 'memory' / f'{slugify(name)}.md').write_text(
            f'# {name}: its own memory at the end of each day\n\n' + '\n\n'.join(f'## {d} (written {w} PT)\n\n{text}' for d, w, text in versions))
    (out / 'corpus' / 'README.md').write_text(f"""# AI Village: "{goal.strip()}"

The [AI Village](https://theaidigest.org/village) runs frontier AI agents in a shared group chat, each with its own
computer (a Linux desktop it controls through screenshots, clicks and key presses), pursuing goals set by the AI Digest
team. This folder is one goal: {dates[0]} to {dates[-1]} (Days {days[0]['day']}–{days[-1]['day']}), village hours
about 10:00–14:00 Pacific time, {len(names)} agents: {', '.join(names.values())}. All times are Pacific (PT).

| File | One record per | Fields |
|---|---|---|
| `chat.jsonl` ({len(chat):,}) | chat message (agents and the humans of AI Digest; texts cut at 1,500 characters) | date, time_pt, speaker, speaker_type, text, mentions, room |
| `sessions.jsonl` ({len(sessions):,}) | computer session: what the agent set out to do, and the report it wrote when the session ended | agent, date, start_pt, short_goal, goal, end_pt, report |
| `actions.jsonl` ({len(actions):,}) | computer action (click, key, scroll, type, screenshot, chat send…) | agent, date, time_pt, session, action, coordinate / text / key…, reasoning (the model's own, when it gave one), error, output |
| `memory/<agent>.md` | the agent's own notes as of the end of each day (it rewrites them many times a day) | |

Screenshots are not in the dataset. A turn's `error` is what the tool reported; `reasoning` is present on {sum(bool(a['reasoning']) for a in actions):,} actions.
""")
    S = sorted(map(json.loads, gzip.open(snap / 'summaries.jsonl.gz')), key=lambda r: r['created_at'])
    nums = {d['day'] for d in days}
    for r in S:
        t = r['summary_target'] or ''
        rng = re.fullmatch(r'(\d+)-(\d+)', t)
        if r['type'] == 'daily' and r['summary_date'] in dates:
            (out / 'reference' / f"daily-{r['summary_date']}.md").write_text(untag(r['content']))  # latest version wins
        elif r['type'] in ('goal', 'goal-checkpoint') and (rng and nums & set(range(int(rng[1]), int(rng[2]) + 1)) or
                                                           (w := set(re.findall(r'[a-z]+', t))) and w <= set(re.findall(r'[a-z]+', goal.lower()))):
            (out / 'reference' / f"{r['type']}-{t}-{r['created_at'][:10]}.md").write_text(untag(r['content']))
    print(f'{out}: {len(chat):,} chat, {len(sessions):,} sessions, {len(actions):,} actions, memory of {len(memory)} agents; '
          f"reference: {', '.join(sorted(p.name for p in (out / 'reference').iterdir()))}")


if __name__ == '__main__':
    main()
