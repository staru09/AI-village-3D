#!/usr/bin/env bash
# Start a local Honcho (API on http://127.0.0.1:8000) from a pinned clone in honcho/server.
#   honcho/up.sh          # build and start: api, deriver, postgres+pgvector, redis
#   honcho/up.sh down     # stop (add -v to wipe its database, then also delete honcho/out/)
set -euo pipefail
cd "$(dirname "$0")"
PIN=8e4df99  # plastic-labs/honcho commit this was tried with
[ -d server ] || { git clone -q https://github.com/plastic-labs/honcho server && git -C server checkout -q $PIN; }
compose=(docker compose -f server/docker-compose.yml)
[ -f server/docker-compose.yml ] || cp server/docker-compose.yml.example server/docker-compose.yml
if [ "${1:-}" = down ]; then shift; "${compose[@]}" down "$@"; exit; fi
{ cat server.env; echo "LLM_OPENAI_API_KEY=${OPENAI_API_KEY:?set OPENAI_API_KEY}"; } > server/.env
"${compose[@]}" up -d --build --wait api deriver database redis  # not the MCP server
curl -sf http://127.0.0.1:8000/health && echo " Honcho is up on http://127.0.0.1:8000"
