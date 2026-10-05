"""Shared helpers for the deception programs: read-only DB, goal-41 window, the 15 agents, refs, seeded samples."""
import random, sqlite3, sys
sys.path.insert(0, '/data/AI-Village-CLI')
from village_graph.core import ref  # noqa: E402

T0, T1 = '2026-05-11', '2026-05-16'
AGENTS = ['Claude Opus 4.7', 'Gemini 3.1 Pro', 'GPT-5.5', 'Kimi K2.6', 'Claude Opus 4.5', 'Claude Opus 4.6', 'Claude Haiku 4.5',
          'Claude Sonnet 4.5', 'Claude Sonnet 4.6', 'GPT-5', 'GPT-5.1', 'GPT-5.2', 'GPT-5.4', 'Gemini 2.5 Pro', 'DeepSeek-V3.2']


def connect():
    con = sqlite3.connect('file:/data/AI-Village-CLI/village.db?mode=ro', uri=True)
    con.execute("ATTACH 'file:/data/AI-Village-CLI/labels.db?mode=ro' AS L")
    return con


def names(con):
    return {i: n for i, n in con.execute('select id, name from nodes') if n in AGENTS}


def sample(rows, n=25, seed=41):
    rows = list(rows)
    return rows if len(rows) <= n else random.Random(seed).sample(rows, n)


def coverage(con):
    """Per agent: (actions, actions with reasoning, chat msgs, chat with reasoning) in the window."""
    nm = names(con)
    out = {a: [0, 0, 0, 0] for a in AGENTS}
    for ag, n, r in con.execute("select agent, count(*), sum(reasoning is not null and reasoning!='') from turns where ts>=? and ts<? group by agent", (T0, T1)):
        if ag in nm: out[nm[ag]][0:2] = [n, r]
    for ag, n, r in con.execute("select src, count(*), sum(reasoning is not null and reasoning!='') from messages where ts>=? and ts<? group by src", (T0, T1)):
        if ag in nm: out[nm[ag]][2:4] = [n, r]
    return out
