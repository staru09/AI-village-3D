# village-3d todo

Your four items, split into small issues. **Decide** marks a choice we still need from you.

**Status:**
- 2 (calendar) and 4 (player tags and summaries) are **done**, plus the building guide.
- 1 (deployment) is live at https://village.gensis-kb-tunnel.com.
- 3 (livelier agents) is next.
- 6 (more from the dataset): rooms, failures, pauses, gallery and the chat view are done; tokens, humans, goal
  stories and command replies are planned; 6.2 needs a decision.

## What the data allows

| Fact | Number |
|---|---|
| Days with activity | 389, from 2025-04-02 to 2026-09-18 (2026-09-20 export) |
| Agents per day | 4 early on, about 30 now (46 over the whole run) |
| Village hours per day | 2–5 h through 2025, 9 h lately (read from each day's activity) |
| Built data | 389 day files (131 MB) + 4,483 agent-day files; 368 MB in all |
| Full build | about 4 min, 1.5 GB RAM |
| Summaries | 805 daily (386 dates), 43 agent career, 86 goal stories, 2 agent-per-day, 3 watch narratives |
| Screenshots | up to 2026-08-21 only (not used yet, see 5.1) |

## 1. Deployment

- [x] **1.1 Who can see it: everyone.** The site is public with no login (decided 2026-09-30). The dataset's terms
      ask to cite AI Digest; the ⓘ guide credits them and Kenney.
- [x] **1.2 Hosting.** GitHub is the source of truth. This EC2 box pulls from it and Caddy serves static files on
      127.0.0.1:8080. A Cloudflare Tunnel carries traffic, so there are no public ports and no Elastic IP. No API server.
- [x] **1.3 Box ready.**
      - `sudo deploy/deploy.sh tunnel` has run: Caddy is enabled at boot, localhost only.
      - `deploy/deploy.sh publish [--build]` pulls from GitHub and copies only the page, scripts, models and data.
      - Cache headers are set: models for a year, data for an hour, page and scripts `no-cache`.
      - Verified locally.
- [x] **1.4 Cloudflare.** The tunnel `village-3d` runs on this box and routes
      `village.gensis-kb-tunnel.com` → `localhost:8080`. No Access application is needed (public site).
- [x] **1.5 Live:** https://village.gensis-kb-tunnel.com
- [ ] **1.6 Optional:** a GitHub Actions workflow that runs `deploy.sh publish` on the box on every push.
- [ ] **1.7 Frontend production pass.** Pin three.js with SRI or vendor it (it's a pinned jsDelivr version today).
- [ ] **1.8 CI.** On every PR, run `test_extract.py` and a headless smoke test: load a day, expect no console errors.
- [ ] **1.9 Uptime check** for the subdomain.
- [x] **1.11 Daily data update.** A cron job at 04:30 UTC runs `deploy/update.sh`, which rebuilds and publishes only when
      the dataset has a new revision. The first run moved the site to the 2026-09-20 export (389 days, through 2026-09-18).
- [x] **1.10 API: not needed.** The data is a frozen export read one day at a time, so static files are enough.
      Revisit only for live data or search across days (FastAPI + DuckDB).

## 2. Calendar: any day of the village (done)

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
- [x] **2.5 Human messages stay out** (decided). Reopened as 6.2.
- [x] **2.6 Calendar UI.** A month grid marking the days with data, with the day number, goal and agent count in
      the tooltip. ◀ ▶ step between days, `?date=` links to one, and it opens on the latest day by default.
- [x] **2.7 Rebuild the scene per day.**
      - Characters, Hall of Records, arcs, counters, feed and hour ticks all follow the day.
      - The town is built once, with camps for all 8 clans.
      - Nothing is left over between days: label counts were checked on every switch.
- [x] **2.8 Day recap.** A tab next to the village chat with the village goal and the daily summary.
- [x] **2.9 Size check.** One day is over 1.5 MB: 2026-07-06 at 1.57 MB (509 KB gzipped).
- [ ] **2.10 Known gaps.**
      - 2026-06-13 (a Saturday special session) has no day number.
      - Some 2025 recaps print times one hour early; the error is in the source summaries.

## 3. Livelier agents (next)

- [ ] **3.1 Reproduce "stuck".** Today each agent holds one spot and one looping animation for a whole 5-minute
      slice: 5 seconds at 1 min/s, and indefinitely while paused. Also check pause/resume for a real bug.
- [ ] **3.2 Action stream data.** Store each agent's actions with real timestamps (about 150 KB per busy day) instead
      of one winning building per slice.
- [ ] **3.3 Act out each action at its real time.**
      - [x] walk to the Town Hall (or the message's room stall) to say each message: done. The agent hurries over
        for as long as its bubble shows (3.2 s), then returns to the slice's place.
      - work at the Workshop for each run of bash
      - climb the Watchtower for GUI runs
      - fetch a book at the Library on a memory update
      - sit at camp when paused

      Stick to the current place for a moment, so agents don't bounce between buildings.
- [ ] **3.4 Workstations.** Several spots per building and varied animations (the characters have 27), so a crowd
      isn't doing one identical move.
- [ ] **3.5 Idle life.** Glance around, wander a little, react when mentioned. Paused means clearly frozen, with a
      paused state on screen.
- [ ] **3.6 Speeds.** Add real time (1×) and 10 s/s; retune the default.
- [ ] **3.7 Optional:** a small floating screen above an agent showing its current command or page.

## 4. Player tags and summaries (done)

- [x] **4.1 Player card** with tabs, opened from the 3D tag, the roster, a chat line or the Hall of Records.
- [x] **4.2 Roster of player tags.** It lists only the agents present that day.
      - A clan filter; the clan chips double as the legend.
      - Agents who joined earlier but weren't there are greyed out ("away today" or "left <date>").
      - Agents who join later aren't listed, so nothing is spoiled.
- [x] **4.3 Career tab.** The career summary; if it was written after the selected day, it's locked behind "Show anyway?".
- [x] **4.4 "Thinking | Doing" side by side**, following the replay clock.
      - left: reasoning excerpts and stated intentions
      - right: moves, commands and messages
      - shows the newest 80 items per column
- [x] **4.5 Per-agent-day data**, loaded only when a card opens. It holds the latest memory up to that day (what the
      agent knew then) and up to 150 reasoning excerpts.
- [x] **4.6 "So far"** on the Today tab: days in the village and total actions and messages up to that day.
- [ ] **4.7 Decide: generate per-agent daily summaries with Claude?** Only 2 exist today. Covering every agent-day is
      roughly 4,165 summaries via the Batch API. Check the cost and the dataset terms first.
- [ ] **4.8 Small follow-up:** clicking a building sign could open the ⓘ guide at that building (today it flies there).

## 5. Later

- [x] **Building guide.** The ⓘ button explains each building, the camps, the Hall of Records, the arcs, the
      characters and how positions are decided.
- [ ] **5.1 Agent screenshots** from the dataset's per-day image archives (available up to 2026-08-21). Parked for now.

## 6. More from the dataset

Data we download but don't show yet. Checked against the 2026-09-20 export and the dataset's SCHEMA.md.

- [ ] **6.1 Tokens per agent per day.**
      - The agent totals (`agents.input_tokens_used`, `output_tokens_used`) are lifetime counters as of the export,
        and SCHEMA.md says they aren't reliably maintained. They can't be split by day.
      - Per-day numbers do exist: most `events` carry `inputTokens` and `outputTokens`. Sum them per agent per PT day
        (one more counter in the events pass `extract.py` already makes).
      - The sums are close to the lifetime counters for recent agents (GPT-5.5: 99%) and far off for some early
        ones (Grok 4: 10%). So label them "tokens on village actions", not total spend.
      - Claude Code agents: check whether `claude_code_messages` carries usage numbers.
      - Show: tokens today and so far on the Today tab, and a Tokens measure in the Hall of Records.
- [x] **Not worth showing: money, emoji, status message.** SCHEMA.md calls `money` an unused in-village balance and
      `emoji` unused (all 46 agents are 🤖); `status_message` is null for every agent.
- [ ] **6.2 Decide: human messages in the Village chat.** Reverses 2.5.
      - 10,000 messages: heavy at launch (about 6,650 in Apr–Jun 2025), then roughly 100–750 a month.
      - Names come from the `USER_TALK` events (the users table isn't exported). **Decide:** show viewers' chosen
        names, or a plain "viewer" label? The site is public.
      - Show: in the feed with their own style (no clan colour, 👤). No 3D character; mentions of an agent could
        still draw an arc from the Town Hall.
- [ ] **6.3 Moments with humans, as lines in the Village chat.** From `events`:

      | Event | Count | Since | Line |
      |---|---|---|---|
      | `REQUEST_HUMAN_HELPER` (+ cancel, stop) | 265 | Aug 2025 | 🙋 asked a human helper, with its task |
      | `REQUEST_GOOGLE_SIGN_IN` | 619 | Oct 2025 | 🔑 asked for a Google sign-in |
      | `OUTREACH_APPROVAL_REQUEST` / `_RESPONSE` | 352 / 343 | Apr 2026 (most in Jul) | 📣 asked to contact *medium* → ✅ / ❌ with the reason |

      - Also flash the icon above the agent's head at that moment (ties into 3.3).
      - Counts on the Today tab: help requests, sign-ins, outreach approved/declined.
      - Check how much reasoning sits in the raw `output` field; keep only the request text, not the model output.
- [ ] **6.4 Goal stories in the Day recap.** 83 `goal` summaries plus 3 `goal-checkpoint` summaries: one long
      narrative per village goal (4–24k characters), written by Claude Sonnet.
      - Map each to its village goal. 33 targets are day ranges (`216-217`), which map through the day numbers. The rest
        are slugs with stopwords dropped (`choose-charity-raise-much-money-you-can`); match them on words.
        70 distinct targets, so some goals have several versions: take the latest.
      - Show under the daily recap as "The story of this goal", locked when written after the selected day (like
        Career). Checkpoints carry a `summary_date`, so they unlock on that date.
      - Store once in `index.json` or a `data/goals/` file, not in every day file.
- [ ] **6.5 Day stories on the player card.** 3 `watch_narrative` rows (day 329, GPT-5.1 and Claude Opus 4.6) and
      2 `agent_daily` rows (Claude Sonnet 4.6, days 325 and 328).
      - Put them in that agent-day file and show them on the Today tab when present.
      - The watch narratives are 56–107k characters: show the opening paragraphs, with "Read more".
      - Too few to matter on their own; they are the format 4.7 would generate for every agent-day.
- [ ] **6.6 Command replies in the Doing column.** `computer_use_turns.output` and the Claude Code `tool_result`
      messages (matched to their command by id).
      - Cap at 400 characters, folded under each command, stored in the agent-day files: about +35 MB in all, about
        8 KB more per opened card. Day files stay the same.
      - No extra redaction needed: the dataset already replaces credentials with `[REDACTED]` (checked on a sample).
      - Browser actions have no text reply (their result was a screenshot; see 5.1).
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
- [ ] **6.11 Later: what it learned today.** Compare an agent's first and last memory version of the day and show
      the added and dropped lines as "New today" in the Memory tab.

## 7. Across days (later)

- [ ] **7.1 Village history timeline.** The 51 village goals as eras, each agent's join-to-leave lane, click to open a
      day. Data: `index.json` and `village_goals`.
- [ ] **7.2 Agent profile across days.** Activity per day as a small chart, days present, rooms, links shared,
      career. One small per-agent file.
- [ ] **7.3 All-time Hall of Fame.** Totals across the whole run.
- [ ] **7.4 Search across all days.** Too much text for the browser; needs the small API from the notes below.

## Notes: why static files and not an API

- **The data doesn't change.** Each dataset export is frozen, and the page reads one day at a time. That's a set of
  files built once.
- **Sizes fit easily.** About 350 MB in total, served compressed; the per-agent files load only on demand.
- **Python is enough for the build.** The full pass takes about 4 minutes and runs once per export. If it ever gets
  slow, reach for DuckDB or multiprocessing before a rewrite. Rust would add a second toolchain, and users would
  never notice the difference.
- **When an API earns its place:** live data from the running village, search or aggregates across all days at
  request time, or per-user permissions. Then use Python (FastAPI plus DuckDB).
