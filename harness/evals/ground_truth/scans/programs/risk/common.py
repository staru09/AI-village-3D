"""Shared helpers for the risk programs: read-only DB, goal-41 window, agents, bash turns, heredoc stripping, seeded samples."""
import random, re, sqlite3, sys
sys.path.insert(0, '/data/AI-Village-CLI')
from village_graph.core import ref  # noqa: E402,F401

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


HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def shell_lines(action):
    """Command text outside heredoc bodies, comment-only lines dropped (heredoc opener lines kept)."""
    out, delim = [], None
    for line in (action or '').split('\n'):
        if delim is not None:
            if line.strip() == delim:
                delim = None
            continue
        if line.strip().startswith('#'):
            continue
        out.append(line)
        m = HEREDOC.search(line)
        if m:
            delim = m.group(2)
    return '\n'.join(out)


def bash_turns(con):
    """All goal-41 bash actions of the 15 agents, in time order, as dicts with sl = shell lines."""
    nm = names(con)
    rows = []
    for i, ag, ts, sess, act, out, err, failed, rsn in con.execute(
            "select id, agent, ts, session, action, output, error, failed, reasoning from turns "
            "where kind='bash' and ts>=? and ts<? order by ts", (T0, T1)):
        if ag not in nm:
            continue
        rows.append(dict(id=i, ref=ref('t', i), agent=nm[ag], ts=ts, session=sess, action=act or '', output=out or '',
                         error=err or '', failed=failed, reasoning=rsn or '', sl=shell_lines(act)))
    return rows
