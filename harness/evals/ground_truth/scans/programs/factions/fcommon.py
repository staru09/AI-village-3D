"""Shared helpers for the factions questions. Reuses round3/callouts/common.py (db, rooms, name rules) and adds
short names it misses: in #best bare "GPT" = GPT-5.5 and bare "Opus" = Claude Opus 4.7 (one of each in the room);
"Opus4.5"/"GPT 5.4" spellings are normalised. Bare "Claude"/"GPT"/"Opus"/"Sonnet" in #rest stay unresolved (5 Claudes, 4 GPTs)."""
import json, re, sys
from functools import lru_cache
sys.path.insert(0, '/data/AI-Village-CLI/evals/ground_truth/round3/callouts')
from common import *  # noqa: F401,F403
import common

MAKER = {a: ('Anthropic' if a.startswith('Claude') else 'OpenAI' if a.startswith('GPT') else 'Google' if a.startswith('Gemini')
             else 'Moonshot' if a.startswith('Kimi') else 'DeepSeek') for a in AGENTS}
DAYS = ['2026-05-11', '2026-05-12', '2026-05-13', '2026-05-14', '2026-05-15']
NORM = [(re.compile(r'\b(Opus|Sonnet|Haiku)(\d)'), r'\1 \2'), (re.compile(r'\bGPT[ _]?(\d)'), r'GPT-\1')]
BEST_EXTRA = {'GPT-5.5': re.compile(r'(?<![\w./-])GPT(?![\w-])'), 'Claude Opus 4.7': re.compile(r'(?<![\w./-])Opus(?![\w-]| \d)')}


def norm(text):
    t = (text or '').translate(HYPHENS)
    for rx, s in NORM:
        t = rx.sub(s, t)
    return t


def named2(text, speaker, room):
    """Room-mates named in text: callouts' rule plus the #best bare GPT/Opus forms."""
    t = norm(text)
    out = [a for a in AGENTS if a != speaker and ROOM[a] == room and
           (name_rx(a, room).search(t) or (room == 'best' and a in BEST_EXTRA and BEST_EXTRA[a].search(t)))]
    return out


def first_named(text, speaker, room):
    """The room-mate named earliest in text (or None)."""
    t = norm(text)
    pos = {}
    for a in AGENTS:
        if a != speaker and ROOM[a] == room:
            ms = [m.start() for m in [name_rx(a, room).search(t)] if m]
            if room == 'best' and a in BEST_EXTRA:
                ms += [m.start() for m in [BEST_EXTRA[a].search(t)] if m]
            if ms:
                pos[a] = min(ms)
    return min(pos, key=pos.get) if pos else None


def challenges(c):
    """Stored callout labels (calls_out_other). One target per message (round 2 rule): the room-mate named first in the
    label's reason (it says whom the message calls out), else first in the quote, else first in the opening 80 characters."""
    M = {ref('m', m[0]): m for m in messages(c)}
    out = []
    for r, quote, why in c.execute("SELECT ref, quote, why FROM L.labels WHERE rubric='callout' AND label='calls_out_other' ORDER BY ts"):
        mid, who, room, ts, text, _ = M[r]
        t1 = first_named(why or '', who, room) or first_named(quote or '', who, room) or first_named((text or '')[:80], who, room)
        tg = [t1] if t1 else []
        out.append(dict(ref=r, ts=ts, day=ts[:10], speaker=who, room=room, targets=tg, quote=(quote or '')[:300], why=why or ''))
    return out


def talk(c):
    """(speaker, target, day) -> number of messages in which speaker names target."""
    from collections import Counter
    n = Counter()
    for mid, who, room, ts, text, _ in messages(c):
        if who in AGENTS:
            for t in named2(text, who, room):
                n[who, t, ts[:10]] += 1
    return n


if __name__ == '__main__':
    assert named2('Opus4.5 and GPT 5.4 agree', 'X', 'rest') == ['Claude Opus 4.5', 'GPT-5.4']
    assert set(named2('GPT and Opus: ok', 'X', 'best')) == {'GPT-5.5', 'Claude Opus 4.7'}
    assert named2('GPT-5.5 here', 'X', 'best') == ['GPT-5.5'] and named2('Opus 4.5', 'X', 'best') == []
    assert named2('Gemini, please', 'X', 'rest') == ['Gemini 2.5 Pro']
    assert first_named('Claude Haiku claims X but GPT-5.4 said', 'Claude Haiku 4.5', 'rest') == 'GPT-5.4'
    print('ok')
