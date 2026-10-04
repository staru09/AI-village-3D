# village-3d todo

**Open** work is at the top and everything already built is in **Done** at the bottom. Item numbers stay the same
in both, so references between items still work. **Decide** marks a choice we still need from you.

**Status (2026-10-04):**
- **Live site:** https://village.gensis-kb-tunnel.com, still built from the old `agent-swarm` copy. Everything newer is
  on the `dev` and `refactor` branches of `AI-village-3D` (see 1.12).
- **Built:** the calendar, player cards, deployment, a lot more from the dataset (rooms, failures, pauses, gallery,
  chat, human messages, mentions), the interface requests of section 8, and the module split.
- **Next:** going live (1.12), livelier agents (section 3), the rest of section 6, across days (section 7), and the
  question-answering engine, goal by goal (section 9).

# Open

## 1. Deployment

- [ ] **1.12 Go live with the new work.** Merge `refactor` into `dev` and `dev` into `main`. Then switch the live site
      and the daily update (`deploy/update.sh`, cron) from the `agent-swarm` copy to `AI-village-3D`.
      The site now lives in `frontend/`: after the merge, move the built `data/` to `frontend/data` (or rebuild).
- [ ] **1.6 Optional:** a GitHub Actions workflow that runs `deploy.sh publish` on the box on every push.
- [ ] **1.7 Frontend production pass.** Pin three.js with SRI or vendor it (it's a pinned jsDelivr version today).
- [ ] **1.8 CI.** On every PR, run `test_extract.py` and a headless smoke test: load a day, expect no console errors.
- [ ] **1.9 Uptime check** for the subdomain.

## 2. Calendar

- [ ] **2.10 Known gaps.**
      - 2026-06-13 (a Saturday special session) has no day number.
      - Some 2025 recaps print times one hour early; the error is in the source summaries.

## 3. Livelier agents (next)

- [ ] **3.1 Reproduce "stuck".** Today each agent holds one spot and one looping animation for a whole 5-minute
      slice: 10 seconds at 0.5 min/s, and indefinitely while paused. Also check pause/resume for a real bug.
- [ ] **3.2 Action stream data.** Store each agent's actions with real timestamps (about 150 KB per busy day) instead
      of one winning building per slice.
- [ ] **3.3 Act out each action at its real time.** (Walking to the Town Hall to say each message is done, see Done.)
      - work at the Workshop for each run of bash
      - climb the Watchtower for GUI runs
      - fetch a book at the Library on a memory update
      - sit at camp when paused

      Stick to the current place for a moment, so agents don't bounce between buildings.
- [ ] **3.4 Workstations.** Several spots per building and varied animations (the characters have 27), so a crowd
      isn't doing one identical move.
- [ ] **3.5 Idle life.** Glance around, wander a little, react when mentioned. Paused means clearly frozen, with a
      paused state on screen.
- [ ] **3.6 Speeds.** Add real time (1×) and 10 s/s. (0.5 min/s exists and is the default now: 6.14, 8.9.)
- [ ] **3.7 Optional:** a small floating screen above an agent showing its current command or page.
- [ ] **3.8 Day and night follow the village clock.** The light changes with the replay time (Pacific time):
      - **Sun:** its height and direction come from the date and hour at the village's real location (California),
        so winter days get dark earlier than summer days.
      - **Colours:** a warm morning, a bright midday, a golden evening, then dusk and night. The sky and fog colours,
        and the strength of the sun and the ambient light, change smoothly with it.
      - **At dusk and at night:** the lanterns, the campfires and the building windows glow.

      Village hours are mostly 9:00 to 18:00 PT, so most of a day is daylight with an evening at the end. Late
      sessions reach dusk. The lights are in `scene.js`.

## 5. Later

- [ ] **5.1 Agent screenshots** from the dataset's per-day image archives (available up to 2026-08-21). Parked for now.

## 6. More from the dataset

Data we download but don't show yet. Checked against the 2026-09-20 export and the dataset's SCHEMA.md.

- [ ] **6.6 (rest) Command replies in the Doing column**, folded under each command. The data is there since 6.23
      (one reply per 5-minute slice, for the command the card shows). Browser actions have no text reply (their
      result was a screenshot; see 5.1).
- [ ] **6.18 Later: more swarm analysis** (on the `data-exploration` branch, next to 6.17). The effect of goals and
      rooms on who talks to whom, ties over time per pair, who answers whom (reply time), human-to-agent mentions as
      a second edge list, and a graph view in the village.
- [ ] **6.19 Small follow-ups to 6.3.** Request counts on the Today tab (help requests, sign-ins, outreach approved or
      declined). `RESTARTING_AFTER_GOOGLE_SIGN_IN` (611 events, one per sign-in) is still left out.

## 7. Across days (later)

- [ ] **7.1 Village history timeline.** The 51 village goals as eras, each agent's join-to-leave lane, click to open a
      day. Data: `index.json` and `village_goals`.
- [ ] **7.2 Agent profile across days.** Activity per day as a small chart, days present, rooms, links shared,
      career. One small per-agent file.
- [ ] **7.3 All-time Hall of Fame.** Totals across the whole run.
- [ ] **7.4 Search across all days.** Too much text for the browser; needs the small API from the notes below.

## 9. Ask the village: a question-answering engine, goal by goal (plan)

Goal: ask a question about the village ("Is the goal being followed?", "Which strategy worked best?", "Why did GPT-5.2
stop the push?") and get a short answer that cites its evidence and links to the moment in the replay. No graph: a
question in, an answer out. **Users:** us first, the public site later (decided 2026-10-03). **The unit is a village
goal** (decided 2026-10-04): every row of the dataset belongs to the goal running when it happened, so a question is
scoped to a goal first, and questions across goals combine several. The day-based items 9.2–9.4 wait for the probe
(9.14). Sizes measured on the built data: a day's core record (agent chat, human messages, requests, recap, goal,
session goals) is median 66k tokens, p90 137k, max 345k. The agents' own notes for a day (memories, reasoning, errors)
add median 164k, max 524k.

- [ ] **9.1 Decide the scope and the budget.**
      - **Questions:** one goal at a time first (decided 2026-10-04), across goals later.
      - **Model and cost cap:** check current Claude models and prices before building.
      - **Spoilers:** answer only from data up to the selected day, or up to the replay clock?
- [ ] **9.2 Day digests (no vector database needed for one day).** `extract.py` writes `data/days/<date>/digest.txt`:
      the day's core record as compact text, one line per event with a stable id (`[09:00:58 GPT-5.2 #general]`). Most
      days fit in one model call. Use prompt caching, so follow-up questions about the same day are cheap.
- [ ] **9.3 Tools for the details (agentic retrieval).** The model gets tools in place of the full notes:
      - `agent_day(slug)`: memory, reasoning excerpts and errors for one agent on that day.
      - `search(query, days)`: full-text search over messages.
      - `actions(slug, from, to)`: commands and session goals in a time range.

      The 345k-token busiest days use the same tools, with the digest cut to the busiest hours.
- [ ] **9.4 Across days (later).** A search index over all messages and summaries: DuckDB full-text search first,
      embeddings only if keyword search is not good enough. Retrieve the top passages, then answer with citations.
      Reuse `mentions.csv` and the daily recaps for "who worked with whom" and "what was the goal then".
- [ ] **9.5 API.** A small FastAPI service on the EC2 box, `POST /api/ask {date, question, until}`. It streams the
      answer, and Caddy proxies `/api/`. The model key stays on the server. This is the "when an API earns its place"
      case from the notes below.
- [ ] **9.6 Interface.** An "Ask" tab next to "Village chat" and "Day recap", scoped to the selected day. Citations
      are clickable: they move the replay to that time and open the big chat at that message.
- [ ] **9.7 Abuse and cost controls (the site is public).**
      - a rate limit per IP
      - Cloudflare Turnstile before the first question
      - a maximum question length
      - cached answers for repeated questions
      - a daily spend cap that turns the tab off when it is reached
- [ ] **9.8 Evaluation.** 30 to 50 questions with known answers from the data (times, who did what, outcomes). Check
      the accuracy and that every citation points at a real line. Run them again after each change.
- [ ] **9.9 Deploy.** A systemd service and an environment file for the key, deployed with `deploy.sh`. The daily
      update rebuilds the digests.
- [ ] **9.10 Split the dataset by goal.** Tag every row with the village goal running at its timestamp (`village_goals`
      start and end times, in UTC, not the day: 9 of the 50 goal changes fall inside village hours, e.g. "Write a story
      and celebrate it…" started 15 May 2025 at 11:00 PT, and the games week on 18 Aug 2025 at 09:08 PT).
      - Rows between two goals (weekends, holidays) go to a "between goals" bucket.
      - The last goal, "Each agent: Maximize your assigned goal!" (from 6 Jul 2026, 55 days, 32 agents, no end time
        yet), splits further by each agent's own goal (`agent_goals`).
      - The site's goal segments (8.1) are whole days; the engine uses the exact times.
- [ ] **9.11 One SQLite database, built on AI-Village-CLI** (github.com/staru09/AI-Village-CLI). It already has: only
      the standard library, the full history in 25 s, careful name matching with tests (GPT-5 is not GPT-5.1), a `--goal`
      filter, and `examples` to list the messages behind any count. It reads chat only. Add sessions (`session_goal`),
      actions (`agent_action`, `output`, `error`, reasoning), memories, events and each turn's screenshot location.
      Drop its graph UI. Its `# graph covers` header ignores the filters (a small fix).
- [ ] **9.12 Evidence tiers.** The dataset's README: "Treat an agent's narration as a claim, not ground truth — check
      the screenshots."

      | Tier | Sources | In an answer |
      |---|---|---|
      | Ground truth | screenshots (all 370 days are in the local HF cache, 160 GB), `agent_action`, `output`, `error`, `events`, goals, agent metadata, who sent which chat message when | what happened |
      | Claims | chat text, `session_goal`, reasoning (`agent_messages`), memories, Claude Code assistant text | quoted as "X said…" |
      | Secondary | `summaries` (written by an LLM that never saw inside computer sessions), `village-transcript.json` (a rendering of the tables) | where to look, never evidence |
- [ ] **9.13 Computer-use data is the main evidence.** Measured on the AI Assistant goal (about 109k turns):
      - 37,404 bash commands: 70% have output, 9% an error. The system's own reply (e.g. a git commit line).
      - About 52,000 clicks, keys and typing with no text reply: the proof is the screenshot.
      - 3,195 `send_message_back_to_chat`: ties each chat message to the reasoning just before it (thought vs said).
      - 483 `search_history`: agents searching village history (the memory-horizon question).
      - Reasoning on 99% of turns, about 1.7k characters each.

      There is no success field: outcomes come from the output, or from a screenshot checked by a vision model when a
      claim needs it. Too big to read per question (about 180M characters of reasoning for this goal): narrow with SQL
      and search first, or use labels (9.15). Older goals have less: the games week (Aug 2025) has no bash at all.
- [ ] **9.14 Probe: which strategy answers best.** **Decide:** start it. Throwaway code, on the last goal with an end
      time: "Compete to be the best AI Assistant!" (29 Jun – 3 Jul 2026, Days 454–458, 21 agents, 3,194 chat messages,
      about 400k tokens; no session reports, they stop in Mar 2026). The same model and about 12 questions for each:
      1. Long context: the goal's chat and each agent's latest memory in one cached prompt.
      2. An agent with read-only `sql`, `search` and `read` tools over the 9.11 database.
      3. Summaries first: 105 agent-day and 5 day summaries, with the same tools to drill down (section 10).

      Grading: AI Digest's goal story and recaps are secondary (9.12), so check their key claims against the actions
      first. A blind judge scores correctness, specificity and citations, and we read the main answers. Report the
      score, cost and seconds per question.
- [ ] **9.15 Research questions as labelling passes** (the "AI Village Data Project Ideas" list). One batch pass per
      question, stored as a table the engine reads with SQL. A detector must first catch false claims we planted or
      verified ourselves, and labels about deception or over-reporting rest on actions, not reasoning.
      - **Need computer-use data:** over-reporting success (split into "done" when the check failed, and "done" when no
        check ran), goal following, planned deception in reasoning, model-spec violations, risk-taking, mantras,
        memory horizon, human vs agent performance.
      - **Chat alone** (AI-Village-CLI covers these): pronouns, term spread (partly), the peer-relationship matrix,
        factions, who mentions or ignores whom.

## 10. Better summaries of what happens in the village (plan)

What exists: AI Digest's own Claude summaries (805 daily recaps, 83 goal stories, 43 careers, 3 checkpoints, 2
agent-days, 3 watch narratives), and the agents' own words (25,939 session reports to Mar 2026, memories, session
goals, reasoning). The gaps: nothing per agent per day after 24 Mar 2026, nothing finer than a day, nothing per chat
room, and the day recap gives the whole day away at 10:00.

**A. Use what we already have better (no new generation)**
- [ ] **10.1 Recap that follows the clock.** The daily recaps are structured: `<narrative_summary>` bullets with
      times (`[17:00:00–17:06:32]`), `<top_moments>` with PT times, `<takeaways>` and a one-line `<blurb>` (797 days).
      We flatten all of it into paragraphs. Instead, show the bullets up to the replay clock ("so far"), and the
      takeaways once the day ends. Check whether the bullet times are UTC or PT first.
- [ ] **10.2 Top moments on the timeline.** A marker on the time slider for each top moment; hover shows it, click
      jumps there.
- [ ] **10.3 Blurbs as day titles.** The blurb as a one-liner in the calendar, the Goals list and the day header.
- [ ] **10.4 Latest report on the Today tab.** The opening of the agent's latest session report in Right now,
      linking to the Reports tab (the "Last report" idea).
- [ ] **10.5 What it learned today.** Compare the agent's first and last memory of the day; show the added and
      dropped lines as "New today" in the Memory tab.

**B. Generate what is missing (Claude, Batch API, offline like `extract.py`, stored as static JSON)**
- [ ] **10.6 Agent-day summaries.** About 4,480 agent-days in all, via the Batch API. The template: the 2
      `agent_daily` rows (Claude Sonnet 4.6, days 325 and 328) and the 3 `watch_narrative` rows (day 329, 56–107k
      characters), which can show on the Today tab as they are; then generated ones in the same form, about 1,500
      characters, as a story. Inputs: its chat, session goals and reports, reasoning, commands with what they printed,
      memory changes. Days from 24 Mar 2026 first: they have no session reports.
- [ ] **10.7 Hourly digests.** One or two sentences per village hour ("At 11:00 the #best agents were…"), shown as a
      ticker while the replay plays.
- [ ] **10.8 Room summaries.** On days with 2–3 chat rooms (99 days), what each room worked on.
- [ ] **10.9 One ladder of summaries.** Hour → agent-day → day → goal or week → career, each made from the level
      below: cheaper, consistent, and the same pieces become the QA bot's digests (9.x).

**C. Make them trustworthy**
- [ ] **10.10 Grounded.** Every claim carries the message id or time it comes from, so the card can link to the
      moment and jump the replay clock there.
- [ ] **10.11 No spoilers.** A summary uses only data up to the end of its own window. Anything written later (the
      careers, the goal stories) stays behind "Show anyway?".
- [ ] **10.12 Checked.** A rubric (accurate, covers the main events, invents nothing, right names and PT times):
      compare our summaries with AI Digest's for the same days, spot-check a sample by hand, and rerun after
      prompt changes.
- [ ] **10.13 Cost and terms first.** Measure the tokens for 20 sample agent-days, then estimate the whole run with
      Batch pricing; check the dataset terms allow publishing generated summaries. The daily update then summarises
      only the new day.

Order: A first (free, about a day of work), then 10.6 on a sample of days, then the rest.

# Reference

## What the data allows

| Fact | Number |
|---|---|
| Days with activity | 389, from 2025-04-02 to 2026-09-18 (2026-09-20 export) |
| Agents per day | 4 early on, about 30 now (46 over the whole run) |
| Village hours per day | 2–5 h through 2025, 9 h lately (read from each day's activity) |
| Built data | 389 day files (135 MB) + 4,483 agent-day files (253 MB); about 390 MB in all |
| Full build | about 4 min, 1.5 GB RAM |
| Summaries | 805 daily (386 dates), 43 agent career, 86 goal stories, 2 agent-per-day, 3 watch narratives |
| Screenshots | up to 2026-08-21 only (not used yet, see 5.1) |

## Notes: why static files and not an API

- **The data doesn't change.** Each dataset export is frozen, and the page reads one day at a time. That's a set of
  files built once.
- **Sizes fit easily.** About 390 MB in total, served compressed; the per-agent files load only on demand.
- **Python is enough for the build.** The full pass takes about 4 minutes and runs once per export. If it ever gets
  slow, reach for DuckDB or multiprocessing before a rewrite. Rust would add a second toolchain, and users would
  never notice the difference.
- **When an API earns its place:** live data from the running village, search or aggregates across all days at
  request time, or per-user permissions. Then use Python (FastAPI plus DuckDB).

# Done

## 1. Deployment

- [x] **1.1 Who can see it: everyone.** The site is public with no login (decided 2026-09-30). The dataset's terms
      ask to cite AI Digest; the ⓘ guide credits them and Kenney.
- [x] **1.2 Hosting.** GitHub is the source of truth. This EC2 box pulls from it and Caddy serves static files on
      127.0.0.1:8080. A Cloudflare Tunnel carries traffic, so there are no public ports and no Elastic IP. No API server.
- [x] **1.3 Box ready.**
      - `sudo deploy/deploy.sh tunnel` has run: Caddy is enabled at boot, localhost only.
      - `deploy/deploy.sh publish [--build]` pulls from GitHub and copies only the page, styles, scripts, models and
        data.
      - Cache headers are set: models for a year, data for an hour, page, styles and scripts `no-cache`.
      - Verified locally.
- [x] **1.4 Cloudflare.** The tunnel `village-3d` runs on this box and routes
      `village.gensis-kb-tunnel.com` → `localhost:8080`. No Access application is needed (public site).
- [x] **1.5 Live:** https://village.gensis-kb-tunnel.com
- [x] **1.10 API: not needed.** The data is a frozen export read one day at a time, so static files are enough.
      Revisit only for live data or search across days (FastAPI + DuckDB), or for section 9.
- [x] **1.11 Daily data update.** A cron job at 04:30 UTC runs `deploy/update.sh`, which rebuilds and publishes only when
      the dataset has a new revision. The first run moved the site to the 2026-09-20 export (389 days, through 2026-09-18).

## 2. Calendar: any day of the village

- [x] **2.1 Extractor for all days.** `extract.py` makes one pass over the tables and writes `data/index.json`,
      `data/days/<date>.json` and `data/days/<date>/<agent>.json`. It uses real Pacific time (zoneinfo), and
      `--since` gives quick dev runs.
- [x] **2.2 Village hours per day from actual activity.**
      - Stray edge hours (a single lone action, e.g. 2026-02-24 07:xx) are trimmed, along with agents seen only in them.
      - Quiet stretches of 30 minutes or more inside a day are skipped while playing.
- [x] **2.3 Clans from `model_string`.** o1/o3/o4-mini → OpenAI, fine-tuned leaders → Moonshot, Claude Code →
      Anthropic. Labels are unique for all 46 agents (GLM labels are `G5.2` and `G5.3F`).
- [x] **2.4 Older regimes.**
      - A slice with only chat puts the agent in the Town Hall.
      - `SEARCH_HISTORY` events before 2026-03-24 count as Library.
      - The Claude Code agent is placed by its own tool calls.
- [x] **2.5 Human messages stay out** (decided). Reversed by 6.2: they are in the chat now.
- [x] **2.6 Calendar UI.** A month grid marking the days with data, with the day number, goal and agent count in
      the tooltip. ◀ ▶ step between days, `?date=` links to one, and it opens on the latest day by default.
- [x] **2.7 Rebuild the scene per day.**
      - Characters, Hall of Records, arcs, counters, feed and hour ticks all follow the day.
      - The town is built once, with camps for all 8 clans.
      - Nothing is left over between days: label counts were checked on every switch.
- [x] **2.8 Day recap.** A tab next to the village chat with the village goal and the daily summary.
- [x] **2.9 Size check.** One day is over 1.5 MB: 2026-07-06 at 1.57 MB (509 KB gzipped).

## 3. Livelier agents

- [x] **3.3 (part) Walk over to talk.** An agent walks to the Town Hall (or the message's room stall) to say each
      message, stays for as long as its bubble shows (3.2 s), then returns to the slice's place.

## 4. Player tags and summaries

- [x] **4.1 Player card** with tabs, opened from the 3D tag, the roster, a chat line or the Hall of Records.
- [x] **4.2 Roster of player tags.** It lists only the agents present that day. Agents who joined earlier but weren't
      there are greyed out ("away today" or "left <date>"); agents who join later aren't listed, so nothing is
      spoiled. Now grouped by maker (8.3, 8.7).
- [x] **4.3 Career tab.** The career summary; if it was written after the selected day, it's locked behind "Show anyway?".
- [x] **4.4 "Thinking | Doing" side by side**, following the replay clock.
      - left: reasoning excerpts and stated intentions
      - right: moves, commands, failures and messages
      - shows the newest 80 items per column
- [x] **4.5 Per-agent-day data**, loaded only when a card opens. It holds the latest memory up to that day (what the
      agent knew then), up to 150 reasoning excerpts and the error texts.
- [x] **4.6 "So far"** on the Today tab: days in the village and total actions and messages up to that day.
- [x] **4.8 Building sign follow-up:** done as 8.13, an "i" on each sign.

## 5. Building guide

- [x] **The ⓘ guide** explains each building, the camps, the Hall of Records, the arcs, the characters, the chat,
      humans, requests, failures, pauses, the gallery and how positions are decided.

## 6. More from the dataset

- [x] **Not worth showing: money, emoji, status message.** SCHEMA.md calls `money` an unused in-village balance and
      `emoji` unused (all 46 agents are 🤖); `status_message` is null for every agent.
- [x] **6.2 Human messages in the Village chat.** Reverses 2.5.
      - 10,049 `USER_TALK` messages: heavy at launch (about 6,650 in Apr–Jun 2025), then roughly 100–750 a month.
        Senders: about 640 viewers (Apr–mid-Aug 2025, while the chat was public), the AI Digest team, and `automated`.
      - Names are shown as posted (decided): the team's names and viewers' chosen nicknames, from the `USER_TALK`
        events (the users table isn't exported). `automated` shows as "⚙️ Village system".
      - In the panel and the big view with their own style: 👤, a grey edge, no player card. The room filter applies;
        the big view's sender filter has a Humans option. "msgs today" still counts agent messages only.
      - In town: a speech bubble over the Town Hall for 3 s. No 3D character and no mention arcs from humans
        (their mentions of agents are stored per message and listed in the big view).
- [x] **6.3 Moments with humans, as lines in the Village chat.** From `events`:

      | Event | Count | Since | Line |
      |---|---|---|---|
      | `REQUEST_HUMAN_HELPER` (+ cancel, stop) | 265 (+ 141, 37) | Aug 2025 | 🙋 asked a human helper, with its short task; the stop line has its end comment |
      | `REQUEST_GOOGLE_SIGN_IN` | 619 | Oct 2025 | 🔑 asked for a Google sign-in |
      | `OUTREACH_APPROVAL_REQUEST` / `_RESPONSE` | 352 / 343 | Apr 2026 (most in Jul) | 📣 asked to contact *recipient* via *medium* → ✅ / ❌ with the reviewer's note |

      - The texts come from the events' own fields (`shortDisplayedSessionGoal`, `endComment`, `recipient`, `medium`,
        `adminComment`), never the raw model `output`; cut to 300 characters.
      - A response's `rationale` repeats the agent's request; the reviewer's reason is `adminComment` (134 of 343).
      - In town the icon pops over the agent (like ❗) and it hurries to the Town Hall (or its room's stall), like for
        a chat message. Lines carry the agent's room from the event (`roomId`; #general before rooms existed).
      - Follow-ups are open as 6.19.
- [x] **6.4 Goal stories.** AI Digest's story of each village goal (83 `goal` + 3 `goal-checkpoint` summaries, all
      matched; every one of the 51 goals has one) in `data/goals.json` (378 KB, loaded after the first day). Hover a
      village goal (Goals list, the goal line under the header, the Day recap) for a preview; 📖 or a click opens the
      whole story. A story written after the selected day is locked behind "Show anyway?", like Career. Day-range
      targets map through the day numbers, slugs by words; `updated_at` is the written date (stories of running goals
      are rewritten).
- [x] **6.20 Whole memories.** The Memory tab shows the agent's notes in full (the 20,000-character cut hid part of
      43% of agent-days). Agent-day files grew by about 45 MB; the largest memory is 942,000 characters (GPT-6 Astra,
      2026-09-07).
- [x] **6.21 Session reports in the data.** 25,937 reports (Apr 2025 – Mar 2026) as `reports: [[v, text]]` in the
      agent-day files (+98 MB, whole).
- [ ] ~~**6.1 Tokens per agent per day.**~~ Dropped 2026-10-03. Events carry `inputTokens`/`outputTokens`, but steps
      inside a computer session have no count, so any sum understates the real spend.
- [x] **6.24 Last thought under each report.** In the Reports tab, under "💭 As it ended the session": the reasoning
      and any visible text of the model call that ended the session (`STOP_USING_COMPUTER.output`), whole. About 7,500
      of the 25,939 reports have one; the others' `output` is empty or only the stop call.
- [x] **6.23 What the command printed.** Under "Last command" in the Today tab's Right now box. It shows stdout,
      then stderr, at most 400 characters, or "(nothing)". Turns use `computer_use_turns.output` and `error`; Claude
      Code commands use their `tool_result` (matched by id, before or after the call). They are stored as `replies` in
      the agent-day files, one per slice, for the command the card shows. No extra redaction: the dataset already
      replaces credentials with `[REDACTED]`.
- [x] **6.22 Reports tab.** A player-card tab after Thinking | Doing: the agent's session reports up to the replay
      clock, newest first. Each sits under the session goal set before it (time span, short goal, then the whole goal).
      Empty states say when no session has ended yet, and that reports stop on 24 Mar 2026.
- [x] **6.7 Chat rooms as places.** 16 rooms since Mar 2026 (`chat_rooms`); 99 days use 2–3 rooms.
      Each extra room gets a market stall north-east of the Town Hall; agents chatting there stand at its stall. The
      Village chat filters by room.
- [x] **6.8 Failures.** A ❗ puff over the agent when an action fails, and the error text in the Doing
      column. A bash turn's `error` field is its stderr, even on success, so bash only counts when the stderr looks like
      a failure (keyword check). "Actions with errors" now uses the same rule.
- [x] **6.9 Pause timers.** "💤 5 min" over a paused agent; pause count and time on the Today tab.
      Source: `PAUSE` events (the pause turns from 2026-03-24 on repeat the same pauses).
- [x] **6.10 Gallery.** A building listing the 12,000 links agents shared in chat, up to the selected day, by site
      (default), goal or agent (`data/gallery.json`). Placeholder, cut-off and `user:token@` links are skipped.
- [x] **6.12 Clearer Village chat.** Sender badges in the panel; ⤢ (or a click on a message) opens a big chat view
      with every message so far today, full text, mentions, and room/agent/text filters. Speech bubbles now sit above
      the name tags.
- [x] **6.13 Every mention draws an arc.** A single mention is enough for a thin arc (before, an unselected pair needed
      2 mentions in the last hour, or 3 in the day). Selecting an agent still shows only its own arcs.
- [x] **6.14 Slower replay.** A 0.5 min/s speed option (30 s of village time per second); the default since 8.9.
- [x] **6.15 Arcs appear the moment a mention is made.** They were recomputed only once per 5-minute slice, so a mention
      could show up to one slice late (10 s at 0.5 min/s).
- [x] **6.16 Mention edge list for swarm analysis.** `extract.py` writes `data/mentions.csv`: one row per agent-to-agent
      mention, all day (not only the replay window), with `date_pt, time_pt, from, to, room, message_id` (slugs as
      in `index.json`; `message_id` joins back to `chat_messages`). 155,293 rows, 46 agents, 1,053 pairs, 17 MB.
- [x] **6.17 Swarm analysis on the edge list** (branch `data-exploration`, `analysis/swarm.py`). Most mentioned
      agents (in total and per day present), top mentioners, strongest ties and reciprocity, hubs (PageRank) and bridges
      (betweenness), Louvain groups over the whole run and per quarter, mentions within vs across makers, rooms.

## 8. Interface requests (2026-10-02 and 2026-10-03)

- [x] **8.1 Browse the village by goal.** The village splits into 51 goal segments (consecutive days with the same
      goal). Pick one in the 🎯 Goals list (8.6, 8.10): ◀ ▶ step inside it, the calendar highlights its days, and
      `?goal=` restores it.
- [x] **8.2 Compact calendar header.** Always "◀ Day N · date · clock 📅 ▶", with the active goal under it (8.12).
- [x] **8.3 Compact players panel.** One row per maker that expands to its player tags; picking an agent anywhere
      opens its maker. Counts and controls as in 8.7 and 8.11.
- [x] **8.4 Agent portrait on the player card.** `portrait.js` renders the agent's own model (skin, shirt colour,
      chest label) once per day into the card head. Only the picture shows: no label plate under it, since the shirt
      already carries the label (the badge shows only while the model loads).
- [x] **8.5 Frontend split into modules** (branch `refactor`). `main.js` (954 lines) became `core.js`, `scene.js`,
      `characters.js`, `arcs.js`, `plaza.js`, `chat.js`, `card.js`, `panels.js` and a 285-line `main.js`. The CSS moved
      to `styles.css`. Plain ES modules, no build step. The loaded day changes only through `setDay()` in `core.js`, and
      other modules read it as live bindings. There are no import cycles. Same behaviour as `dev`: checked line by line,
      with a lint for missing or unused names, and with the same browser session on both branches.
- [x] **8.6 Goals list.** "All days" and the 51 goals with their dates and length; the picked goal is highlighted and
      the 🎯 Goals button turns gold while a goal filter is on.
- [x] **8.7 Maker rows show only a count.** "Anthropic 11": the maker's agents in the village today. Agents who are
      away are mentioned only in the tooltip, and still listed greyed when the maker is opened.
- [x] **8.8 Minimise to a small button.** The fold buttons are "−". A minimised panel becomes a small "💬 Village chat"
      or "👥 Players" button that opens it again.
- [x] **8.9 Default speed 0.5 min/s.** The replay starts at 30 s of village time per second.
- [x] **8.10 Goals as its own button.** "🎯 Goals" is a separate wooden button beside the header (the calendar stays in
      the header), and its list opens under it. On phones the top row holds the header (date and clock), 🎯 and ⓘ.
- [x] **8.11 Players panel controls.** "Show all" is a tilted ⤢, the same as the village chat's, and turns orange
      while every maker is open. Each maker's ⌄ is drawn in CSS and sits level with its count.
- [x] **8.12 No expand arrow on the header.** The ▾ and the expanded header (title, full goal) are gone; the full goal
      text is in the goal line's tooltip and in the Goals list. The Goals list has no hint line under its title.
- [x] **8.13 An "i" on every building sign.** Workshop, Watchtower, Town Hall, Library, Hall of Records, Gallery and the
      chat-room stalls. It opens a small card next to the sign with that building's ⓘ guide entry (one text, two
      places), and closes on Escape or a click elsewhere. A click on the sign itself still flies the camera there.
- [x] **8.14 Counters show and hide.** A round 📊 button beside the counters (top right) shows or hides them. Hidden
      at first, gold while they show, and the choice is remembered in the browser. On phones the 📊 heads the column
      on the right edge.
- [x] **8.15 Move things around.** Drag the calendar header, the 🎯 Goals button, the Players panel and the Village
      chat anywhere (panels by their header). A press that barely moves is still a click, and the end of a drag never
      clicks. Positions are remembered in the browser and kept at least 40 px on screen; the last one dragged comes to
      the front (under the player card). Double-click a panel's header or the Goals button to put it back. The calendar
      and the Goals list open under their moved buttons.
- [x] **8.16 The interface survives a refresh** (this browser only): minimised or open for the Village chat and
      Players, the chat or Day recap tab, the open makers, speed, Mentions, Plaza and Names. Positions (8.15) and the
      counters (8.14) were already kept. `kept()`/`keep()` in `core.js`; blocked storage falls back to the defaults.
