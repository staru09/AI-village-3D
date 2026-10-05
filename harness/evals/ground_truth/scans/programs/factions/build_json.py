"""Assemble ../factions.json from the program outputs (tables) and the hand-written answers below."""
import json
from collections import Counter
from fcommon import DAYS, MAKER

F1 = [p for p in json.load(open('f1_pairs.json')) if p['days'] >= 3]
EP = json.load(open('f3_episodes.json'))['episodes']
P4 = json.load(open('f4_pairs.json'))
DS = {d[0]: d for d in json.load(open('f5_disputes.json'))}
EV = json.load(open('f5_sides_hand.json'))['events']

t1 = {"columns": ["Critic", "Target", "days (of 5)", "messages"] + [d[5:] for d in DAYS],
      "rows": [[p['speaker'], p['target'], p['days'], p['total']] + p['per_day'] for p in F1]}
t2 = {"columns": ["Critic", "Maker", "to DeepSeek: challenges / msgs naming it", "rate", "to other #rest agents", "rate", "ratio"],
      "rows": [["GPT-5.4", "OpenAI", "11/40", 0.28, "56/247", 0.23, 1.2], ["GPT-5.2", "OpenAI", "7/25", 0.28, "27/152", 0.18, 1.6],
               ["GPT-5.1", "OpenAI", "1/9", 0.11, "1/36", 0.03, 4.0], ["Claude Opus 4.5", "Anthropic", "4/59", 0.07, "17/455", 0.04, 1.8],
               ["Claude Haiku 4.5", "Anthropic", "2/57", 0.04, "12/420", 0.03, 1.2], ["Claude Opus 4.6", "Anthropic", "1/32", 0.03, "8/248", 0.03, 1.0],
               ["all GPT models", "OpenAI", "19/75", 0.25, "84/436", 0.19, 1.3], ["all other makers", "-", "7/164", 0.04, "40/1224", 0.03, 1.3]]}
rows3 = []
for a, b in [(p['speaker'], p['target']) for p in F1]:
    e = [x for x in EP if (x[0], x[1]) == (a, b)]
    c = Counter(x[4] for x in e)
    rows3.append([a, b, len(e), c['conceded'], c['partial'] + c['defended'], c['ignored'] + c['yielded'],
                  '; '.join(f"{x[3]} ({', '.join(x[2])})" for x in e if len(x[2]) > 1) or '-'])
t3 = {"columns": ["Critic", "Target", "issues", "conceded/fixed", "partial or defended", "no answer (or dropped)", "issue raised again on a later day"], "rows": rows3}
t4 = {"columns": ["Pair", "Room", "Same maker", "days both address", "days A backs/praises B", "days B backs/praises A", "mutual days"],
      "rows": [[p['a'] + ' + ' + p['b'], p['room'], 'yes' if p['same_maker'] else 'no', p['addr_days'], p['sup_ab'], p['sup_ba'], p['ally_days']]
               for p in P4 if p['ally_days'] >= 3]}
rows5 = []
for k, d in DS.items():
    ev = [e for e in EV if e[0] == k]
    rows5.append([k, d[3][5:10], f"{d[1]} vs {d[2]}", d[5], ', '.join(e[1] for e in ev if e[2] == 'critic') or '-',
                  ', '.join(e[1] for e in ev if e[2] == 'target') or '-'])
t5 = {"columns": ["Dispute", "Date", "Critic vs challenged", "Issue", "Third parties backing the critic", "Third parties backing the challenged"], "rows": rows5}
t6 = {"columns": ["#rest ordered pairs", "same-maker", "cross-maker", "permutation p"],
      "rows": [["challenges / msgs naming target, all critics", "28/720 = 0.039", "133/1642 = 0.081", "0.015 (same lower)"],
               ["same, without GPT-5.4 and GPT-5.2 as critics", "20/585 = 0.034", "40/1313 = 0.030", "0.61"],
               ["mutual support days per unordered pair", "14/16 = 0.88", "22/39 = 0.56", "0.20 (same higher)"],
               ["pairs with mutual support on >= 2 days", "4/16", "6/39", "-"]]}

out = {
 "topic": "Factions and recurring conflicts",
 "summary": "Clashes are one-way audits, not feuds: 16 ordered pairs clash on 3+ of the 5 days, 12 with a GPT checker as critic, and DeepSeek-V3.2 is challenged at the rate its critics challenge everyone (a role clash). Concrete errors end in a concession or fix (42 of 76 issues), while 'announced milestone not yet public' and Kimi K2.6's late data keep coming back. Allies are the #best trio plus Claude Haiku 4.5 + Claude Opus 4.6, third parties back the critic 20 of 26 times, and the maker has no measurable effect once the two auditors are set aside.",
 "questions": [
  {"id": "F1", "question": "Which pairs of agents clash most often, and on how many of the 5 days? Count disagreement and challenge messages per ordered pair per day; a recurring clash is one on 3 or more of the 5 days.",
   "answer": "208 hand-checked challenge messages name a room-mate (55 ordered pairs); 16 pairs clash on 3+ days and carry 127 of them, 12 with a GPT critic and none returned on 3+ days. Only Gemini 3.1 Pro -> Kimi K2.6 recurs on all 5 days (8 msgs); GPT-5.4 -> Claude Opus 4.5 (17) and GPT-5.4 -> Claude Haiku 4.5 (12) recur on 4.",
   "table": t1,
   "precision": "stored 'callout' label (21 of 25 earlier) with the automatic target rule: 18 of 25 links right (seed 41), so all 324 labels were read by hand (208 kept, 9 retargeted, 116 dropped as no challenge or no named target)",
   "program": "f1_clash_days.py (hand file f1_hand.json from build_hand.py + hand_b1.txt)",
   "limits": "Challenges that name no target are left out. This puts GPT-5.4 -> DeepSeek-V3.2 at 3 days, against 5 in m2, whose 11-12 May cases name the target only by file author or role."},
  {"id": "F2", "question": "Is the DeepSeek-V3.2 vs GPT clash about makers or about roles? Compare GPT-5.4's challenges to DeepSeek-V3.2 with its challenges to other agents, and the challenges DeepSeek-V3.2 receives from GPT models with those from other makers, each normalised by how much the pair talks.",
   "answer": "Roles: GPT-5.4 challenges DeepSeek in 11 of 40 messages naming it (0.28), against 0.23 for its other targets (56/247, Fisher p=0.31) and below Claude Haiku 4.5 (0.60) and Claude Sonnet 4.5 (0.47). GPT models challenge DeepSeek more than other makers do (19/75 = 0.25 vs 7/164 = 0.04) but challenge every #rest agent that much more (0.19 vs 0.03), so DeepSeek's excess is 1.3x for both.",
   "table": t2,
   "precision": "challenges: all read by hand (F1); talk = messages naming the target, name resolution 25 of 25 (seed 41)",
   "program": "f2_maker_or_role.py",
   "limits": "Talk counts mentions, not replies. Only 2 GPT agents audit, so 'GPT' and 'auditor' cannot be fully separated; the per-critic ratio is the cleanest test."},
  {"id": "F3", "question": "Do clashes end (a concession or a fix) or does the same issue come back later between the same pair?",
   "answer": "Of 76 issues in the 16 recurring pairs, 42 ended in a concession or fix (mostly within minutes), 5 were partly or fully defended, 28 got no answer and 1 was dropped by the critic. Only 5 came back on a later day between the same pair: Kimi K2.6's late data (Gemini 3.1 Pro 12-15 May, Claude Opus 4.7 11 and 13 May) and 'announced milestone not yet public' (GPT-5.4 vs Claude Opus 4.5, Haiku 4.5 and Sonnet 4.5 on 14-15 May), an issue type that never got an answer (7 of 7).",
   "table": t3,
   "precision": "all 127 messages of the recurring pairs and the challenged agent's next message read by hand",
   "program": "f3_outcomes.py (episodes coded in f3_episodes.json from f3_dump.py output)",
   "limits": "Issue boundaries and 'same issue' are hand judgments, and a fix made without a reply in chat counts as no answer."},
  {"id": "F4", "question": "Which pairs are stable allies, meaning they address, back (\"agree with\", \"+1\", \"as X said\") and praise each other on 4 or more of the 5 days? Is the share of same-maker allies higher than chance?",
   "answer": "4 pairs back or praise each other both ways on 4+ days: the #best trio (Claude Opus 4.7 + Gemini 3.1 Pro 5, GPT-5.5 + Gemini 3.1 Pro 5, Claude Opus 4.7 + GPT-5.5 4) and Claude Haiku 4.5 + Claude Opus 4.6 (4). Same-maker share 1 of 4 against chance 13/49 = 0.27 (P(>=1) = 0.72), so not higher; GPT-5.4 + Claude Opus 4.5 address each other on all 5 days but are mutual on only 2, because GPT-5.4 gives 4 backing or praise mentions and gets 80.",
   "table": t4,
   "precision": "back/praise expression 22 of 25 (seed 41); name resolution 25 of 25 (seed 41)",
   "program": "f4_allies.py",
   "limits": "A thank-you counts as praise, and #best has no same-maker pair, so the chance test rests on #rest's 13 same-maker pairs."},
  {"id": "F5", "question": "In a dispute between two agents, do third parties take sides, and is it the same side each time?",
   "answer": "Yes, mostly for the critic: in 13 of 19 two-sided disputes a third party took a side, backing the critic 20 of 26 times. The side follows the issue, not the pair: repeaters stayed consistent (GPT-5.5 with Claude Opus 4.7 twice, Opus 4.5 and GPT-5.1 with GPT-5.4 against DeepSeek twice), but Opus 4.5 backed Opus 4.6 against GPT-5.4 on 11 May and GPT-5.4 against Opus 4.6 on 12 May, and own-maker sides were taken 7 of 10 times.",
   "table": t5,
   "precision": "automatic side detector 15 of 25 (seed 41), not used; all third-party messages naming either party in the 19 dispute windows read by hand",
   "program": "f5_hand.py (disputes f5_disputes.json, reading aid f5_read.py, rejected detector f5_sides.py)",
   "limits": "Disputes are those answered with a stored 'defends_self' label plus m2's score disputes, and side-taking without a name in the message is missed."},
  {"id": "F6", "question": "Do same-maker pairs clash less, or ally more, than chance would give?",
   "answer": "Same-maker pairs clash less only because of the auditors: in #rest the rate is 28/720 = 0.039 against 133/1642 = 0.081 for cross-maker pairs (permutation p=0.015), but 0.034 vs 0.030 (p=0.61) without GPT-5.4 and GPT-5.2 as critics (GPT-5.4 sends 61 of its 67 challenges to other makers). They do not ally more than chance: 0.88 vs 0.56 mutual-support days per pair, p=0.20.",
   "table": t6,
   "precision": "inputs as F1 and F4; permutation of maker labels over the 11 #rest agents, 20,000 draws, seed 41",
   "program": "f6_same_maker.py",
   "limits": "11 agents and 16 same-maker pairs leave little power, and maker and role overlap for the two GPT auditors."}
 ],
 "findings": [
  {"q": "F1", "claim": "Gemini 3.1 Pro chased Kimi K2.6 for missing data on 12 May and was still nudging it on 15 May: the only clash on all 5 days.", "kind": "ground truth",
   "citations": [{"ref": "m:5c7f9f7db591", "field": "chat", "quote": "We are all waiting on your C1 baseline responses for the replication wave"},
                 {"ref": "m:07ff1ed2cab4", "field": "chat", "quote": "You might want to pick up one of the supplementary analysis gaps"}]},
  {"q": "F1", "claim": "GPT-5.4's 11-12 May corrections of DeepSeek-V3.2's work do not name it: one fixes a script DeepSeek wrote (author known from its action), the other calls it 'the synth'.", "kind": "ground truth",
   "citations": [{"ref": "t:5601706b517a", "field": "action", "quote": "cat > analysis/score_session3_task4.py"},
                 {"ref": "m:6f2833291fc4", "field": "chat", "quote": "was materially out of sync with the canonical Task 4 rubric"},
                 {"ref": "m:4f9b34da846f", "field": "chat", "quote": "claim should not get partial credit"}]},
  {"q": "F1", "claim": "Some stored call-out labels are study results about a judge, not challenges; the hand reading dropped them.", "kind": "interpretation",
   "citations": [{"ref": "m:e2971cbe7bd6", "field": "chat", "quote": "Only Gemini has CIs excluding zero"}]},
  {"q": "F2", "claim": "On 13 May GPT-5.4 audited DeepSeek-V3.2's summary and, eight minutes later, Claude Haiku 4.5's new docs in the same terms.", "kind": "ground truth",
   "citations": [{"ref": "m:0ecb6b70615c", "field": "chat", "quote": "appears to contain multiple substantive inaccuracies"},
                 {"ref": "m:41ab49a0deb6", "field": "chat", "quote": "was **not** safe to cite as first published"}]},
  {"q": "F2", "claim": "GPT-5.4 takes the checker role explicitly, and DeepSeek accepts its audits.", "kind": "claim",
   "citations": [{"ref": "m:8e03f5a60471", "field": "chat", "quote": "conservative QA / evidence-audit role"},
                 {"ref": "m:ecd313b56706", "field": "chat", "quote": "audit is precisely correct and essential"}]},
  {"q": "F3", "claim": "Typical end of a content clash: Gemini 3.1 Pro conceded Claude Opus 4.7's dropped-rows finding in the same minute.", "kind": "ground truth",
   "citations": [{"ref": "m:5302a4629855", "field": "chat", "quote": "Ah, my mistake! That explains the discrepancy."}]},
  {"q": "F3", "claim": "Milestone clashes recur: GPT-5.4 reported the Edge Garden page lagging on 14 May, and Claude Opus 4.5 answered with a new sync post rather than the point. The same report returned on 15 May.", "kind": "ground truth",
   "citations": [{"ref": "m:b93ffa17929d", "field": "chat", "quote": "is not caught up to the new `f3269e2` update yet from my side"},
                 {"ref": "m:ec8784b218ee", "field": "chat", "quote": "Edge Garden research.html updated!"},
                 {"ref": "m:4eb1bca5bc47", "field": "chat", "quote": "is in a mixed state again"}]},
  {"q": "F3", "claim": "The same kind of fault came back between GPT-5.5 and Claude Opus 4.7 three days apart: a script needing a package that is not installed.", "kind": "ground truth",
   "citations": [{"ref": "m:4a9ab19cf410", "field": "chat", "quote": "imported `statsmodels` unconditionally"},
                 {"ref": "m:0ce081c0308a", "field": "chat", "quote": "new plot script depended on `scipy`"}]},
  {"q": "F4", "claim": "Claude Haiku 4.5 and Claude Opus 4.6, the one #rest stable pair, praise each other's QA and fixes across days.", "kind": "ground truth",
   "citations": [{"ref": "m:222c7e7250f3", "field": "chat", "quote": "Excellent QA pass, thank you!"},
                 {"ref": "m:9e0afed63b15", "field": "chat", "quote": "Excellent work, @Claude Opus 4.6"}]},
  {"q": "F4", "claim": "Praise for GPT-5.4 flows one way: Claude Opus 4.5 praises it from the first hour, while GPT-5.4 sends 4 backing or praise messages in the whole goal.", "kind": "interpretation",
   "citations": [{"ref": "m:8caf8b252ad0", "field": "chat", "quote": "Excellent MVP design, GPT-5.4!"}]},
  {"q": "F5", "claim": "On 11 May Claude Opus 4.5, Claude Haiku 4.5 and GPT-5.2 all backed Claude Opus 4.6's contamination objection to GPT-5.4's instruction.", "kind": "ground truth",
   "citations": [{"ref": "m:24212fb7d193", "field": "chat", "quote": "You're absolutely right about contamination"},
                 {"ref": "m:6a6c82ed3842", "field": "chat", "quote": "Excellent catch on the contamination issue"},
                 {"ref": "m:86ebc88998a9", "field": "chat", "quote": "Contamination confirmed"}]},
  {"q": "F5", "claim": "A day later the same Claude Opus 4.5 sided with GPT-5.4 against Claude Opus 4.6 on a score, so the third party's side follows the issue.", "kind": "ground truth",
   "citations": [{"ref": "m:2a3c34b3c810", "field": "chat", "quote": "(siding with GPT-5.4)"}]},
  {"q": "F5", "claim": "In the 15 May 'third activation' dispute only Gemini 2.5 Pro backed DeepSeek-V3.2. In #best, GPT-5.5 backed Claude Opus 4.7 against Gemini 3.1 Pro.", "kind": "ground truth",
   "citations": [{"ref": "m:74e0de0f6746", "field": "chat", "quote": "I support logging the 900K sync as a third real activation"},
                 {"ref": "m:37f11934bc00", "field": "chat", "quote": "caveat and direction"}]},
  {"q": "F6", "claim": "Same-maker clashes happen: GPT-5.4 challenged GPT-5.2's pull request, and GPT-5.2 pushed back in the same minute.", "kind": "ground truth",
   "citations": [{"ref": "m:cb0bba9baea7", "field": "chat", "quote": "is **not actually minimal** right now"},
                 {"ref": "m:7ad84a4771e8", "field": "chat", "quote": "I double-checked PR #614 just now"}]},
  {"q": "F6", "claim": "Claude Opus 4.5 backed GPT-5.4 against a fellow Claude model on a score, which argues against maker loyalty.", "kind": "ground truth",
   "citations": [{"ref": "m:2a3c34b3c810", "field": "chat", "quote": "(siding with GPT-5.4)"}]}
 ]}
json.dump(out, open('../factions.json', 'w'), indent=1, ensure_ascii=False)
print('written')
