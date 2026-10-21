#!/usr/bin/env bash
# Runs full_test.py against a throwaway local Swarm Lab server: a temporary Git repository, the offline fake model
# (no API key, no cost; prices are set so the cost reports show numbers), scoped memory, an API key that may write
# profiles, and 127.0.0.1 allowed for the hooks and MCP servers that full_test.py starts itself.
#
#   bash run_full_test.sh                 # uses ../../dist/server/main.js (or $SWARMLAB_SERVER)
#   bash run_full_test.sh --experiment    # also the small experiment
#
# For a real model, use your own server configuration (provider, keys, repositories) and run full_test.py directly.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SERVER="${SWARMLAB_SERVER:-$HERE/../../dist/server/main.js}"
[ -f "$SERVER" ] || { echo "Server not found: $SERVER (build it with npm run bundle, or set SWARMLAB_SERVER)"; exit 1; }
PORT="${PORT:-8797}"
WORK="$(mktemp -d)"
trap 'kill $SP 2>/dev/null || true; rm -rf "$WORK"' EXIT

# A small project to work on.
REPO="$WORK/app"; mkdir -p "$REPO/src"
printf 'def average(n):\n    return sum(n) / len(n)\n' > "$REPO/src/stats.py"
printf '# Demo app\n\nA tiny project for the Swarm Lab full test.\n' > "$REPO/README.md"
git -C "$REPO" init -q -b main && git -C "$REPO" -c user.email=t@t -c user.name=t add -A && git -C "$REPO" -c user.email=t@t -c user.name=t commit -qm init

KEY="sl_fulltest_$(date +%s)"
SHA="$(printf '%s' "$KEY" | sha256sum | cut -d' ' -f1)"
cat > "$WORK/server.json" <<EOF
{
  "host": "127.0.0.1", "port": $PORT, "dataDir": "$WORK/data",
  "repos": { "app": { "path": "$REPO", "baseRef": "main" } },
  "provider": { "type": "mock", "leadModel": "lead-model", "workerModel": "worker-model" },
  "models": { "pool": [ { "id": "lead-model", "tier": "large", "input": 3, "output": 15 }, { "id": "worker-model", "tier": "small", "input": 0.25, "output": 1.25 } ] },
  "memory": { "mode": "scoped" },
  "mcpAllowHosts": ["127.0.0.1"],
  "hooks": { "allowHosts": ["127.0.0.1"] },
  "workers": { "concurrency": 3, "pollMs": 300, "heartbeatSec": 10, "staleSec": 90 },
  "apiKeys": [ { "name": "tester", "sha256": "$SHA", "roles": ["submit", "read", "approve"] } ],
  "approvals": { "edits": "auto", "fileOps": "auto", "commands": "allowlist", "commandAllowList": [], "mcp": "auto", "messages": "off", "timeoutSec": 30 }
}
EOF

node "$SERVER" serve --config "$WORK/server.json" > "$WORK/server.log" 2>&1 & SP=$!
for i in $(seq 1 50); do curl -sf "http://127.0.0.1:$PORT/v1/health" >/dev/null 2>&1 && break; sleep 0.2; done
echo "Server on http://127.0.0.1:$PORT (log: $WORK/server.log)"

OUT="${OUT:-$PWD/swarmlab-reports}"
python3 "$HERE/full_test.py" --url "http://127.0.0.1:$PORT" --key "$KEY" --repo app --out "$OUT" "$@"
echo "Reports in $OUT"
