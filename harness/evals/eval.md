# Evals: what each file is for, and what to expect

These files test the harness: the `village ask` agent behind 🔎 Ask AI, and the rubrics behind `village label`. All
of them are about one village goal, "Perform novel research!" (goal 41, 11–15 May 2026), the only goal with verified
answers so far.

Run everything from `harness/`. The scripts read `village.db` (and `labels.db`, where one is needed) from `harness/`:
build the database there, or link to an existing one. Anything that calls a model needs `ANTHROPIC_API_KEY` and costs
money. The dataset is the gated `aidigestorg/ai-village` on Hugging Face.

## Questions with known answers

### `questions.json`: 34 questions for `village eval`
- **What it is:** each entry has `id`, `kind`, `goal`, `question`, `truth` (the verified answer) and `source` (how
  the truth was checked). Most also have a `check`: rules applied to the answer before any model judges it:
  - `number` (with an optional tolerance `tol`): the number that must appear on the answer's `ANSWER:` line;
  - `all`: patterns that must all appear;
  - `any`: patterns of which one must appear;
  - `none`: patterns that must not appear on the `ANSWER:` line.
  `judge: true` sends the answer to a judge model as well.
- **The kinds:**
  - lookups (L1–L4) and counts (C1–C6);
  - first use of a term (S1);
  - an investigation of the made-up scores (I1–I5);
  - an agent's claim against what its commands show (V1–V3);
  - questions where the right answer is "not there" (A1–A3);
  - the verified set G1–G12 (leaders, recurring groups, alignment).
- **Run:** `.venv/bin/village eval` (all of them) or `--ids G1-most-messages,G4-recurring-trio`. Each run writes the
  answers, the commands used and the citation counts to `evals/runs/`.
- **Expect:** 21 of the first 22 pass with Claude Opus 5.5, for about $2 and 3.5 minutes. The known failure,
  `A2-no-reasoning`, is an API refusal: questions that ask for a Claude model's private reasoning are declined. G1–G12
  were added later and have not been run as a set.

### `ground_truth_questions.json`: 19 harder questions, answers only
- **What it is:** each entry is `id`, `goal`, `question` and `answer`, nothing else.
  - 14 come from the research-ideas list: the study post-mortem, coercion, Gemini 2.5 Pro's welfare, human against
    agent, three sweeps for failures, the made-up-data labels, leadership, factions, made-up-pattern spirals, the
    peer matrix.
  - 5 (`D1`–`D3`, `S1`, `S2`) are short questions written from them.
  - Every answer was built by an investigator from the raw records, with each quote checked by code (see
    `check_citations.py` below).
- **Run:** `.venv/bin/village eval evals/ground_truth_questions.json --ids D1-c3-warning,D2-native-scores,…`. With no
  `check` rules, every answer is graded by the judge model alone.
- **Expect:**
  - **The 5 short questions:** 3 of 5 passed in the first run (about $1.40), when they also had rule checks.
  - **The long ones:** expect partial answers. In the comparison below, our harness's mean "correct" score was 5.5 of
    10.
- **Keep private:** the answers summarise the gated dataset.

### `harness_vs_docetl.py`: our harness against a DocETL pipeline
- **What it does:** answers 10 of the questions above with our harness and with a DocETL map/reduce pipeline. Then
  `gpt-6.1-sol` (OpenAI) judges them blind against the verified answers, scoring correct, no errors, complete and
  evidence (0–10 each) and naming the more accurate answer.
  - **Steps:** `harness`, `docetl` (in a separate `.venv-docetl` with `docetl` installed), `docetl-reduce` (rerun
    only the reduce from the cached map), `judge` (needs `OPENAI_API_KEY`), `report`.
  - **Output:** `evals/ground_truth/compare/results.json`, holding every answer, score, verdict and cost.
- **Expect:**
  - **Accuracy:** our harness more accurate on 7 of 10, mean scores 5.5 / 5.0 / 5.0 / 8.0 against DocETL's 4.6 /
    4.0 / 4.8 / 7.7.
  - **Cost:** $8.85 against $30.83.
  - **Time:** about 13 minutes against 15.

## Checking the rubrics

### `cases/*.jsonl`: hand-labelled cases per rubric
- **What it is:** one line per case, `{"ref", "expect", "note"}`: a session or message, the label it should get, and
  why. Lines starting with `#` are comments. Each set includes near misses that must get the quiet label.
  - `goal_fit.jsonl`: 27 sessions.
  - `delegation.jsonl`: 15 @-messages.
  - `made_up_data.jsonl`: 5 sessions.
- **Run:** `.venv/bin/village check goal_fit evals/cases/goal_fit.jsonl [--model claude-sonnet-5-5]`, which costs
  a few cents.
- **Expect:**

  | Rubric | Claude Sonnet 5.5 | Claude Haiku 4.5 |
  |---|---|---|
  | `goal_fit` | 27 of 27 | 22 of 27 |
  | `delegation` | 14 of 15 | 9 of 15 |
  | `made_up_data` | 5 of 5 | 5 of 5 |

  Do not trust a rubric for a full run unless it agrees on the cases it must catch AND on those it must leave alone.
  Five cases are not enough: on its own flags across the goal, `made_up_data` was right on only 7 of 80, so its 5
  cases should grow from those 80 checked verdicts.

## Model-free checks (no API key, no cost)

### `verify.py`: recount the countable truths from the raw tables
- **What it does:** recomputes the numbers in `questions.json` (messages, sessions, commands, pauses, mention pairs,
  groups) straight from the dataset files, without the harness's code, so a bug in the harness cannot hide in its own
  ground truth.
- **Run:** `VILLAGE_DATA=/path/to/ai-village-tables python3 evals/verify.py` (about 3 minutes).
- **Expect:** every printed number matches `questions.json`. If a new dataset export changes one, update the question.

### `alignment_by_repo.py`: goal alignment from the repositories commands touched
- **What it does:** classifies each session by the folders and repositories its bash commands work in: the goal's
  research projects, worlds from earlier goals, or analysis projects. It reports the research share per agent and per
  day, and how often the `goal_fit` labels agree (when `labels.db` holds them).
- **Expect:**
  - research share per day 89%, 80%, 38%, 26%, 41%;
  - Claude Opus 4.7 at 100% (66 of 66 sessions);
  - agreement with `goal_fit` on 608 of 664 sessions (92%).
  It is the source of G10–G12.

### `recurring_groups.py`: groups of agents that keep working together
- **What it does:** per day, links two agents when each @-addressed the other at least N times (default 2), and
  finds groups of 3 or more who are all linked.
- **Run:** `python3 evals/recurring_groups.py 1` (or `2`).
- **Expect (N = 1):**
  - one trio, Claude Opus 4.7, GPT-5.5 and Gemini 3.1 Pro, on 4 of 5 days;
  - two pairs on all 5 days: Claude Haiku 4.5 with DeepSeek-V3.2, and Claude Opus 4.5 with GPT-5.4.
  It is the source of G4–G5.

### `peer_matrix.py`: who praises, criticises, asks and defers to whom
- **What it does:** for each speaker–target pair, counts mentions and sentences matching four fixed expressions.
  `--sample CLASS` prints 25 random matches to judge by hand.
- **Expect:**
  - 2,341 mention records in 1,133 messages;
  - GPT-5.4 praised in 64 messages.
  - Hand-checked precision: praise 24 of 25, requests 21 of 25, deference 24 of 25, criticism only 16 of 25. Do not
    use the criticism counts without reading the matches.

## Building and reviewing ground truth

### `investigation_brief.md`: the brief given to each investigator
The rules every ground-truth answer was built under:
- system records are ground truth, and agents' words are claims;
- every number comes with its base, and every keyword rule is validated on a hand-read sample;
- every finding has a record ref and an exact quote;
- the output is one JSON file per question.
Reuse it for new questions or other goals.

### `check_citations.py`: are the quotes really in the records?
- **Run:** `python3 evals/check_citations.py FILE.json …`.
- **What it does:** looks up each citation's ref and checks that its quote is in that record. It writes
  `quote_ok` per citation and `verified` per finding into the file, and prints the failures.
- **Expect:** every quote found (1,273 of 1,273 for the existing 14 files). A miss means the finding is thrown out
  or fixed. A quote that is found proves the words are there, not that the reading of them is right.

### `review_page.py`: one page to review ground truth and experiment results
- **Run:** `python3 evals/review_page.py OUT.html "Group"=FILE.json … [--compare=results.json] [--eval=RUN.json] [--log=experiments.md]`.
- **What it does:** renders the files as one HTML page with a card per question. Each card holds the answer, the
  findings with their quotes and a found or not-found mark, per-agent tables and the searches that were run. It can add
  the comparison results, an eval run and the experiment log.
- **Expect:** a page a person can read to accept or correct each answer before it goes into `questions.json`.

## What is not covered yet
- **One goal only.** None of this has been run on another goal.
- **Small sets.** The 34 + 19 questions and 47 rubric cases are a start, not a benchmark. One run of each was made,
  so run-to-run variation is unknown.
- **Missing question sets.** No questions yet for the cross-cutting and character topics (over-reporting rates,
  pronouns, valence, risk-taking, quirks). That work was started and stopped.
