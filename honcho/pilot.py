# /// script
# requires-python = ">=3.11"
# dependencies = ["honcho-ai==2.5.1"]
# ///
"""Feed one village agent's days into a local Honcho, one day per step, and snapshot what Honcho knows after each.

    honcho/up.sh                                          # once: start Honcho on 127.0.0.1:8000
    uv run honcho/pilot.py --agent glm-5-3-flash          # import the next day not imported yet
    uv run honcho/pilot.py --agent glm-5-3-flash --days 5 # the next five

Reads frontend/data (built by extract.py): that day's chat (every speaker, for context), human messages, and the agent's
own session goals, commands with what they printed, failures, pauses, room moves, reasoning excerpts, reports, requests
and the changes to its own notes. Only the agent is observed (observe_me), so Honcho's deriver reasons about it alone.

After each day: wait for the queue, run a dream (consolidation), wait again, then write honcho/out/<agent>/<date>.json
with its peer card, representation and answers to QUESTIONS. Honcho can't be asked about an earlier date later, so the
snapshot is the as-of-that-day record. A day with a snapshot counts as imported: wiping Honcho means deleting out/ too.
"""
import argparse, json, re, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'frontend' / 'data'
PT = ZoneInfo('America/Los_Angeles')
MAX = 24000  # Honcho's MAX_MESSAGE_SIZE is 25,000 characters
# Honcho summarises a session every 20 messages (short) and 60 (long) by default, one after another, ~7 s each:
# the slowest part of a day. Less often is enough for one day's recap (short must be < long; long >= 20).
SUMMARY = {'messages_per_short_summary': 60, 'messages_per_long_summary': 300}
QUESTIONS = [
    'What is {name} working on right now, and why?',
    'What has {name} learned or changed its mind about so far?',
    'Which agents or humans does {name} work with most, and how?',
    'What does {name} struggle with or keep getting wrong?',
    "How would you describe {name}'s personality and working style?",
]


def when(date, open_h, v):
    """Village time (seconds since the day's window opened at open_h PT) -> UTC datetime."""
    return (datetime.fromisoformat(date).replace(tzinfo=PT) + timedelta(hours=open_h, seconds=v)).astimezone(timezone.utc)


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'someone'


def pieces(text):
    """Text -> parts that fit in one Honcho message."""
    return [text[i:i + MAX] for i in range(0, len(text), MAX)] or ['']


def notes_change(before, after):
    """Yesterday's and today's notes -> one line saying what changed ('' = no change)."""
    if not after or after == before:
        return ''
    if not before:
        return f'[its own notes]\n{after}'
    old, new = set(before.splitlines()), set(after.splitlines())
    added = [l for l in after.splitlines() if l not in old and l.strip()]
    dropped = [l for l in before.splitlines() if l not in new and l.strip()]
    return '\n'.join(filter(None, ['[added to its notes]\n' + '\n'.join(added) if added else '',
                                   '[dropped from its notes]\n' + '\n'.join(dropped) if dropped else '']))


def day_items(date, me, previous_notes):
    """One village day -> ([(utc time, speaker slug, text, metadata)] in time order, today's notes)."""
    d = json.loads((DATA / 'days' / f'{date}.json').read_text())
    n = json.loads((DATA / 'days' / date / f'{me}.json').read_text())
    agents, rooms, o = d['agents'], d['rooms'], d['open']
    a = next(x for x in agents if x['slug'] == me)
    room = (lambda r: f'[#{rooms[r]}] ') if len(rooms) > 1 else (lambda r: '')
    items = [(v, agents[i]['slug'], room(r) + text, {'kind': 'chat', 'room': rooms[r]}) for v, i, text, _, r in d['messages']]
    items += [(v, f'human-{slug(who)}', room(r) + text, {'kind': 'human', 'room': rooms[r]}) for v, who, text, _, r in d['human']]
    items += [(v, me, f'{icon} {text}', {'kind': 'request'}) for v, i, icon, text, _ in d['asks'] if agents[i]['slug'] == me]
    mine = [(v, f'[started a computer session] {goal or short}', 'session') for v, short, goal in a['intents']]
    mine += [(int(k) * d['slice'], f"[ran a command] {line}\n[it printed] {n.get('replies', {}).get(k) or '(nothing)'}", 'command')
             for k, line in a['bash'].items()]
    mine += [(v, f'[an action failed] {text}', 'failure') for v, text in n.get('errors', [])]
    mine += [(v, f'[paused for {s // 60} min]', 'pause') for v, s in a['pauses']]
    mine += [(v, f'[moved to #{rooms[r]}]', 'room') for v, r in a['enter']]
    mine += [(v, f'[thought] {text}', 'thought') for v, text in n.get('thinking', [])]
    mine += [(v, f'[ended a computer session; its report] {text}' + (f'\n[its last thought] {last}' if last else ''), 'report')
             for v, text, last, *_ in n.get('reports', [])]
    notes = (n.get('memory') or {}).get('text') or ''
    if change := notes_change(previous_notes, notes):
        at = datetime.fromisoformat(n['memory']['written']).replace(tzinfo=PT).astimezone(timezone.utc)
        mine.append(((at - when(date, o, 0)).total_seconds(), change, 'notes'))
    items += [(v, me, text, {'kind': kind}) for v, text, kind in mine]
    items.sort(key=lambda x: x[0])
    return [(when(date, o, v), who, part, meta) for v, who, text, meta in items for part in pieces(text)], notes


def main():
    from honcho import Honcho
    from honcho.api_types import PeerConfig

    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--agent', default='glm-5-3-flash', help='agent slug, as in frontend/data/index.json')
    ap.add_argument('--days', type=int, default=1, help='how many not-yet-imported days to import now')
    args = ap.parse_args()
    ix = json.loads((DATA / 'index.json').read_text())
    if args.agent not in ix['agents']:
        sys.exit(f"unknown agent {args.agent}; one of: {', '.join(ix['agents'])}")
    name = ix['agents'][args.agent]['name']
    days = [(x['date'], x['day']) for x in ix['days'] if args.agent in x['agents']]
    out = HERE / 'out' / args.agent
    out.mkdir(parents=True, exist_ok=True)
    todo = [(d, n) for d, n in days if not (out / f'{d}.json').exists()][:args.days]
    if not todo:
        return print(f'{name}: all {len(days)} days imported')

    honcho = Honcho(base_url='http://127.0.0.1:8000', workspace_id=f'village-{args.agent}')
    me = honcho.peer(args.agent, metadata={'name': name})
    peers = {args.agent: me}

    def wait(what):  # until the deriver has nothing pending or running
        t = time.time()
        while (q := honcho.queue_status()).pending_work_units or q.in_progress_work_units:
            print(f'  {what}: {q.completed_work_units}/{q.total_work_units} done', end='\r', flush=True)
            time.sleep(3)
        print(f'  {what}: done in {time.time() - t:.0f}s' + ' ' * 20)

    for date, num in todo:
        before = [p for p in sorted(out.glob('*.json')) if p.stem < date]
        notes_before = json.loads(before[-1].read_text())['own_notes'] if before else ''
        items, notes = day_items(date, args.agent, notes_before)
        print(f'{name} · {date} (Day {num}): {len(items)} messages, {sum(w == args.agent for _, w, _, _ in items)} by the agent')
        session = honcho.session(f'day-{date}', metadata={'date': date, 'day': num}, configuration={'summary': SUMMARY})
        for who in {w for _, w, _, _ in items} - peers.keys():  # everyone else: context only, not observed
            peers[who] = honcho.peer(who, configuration=PeerConfig(observe_me=False))
        msgs = [peers[w].message(text, metadata=meta, created_at=t) for t, w, text, meta in items]
        for i in range(0, len(msgs), 100):  # add_messages takes at most 100
            session.add_messages(msgs[i:i + 100])
        time.sleep(2)  # let the API enqueue before the first status check
        wait('deriver')
        honcho.schedule_dream(observer=me)
        time.sleep(2)
        wait('dream')
        snap = {'agent': args.agent, 'name': name, 'date': date, 'day': num, 'messages': len(items),
                'card': me.get_card(), 'representation': me.representation(max_conclusions=100),
                'answers': {q.format(name=name): str(me.chat(q.format(name=name), reasoning_level='low')) for q in QUESTIONS},
                'own_notes': notes}
        (out / f'{date}.json').write_text(json.dumps(snap, ensure_ascii=False, indent=1, default=str))
        print(f'  saved {out.relative_to(HERE.parent)}/{date}.json: card of {len(snap["card"] or [])} lines')


if __name__ == '__main__':
    main()
