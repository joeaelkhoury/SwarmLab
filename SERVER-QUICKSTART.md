# Swarm Lab server: run it and test it, step by step

## Public VSIX users: start here, without source

The public release supplies an installable VSIX, documentation, and Python starters;
extension source publication is planned for a later update. No source ZIP or npm
build is required to run the native server bundled with the installed extension.
Docker is optional.

1. Open your practice Git project in VS Code and open Swarm Lab.
2. Save a supported API/local provider and models in Setup; save its key if needed.
   VS Code language models are not available to a standalone server. Offline mock
   is scripted demonstration only, not evidence of real-model correctness.
3. Choose **Server → Start local server**. The first click creates/opens server
   configuration; review it, then click again. The launcher forwards supported
   saved provider credentials to the child without writing them into configuration.
4. Review registered repository names/paths, an existing commit/base reference,
   permissions and approvals. Install the project's dependencies on the host.
   Restart after changing provider/model settings.
5. Save/test the Server connection. Keep the generated unauthenticated configuration
   loopback-only; configure authentication and network/TLS protections before sharing.

Follow [Python workflows](docs/PYTHON-WORKFLOWS.md) for the separate downloadable
starter files, offline previews, environment credentials, and approval handling.
Example payloads use demo-app; configure that repository name or override it.
Worktrees use committed files and are not an operating-system sandbox.
See the [Manual](MANUAL.md) for the full reference or [README](README.md) to begin.

## Developer-only reference below

**The remaining source-build and full-test instructions require a separately
available full developer checkout. They cannot be run from the minimal public
binary/documentation repository. The full test Python/shell scripts are not public
starter prerequisites.** The original detailed reference is retained below.

This developer guide takes you from an available source zip to a running Swarm Lab server, tested end to end with the full test script:
agents and prompts set from a script, single, swarm and workflow jobs, shared memory, MCP servers, skills, hooks,
profiles, reports and costs. Part A needs no API key and costs nothing (it uses an offline fake model). Part B runs your
own server with a real model.

---

## 0. What you need

| | Version | Check with |
|---|---|---|
| Node.js | 18 or newer (tested with 22) | `node --version` |
| npm | comes with Node.js | `npm --version` |
| Git | any recent version | `git --version` |
| Python | 3.8 or newer (only the standard library) | `python3 --version` |
| curl | any | `curl --version` |

**Operating system:** Linux, macOS, or Windows through WSL. On **macOS**, `run_full_test.sh` uses `sha256sum`: install
it with `brew install coreutils`, or replace `sha256sum` with `shasum -a 256` in the script. On **Windows**, run
everything inside WSL (Ubuntu).

---

## 1. Get the source and build the server

```bash
unzip swarm-lab-source.zip
cd swarm-lab
npm ci             # installs the dependencies (about a minute)
npm run bundle     # builds dist/extension.js (VS Code) and dist/server/main.js (the server)
```

Check that it worked:

```bash
node dist/server/main.js help
```

You should see the list of commands (`init`, `check`, `serve`, `experiment`, `hash-key`…).

> 💡 Optional: make a short alias for the rest of this guide:
> `alias swarm-lab="node $PWD/dist/server/main.js"` (Linux and macOS).

Optional, to be sure everything is fine: `npm test` runs every test suite (a few minutes). Every line should end in
`ok`, and each suite with `… checks passed.` (the PostgreSQL suite says `skipped` unless you give it a database).

---

## Part A: the five-minute test (offline, no key, no cost)

### A1. Run the test

From the `swarm-lab` folder:

```bash
bash clients/python/run_full_test.sh
```

What the script does, by itself:

1. Creates a small temporary Git repository to work on.
2. Writes a temporary server configuration: the **offline fake model** (with example prices, so the cost reports show
   numbers), scoped memory, an API key that may write profiles, and `127.0.0.1` allowed for hooks and MCP servers.
3. Starts the server on port 8797 and waits until it answers.
4. Runs `clients/python/full_test.py` against it, which:
   - starts a small **MCP server** and a **hook receiver** inside the script;
   - saves a **profile** on the server: agents, prompts, a skill, the check of "done", the hooks and the MCP server;
   - runs a **single** job, then a **swarm** and a **graph** (workflow) job, all from that profile and sharing one
     **memory** session;
   - prints and saves each job's **report**, what the **hooks** saw and blocked, what the **MCP server** served, and the
     **usage** by mode, model and label.
5. Stops the server and deletes the temporary files (the reports are kept).

### A2. What you should see

```text
Server on http://127.0.0.1:8797 (log: /tmp/…/server.log)
local MCP server http://127.0.0.1:…/mcp · hook receiver http://127.0.0.1:…/hook
profile 'full-test' saved (…); profiles on the server: full-test
submitted single …
submitted swarm  …
submitted graph  …
single succeeded     2,536 tokens  $0.0093
swarm  succeeded    32,870 tokens  $0.0246
graph  succeeded    12,361 tokens  $0.0035

Reports
  single 3 calls · … · 1 blocked by hooks · memory used 0 → swarmlab-reports/single-….md
         blocked: hook denied list_files: Listing every file is not allowed in this test: read README.md instead.
  swarm  16 calls · … · 2 blocked by hooks · memory used 1 → swarmlab-reports/swarm-….md
  graph  9 calls · … · 3 blocked by hooks · memory used 1 → swarmlab-reports/graph-….md

Hooks: 54 calls, all signed: True · after:call 28, before:tool 23, job:end 3 · list_files denied 6×
MCP server: initialize, notifications/initialized, tools/list (9 requests)
…
Reports in …/swarmlab-reports
```

The exact numbers vary a little. What matters:

- the three jobs **succeeded**;
- the swarm and graph jobs show **memory used 1** (the single job's progress note, through the shared session);
- **blocked by hooks** and **list_files denied**: the hook receiver blocked a tool, and the agents got its reason;
- **all signed: True**: every hook call carried a valid signature;
- the **MCP server** was reached (`tools/list`).

The script exits with code 0 when all of this worked, 1 otherwise.

### A3. Look at the results

```bash
ls swarmlab-reports
```

- `single-….md`, `swarm-….md`, `graph-….md`: one full report per job. Open one: totals, a table by agent and by model
  (calls, tokens, cost, time), the memory used, then **every step** in order (model calls, tools, hooks, edits…).
- `usage-by-kind.md`: tokens and cost of the three jobs, by kind.
- `usage-by-day.csv`: usage by day, for a spreadsheet.

### A4. Variants

```bash
bash clients/python/run_full_test.sh --experiment       # also a small experiment: single vs swarm, with a cost limit
PORT=8798 bash clients/python/run_full_test.sh          # if port 8797 is taken
OUT=$HOME/sl-reports bash clients/python/run_full_test.sh   # reports somewhere else
```

---

## Part B: your own server, with a real model

### B1. Write a configuration

```bash
cd swarm-lab
node dist/server/main.js init swarmlab.server.json
```

This writes an example configuration. Open `swarmlab.server.json` and edit it as below.

**The model provider.** Pick one, and put the key in an environment variable (never in the file):

```json
"provider": { "type": "anthropic", "apiKeyEnv": "ANTHROPIC_API_KEY", "leadModel": "claude-sonnet-5-5", "workerModel": "claude-haiku-5-5" }
```

```json
"provider": { "type": "openrouter", "apiKeyEnv": "OPENROUTER_API_KEY", "leadModel": "<an OpenRouter model id>", "workerModel": "<a cheaper one>" }
```

```json
"provider": { "type": "openai", "baseUrl": "http://localhost:11434/v1", "apiKeyEnv": "LLM_API_KEY", "leadModel": "your-model", "workerModel": "your-model" }
```

(The last one is any OpenAI-compatible endpoint: Ollama, vLLM, LM Studio, a company gateway.)

**Your repositories.** Each one a name and a local path (or a `url` the server clones):

```json
"repos": { "app": { "path": "/home/me/code/my-app", "baseRef": "main" } }
```

**Prices**, so costs and cost limits work (USD per million tokens; use your provider's real prices):

```json
"models": { "pool": [
  { "id": "claude-sonnet-5-5", "tier": "large", "input": 0, "output": 0 },
  { "id": "claude-haiku-5-5", "tier": "small", "input": 0, "output": 0 }
] }
```

**Memory for every job** (optional; without it, only jobs that ask for `memory` get it):

```json
"memory": { "mode": "scoped" }
```

**For the test script** (Part B4) also allow its local MCP server and hook receiver, and let MCP tools run without an
approval:

```json
"mcpAllowHosts": ["127.0.0.1"],
"hooks": { "allowHosts": ["127.0.0.1"] }
```

and in `"approvals"`, set `"mcp": "auto"`.

### B2. Make an API key

```bash
node dist/server/main.js hash-key
```

It prints a **key** (`sl_…`, for you and your scripts) and its **sha256** (for the configuration). Put the sha256 in
`apiKeys`:

```json
"apiKeys": [
  { "name": "me", "sha256": "<the sha256>", "roles": ["admin"] },
  { "name": "ci", "sha256": "<another sha256>", "roles": ["submit", "read"] }
]
```

Roles: `read` (see jobs and reports), `submit` (run jobs and experiments), `approve` (answer approvals, write
profiles), `admin` (everything, including local MCP programs). The test script needs a key with `approve` or `admin`.

Keep the key itself somewhere safe, for example:

```bash
export SWARMLAB_KEY=sl_…
```

### B3. Check and start

**From VS Code:** choose your provider and lead/worker models in Swarm Lab Setup → **Save settings**, and save your provider key once through **Set API key**. Each **Start local server** synchronizes the saved provider, base URL (OpenAI-compatible/Anthropic), network proxy, and lead/worker models into `swarmlab.server.json`, including model defaults for dashboard jobs. Repositories, server access controls, storage, limits, decisions, embeddings, routing strategies and other settings remain server-managed. Connection-specific headers/body overrides are cleared so old provider options cannot leak across provider switches. Explicit job/profile/agent models and configured automatic routing may still select other models. VS Code language models cannot run in the standalone server: choose an API provider or Offline mock instead.

The launcher forwards that provider's saved key to both configuration checking and the child server. Saved keys take precedence over inherited environment values. No key is written to the configuration or command arguments. Stop and restart the local server after changing Setup or a key; starting an already-running server does not interrupt its jobs or hot-reload settings.

Choosing OpenRouter in Setup sets `provider.type` to `openrouter` and `provider.apiKeyEnv` to `OPENROUTER_API_KEY` automatically. OpenRouter decisions can use that same variable (or their own variable, populated with the same saved OpenRouter key). OpenRouter embeddings can use it too when their embedding base URL explicitly points to `https://openrouter.ai/api/v1`. Distinct providers/custom endpoints retain their own credentials; automatic forwarding of a saved OpenRouter key to a different host is rejected. The dashboard's server access key (`sl_…`) is separate and must not be replaced with your OpenRouter key.

**Standalone or remote server:** it cannot read VS Code Secret Storage. Supply the provider key through its environment as below. Setup synchronization only happens when the extension starts its local server; it does not reconfigure a remote server or a process launched independently. The synchronized local JSON keeps its updated model selection for later standalone launches, but secrets still require environment provisioning.


```bash
export ANTHROPIC_API_KEY=…          # the variable named in provider.apiKeyEnv
node dist/server/main.js check --config swarmlab.server.json
node dist/server/main.js serve --config swarmlab.server.json
```

`check` lists anything wrong (a missing key variable, a repository path that does not exist…) before you start.
`serve` runs the API and the workers in one process and prints `API on http://127.0.0.1:8787 …`.

Open **http://127.0.0.1:8787/** in a browser: that is the dashboard. Paste your key (`sl_…`) in its key box.

> ⚠️ The server listens on `127.0.0.1` (this machine only) by default. Before setting `"host": "0.0.0.0"` to reach it
> from other machines, make sure `apiKeys` is set: a server without keys is open to anyone who can reach it.

More workers (jobs at once): `SWARMLAB_WORKERS=6 node dist/server/main.js serve --config swarmlab.server.json`.

### B4. Test your server with the full test script

In another terminal, from the `swarm-lab` folder:

```bash
cd clients/python
python3 full_test.py --url http://127.0.0.1:8787 --key "$SWARMLAB_KEY" --repo app --out ~/sl-reports
```

- `--repo app`: a repository name from your configuration.
- `--experiment`: also a small experiment (single vs swarm), bounded by `--max-cost` (default 1 USD).
- With a real model, jobs take minutes and cost real money: start with a small repository.

You should see the same kind of output as in Part A2, with your real models and costs.

---

For the full programmatic surface — the `RunSettings` fields, the `allowedSettingOverrides` whitelist, `providers` (RAG/decision), and the security/cost model — see [docs/PROGRAMMATIC-CONFIGURATION.md](docs/PROGRAMMATIC-CONFIGURATION.md).

## Part C: use your VS Code setup on the server

1. Install the extension: in VS Code, **Extensions → … → Install from VSIX…**, pick `swarm-lab-0.42.4.vsix` (example filename matching the current source version; no package is built by these instructions).
2. Open the Swarm Lab panel → **Server** tab → **Server address** `http://127.0.0.1:8787` → **Save** → **Set API key**
   (a key with `approve` or `admin`) → **Test**.
3. **Your setup on the server** → type a name (for example `team-default`) → **Export to the server**. It saves your
   agents, prompts, workflow, models, automatic model choice, tests and the check of "done", memory, skills and MCP
   servers as a profile (never your keys).
4. Any job or script can now say `"profile": "team-default"`; anything in the job itself wins.

---

## Part D: from your own scripts

The client is one file, `clients/python/swarmlab_client.py` (standard library only). Copy it next to your script.

```python
from swarmlab_client import SwarmLabClient

sl = SwarmLabClient("http://127.0.0.1:8787", api_key="sl_...")

job = sl.submit("app", "Find and fix the failing date test", "graph",
                profile="team-default",                         # your exported VS Code setup
                workflow="default",                             # or a whole workflow as a dict
                memory={"session": "date-bugs"},                # shared with other jobs of this session
                checks={"tests": True, "verify": True},         # run_tests + the check of "done"
                hooks=[{"url": "http://127.0.0.1:9000/hook", "events": ["before:command", "job:end"], "secret": "s3"}],
                labels={"team": "core"})
job = sl.wait(job["id"])
print(job["status"], job["tokens"], job["costUsd"])
print(sl.report(job["id"]))                                     # every step, with tokens, cost and time
print(sl.costs(group_by="model", fmt="md", label="team=core"))  # usage across jobs
```

A hook receiver answers `{"decision": "allow"}`, `{"decision": "deny", "note": "why"}` or
`{"decision": "allow", "note": "for the agent"}` to `before:` events, and checks the signature with
`SwarmLabClient.verify_signature(secret, body, request.headers["X-SwarmLab-Signature"])`. `full_test.py` has a
complete example (`HookHandler`).

---

## Part E: see what happened

**Dashboard** (`http://127.0.0.1:8787/`):

- **Jobs**: click one for its events live, its answer, and its artifacts: `report.md` (every step), `report.json`,
  `changes.patch`.
- **Reports**: a date range and a grouping (day, mode, model, repository, key, status, label) → a table, or **CSV** /
  **Markdown** to download.
- **Experiments**: paste a bench suite, set *at once* and *most $*, **Start**; progress and the summary per setup.

**API** (with `-H "authorization: Bearer $SWARMLAB_KEY"`):

```bash
curl -s -H "authorization: Bearer $SWARMLAB_KEY" http://127.0.0.1:8787/v1/jobs/<id>/report                    # Markdown
curl -s -H "authorization: Bearer $SWARMLAB_KEY" "http://127.0.0.1:8787/v1/reports?groupBy=mode&format=csv"   # CSV
curl -s -H "authorization: Bearer $SWARMLAB_KEY" http://127.0.0.1:8787/v1/profiles                            # profiles
```

**Command line**: `node dist/server/main.js experiment suite.json --repo app --concurrency 8 --max-cost 5 --key "$SWARMLAB_KEY"`.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| `Server not found: …/dist/server/main.js` | Run `npm run bundle` in the `swarm-lab` folder (or set `SWARMLAB_SERVER` to the file). |
| `sha256sum: command not found` (macOS) | `brew install coreutils`, or use `shasum -a 256` in `run_full_test.sh`. |
| `address already in use` | Another program uses the port: `PORT=8798 bash clients/python/run_full_test.sh`, or start the server with `--port 9001` (or change `"port"` in your configuration). |
| `401` | No key, or a wrong key: check `--key` / `SWARMLAB_KEY`, and the sha256 in `apiKeys`. |
| `403` when saving the profile | The key needs the `approve` or `admin` role. |
| `… is not in the server's hooks.allowHosts` / `mcpAllowHosts` | Add `127.0.0.1` (the test script's own servers) as in B1. |
| `"repo" must be one of: …` | Use a repository name from `repos` in your configuration. |
| A job stays `waiting` | It waits for an approval: answer it in the dashboard, or allow it in `approvals` (for example `"mcp": "auto"`). |
| Costs are `$0.0000` | Add your models' prices to `models.pool` (B1). |
| `memory used 0` everywhere | Normal for the first job of a session; later jobs of the same session use it. Without `memory` in the job, set `"memory": { "mode": "scoped" }` in the configuration. |
| `check` reports an empty key variable | Export the variable named in `provider.apiKeyEnv` in the same terminal before `serve`. |

## Restart, replace an old server, several ports

- **Start local server** (Server tab) stops an old Swarm Lab server on the same port first, then starts the new one at
  once. When this window's server runs, it restarts it (Setup changes apply). Another program on the port is never
  stopped without asking. Turn this off with `swarmLab.server.replaceOld`.
- **✕ Kill old server** stops the server at the Server tab's address, also one started in a terminal or by an older
  version: first through `POST /v1/admin/shutdown`, then through its process.
- **Local servers → Start on port**: one more server with the same configuration on another port, with its own data
  folder (`<dataDir>-<port>`). **Use** sends the Server tab's jobs to it; **Stop** and **↻** per server.
- From the command line: `swarm-lab serve --port 8788 --data-dir ./swarmlab-data-8788`. `--wait-port 10` waits up
  to 10 seconds for a port that an old server is still freeing.
- Over the API (admin key): `curl -X POST -H "Authorization: Bearer $KEY" -d '{"restart":true}' http://127.0.0.1:8787/v1/admin/shutdown`.
  The dashboard has **↻ Restart server** and **■ Stop server**. `/v1/health` reports `pid` and `startedAt`;
  `<dataDir>/server.pid` tells which process serves which port.

## Same setup as the chat, and run files

- **Start local server** copies your Setup into `swarmlab.server.json` every time (provider, models, reasoning
  effort, extra request fields and headers, limits, tool mode, approvals, code search, decisions, automatic model
  choice, memory): jobs on the server run like the chat. `swarmLab.server.syncSetup`: `all`, `models`, `off`.
- **📄 Create run files** writes `swarmlab-run/`: `start-server.sh` / `.cmd`, `.env.example`,
  `swarmlab.client.json`, `example.py` and the Python library. Copy `.env.example` to `.env`, fill in the keys,
  `./swarmlab-run/start-server.sh`, then `python swarmlab-run/example.py "your task"`.
- *"Function tools with reasoning_effort are not supported … set reasoning effort to none"*: fixed in 0.41.0 (the
  client retries with `"none"`); to send it from the first call, choose Setup → Reasoning effort → none.

## Let the server choose the mode

Send `"mode": "auto"` (Server tab: **Organization → Automatic**; Python: `sl.run(task, mode="auto")`). A decision
picks single, tree, swarm or graph for the task: the decision model when Setup → Decisions is on, otherwise the worker
model. When it is not sure, the job runs as **single**. The job's events and `result.chosenMode` say what was chosen.

