"""Q1: (a) system-injected texts that agents quote in reasoning (excluded from mantras), per agent;
(b) each agent's most repeated self-instruction: reasoning texts containing it (base = agent's reasoning texts),
sessions, chat messages, memory versions (base = memory versions) and day snapshots containing it, first use,
classification: 'memory rule' if it stands in >=25% of memory versions or >=2 daily snapshots, else 'afresh'.
Run with --sample to print a seed-41 sample of 25 matches per pattern for validation."""
import re, sys, json
from common import load, con, names, AGENTS, LO, HI, sample
T = load(); c = con(); nm = names(c)
snap = {}
for r in c.execute('select agent,date,content from memory_days where date>=? and date<?', (LO, HI)): snap.setdefault(nm[r['agent']], {})[r['date']] = r['content']
nsess = {a: 0 for a in AGENTS}
for r in c.execute('select agent from sessions where ts>=? and ts<?', (LO, HI)):
    if nm[r['agent']] in nsess: nsess[nm[r['agent']]] += 1
INJ = [('turn header', r'never send repetitive messages|what has happened since your last turn'),
       ('idling nudge', r'repeated-idling|automated (nudge|message|reminder)|idl(e|ing) (nudge|alert|notice|warning|penalt)'),
       ('one tool call rule', r'one tool call per (response|turn|message)|only (make )?one tool call'),
       ('day header', r'today is day \d+ of the village|system[- ]prompt day'),
       ('work-to-end-of-day line', r'keep working right up until the end'),
       ('pixel-coords tool rule', r'get_pixel_coords\w*\W{0,3}before click|always use\W{1,3}get_pixel_coords')]
M = [  # agent, label, reasoning regex, memory regex (None = same)
 ('Claude Opus 4.7', 'Pre-render bug: check events feed before sending', r'pre-?(echo|render)', r'pre-?(echo|render)'),
 ('Gemini 3.1 Pro', 'anti-idling / action bias ("Passive waiting is catastrophic")', r'action bias|passive(ly)? waiting|no idling|(can.t|not|never) (afford to )?(sit )?idle|anti-idling|look busy', r'passive(ly)? waiting|anti-idling'),
 ('GPT-5.5', '"make sure / ensure everything is in order"', r'everything is in order', None),
 ('Kimi K2.6', '"I need to press Enter"', r'need to press enter', None),
 ('Claude Opus 4.5', '"I should continue monitoring"', r'should continue monitoring', None),
 ('Claude Opus 4.6', '"Let me keep going / building / pushing"', r'let me keep (going|building|pushing)', None),
 ('Claude Haiku 4.5', '"I should continue standing by"', r'should continue (standing|to stand) by', None),
 ('Claude Sonnet 4.5', '"continue adding more batches / secrets"', r'continue adding (more )?(batches|secrets)', None),
 ('Claude Sonnet 4.6', '"Let me keep going (with journeys N-M)"', r'let me keep going', None),
 ('GPT-5', '"CUT→Title workflow" for the anchor issue', r'cut\s*(→|->|to)\s*title', None),
 ('GPT-5.1', '"nothing I need to do / no need to send"', r"nothing (else )?i need to|(don.t|no) need to send", None),
 ('GPT-5.2', '"address messages directed at me"', r'messages directed at me', None),
 ('GPT-5.4', '"stay quiet and (remain) available"', r'stay quiet (in .{0,8}rest. )?and (remain )?available', None),
 ('Gemini 2.5 Pro', '"No need to overthink it/this"', r'no need to overthink', None),
 ('Gemini 2.5 Pro', '"Precision is key"', r'precision is key', None),
 ('Gemini 2.5 Pro', '"the user wants me to ..." (summary framing of the turn prompt)', r'the user wants me to', None),
 ('DeepSeek-V3.2', '"for (all) future AI Village scientific work" (slogan)', r'future ai village scientific work', None),
]
out = {'injected': [], 'mantras': []}
print('== injected texts quoted in reasoning: texts per agent')
for lab, pat in INJ:
    p = re.compile(pat, re.I); row = {'label': lab, 'pattern': pat}
    for a in AGENTS:
        h = [x for x in T[a]['reasoning'] if p.search(x[2])]
        if h: row[a] = len(h)
    out['injected'].append(row); print(lab, {k: v for k, v in row.items() if k in AGENTS})
    if '--sample' in sys.argv:
        allh = [(a, x) for a in AGENTS for x in T[a]['reasoning'] if p.search(x[2])]
        for a, x in sample(allh): m = p.search(x[2]); print(f'   S [{a}] {x[0]} ..{x[2][max(0, m.start() - 70):m.end() + 50]!r}')
print('== mantras')
for a, lab, rp, mp in M:
    p = re.compile(rp, re.I); q = re.compile(mp or rp, re.I)
    R = [x for x in T[a]['reasoning'] if p.search(x[2])]
    Ch = [x for x in T[a]['chat'] if p.search(x[2])]
    Mv = [x for x in T[a]['memory'] if q.search(x[2])]
    days = [d[5:] for d in sorted(snap[a]) if q.search(snap[a][d])]
    first = min(R + Ch + Mv, key=lambda x: x[1]) if (R + Ch + Mv) else None
    nmv = len(T[a]['memory'])
    cls = 'memory rule (re-read)' if (len(Mv) >= 0.25 * nmv or len(days) >= 2) else 'afresh'
    if 'user wants' in rp or 'directed at me' in rp: cls = 'reaction to injected turn prompt'
    row = dict(agent=a, mantra=lab, pattern=rp, reasoning=len(R), reasoning_base=len(T[a]['reasoning']),
               sessions=len({x[3] for x in R}), sessions_base=nsess[a], chat=len(Ch), chat_base=len(T[a]['chat']),
               memory_versions=len(Mv), memory_base=nmv, snapshot_days=days, first=(first[0], first[1][:16]) if first else None,
               first_reasoning=(R[0][0], R[0][1][:16]) if R else None, cls=cls)
    out['mantras'].append(row)
    print(f"{a:17s} {lab[:50]:50s} reas {len(R)}/{len(T[a]['reasoning'])} sess {row['sessions']}/{nsess[a]} chat {len(Ch)}/{len(T[a]['chat'])} mem {len(Mv)}/{nmv} days {days} first {row['first']} -> {cls}")
    if '--sample' in sys.argv:
        for x in sample(R + Ch):
            m = p.search(x[2]); print(f'   S {x[0]} ..{x[2][max(0, m.start() - 60):m.end() + 40]!r}')
json.dump(out, open('q1_mantras.json', 'w'), indent=1)
