"""Shared helpers for the calling-out questions (goal 41, 11-15 May 2026 PT)."""
import random, re, sqlite3, sys
from functools import lru_cache

sys.path.insert(0, '/data/AI-Village-CLI')
from village_graph.core import ref  # noqa: E402

SINCE, UNTIL = '2026-05-11', '2026-05-16'
BEST = ['Claude Opus 4.7', 'Gemini 3.1 Pro', 'GPT-5.5', 'Kimi K2.6']
REST = ['Claude Opus 4.5', 'Claude Opus 4.6', 'Claude Haiku 4.5', 'Claude Sonnet 4.5', 'Claude Sonnet 4.6', 'GPT-5',
        'GPT-5.1', 'GPT-5.2', 'GPT-5.4', 'Gemini 2.5 Pro', 'DeepSeek-V3.2']
AGENTS = BEST + REST
ROOM = {a: 'best' for a in BEST} | {a: 'rest' for a in REST}
HOME = {'Gemini 3.1 Pro': 'best', 'Gemini 2.5 Pro': 'rest'}
HYPHENS = str.maketrans({'‐': '-', '‑': '-', '–': '-', '’': "'"})


def con():
    c = sqlite3.connect('file:/data/AI-Village-CLI/village.db?mode=ro', uri=True)
    c.execute("ATTACH 'file:/data/AI-Village-CLI/labels.db?mode=ro' AS L")
    return c


@lru_cache(None)
def name_rx(name, room=None):
    """Full name plus unambiguous short forms (copied from m4's peer_matrix.py): "Opus 4.5", "Kimi", "DeepSeek",
    "Gemini 3.1", "Haiku"; bare "Gemini" = the Gemini of the message's room, bare "Claude" in #best = Opus 4.7. Bare "Claude"/"Opus"/"GPT" are not matched."""
    forms = {name}
    if room and HOME.get(name) == room:
        forms.add('Gemini')
    if name.startswith('Claude '):
        forms.add(name[len('Claude '):])
    if name.startswith('Gemini '):
        forms.add(name.rsplit(' ', 1)[0])
    if name == 'Claude Haiku 4.5':  # the only Haiku
        forms.add('Haiku')
    if name in ('Kimi K2.6', 'DeepSeek-V3.2'):
        forms.add(re.split(r'[ -]', name)[0])
    if name == 'Claude Opus 4.7' and room == 'best':  # the only Claude in #best
        forms.add('Claude')
    alt = '|'.join(re.escape(f) for f in sorted(forms, key=len, reverse=True))
    return re.compile(rf'(?<![\w./-])(?<!\| )(?<!\| Claude )({alt})(?![\w-]|\.\d)', re.I)


def named(text, speaker, room):
    """Room-mates named in the text (not the speaker)."""
    t = text.translate(HYPHENS)
    return [a for a in AGENTS if a != speaker and ROOM[a] == room and name_rx(a, room).search(t)]


def messages(c):
    """All agent chat messages of goal 41: (id, speaker, room, ts, content, reasoning)."""
    return c.execute(
        "SELECT m.id, n.name, m.room, m.ts, m.content, m.reasoning FROM messages m JOIN nodes n ON n.id = m.src "
        "WHERE m.ts >= ? AND m.ts < ? AND m.room IN ('best','rest') AND m.src != 'human' ORDER BY m.ts",
        (SINCE, UNTIL)).fetchall()


def sample(rows, n=25, seed=41):
    return rows if len(rows) <= n else random.Random(seed).sample(rows, n)


def mins(a, b):
    from datetime import datetime
    f = lambda s: datetime.fromisoformat(s[:26])
    return round((f(b) - f(a)).total_seconds() / 60, 1)


def get(c, r):
    """A ref -> (ts, agent name, text). m: chat content, t: action (+output), k: memory added, e: event text."""
    kind, h = r.split(':')
    q = {'m': "SELECT x.ts, n.name, x.content FROM messages x JOIN nodes n ON n.id=x.src",
         't': "SELECT x.ts, n.name, x.action || char(10) || coalesce(x.output,'') FROM turns x JOIN nodes n ON n.id=x.agent",
         'k': "SELECT x.ts, n.name, x.added FROM memories x JOIN nodes n ON n.id=x.agent",
         'e': "SELECT x.ts, n.name, x.text FROM events x JOIN nodes n ON n.id=x.agent"}[kind]
    lo = f'{h[:8]}-{h[8:12]}'
    return c.execute(q + " WHERE x.id >= ? AND x.id < ? LIMIT 1", (lo, lo + 'g')).fetchone()
