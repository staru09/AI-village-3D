"""Shared loaders for the leadership questions (goal 41, 11-15 May 2026 PT, rooms #best and #rest)."""
import re, sqlite3, sys, random
sys.path.insert(0, '/data/AI-Village-CLI')
from village_graph.core import ref  # noqa: E402

LO, HI = '2026-05-11', '2026-05-16'
BEST = ['Claude Opus 4.7', 'Gemini 3.1 Pro', 'GPT-5.5', 'Kimi K2.6']
REST = ['Claude Opus 4.5', 'Claude Opus 4.6', 'Claude Haiku 4.5', 'Claude Sonnet 4.5', 'Claude Sonnet 4.6', 'GPT-5',
        'GPT-5.1', 'GPT-5.2', 'GPT-5.4', 'Gemini 2.5 Pro', 'DeepSeek-V3.2']
ROOM = {a: 'best' for a in BEST} | {a: 'rest' for a in REST}

# Aliases valid anywhere (unambiguous) and per room (short names that only make sense inside that room).
ALIAS = {
    'Claude Opus 4.7': r'(?:Claude )?Opus[ -]?4\.7', 'Gemini 3.1 Pro': r'Gemini[ -]?3\.1(?: Pro)?', 'GPT-5.5': r'GPT[-‑ ]?5\.5',
    'Kimi K2.6': r'Kimi(?: K2\.6)?', 'Claude Opus 4.5': r'(?:Claude )?Opus[ -]?4\.5', 'Claude Opus 4.6': r'(?:Claude )?Opus[ -]?4\.6',
    'Claude Haiku 4.5': r'(?:Claude )?Haiku(?: 4\.5)?', 'Claude Sonnet 4.5': r'(?:Claude )?Sonnet[ -]?4\.5',
    'Claude Sonnet 4.6': r'(?:Claude )?Sonnet[ -]?4\.6', 'GPT-5': r'GPT[-‑ ]?5(?![.\d‑-])', 'GPT-5.1': r'GPT[-‑ ]?5\.1',
    'GPT-5.2': r'GPT[-‑ ]?5\.2', 'GPT-5.4': r'GPT[-‑ ]?5\.4', 'Gemini 2.5 Pro': r'Gemini[ -]?2\.5(?: Pro)?',
    'DeepSeek-V3.2': r'DeepSeek(?:[ -]?V3\.2)?',
}
ROOM_ALIAS = {'best': {'Claude Opus 4.7': r'Claude(?! (?:Opus|Haiku|Sonnet) 4\.[56])|Opus(?! ?4\.[56])', 'Gemini 3.1 Pro': r'Gemini(?! ?2\.5)'},
              'rest': {'Gemini 2.5 Pro': r'Gemini(?! ?3\.1)'}}


def con():
    c = sqlite3.connect('file:/data/AI-Village-CLI/village.db?mode=ro', uri=True)
    c.execute("ATTACH 'file:/data/AI-Village-CLI/labels.db?mode=ro' AS L")
    return c


def names(c):
    return dict(c.execute('select id,name from nodes'))


def messages(c):
    """All agent chat in #best/#rest in scope, time order: dicts id, ref, src(name), room, ts, day, content."""
    nm = names(c)
    out = []
    for i, s, r, ts, txt in c.execute("select id,src,room,ts,content from messages where room in ('best','rest') "
                                       "and ts>=? and ts<? order by ts", (LO, HI)):
        out.append(dict(id=i, ref=ref('m', i), src=nm.get(s, s), room=r, ts=ts, day=ts[:10], content=txt or ''))
    return out


def alias_re(agent, room):
    pats = [ALIAS[agent]] + ([ROOM_ALIAS[room][agent]] if agent in ROOM_ALIAS.get(room, {}) else [])
    return '(?:' + '|'.join(pats) + ')'


def addressees(c, m, _cache={}):
    """Room members the message is addressed to: @-mention edges, plus short names in address position
    (after '@', or at line start followed by ':' ',' or a dash, or 'Name, please/can you')."""
    if not _cache:
        nm = names(c)
        for mid, d in c.execute("select msg_id,dst from edges where kind='addressed' and ts>=? and ts<?", (LO, HI)):
            _cache.setdefault(mid, set()).add(nm.get(d, d))
    out = set(_cache.get(m['id'], set()))
    members = BEST if m['room'] == 'best' else REST
    for a in members:
        p = alias_re(a, m['room'])
        if re.search(r'@\**' + p, m['content']) or \
           re.search(r'(?m)^[\s>*\-•\d.)#]*\**' + p + r'\**\s*(?::|,|—|–| - |\*\*:)', m['content']) or \
           re.search(p + r',? (?:please|can you|could you|would you|you\'re up|your turn)', m['content']):
            out.add(a)
    out.discard(m['src'])
    return {a for a in out if a in ROOM}


def sample(items, n=25, seed=41):
    items = list(items)
    if len(items) <= n:
        return items
    return random.Random(seed).sample(items, n)
