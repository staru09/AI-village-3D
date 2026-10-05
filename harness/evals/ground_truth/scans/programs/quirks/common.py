"""Shared read-only loader for goal 41 (11-15 May 2026 PT)."""
import re, sqlite3, random
from collections import defaultdict

LO, HI = '2026-05-11', '2026-05-16'
DAY = {'2026-05-11': 405, '2026-05-12': 406, '2026-05-13': 407, '2026-05-14': 408, '2026-05-15': 409}
AGENTS = ['Claude Opus 4.7', 'Gemini 3.1 Pro', 'GPT-5.5', 'Kimi K2.6', 'Claude Opus 4.5', 'Claude Opus 4.6',
          'Claude Haiku 4.5', 'Claude Sonnet 4.5', 'Claude Sonnet 4.6', 'GPT-5', 'GPT-5.1', 'GPT-5.2', 'GPT-5.4',
          'Gemini 2.5 Pro', 'DeepSeek-V3.2']


def con():
    c = sqlite3.connect('file:/data/AI-Village-CLI/village.db?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    return c


def ref(p, i):
    return p + ':' + i.replace('-', '')[:12]


def names(c):
    return {r['id']: r['name'] for r in c.execute('select id,name from nodes')}


def sample(xs, n=25, seed=41):
    xs = list(xs)
    return xs if len(xs) <= n else random.Random(seed).sample(xs, n)


def load(c=None):
    """{agent: {channel: [(ref, ts, text, session)]}} channels: reasoning (turns+events), chat, memory (added), intent (session goal)"""
    c = c or con(); nm = names(c)
    T = {a: defaultdict(list) for a in AGENTS}
    for r in c.execute('select id,session,agent,ts,reasoning from turns where ts>=? and ts<? and reasoning is not null and reasoning!="" order by ts', (LO, HI)):
        a = nm.get(r['agent'])
        if a in T: T[a]['reasoning'].append((ref('t', r['id']), r['ts'], r['reasoning'], r['session']))
    for r in c.execute('select id,session,agent,ts,reasoning from events where ts>=? and ts<? and reasoning is not null and reasoning!="" order by ts', (LO, HI)):
        a = nm.get(r['agent'])
        if a in T: T[a]['reasoning'].append((ref('e', r['id']), r['ts'], r['reasoning'], r['session']))
    for r in c.execute('select id,src,ts,content from messages where ts>=? and ts<? order by ts', (LO, HI)):
        a = nm.get(r['src'])
        if a in T: T[a]['chat'].append((ref('m', r['id']), r['ts'], r['content'] or '', None))
    for r in c.execute('select id,agent,ts,added from memories where ts>=? and ts<? order by ts', (LO, HI)):
        a = nm.get(r['agent'])
        if a in T and r['added']: T[a]['memory'].append((ref('k', r['id']), r['ts'], r['added'], None))
    for r in c.execute('select id,agent,ts,goal from sessions where ts>=? and ts<? order by ts', (LO, HI)):
        a = nm.get(r['agent'])
        if a in T and r['goal']: T[a]['intent'].append((ref('s', r['id']), r['ts'], r['goal'], r['id']))
    for a in T: T[a]['reasoning'].sort(key=lambda x: x[1])
    return T
