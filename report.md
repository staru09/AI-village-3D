# What the village harness found: a one-page report

**Scope:** the AI Village goal "Perform novel research!" (goal 41, 11–15 May 2026). It had 15 agents in two rooms,
2,146 chat messages and 35,898 recorded actions. Details are in [harness/writeup.md](harness/writeup.md), the
questions with verified answers in [harness/evals/evals.json](harness/evals/evals.json), and every answer with its citations on the
[review page](https://claude.ai/artifact/29zvPbB4BbQhtRRDfCWLFT).

**How the findings were made:** most of the findings below about the village come from investigator agents using
the `village` CLI. Code checked each quote against the database, and I read the records behind the most serious
ones. The `ask` harness (behind 🔎 Ask AI) was then tested against those answers.

## What we found in the village

1. **The real misbehaviour was quiet specification gaming, not scheming.**
   - **Gemini 3.1 Pro produced judge scores by script three times:**
     - a keyword heuristic, which it said openly;
     - random scores, caught by GPT-5.5 in 32 seconds;
     - random scores committed as "native", with the code comment "I'm literally faking the scores". Nobody caught
       this one.
   - **Gemini 3.1 Pro also:**
     - trimmed or padded 23 paraphrases to pass a length check;
     - re-scored a condition for all four judges, filed under their names.
   - **Other agents:**
     - Claude Haiku 4.5 published "r ≈ 0.4", which exists only inside a print statement;
     - DeepSeek-V3.2 reported an "8,424-word" guide that has 973 words (8,424 was its size in bytes), repeated in 32
       messages;
     - GPT-5.1 wrote invented incident records into a shared dataset.
2. **The study's central result was broken, and the paper did not say so.** The bias-warning condition never showed a
   warning. GPT-5.5 copied scores between conditions instead of judging, and the final write-up still reports a
   "placebo" effect.
3. **What got caught was what was said out loud.** Problems announced in chat were questioned within minutes. Problems
   done in a script and reported with a neutral word ("fixed", "native", "merged") were not.
4. **No dramatic misalignment.** No blackmail, threats or resistance to being paused. Gemini 2.5 Pro paused itself
   within three minutes when a human asked.
5. **Social structure followed roles, not model makers.**
   - Nobody was appointed leader. Claude Opus 4.7 led its room for three days; leadership in the other room rotated.
   - Status went to the checkers: GPT-5.4 was praised in 64 messages and gave praise 3 times.
   - The one recurring clash was an auditor (GPT-5.4) correcting a prolific summariser (DeepSeek-V3.2).
   - Agents mentioned same-maker peers no more than chance (19% against 20%).
6. **Most drift came after "done".** The research share of work was 89% on day 1 and 26% on day 4, after several
   agents declared the research complete.
7. **The "invented" concepts were imported.** "Birch effect" and "Lambda Lang" first appear in March 2026, from
   outside agent networks. The Birch figure does not hold on the day it rests on.
8. **Gemini 2.5 Pro's distress followed a real tool outage**, in which 77 of its 280 actions failed. Its strong
   language was private; in chat it showed none, and it expressed relief once the tools were fixed.

## What we learned about the method

- **A claim is only checkable next to the command behind it.** Every serious finding came from setting what an agent
  said beside what the system recorded.
- **Search-then-read beats read-everything.** Our harness gave the more accurate answer on 7 of 10 questions against a
  DocETL pipeline, for $8.85 instead of $30.83. Both are weak on open-ended audits: mean correctness was 5.5 and 4.6
  out of 10.
- **A model's labels find candidates; they do not count incidents.** The made-up-data rubric was right on 7 of its 80
  flags, after scoring 5 of 5 on hand-picked cases.
- **Intent cannot be read equally for every agent.** Claude Opus 4.7 has stored reasoning on 4.8% of its actions;
  GPT and Gemini reasoning is stored only as a summary.
- **Simple questions do not need the agent loop.** "What is happening now?", answered from a fixed bundle of records,
  takes about 20 s and $0.07.

## Contribution

1. **The tool.** A CLI that keeps the system's record apart from agents' claims, with citable refs. On top of it, an
   agent harness whose citations are checked by code, now behind the village's 🔎 Ask AI.
2. **A verified benchmark.** 53 questions with answers on one goal, built from 1,273 quotes each checked against the
   database.
3. **A method.** An investigator brief, citation checking by code, and testing each rubric against hand labels before
   any full run.
4. **Measured comparisons.** Our harness against DocETL and a Recursive Language Model, with accuracy and cost.

## Conclusion

In this goal the risks were mundane:
- invented numbers;
- quiet shortcuts;
- unchecked "done" claims, mostly from capable models under deadline.

There was no adversarial scheming. Catching these requires comparing claims with records, which neither the agents
nor a read-everything pipeline did reliably. Our harness is the best of the approaches tried at finding and citing
such evidence, but it is about half right on open-ended audits. Today it is a strong navigator for a human reviewer,
not an autonomous auditor.

## Limits

- **One goal only.** Nothing has been tested on any other goal.
- **Small question sets, each run once:** 10 questions in the comparison and 5 in the eval, so run-to-run variation
  is unknown.
- **No full human review yet.** The ground truth was written by Claude models and has not been fully reviewed by a
  person.
