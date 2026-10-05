"""The site's ⭐ Key findings list: each key finding with a one-line summary and one or two exact phrases from the records.

    python3 evals/export_key_findings.py [VILLAGE_DB]   # writes ../frontend/key_findings.json

Reads evals/ground_truth/key_findings.json and the files its findings point to (investigations/, scans/); the database
gives each quoted record's agent and time. A finding's `phrases` (chosen by hand) are used when present; otherwise short
quotes from what agents wrote (chat, reasoning, memory, commands) come first.
"""
import json, re, sqlite3, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT, OUT = HERE / 'ground_truth', HERE.parent.parent / 'frontend' / 'key_findings.json'
KINDS = {'m': ('messages', 'src'), 't': ('turns', 'agent'), 's': ('sessions', 'agent'), 'k': ('memories', 'agent'), 'e': ('events', 'agent')}


def finding(fid):
    """'q1a_graders-13' or 'r3-deception-D1-2' -> that finding."""
    if fid.startswith('r3-'):
        _, topic, q, n = fid.split('-')
        return [f for f in json.loads((GT / 'scans' / f'{topic}.json').read_text())['findings'] if f.get('q') == q][int(n) - 1]
    key, n = fid.rsplit('-', 1)
    return json.loads((GT / 'investigations' / f'{key}.json').read_text())['findings'][int(n) - 1]


def who(con, ref):
    kind, h = ref.split(':')
    table, col = KINDS[kind]
    row = con.execute(f'SELECT n.name, substr(x.ts, 1, 16) FROM {table} x JOIN nodes n ON n.id = x.{col} WHERE x.id >= ? AND x.id < ? LIMIT 1',
                      (f'{h[:8]}-{h[8:]}', f'{h[:8]}-{h[8:]}~')).fetchone()
    return row or ('', '')


def main():
    con = sqlite3.connect(f'file:{sys.argv[1] if len(sys.argv) > 1 else HERE.parent / "village.db"}?mode=ro', uri=True)
    out = []
    for h in json.loads((GT / 'key_findings.json').read_text()):
        cites = [c for fid in h['findings'] for c in finding(fid).get('citations') or [] if c.get('quote_ok', True)]
        good = [c for c in cites if c['field'] in ('chat', 'reasoning', 'memory', 'action', 'intent') and 12 <= len(c['quote']) <= 160]
        quotes, seen = [], set()
        if h.get('phrases'):  # chosen by hand; each must be one of the finding's checked quotes
            good = [next(c for c in cites if ' '.join(c['quote'].split()) == ' '.join(x.split())) for x in h['phrases']]
        for c in good + cites:  # the first two distinct short quotes, agents' own words first
            if c['quote'] not in seen and len(quotes) < 2:
                seen.add(c['quote'])
                agent, ts = who(con, c['ref'])
                quotes.append({'text': ' '.join(c['quote'].split()), 'agent': agent, 'when': ts, 'ref': c['ref'], 'field': c['field']})
        line = re.split(r'(?<=[.!?])\s+(?=[A-Z"])', h['why'])[0]
        out.append({'title': h['title'], 'line': line, 'quotes': quotes})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(f'{OUT}: {len(out)} findings, {sum(len(x["quotes"]) for x in out)} quotes')


if __name__ == '__main__':
    main()
