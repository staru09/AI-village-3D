# Harness

The engine behind the site's 🔎 Ask AI. A question goes to Claude with one tool, the `village` CLI. The CLI searches and
reads the AI Village records (chat, computer sessions, commands and their outputs, memories, events), and the answer
cites the records it rests on. The code checks that every ref it cites appeared in a tool result. "What is happening in the
village?" for a given day and time skips the search: one call over that moment's records.

| Path | What |
|---|---|
| `village_graph/llm.py` | the harness: the agent loop (`ask`), the "what is happening" fast path, rubric labelling (`label`, `check`) and `eval` |
| `village_graph/cli.py`, `commands.py`, `evidence.py`, `core.py`, `mentions.py` | the commands the agent can run: search, read, count, sessions, timelines, memory, mention graphs |
| `village_graph/db.py` | builds `village.db` (SQLite) from the dataset |
| `village_graph/web.py`, `web.html` | `village web`: the HTTP endpoint Ask AI calls (`/api/run`), and a page to run commands by hand |
| `rubrics/*.md` | what `village label` asks a model to judge per session or message (goal fit, made-up data, delegation, …) |
| `evals/` | questions with verified answers, rubric test cases, recount scripts and the harness-vs-DocETL comparison; [evals/eval.md](evals/eval.md) explains each file and what to expect |
| `test_village.py` | self-check on a small synthetic database: `python3 test_village.py` prints `ok` |

```bash
cd harness
uv sync --extra llm                                  # Python 3.11+, the Anthropic SDK
VILLAGE_DATA=/path/to/ai-village-tables .venv/bin/village build --all   # every goal: about 30 min, 10 GB
ANTHROPIC_API_KEY=… .venv/bin/village web            # 127.0.0.1:8765; Caddy proxies /api/ to it for Ask AI
.venv/bin/village ask "What is happening in the village?" --date "2026-05-13 11:30"
```

The data is the gated Hugging Face dataset `aidigestorg/ai-village`. No login or rate limit yet: anyone who can reach
`/api/` can spend API credit. The experiments behind this (ground truth, comparisons with DocETL and an RLM, costs)
are in the separate AI-Village-CLI repo (branch `experiments`, `writeup.md`).
