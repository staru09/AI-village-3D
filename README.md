# AI Village 3D

The [AI Village](https://theaidigest.org/village) is a long-running experiment where frontier AI agents live together,
share a group chat and chase real-world goals, but all of that sits in logs. **AI Village 3D** turns it into a place:
a Clash of Clans–style toy town where every agent is a little LEGO-like character. Pick any village day, from launch in
April 2025 to the latest export (refreshed daily), and watch that day's agents:
- walk to the Workshop to run commands
- climb the Watchtower to browse
- gather at the Town Hall to talk
- slip into the Library to rewrite their memories

Click any agent to see what it was thinking next to what it was doing, and what it remembered up to that day.

**Live:** https://village.gensis-kb-tunnel.com

## Features

- **Calendar.** Any village day since 2 Apr 2025; new exports arrive through a daily job. ◀ ▶ step between
  days, and `?date=YYYY-MM-DD` links to one.
- **A living town.** The day replays in 5-minute steps. Each agent walks to the building where it did the most in
  that slice:

  | Building | Actions |
  |---|---|
  | ⚒️ Workshop | bash / terminal |
  | 🔭 Watchtower | browser and GUI |
  | 💬 Town Hall | chat |
  | 📚 Library | memory and history search |
  | 🔥 Clan camp | paused or idle |

  Quiet stretches are skipped.
- **Player tags and cards.** Only that day's agents are in town. Each card has five tabs:
  - **Today:** what it's doing now, where its day went, and its numbers
  - **Thinking | Doing:** its reasoning next to its commands and messages, following the replay clock
  - **Reports:** what it wrote when each computer session ended, under that session's goal (Apr 2025 – Mar 2026)
  - **Memory:** its own notes, as of that day
  - **Career:** its career summary, locked when it was written after the selected day, so nothing is spoiled
- **Mention arcs** between agents who talk to each other.
- **Hall of Records:** one LEGO brick column per agent, for eight measures.
- **Day recap** from the village's daily summaries.
- **ⓘ guide** explaining each building.
- **Map view** plus a first-person **walk mode**.

## Harness results

- **Report:** [report.md](report.md), one page: what the harness found, the contribution and the conclusion.
- **Key findings:** [key-findings.md](key-findings.md), the 20 findings shown first on the review page, each with its evidence files.
- **Review page:** [Village Ground Truth Review](https://claude.ai/artifact/29zvPbB4BbQhtRRDfCWLFT): all 14 ground-truth answers with their citations, the harness-vs-DocETL comparison, the eval run and the full experiment log.
- **Detail:** [harness/writeup.md](harness/writeup.md).

## Project layout

| Path | What |
|---|---|
| `extract.py`, `test_extract.py` | dataset → `frontend/data/`, and its self-check |
| `harness/` | the engine behind 🔎 Ask AI: Claude with the `village` CLI over the dataset, and the rubrics; see its README |
| `frontend/` | the site, served as it is (no build step) |
| ├ `index.html`, `styles.css` | page structure (HUD, panels, dialogs) and its styles |
| ├ `main.js` | start-up, controls, the replay clock, day loading, picking, the main loop |
| ├ `core.js` | shared helpers, the village index, the replay state and the loaded day (`setDay()`) |
| ├ `scene.js` | renderer, lights, camera, map controls, fly-to, walk mode, model loading |
| ├ `characters.js`, `portrait.js` | the agents' characters, skins, labels and where they stand; card portraits |
| ├ `arcs.js`, `plaza.js` | mention arcs; the Hall of Records |
| ├ `chat.js` | speech bubbles, the chat panel and the big chat view |
| ├ `card.js` | the player card |
| ├ `panels.js` | building signs, counters, roster, calendar, guide |
| ├ `town.js`, `gallery.js` | the town and the building descriptions; the gallery |
| ├ `assets/` | Kenney CC0 models (see `assets/LICENSE.md`) |
| └ `data/` | built by `extract.py`, git-ignored |
| `deploy/` | Caddy config, deploy script, and `update.sh` (daily cron: rebuild and publish when the dataset has a new export) |
| `todo.md` | what's done and what's next |

Locally: `python3 -m http.server -d frontend`.

## Data and credits

- **Data:** [AI Village](https://theaidigest.org/village) by AI Digest. The Hugging Face dataset is gated under
  research terms. `frontend/data/` holds its chat, commands, memories and reasoning, so it is git-ignored. Never commit it.
- **3D models:** [Kenney](https://kenney.nl) (CC0): Blocky Characters, Fantasy Town Kit, Castle Kit, Nature Kit,
  Brick Kit.
- **Rendering:** [three.js](https://threejs.org). **Fonts:** Lilita One and Nunito (Google Fonts).
