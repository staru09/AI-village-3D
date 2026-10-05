"""Shared helpers for the character questions (goal 41, 11-15 May 2026 PT). Reuses the peers name resolver."""
import sys
sys.path.insert(0, '/data/AI-Village-CLI/evals/ground_truth/round3/peers')
from core import (con, messages, sample, ref, AGENTS, ROOM, BEST, REST, SINCE, UNTIL,  # noqa: F401
                  scan, find, clean, day, SPLIT, QUOTED, HYPHENS)

DAYS = ['05-11', '05-12', '05-13', '05-14', '05-15']


def ids(c):
    return {n: i for i, n in c.execute("SELECT id, name FROM nodes") if n in AGENTS}


def sessions(c):
    """(id, agent name, ts, goal intent) for goal-41 sessions."""
    return c.execute("SELECT s.id, n.name, s.ts, s.goal FROM sessions s JOIN nodes n ON n.id=s.agent "
                     "WHERE s.ts>=? AND s.ts<? ORDER BY s.ts", (SINCE, UNTIL)).fetchall()


def mems(c):
    """(id, agent name, ts, added) memory updates written during goal 41."""
    return c.execute("SELECT m.id, n.name, m.ts, m.added FROM memories m JOIN nodes n ON n.id=m.agent "
                     "WHERE m.ts>=? AND m.ts<? ORDER BY m.ts", (SINCE, UNTIL)).fetchall()


def carried(c):
    """{agent: memory text at the end of 8 May (the last memory_days before goal 41)}."""
    return {n: t for n, t in c.execute(
        "SELECT n.name, d.content FROM memory_days d JOIN nodes n ON n.id=d.agent WHERE d.date = "
        "(SELECT max(date) FROM memory_days x WHERE x.agent=d.agent AND x.date < '2026-05-11')") if n in AGENTS}


def mem_ref(c, agent, quote):
    """The latest pre-goal memories row (k: ref) whose added text holds the quote, else None."""
    r = c.execute("SELECT m.id FROM memories m JOIN nodes n ON n.id=m.agent WHERE n.name=? AND m.ts<? "
                  "AND instr(m.added, ?) > 0 ORDER BY m.ts DESC LIMIT 1", (agent, SINCE, quote)).fetchone()
    return r and ref('k', r[0])
