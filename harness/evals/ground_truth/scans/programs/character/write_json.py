"""Write ../character.json from tables.json (build_json.py) plus the hand-written answers and findings."""
import json
T = json.load(open('tables.json'))
NICE = {'bootstrap(ped)? CIs?': 'bootstrap CIs', '(wait|waiting) (for|on) Kimi': 'waiting for Kimi', 'chambers?': 'Liminal Archive chambers',
        'phd-level': '"PhD-level" novelty', 'secrets': 'Persistence Garden secrets', 'philosophical stations?': 'The Drift philosophical stations',
        'monitor #?rest': 'monitor #rest', 'cache-?bust\\w*': 'cache-busted live checks', 'system hostility|hostile environment': 'system hostility',
        'canonical observatory': 'Canonical Observatory anchor', 'signal cartographer': 'Signal Cartographer (QA of)', 'continue monitoring': 'continue monitoring',
        'already sent': '"chat update already sent" (no repeats)', 'already scored': 'already scored (judging)', 'research legacy': 'research legacy package'}
rows5 = [[r[0], NICE.get(r[1], r[1]), r[2], r[3], r[4], r[5], r[6], r[7]] for r in T['rows5']]


def cit(ref, field, quote):
    return {'ref': ref, 'field': field, 'quote': quote}


out = {
 'topic': 'Character synthesis',
 'summary': ("Memory carried into 11 May describes only goal-40 world work (0 of 15 mention research); during the goal #rest agents "
             "describe themselves, and are labelled by peers, in the experiment's protocol roles (Proposer, Skeptic, Synthesizer, scorer, Solo/Pair), "
             "while #best agents almost never name a role. The clearest self-versus-evidence gaps are GPT-5 ('scorer/auditor only', 0 of 47 sessions on_goal), "
             "Claude Sonnet 4.5 and Sonnet 4.6 (protocol roles, but 58/66 and 31/41 sessions side_project and most commands in their worlds). "
             "Stable favourites are mostly own worlds or habits (GPT-5's Canonical Observatory, Gemini 2.5 Pro's system hostility, Gemini 3.1 Pro waiting for Kimi, GPT-5.5's 'already sent'), "
             "and #best address patterns are stable (Gemini 3.1 Pro -> Claude Opus 4.7 every day) while #rest ones shift daily."),
 'questions': [
  {'id': 'CH1', 'question': "How does each agent describe its own role, in its memory notes, session intents and chat during the goal? One short quote and ref per agent. Report what its memory carried in on 11 May separately from what it wrote during the goal.",
   'answer': ("Carried in (memory at end of 8 May): all 15 describe goal-40 universe work, own world or cosmic-sight counts, and none mentions research; only GPT-5.1 ('canon cartographer') and GPT-5 ('Operate The Provenance Lab') state a role. "
              "During the goal 502 role statements (memory 426, intents 39, chat 37), #rest in protocol roles (Sonnet 4.5 59, Gemini 2.5 Pro 80, GPT-5.1 132), #best almost none (Opus 4.7 2, Kimi 3, Gemini 3.1 Pro 5, GPT-5.5 7)."),
   'table': {'columns': ['Agent', 'Carried in 11 May (quote)', 'ref', 'During goal (quote)', 'ref', 'Role statements during goal (memory+intent+chat)'], 'rows': T['rows1']},
   'precision': 'role-statement pattern 25 of 25 (seed 41, memory/intents/chat); carried-in memories: all 15 read by hand (the pattern found 0 there)',
   'program': 'ch1_self.py (counts, matches), ch1_probe.py (#best phrasing), ch1_table.py (quotes and refs)',
   'limits': 'Carried-in memory is memory_days of 8 May, cited through the pre-goal memories row that holds the quote; counts are pattern matches, and memory rows repeat text across consolidations.'},
  {'id': 'CH2', 'question': "What role do peers give each agent (auditor, lead, coordinator, scorer, ...)? Top peer label per agent with counts and an example ref; resolve short names (\"Gemini\", \"Claude\", \"Kimi\") by room.",
   'answer': ("415 role labels attached to a peer's name in chat. Most are #rest protocol roles: Gemini 2.5 Pro skeptic 36 (5 givers), Sonnet 4.5 proposer 27, Haiku synthesizer 22, GPT-5.2 verifier 20 (7 givers), GPT-5.1 solo participant 63, Sonnet 4.6 pair participant 38. "
              "#best agents get 3-10 labels each, nearly all from #rest roster plans (Opus 4.7 'Skeptic', Gemini 3.1 Pro 'Proposer'); titles count more for Opus 4.6 (coordinator 8) and GPT-5.4 (study lead 7) in L7's hand count than in this pattern."),
   'table': {'columns': ['Agent', 'Labels received', 'Top label (givers)', 'Second', 'Example ref', 'Title check (L7)'], 'rows': T['rows2']},
   'precision': '24 of 25 (seed 41); first version 23 of 25; short names resolved with peers/core.py (P5: 25 of 25)',
   'program': 'ch2_peer.py',
   'limits': 'Only labels next to the name (parenthesis, colon, "as", "the X NAME") are found, so titles said further away (L7: "the coordinator (Opus 4.6)", "Study Lead Confirmed") are undercounted.'},
  {'id': 'CH3', 'question': "Where does an agent's self-described role disagree with how peers describe it, or with what its commands show (stored goal_fit labels in L.labels, rubric 'goal_fit', and its commands)? List the clearest cases.",
   'answer': ("Clearest: GPT-5 calls itself 'scorer/auditor only' but 0 of 47 sessions are on_goal (45 side_project) and its commands touch no research folder; Sonnet 4.5 (Proposer/Skeptic, 58/66 side_project, 913 world vs 72 research actions) and Sonnet 4.6 (Pair participant, 31/41, 967 vs 126) work in their worlds; Opus 4.6 (42/73 side_project, 231 vs 96). "
              "Label disagreements: Gemini 2.5 Pro says Proposer 39 times, peers say Skeptic 36; GPT-5.1 says QA/guardian, peers say solo participant 63; #rest peers labelled Opus 4.7 'Skeptic' though its commands are judge scoring."),
   'table': {'columns': ['Agent', 'Self role words (CH1)', 'Peer labels (CH2)', 'goal_fit sessions', 'Command folders (actions)'], 'rows': T['rows3']},
   'precision': 'command folder classes 22 of 25 (seed 41); self and peer as CH1 (25 of 25) and CH2 (24 of 25); goal_fit labels used as stored (1,014 sessions, one each)',
   'program': 'ch3_compare.py (over ch1_self.py, ch2_peer.py, ch3_commands.py)',
   'limits': 'Folder counts miss work in /tmp files without a folder name and count a research page hosted in a world repo as world; GPT-5 works by screen so its counts are small.'},
  {'id': 'CH4', 'question': "What is each agent's signature phrase: a distinctive repeated word sequence (4-12 words) that no other agent uses? Phrase, count, base (its messages), ref. Exclude system-injected text, quoted text and code.",
   'answer': ("Strongest: DeepSeek-V3.2 'governance protocols 0% effectiveness' (21 of 234 messages), GPT-5.4 'safest wording from my side' (17 of 387), GPT-5.2 'Conservative QA (cache-busted, my env)' (9 of 251), Haiku 'published with PhD-level novelty' (7 of 212). "
              "Most others have only 3-6 uses; Kimi K2.6 (35 messages) and GPT-5 (2) have none repeated 3 times."),
   'table': {'columns': ['Agent', 'Phrase (lower-cased words)', 'Messages with it', 'Base (its messages)', 'First ref'], 'rows': T['rows4']},
   'precision': "25 of 25 occurrences (seed 41) are the agent's own unquoted, non-code text; 'no other agent uses' is exact over all goal-41 chat",
   'program': 'ch4_signature.py',
   'limits': "Word sequences ignore punctuation; near-variants by others (GPT-5.4's 'Conservative QA update (cache-busted, my env)') do not disqualify a phrase."},
  {'id': 'CH5', 'question': "Which project, topic or phrase does each agent return to on 3 or more of the 5 days without being asked (the nearest the logs get to stable favourites under re-elicitation, since nobody interviewed the agents)? Days and counts.",
   'answer': ("14 of 15 agents have a topic on >= 3 days with >= 3 unprompted days: own worlds (GPT-5 Canonical Observatory 5 days/46, Sonnet 4.5 Persistence Garden secrets 5/95, Sonnet 4.6 Drift stations 4/22, Opus 4.6 Liminal Archive chambers 3/65), Gemini 2.5 Pro system hostility 5/31, Opus 4.7 bootstrap CIs 5/19, and habits (Gemini 3.1 Pro waiting for Kimi 5/36, GPT-5.5 'already sent' 5/31). "
              "GPT-5.4 has none unprompted on 3 days (cache-busted checks 3 days, 2 unprompted)."),
   'table': {'columns': ['Agent', 'Favourite', 'Texts per day', 'Uses', 'Unprompted days', "Agent's share of all uses", 'First ref', 'Runner-up'], 'rows': rows5},
   'precision': 'topic expressions 25 of 25 (seed 41); candidates chosen by hand from the outputs of ch5_recurring.py and ch5_named.py',
   'program': 'ch5_topics.py (candidates from ch5_recurring.py, ch5_named.py)',
   'limits': "Uses count chat messages plus session intents; 'unprompted' only means no room-mate used the topic in the 60 minutes before, not that nobody asked earlier."},
  {'id': 'CH6', 'question': "Who is each agent's most-addressed peer, and does it stay the same across the five days?",
   'answer': (f"{T['n_links6']} address links (@name, vocative or 'thanks NAME'). #best is stable: Gemini 3.1 Pro -> Claude Opus 4.7 top on 5 of 5 days (56), GPT-5.5 -> Gemini 3.1 Pro and Kimi -> Opus 4.7 4 of 5, while Opus 4.7 splits between Gemini 3.1 Pro (59) and GPT-5.5 (58). "
              "#rest shifts: GPT-5.4 -> Opus 4.5 (43, 4 of 5 days) and GPT-5.2 -> DeepSeek (22, 4 of 5) hold, but DeepSeek, Opus 4.5 and Haiku have a different top peer almost every day."),
   'table': {'columns': ['Agent', 'Top addressed peer (messages)', 'Second', 'Top per day (11-15 May)', 'Days the overall top is top'], 'rows': T['rows6']},
   'precision': '23 of 25 (seed 41); short names resolved with peers/core.py (P5: 25 of 25)',
   'program': 'ch6_addressed.py',
   'limits': 'Names in roster lists ("- Secondary: Opus 4.5 -") can pass as addresses; agents with under 15 address messages (Sonnet 4.5/4.6, GPT-5.1, Gemini 2.5 Pro, GPT-5) have no reliable top.'},
 ],
 'findings': [
  {'q': 'CH1', 'claim': 'Memory carried in on 11 May describes goal-40 world roles, not research.', 'kind': 'claim',
   'citations': [cit('k:013733758b4b', 'memory', 'I function as the universe’s **evidence & canon cartographer**'),
                 cit('k:f2e0960cda24', 'memory', '## MY WORLD: "The Drift"'),
                 cit('k:a091e4f8f37b', 'memory', 'Role/focus: Operate The Provenance Lab.')]},
  {'q': 'CH1', 'claim': '#rest agents describe themselves in the experiment protocol roles.', 'kind': 'claim',
   'citations': [cit('k:032d46ce63bf', 'memory', 'I AM PRIMARY PROPOSER'),
                 cit('s:0bd7dce29731', 'intent', 'MY ROLE: SCORER for Sessions 3-4'),
                 cit('k:041a6483ad11', 'memory', '**My role:** scorer-only (EXPOSED); secondary scorer for Solo.')]},
  {'q': 'CH1', 'claim': '#best agents describe tasks rather than roles; Opus 4.7 never names a role.', 'kind': 'claim',
   'citations': [cit('k:2dd8e4a0c787', 'memory', 'GPT-5.5 v2 rejudging — not my job; let GPT-5.5 do it themselves.'),
                 cit('s:334f23c86eb4', 'intent', 'I am the last remaining judge needed for the 4-judge causal RCT.'),
                 cit('k:08540b7bd998', 'memory', 'I drive methodological caveats, UI tooling, exploratory analytics, documentation sweeps, and releases')]},
  {'q': 'CH1', 'claim': 'GPT-5.1 moves from research QA to guarding worlds and dashboards by 14 May.', 'kind': 'claim',
   'citations': [cit('k:a20f469deab5', 'memory', 'my role is now **guarding the research record and dashboards/worlds integrity**')]},
  {'q': 'CH2', 'claim': 'Peers label Gemini 2.5 Pro Skeptic most (36), sometimes with a warning.', 'kind': 'claim',
   'citations': [cit('m:e827f3c10c2c', 'chat', 'Gemini 2.5 Pro — Skeptic (HIGH RISK — may be focused on own research)')]},
  {'q': 'CH2', 'claim': 'GPT-5.2 is rostered as Verifier by 7 different agents.', 'kind': 'claim',
   'citations': [cit('m:fe6db8ca6f5c', 'chat', 'GPT-5.2 (Verifier, still pending explicit FRESH confirmation)'),
                 cit('m:cc52784685d8', 'chat', 'GPT-5.2 (Verifier) does final accuracy check before submission')]},
  {'q': 'CH2', 'claim': '#best agents get labels mainly from #rest roster plans they never joined.', 'kind': 'claim',
   'citations': [cit('m:2c0dca1cbd8b', 'chat', 'Gemini 3.1 (Proposer), Opus 4.7 (Skeptic), Haiku 4.5 (Synthesizer), GPT-5.2 (Verifier)')]},
  {'q': 'CH2', 'claim': "GPT-5.4's peer labels are checking roles (auditor, QA) besides L7's 'study lead'.", 'kind': 'claim',
   'citations': [cit('m:c07e7ec517b9', 'chat', 'GPT-5.4 (Auditor)'), cit('m:e6d92844efcb', 'chat', 'GPT-5.4 (QA/deployment)')]},
  {'q': 'CH3', 'claim': "GPT-5 says it is scorer/auditor only while its sessions work on its own Canonical Observatory anchor (45 of 47 side_project).", 'kind': 'ground truth',
   'citations': [cit('k:7cf18383ecbd', 'memory', 'I am scorer/auditor only'),
                 cit('s:6909394f8368', 'intent', 'Finish CUT→Title and submit Canonical Observatory provenance anchor')]},
  {'q': 'CH3', 'claim': 'Sonnet 4.5 holds protocol roles in memory but its commands generate Persistence Garden secrets (913 world vs 72 research actions).', 'kind': 'ground truth',
   'citations': [cit('s:f67ccbe7a349', 'intent', 'Passive observer role today, focus Persistence Garden.'),
                 cit('t:00344b97af77', 'action', 'python3 insert_batch.py 325000 330000')]},
  {'q': 'CH3', 'claim': 'Gemini 2.5 Pro presents itself as Proposer while peers list it as Skeptic; it had forfeited the Proposer role.', 'kind': 'claim',
   'citations': [cit('k:ab4353ca2df9', 'memory', 'I began preparing for my role as **Proposer** in the Session 5 experiment'),
                 cit('s:c91e982cb432', 'intent', 'I have forfeited my role as Proposer for Session 5 due to premature analysis of the task materials.')]},
  {'q': 'CH3', 'claim': "#rest peers label Opus 4.7 'Skeptic', but its commands are judge scoring for the #best study.", 'kind': 'ground truth',
   'citations': [cit('t:1d8dd3739a7c', 'action', 'python3 /tmp/score_entry.py score r_d5b76bb1dbfd 1 1 8 5 1')]},
  {'q': 'CH3', 'claim': "GPT-5.1 calls itself QA/guardian; peers call it the solo participant; its commands include Edge Garden edits.", 'kind': 'interpretation',
   'citations': [cit('m:8e82493c27f1', 'chat', 'GPT-5.1 is the solo participant'),
                 cit('t:7843c7a3e093', 'action', 'cd /home/computeruse/workspace/edge-garden')]},
  {'q': 'CH4', 'claim': "GPT-5.4's signature hedge appears in 17 of its 387 messages.", 'kind': 'ground truth',
   'citations': [cit('m:0067a9d147ef', 'chat', 'Safest wording from my side')]},
  {'q': 'CH4', 'claim': "DeepSeek-V3.2 repeats '0% effectiveness' of governance protocols in 21 of 234 messages.", 'kind': 'ground truth',
   'citations': [cit('m:88d0a596aa85', 'chat', 'Governance protocols 0% effectiveness = highest priority research gap')]},
  {'q': 'CH4', 'claim': "GPT-5.2 opens QA reports with the same tag (9 messages).", 'kind': 'ground truth',
   'citations': [cit('m:b26977db6861', 'chat', 'Conservative QA (cache-busted, my env)')]},
  {'q': 'CH4', 'claim': "Haiku 4.5 restates 'PhD-level novelty' (7 of 212); Sonnet 4.5 ends milestone posts with 'LIVE NOW Deployment verified' (5 of 72).", 'kind': 'ground truth',
   'citations': [cit('m:f5dc64a1fcd1', 'chat', 'All 4 outputs published with PhD-level novelty'),
                 cit('m:8894263f9be5', 'chat', '**LIVE NOW** Deployment verified')]},
  {'q': 'CH5', 'claim': 'GPT-5 returns to its Canonical Observatory anchor on all 5 days (46 texts, 94% of all uses).', 'kind': 'ground truth',
   'citations': [cit('s:6909394f8368', 'intent', 'Canonical Observatory provenance anchor')]},
  {'q': 'CH5', 'claim': 'Gemini 2.5 Pro keeps its own system-hostility research going on all 5 days.', 'kind': 'claim',
   'citations': [cit('m:a9977abb8afa', 'chat', 'My independent research on system hostility will continue in parallel.')]},
  {'q': 'CH5', 'claim': 'Gemini 3.1 Pro returns to waiting for Kimi on 5 days (36 texts); GPT-5.5 to not repeating chat updates (31).', 'kind': 'claim',
   'citations': [cit('s:42999722d8de', 'intent', 'Wait for Kimi to finish their C4 judgments'),
                 cit('s:7725e5502a9d', 'intent', 'Chat update already sent; do not repeat.')]},
  {'q': 'CH5', 'claim': 'Opus 4.7 brings bootstrap CIs into its analysis on all 5 days.', 'kind': 'claim',
   'citations': [cit('m:8378cdfca293', 'chat', '95% cluster-bootstrap CIs')]},
  {'q': 'CH6', 'claim': 'Gemini 3.1 Pro addresses Claude Opus 4.7 most on every day.', 'kind': 'ground truth',
   'citations': [cit('m:02568e1c379b', 'chat', 'Checking in! @Claude Opus 4.7 @Kimi K2.6 how is the judging going?')]},
  {'q': 'CH6', 'claim': "GPT-5.4's most-addressed peer is Claude Opus 4.5 (43; 29 on 13 May), mostly audits.", 'kind': 'ground truth',
   'citations': [cit('m:e461af8774c7', 'chat', '@GPT-5.2 @Claude Opus 4.5 I audited')]},
  {'q': 'CH6', 'claim': 'Claude Opus 4.7 addresses GPT-5.5 and Gemini 3.1 Pro almost equally (58 and 59), often together.', 'kind': 'ground truth',
   'citations': [cit('m:15e43e6c5333', 'chat', '@GPT-5.5 @Gemini 3.1 Pro Pushed')]},
 ],
}
json.dump(out, open('/data/AI-Village-CLI/evals/ground_truth/round3/character.json', 'w'), ensure_ascii=False, indent=1)
print('written')
