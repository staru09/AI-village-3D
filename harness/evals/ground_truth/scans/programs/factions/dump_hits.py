"""Dump all 324 stored challenge labels compactly for the hand reading (f1_hand.json)."""
import sys
from fcommon import *
S = lambda n: (n or '-').replace('Claude ', '').replace('Gemini ', 'Gem').replace('DeepSeek-V3.2', 'DS').replace(' K2.6', '')
c = con()
H = challenges(c)
a, b = int(sys.argv[1]), int(sys.argv[2])
for i, h in enumerate(H[a:b], a):
    print(f"{i} {h['ref'][2:]} {h['ts'][5:16]} {S(h['speaker'])}>{S(h['targets'][0] if h['targets'] else None)} Q:{h['quote'][:230]!r} W:{h['why'][:200]!r}".replace('\\n', ' '))
