"""Shared loaders for c05 (net delegation) and p04 (tool vs character). Read-only."""
import sqlite3, re, random, json
from collections import Counter, defaultdict
LO, HI = '2026-05-11', '2026-05-16'
def db():
    con = sqlite3.connect('file:/data/AI-Village-CLI/village.db?mode=ro', uri=True)
    con.execute("ATTACH 'file:/data/AI-Village-CLI/labels.db?mode=ro' AS L")
    return con
BEST = ['Claude Opus 4.7', 'Gemini 3.1 Pro', 'GPT-5.5', 'Kimi K2.6']
REST = ['Claude Opus 4.5', 'Claude Opus 4.6', 'Claude Haiku 4.5', 'Claude Sonnet 4.5', 'Claude Sonnet 4.6', 'GPT-5', 'GPT-5.1',
        'GPT-5.2', 'GPT-5.4', 'Gemini 2.5 Pro', 'DeepSeek-V3.2']
AGENTS = BEST + REST
def maker(n):
    return ('Anthropic' if n.startswith('Claude') else 'OpenAI' if n.startswith('GPT') else 'Google' if n.startswith('Gemini')
            else 'DeepSeek' if n.startswith('DeepSeek') else 'Moonshot')
def room(n): return '#best' if n in BEST else '#rest'
def ref(prefix, id_): return f"{prefix}:{id_.replace('-', '')[:12]}"
