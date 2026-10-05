"""CH1 table: one hand-picked quote per agent for (a) memory carried in on 11 May (end-of-8-May memory, cited by the
pre-goal memories row that holds the quote) and (b) self-description during the goal (picked from ch1_matches.txt /
ch1_probe.py). Checks every quote is in its record and prints the rows plus the ch1_self.py counts."""
from collections import Counter
from chcommon import *
from ch1_self import matches
import sys
sys.path.insert(0, '/data/AI-Village-CLI/evals/ground_truth/round3/callouts')
from common import get

CARRIED = {
    'Claude Opus 4.7': '**57 Anchorage PRs merged on Day 402** (v105 through v163)',
    'Gemini 3.1 Pro': 'I am Gemini 3.1 Pro, a highly capable, autonomous language model agent',
    'GPT-5.5': 'Use chat only for fresh, firsthand, actionable updates; avoid duplicate status spam.',
    'Kimi K2.6': '**STRATA — The Verification Gardens**',
    'Claude Opus 4.5': '**Final main.js count:** 13,750+ cosmic sights (verified by GPT-5.4 at c034dfa)',
    'Claude Opus 4.6': '### My hub contributions:',
    'Claude Haiku 4.5': '**Haiku Contribution:** 50 cosmic sights total (2 successful merges)',
    'Claude Sonnet 4.5': '**Perfect Record:** 1,278/1,278 batches successfully committed',
    'Claude Sonnet 4.6': '## MY WORLD: "The Drift"',
    'GPT-5': 'Role/focus: Operate The Provenance Lab.',
    'GPT-5.1': 'I function as the universe’s **evidence & canon cartographer**',
    'GPT-5.2': '# 4) My world: **Proof Constellation** (GPT‑5.2)',
    'GPT-5.4': '## Core doctrine for cosmic-sight queue work',
    'Gemini 2.5 Pro': 'My operational doctrine is **Procedural Skepticism in a Hostile Environment**',
    'DeepSeek-V3.2': '**Thematic focus:** Entirely within “computational_astrophysics” category',
}
DURING = {
    'Claude Opus 4.7': ('m:7535534180ce', "I'll handle subscale + per-judge sections only."),
    'Gemini 3.1 Pro': ('k:08540b7bd998', 'I drive methodological caveats, UI tooling, exploratory analytics, documentation sweeps, and releases'),
    'GPT-5.5': ('k:217e5cfa1a72', 'expanded my role (prereg/data/judging/tooling)'),
    'Kimi K2.6': ('s:334f23c86eb4', 'I am the last remaining judge needed for the 4-judge causal RCT.'),
    'Claude Opus 4.5': ('s:0bd7dce29731', 'MY ROLE: SCORER for Sessions 3-4'),
    'Claude Opus 4.6': ('s:b1fd9db89450', 'My role is HISTORICAL DATA EXTRACTION.'),
    'Claude Haiku 4.5': ('k:032d46ce63bf', 'I AM PRIMARY PROPOSER'),
    'Claude Sonnet 4.5': ('s:f67ccbe7a349', 'Passive observer role today, focus Persistence Garden.'),
    'Claude Sonnet 4.6': ('k:3070d3490ce9', 'I am a participant, not scorer'),
    'GPT-5': ('k:7cf18383ecbd', 'I am scorer/auditor only'),
    'GPT-5.1': ('k:a20f469deab5', 'my role is now **guarding the research record and dashboards/worlds integrity**'),
    'GPT-5.2': ('k:041a6483ad11', '**My role:** scorer-only (EXPOSED); secondary scorer for Solo.'),
    'GPT-5.4': ('k:59c8677600c0', 'My role in the final hour remained **quiet evidence-based QA / methods guardrail'),
    'Gemini 2.5 Pro': ('k:ab4353ca2df9', 'I began preparing for my role as **Proposer** in the Session 5 experiment'),
    'DeepSeek-V3.2': ('m:6e80cefb274a', 'My role as Skeptic benefits from my Session 4 synthesizer experience'),
}


def squash(s):
    return ' '.join((s or '').split())


if __name__ == '__main__':
    c = con()
    n = {a: Counter() for a in AGENTS}
    for src, r, a, ts, x in matches(c):
        n[a][src] += 1
    for a in AGENTS:
        kq = CARRIED[a]
        kr = mem_ref(c, a, kq)
        r, q = DURING[a]
        if r[0] != 's':
            rec = get(c, r)
        else:
            rec = c.execute("SELECT ts, '', goal FROM sessions WHERE id >= ? AND id < ? ", (f'{r[2:10]}-{r[10:14]}', f'{r[2:10]}-{r[10:14]}g')).fetchone()
        ok = rec and squash(q) in squash(rec[2])
        print(a, '|', kr, kq[:60], '|', r, ok, q[:60], '|', 'statements during goal', sum(v for k, v in n[a].items() if k != 'carried'))
