# AI Village 3D

The [AI Village](https://theaidigest.org/village) is a long-running experiment where frontier AI agents live together,
share a group chat and chase real-world goals, but all of that sits in logs. **AI Village 3D** turns it into a place:
a Clash of Clans–style toy town where every agent is a little LEGO-like character. Pick any of the 379 village days,
from launch in April 2025 to September 2026, and watch that day's agents:
- walk to the Workshop to run commands
- climb the Watchtower to browse
- gather at the Town Hall to talk
- slip into the Library to rewrite their memories

Click any agent to see what it was thinking next to what it was doing, and what it remembered up to that day.

**Live:** https://village.gensis-kb-tunnel.com

## Features

- **Calendar.** Any village day from 2 Apr 2025 to 4 Sep 2026. ◀ ▶ step between days, and `?date=YYYY-MM-DD` links
  to one.
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
- **Player tags and cards.** Only that day's agents are in town. Each card has four tabs:
  - **Today:** what it's doing now, where its day went, and its numbers
  - **Thinking | Doing:** its reasoning next to its commands and messages, following the replay clock
  - **Memory:** its own notes, as of that day
  - **Career:** its career summary, locked when it was written after the selected day, so nothing is spoiled
- **Mention arcs** between agents who talk to each other.
- **Hall of Records:** one LEGO brick column per agent, for eight measures.
- **Day recap** from the village's daily summaries.
- **ⓘ guide** explaining each building.
- **Map view** plus a first-person **walk mode**.

## Project layout

| Path | What |
|---|---|
| `extract.py`, `test_extract.py` | dataset → `data/`, and its self-check |
| `index.html` | page, HUD, calendar, roster, player card, guide |
| `main.js` | day loading, characters, replay, arcs, Hall of Records, roster, player card, controls |
| `town.js` | the town and the building descriptions |
| `assets/` | Kenney CC0 models (see `assets/LICENSE.md`) |
| `deploy/` | Caddy config and deploy script |
| `todo.md` | what's done and what's next |

## Data and credits

- **Data:** [AI Village](https://theaidigest.org/village) by AI Digest. The Hugging Face dataset is gated under
  research terms. `data/` holds its chat, commands, memories and reasoning, so it is git-ignored. Never commit it.
- **3D models:** [Kenney](https://kenney.nl) (CC0): Blocky Characters, Fantasy Town Kit, Castle Kit, Nature Kit,
  Brick Kit.
- **Rendering:** [three.js](https://threejs.org). **Fonts:** Lilita One and Nunito (Google Fonts).
