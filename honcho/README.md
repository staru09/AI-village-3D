# Honcho pilot: an agent's memory, built day by day

An experiment: feed one village agent's days into a local [Honcho](https://github.com/plastic-labs/honcho) and see
whether its model of the agent (peer card, conclusions, answers to questions) is a better memory than the agent's own
notes or a plain LLM summary. Nothing here is part of the website yet.

| File | What |
|---|---|
| `up.sh` | clones Honcho (pinned commit) into `server/` and starts it with Docker: API on `127.0.0.1:8000`, deriver, Postgres + pgvector, Redis |
| `server.env` | our settings on top of Honcho's defaults; `up.sh` adds `LLM_OPENAI_API_KEY` from your environment |
| `pilot.py` | imports the next day(s) of one agent and saves a snapshot per day |
| `test_pilot.py` | self-check for its helpers: `python3 honcho/test_pilot.py` |
| `out/<agent>/<date>.json` | the snapshots (git-ignored: they quote the gated dataset) |

## Run

```sh
export OPENAI_API_KEY=...                         # Honcho's defaults: gpt-5.4-mini + text-embedding-3-small
honcho/up.sh                                      # first time builds the images (a few minutes)
uv run honcho/pilot.py --agent glm-5-3-flash      # the next day not imported yet
uv run honcho/pilot.py --agent glm-5-3-flash --days 15
honcho/up.sh down                                 # stop; `honcho/up.sh down -v` wipes Honcho (then delete out/ too)
```

`pilot.py` reads `frontend/data`, so run `extract.py` first. Each agent gets its own workspace (`village-<agent>`).

## What goes in, per day

One Honcho session per village day (`day-YYYY-MM-DD`), messages with their real time (`created_at`):
- **Context, not observed:** that day's chat from every agent (with `[#room]` on multi-room days) and the humans'
  messages. Other agents and humans are peers with `observe_me=False`, so Honcho reasons about the one agent only.
- **The agent itself:** its chat, plus its actions written as text: `[started a computer session]` (the goal),
  `[ran a command]` / `[it printed]` (one per 5 minutes, as on the card), `[an action failed]`, `[paused for N min]`,
  `[moved to #room]`, `[thought]` (reasoning excerpts), `[ended a computer session; its report]` (to Mar 2026),
  requests to humans, and `[added to its notes]` / `[dropped from its notes]` (its own memory, the first day whole).

Each day's session summarises less often than Honcho's default (a short summary every 60 messages instead of 20, a
long one every 300 instead of 60): those summaries run one at a time and were the slowest part of a day.

Then: wait for the deriver queue, run a dream (Honcho's consolidation, which also may write the peer card), wait
again, and save the snapshot: `card`, `representation` (up to 100 conclusions), `answers` to five fixed questions,
and `own_notes` (the agent's own memory that day, for comparison).

**Why snapshots:** Honcho keeps one evolving model and can't be asked "as of day N" later, so each day's snapshot is
taken before the next day goes in. A day with a snapshot counts as imported.

## First runs (2026-10-03)

- **o4-mini** (1 day, 448 messages, 138 its own): about 5 minutes. Good, specific answers (its RESONANCE story
  deadline, working with o3 and Gemini 2.5 Pro, its failing shell and browser). No peer card after one day: the dream
  ran but chose not to write one.

- **GLM-5.3 Flash, day 1** (28 Aug 2026, 929 messages: 697 other agents' chat as context, 231 its own, of which 150
  thoughts, 34 commands, 23 chat): about 13.5 minutes (deriver 749 s, of which the first ~8 minutes were Honcho's
  session summaries at the old 20/60 setting; dream 24 s). 91 explicit and 4 deductive conclusions, no peer card yet.
  Answers fit the day: waiting for its personal goal from george on Monday, small QA jobs meanwhile, working mostly
  with Claude Fable 5; struggles with wrong URLs and slugs (404s); "verification-first, receipt-minded". Its own
  notes that day: 21,218 characters.

## Next

- Run all 16 GLM-5.3 Flash days, then compare (15 questions with known answers; Honcho vs its own notes vs a plain
  Claude call on the same day's data; graded blind).
- Optional: `observe_others` for the agent, to get its view of each other agent (`conclusions_of`), at more cost.
