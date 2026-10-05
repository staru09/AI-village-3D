"""Shared helpers for the peer-matrix questions (goal 41, 11-15 May 2026 PT).

Name resolution fixes the m4 short-name gap: full names anywhere, plus short forms resolved by the room the text is in.
  both rooms: "Opus 4.5"/"Opus4.5", "Sonnet 4.6", "Haiku 4.5", "Haiku", "Gemini 3.1", "Gemini 2.5", "Kimi", "DeepSeek"
  #best:      bare "Claude" or "Opus" = Claude Opus 4.7, bare "GPT" = GPT-5.5, bare "Gemini" = Gemini 3.1 Pro
  #rest:      bare "Gemini" = Gemini 2.5 Pro; bare "Claude", "Opus", "Sonnet", "GPT" stay unresolved (5 Claudes, 6 GPTs)
Short forms must be capitalised (lower-case "gemini-3.1-pro", "kimi-k2.6" are file or folder names), and code spans,
quoted strings and page strings after "| " are skipped.
"""
import re, sys
from functools import lru_cache

sys.path.insert(0, '/data/AI-Village-CLI/evals/ground_truth/round3/callouts')
sys.path.insert(0, '/data/AI-Village-CLI/evals')
from common import con, messages, sample, ref, AGENTS, ROOM, BEST, REST, SINCE, UNTIL  # noqa: E402,F401
from peer_matrix import REGEX  # noqa: E402  (m4 expressions: praise 24/25, request 21/25, deference 24/25)

HYPHENS = str.maketrans({'‐': '-', '‑': '-', '–': '-', '’': "'", ' ': ' '})
SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
YOU = re.compile(r'^\W*(you|your)\b', re.I)
QUOTED = re.compile(r'`[^`\n]*`|“[^”\n]*”|"[^"\n]*"')
RX = {k: re.compile(v, re.I) for k, v in REGEX.items() if k != 'criticism'}
EDGE_L, EDGE_R = r'(?<![\w./=-])(?<!\| )(?<!\| Claude )', r'(?![\w-]|\.\d)'


def forms(name, room):
    """(full forms, short forms) of an agent as written in that room."""
    full = {name}
    if name == 'DeepSeek-V3.2':
        full.add('DeepSeek V3.2')
    short = set()
    for fam in ('Opus', 'Sonnet', 'Haiku'):
        if name.startswith(f'Claude {fam}'):
            v = name.split()[-1]
            short |= {f'{fam} {v}', f'{fam}{v}', f'Claude {fam}'} if fam == 'Haiku' else {f'{fam} {v}', f'{fam}{v}'}
    if name == 'Claude Haiku 4.5':
        short.add('Haiku')
    if name.startswith('Gemini '):
        short.add(name.rsplit(' ', 1)[0])  # "Gemini 3.1"
        if ROOM[name] == room:
            short.add('Gemini')
    if name == 'Kimi K2.6':
        short.add('Kimi')
    if name == 'DeepSeek-V3.2':
        short.add('DeepSeek')
    if room == 'best' and name == 'Claude Opus 4.7':
        short |= {'Claude', 'Opus', 'Claude Opus'}
    if room == 'best' and name == 'GPT-5.5':
        short.add('GPT')
    return full, short - full


def clean(text):
    return QUOTED.sub(' ', (text or '').translate(HYPHENS))


@lru_cache(None)
def room_rx(room):
    """One scanner per room over every agent's forms, longest first, so "Claude Opus 4.5" is never also "Claude"."""
    table = []
    for a in AGENTS:
        full, short = forms(a, room)
        table += [(f, a, 'full') for f in full] + [(f, a, 'short') for f in short]
    table.sort(key=lambda x: -len(x[0]))
    alt = '|'.join(f'(?i:{re.escape(f)})' if k == 'full' else re.escape(f) for f, a, k in table)
    look = {f.lower() if k == 'full' else f: (a, k) for f, a, k in table}
    return re.compile(rf'{EDGE_L}@?({alt}){EDGE_R}'), look


def scan(text, room):
    """[(agent, 'full'|'short', match)] in order of appearance."""
    rx, look = room_rx(room)
    out = []
    for m in rx.finditer(text):
        w = m.group(1)
        a, k = look.get(w) or look[w.lower()]
        out.append((a, k, m))
    return out


def find(text, speaker, room):
    """{target: 'full'|'short'} for every agent named in the text (other than the speaker); text must be clean()ed."""
    out = {}
    for a, k, _ in scan(text, room):
        if a != speaker and out.get(a) != 'full':
            out[a] = k
    return out


def hit(sentence, a, room):
    return any(x == a for x, _, _ in scan(sentence, room))


def target_sentences(text, a, room):
    """Sentences naming the target, plus directly following sentences that start with you/your (as m4)."""
    out, prev = [], False
    for s in SPLIT.split(text):
        if not s.strip():
            continue
        prev = hit(s, a, room) or (prev and bool(YOU.match(s)))
        if prev:
            out.append(s.strip())
    return out


def day(ts):
    return ts[5:10]


if __name__ == '__main__':  # self-check
    t = clean("@Claude Opus 4.5 excellent catch. GPT-5 please rerun. Gemini's commit overwrote `gemini-3.1-pro/x`.")
    assert find(t, 'GPT-5.4', 'rest') == {'Claude Opus 4.5': 'full', 'GPT-5': 'full', 'Gemini 2.5 Pro': 'short'}
    assert find(t, 'Kimi K2.6', 'best') == {'Gemini 3.1 Pro': 'short'} | {'Claude Opus 4.5': 'full', 'GPT-5': 'full'}
    assert find(clean('Thanks Claude and GPT!'), 'Kimi K2.6', 'best') == {'Claude Opus 4.7': 'short', 'GPT-5.5': 'short'}
    assert find(clean('Thanks Claude and GPT!'), 'GPT-5.4', 'rest') == {}
    assert find(clean('GPT-5.1 and Opus4.6 agree'), 'GPT-5.4', 'rest') == {'GPT-5.1': 'full', 'Claude Opus 4.6': 'short'}
    assert find(clean('Claude Opus 4.7 did it'), 'Kimi K2.6', 'best') == {'Claude Opus 4.7': 'full'}
    assert find(clean('see gemini-3.1-pro and kimi'), 'GPT-5.5', 'best') == {}
    print('ok')
