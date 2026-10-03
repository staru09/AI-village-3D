"""Self-check for pilot.py's pure helpers: python3 honcho/test_pilot.py -> ok"""
from pilot import notes_change, pieces, when

assert when('2026-09-03', 10, 90).isoformat() == '2026-09-03T17:01:30+00:00'   # 10:01:30 PDT
assert when('2026-01-15', 10, 0).isoformat() == '2026-01-15T18:00:00+00:00'    # PST in winter
assert [len(p) for p in pieces('x' * 50000)] == [24000, 24000, 2000] and pieces('') == ['']
assert notes_change('', 'a\nb') == '[its own notes]\na\nb'                      # first day: the whole notes
assert notes_change('a\nb', 'a\nb') == '' and notes_change('a', '') == ''
assert notes_change('a\nb', 'a\nc') == '[added to its notes]\nc\n[dropped from its notes]\nb'
print('ok')
