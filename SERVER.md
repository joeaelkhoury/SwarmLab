# Swarm Lab server

Run Swarm Lab's agents, workflows and swarms as a **service**: many jobs, a queue, workers on many machines, a history of everything, approvals that wait for a human, and an API that anything can call (CI pipelines, webhooks, scripts, a dashboard, the VS Code panel).

The server runs the **same engine** as the VS Code extension: same organizations (single, tree, swarm, graph), same agents, prompts, permissions, workflows, skills, MCP tools, code search and limits. It reads them from the repository's `.swarmlab/` folder, so a team configures agents once in VS Code, commits `.swarmlab/`, and the server uses them.

---

## 1. How it works

```
 Callers                         Swarm Lab                                      Results
 ───────                         ─────────                                      ───────
 curl / scripts  ─┐        ┌─────────────────────────────┐
 CI pipeline     ─┤ POST   │ API processes (1…n)         │   job branch, commit, patch
 GitHub webhook  ─┼─/v1/──▶│  jobs · events · approvals  │──▶ pushed branch, pull request
 dashboard       ─┘  jobs  ├─────────────────────────────┤   report.json, history
                           │ Queue in the store          │
                           ├─────────────────────────────┤   dashboard, metrics,
                           │ Worker processes (1…n)      │──▶ live event stream
                           │  each job: own Git worktree │
                           │  and branch, same engine    │
                           └──────────────┬──────────────┘
                                          │
                           Store: files (one machine) or PostgreSQL (many)
```

**A job** is one task on one repository: `{"repo": "app", "task": "Fix the date bug", "mode": "graph"}`.
1. The API checks it, stores it, and puts it in the queue.
2. A worker claims it, creates a fresh **Git worktree on a new branch** `swarmlab/job-<id>`, and runs the agents there.
3. Every model call, tool call, message, edit and command is stored as an **event**, which you can read or stream live.
4. Anything that needs a human (by your rules) becomes an **approval**: the job waits; someone answers through the API or the dashboard.
5. At the end, the changes are **committed on the job branch**. The patch and a report are stored. If configured, the branch is **pushed** and a **pull request** is opened.
6. Your main branch is never changed directly: humans review and merge.

---

## 2. Quick start on one machine (no database)

```bash
npm install && npm run compile     # or use the Docker image (section 7)
npx swarm-lab init                 # writes swarmlab.server.json
```

Edit `swarmlab.server.json`:
1. `repos`: your repository, for example `{"app": {"path": "../my-app", "baseRef": "main"}}`.
2. `provider`: your model (section 4.2). Keep `"type": "mock"` to try without a model.
3. `apiKeys`: run `npx swarm-lab hash-key`, then put the printed `sha256` in a key with `"roles": ["admin"]`, and keep the printed key for yourself.

Then:

```bash
npx swarm-lab check                # ✓ No problems found.
npx swarm-lab serve                # API + workers, file store
```

Open **http://127.0.0.1:8787**, paste your key into **API key**, and submit a job. Or use curl:

```bash
curl -s -X POST http://127.0.0.1:8787/v1/jobs \
  -H "Authorization: Bearer $KEY" -H "content-type: application/json" \
  -d '{"repo": "app", "task": "Explain how this project is organized"}'
```

---

## 3. One job from the command line (CI)

`run` executes one job in the current process and exits with code 0 if it succeeded and 1 otherwise. No server is needed.

```bash
npx swarm-lab run --repo app --task "Fix the failing date test" --mode graph --workflow default
npx swarm-lab run --repo app --task-file task.md --agent reviewer --json > result.json
```

For CI, set approvals that never wait for a human: `"edits": "auto"` and `"commands": "allowlist"`. A command outside the allow-list would wait, so add the commands your workflow needs to the list.

`run` needs no configuration file. It takes the same JSON as `POST /v1/jobs`, a repository by path, and the model on the command line:

```bash
# A repository by path, a job spec from a file, an environment, approvals answered here, artifacts saved
swarm-lab run --repo-path ../my-app --spec job.json --env auto --approve auto --out result/ \
  --provider anthropic --model claude-sonnet-5-5           # key from ANTHROPIC_API_KEY
swarm-lab run --repo-path . --task "Fix the date test" --workflow fix-and-test.json --set maxStepsPerAgent=20
swarm-lab run --repo-path . --task "…" --jsonl            # every event as one JSON line (for other programs)
```

`--approve`: `ask` (default in a terminal), `auto` (approve everything), `reject` (default otherwise), or `stdin` (requests
go out as JSON lines, answers come back on standard input; the Python library uses it). `--workflow` takes a saved
workflow's name or a file: a bare graph, or a saved workflow with its agents and environment.

`swarm-lab env PATH` prepares an environment for a folder and runs commands in it, with no agents:
`swarm-lab env . --test`, `swarm-lab env . --runtime docker --image node:22 --run "npm ci" --run "npm test"`.
See [docs/ENVIRONMENTS.md](docs/ENVIRONMENTS.md).

---

## 4. Configuration

One file, `swarmlab.server.json` (or `--config FILE`, or `SWARMLAB_CONFIG`).
- `${NAME}` anywhere in the file is replaced by the environment variable `NAME`.
- Secrets (model keys, Git tokens, webhook secrets) always come from **environment variables**, never from the file.
- `npx swarm-lab check` explains every problem.

### 4.1 Server, store and workers

| Key | Default | Meaning |
|---|---|---|
| `host`, `port` | `127.0.0.1`, `8787` | Where the API listens. Use `0.0.0.0` in containers (API keys are then required). |
| `dataDir` | `./swarmlab-data` | Clones, worktrees, file store, memory, code index |
| `store` | `{"type": "file"}` | `{"type": "postgres", "url": "postgres://…", "poolSize": 10}` to scale |
| `workers.concurrency` | `2` | Jobs at the same time **per worker process** |
| `workers.pollMs` | `1000` | How often an idle worker looks for jobs |
| `workers.heartbeatSec` / `staleSec` | `10` / `90` | A job whose worker is silent for `staleSec` goes back to the queue (the worker crashed or its machine stopped) |

Environment overrides: `SWARMLAB_DATABASE_URL` (switches to PostgreSQL), `SWARMLAB_HOST`, `SWARMLAB_PORT`, `SWARMLAB_WORKERS`, `SWARMLAB_DATA_DIR`.

**Several servers on one machine.** `serve`, `api`, `worker` and `check` take `--port N`, `--host ADDRESS` and
`--data-dir FOLDER`, which override the configuration and the environment. Give each server its own data folder
(with the file store, two servers must never share one):

```bash
node dist/server/main.js serve --config swarmlab.server.json --port 8787 --data-dir ./swarmlab-data
node dist/server/main.js serve --config swarmlab.server.json --port 9001 --data-dir ./swarmlab-data-9001
```

The startup line shows the version and the Studio address; `GET /v1/health` also returns `version`.

### 4.2 Model provider

```json
"provider": {
  "type": "openai",
  "baseUrl": "http://localhost:11434/v1",
  "apiKeyEnv": "LLM_API_KEY",
  "leadModel": "mistral-large-latest",
  "workerModel": "mistral-small-latest",
  "proxy": "http://proxy.company.com:8080",
  "keyHeader": "authorization",
  "extraHeaders": {},
  "extraBody": { "reasoning_effort": "none" }
}
```

`type` is `anthropic`, `openai` (any OpenAI-compatible server or gateway), `openrouter` or `mock`. The options mean the same as in the extension (see the MANUAL.md, section 3). Agents without tool calling: set `"toolMode": "text"` in `defaults.settings` or per agent in `.swarmlab/policy.json`.

### 4.3 Repositories

```json
"repos": {
  "app": {
    "url": "https://github.com/your-org/your-app.git",
    "baseRef": "main",
    "push": { "remote": "origin", "tokenEnv": "GITHUB_TOKEN" },
    "pullRequest": { "owner": "your-org", "repo": "your-app", "base": "main", "tokenEnv": "GITHUB_TOKEN", "draft": true }
  },
  "local-tool": { "path": "/srv/repos/tool" }
}
```

- **`path`**: a repository on the server. **`url`**: cloned once (as a mirror in `dataDir/repos/`) and fetched before each job.
- **`baseRef`**: where jobs start (a job can override it with `ref`).
- **`push`**: push the job branch after a successful job that changed files. The token is passed to Git for that one command only, never written to disk.
- **`pullRequest`**: open a GitHub pull request (draft by default) with the agents' answer and the diff summary. GitHub Enterprise: set `apiUrl`.

### 4.4 Defaults for jobs

```json
"defaults": {
  "settings": { "maxStepsPerAgent": 12, "maxAgents": 5, "tokenBudget": 400000, "maxTokensPerCall": 2048,
                "allowEdits": true, "allowCommands": true, "useMemory": true },
  "approvals": { "edits": "auto", "fileOps": "auto", "commands": "allowlist", "mcp": "ask", "messages": "off",
                 "timeoutSec": 86400, "commandAllowList": ["npm test", "pytest"] },
  "maxAttempts": 2,
  "timeoutSec": 3600
},
"allowedSettingOverrides": ["maxStepsPerAgent", "maxAgents", "tokenBudget", "maxTokensPerCall", "answerLength", "toolMode", "maxContinuations", "ragTopK"]
```

`settings` are the engine settings (the same names as the extension's `RunSettings`). A job may change only the settings listed in `allowedSettingOverrides`.

### 4.5 Approvals: what runs alone, what waits for a human

| Rule | Values | Meaning |
|---|---|---|
| `edits` | `auto` · `ask` · `off` | File changes in the job's sandbox. `auto` is safe for most teams: the result is a branch that a human reviews before merging. |
| `fileOps` | `auto` · `ask` · `off` | Delete and rename |
| `commands` | `auto` · `allowlist` · `ask` · `off` | `allowlist`: the listed commands run alone, others wait. A command with `;` `&` `|` `` ` `` `$` `<` `>` never matches the list. |
| `commandAllowList` | list | Commands or prefixes, for example `npm test` |
| `mcp` | `auto` · `ask` · `off` | MCP tool calls (a server set to `"approval": "allow"` never asks) |
| `messages` | `off` · `lead` · `all` | Review of messages between agents |
| `timeoutSec` | `86400` | An unanswered request is rejected (expired) after this time |

A job can tighten or loosen these with its own `approvals` field, for example `{"edits": "ask"}` for a sensitive repository. While a request waits, the job's status is **waiting**; cancelling the job rejects its open requests.

### 4.6 API keys and limits

```json
"apiKeys": [
  { "name": "admin",  "keyEnv": "SWARMLAB_KEY_ADMIN", "roles": ["admin"] },
  { "name": "ci-bot", "sha256": "3f9a…", "roles": ["submit", "read"], "maxActiveJobs": 10 },
  { "name": "lead-dev", "sha256": "a1c2…", "roles": ["read", "approve"] }
],
"limits": { "maxQueued": 1000, "maxActivePerKey": 20, "maxTaskChars": 20000 }
```

| Role | Can |
|---|---|
| `submit` | Create jobs, cancel and retry its own jobs |
| `read` | Read its own jobs, events, artifacts, metrics |
| `approve` | See and answer every approval, read every job |
| `admin` | Everything |

Store keys as **sha256** (from `npx swarm-lab hash-key`), or the key itself in an environment variable (`keyEnv`). Callers send `Authorization: Bearer <key>`. With no `apiKeys`, the API is open, and the server refuses to listen on anything other than `127.0.0.1`.

### 4.7 Triggers (webhooks)

A trigger turns a webhook into a job: `POST /v1/triggers/<name>`.

```json
"triggers": {
  "github-bug": {
    "secretEnv": "GITHUB_WEBHOOK_SECRET",
    "filter": { "action": "labeled", "label.name": "bug" },
    "job": { "repo": "app", "mode": "graph", "workflow": "default", "priority": 5,
             "task": "Fix this bug.\n\nTitle: {{issue.title}}\n\n{{issue.body}}",
             "labels": { "source": "github", "issue": "{{issue.number}}" } }
  }
}
```

- **`job`** is a job template: `{{path.in.payload}}` is replaced by the webhook's value.
- **`filter`**: only payloads whose fields equal these values start a job (others answer 202 "skipped").
- **`secretEnv`**: checks GitHub's `X-Hub-Signature-256` HMAC. Without a secret, the caller needs an API key with `submit`.

**GitHub setup:** repository **Settings → Webhooks → Add webhook**.
- Payload URL: `https://your-server/v1/triggers/github-bug`
- Content type: `application/json`
- Secret: the value of `GITHUB_WEBHOOK_SECRET`
- Events: **Issues**

Labelling an issue `bug` then starts the fix workflow and, with `pullRequest` configured, opens a draft pull request.

### 4.8 MCP servers and code search

**Add an MCP server with one command.** It is saved in the configuration file and checked right away. Running workers use it from their next job, with no restart:

```bash
npx swarm-lab mcp add jira --command npx --arg -y --arg <jira-mcp-package> --env JIRA_URL='${JIRA_URL}' --env JIRA_TOKEN='${JIRA_TOKEN}'
npx swarm-lab mcp add search --url https://mcp.example.com/mcp --header Authorization='Bearer ${SEARCH_TOKEN}'
npx swarm-lab mcp list          # ✓ jira  … tools: create_issue, search_issues, …
npx swarm-lab mcp remove search
```

- Write secrets as `${NAME}` (in single quotes on the command line) and set `NAME` in the environment: the file then holds no secret.
- `--approval allow` lets calls run without asking; the default `ask` makes each call an approval, unless a job sets `"approvals": {"mcp": "auto"}`.
- With Docker, the configuration is mounted from `deploy/`: run the command on the host with `--config deploy/swarmlab.server.json`.

The same section by hand:

```json
"mcp": { "github": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } } },
"rag": { "enabled": true, "embeddingModel": "nomic-embed-text", "embeddingBaseUrl": "http://ollama:11434/v1", "embeddingKeyEnv": "" }
```

MCP servers come **only from the server's configuration**, never from a repository's files: a repository cannot make the server start programs. The code index is kept per repository and per worker machine, and updated by content, so unchanged files are not re-indexed by each new job.

### 4.9 Jobs with or without a repository, with or without files

| Option | With | Without |
|---|---|---|
| **Repository** (`repo`) | `"repo": "app"`: the job works on your code, in a worktree on its own branch; the result is a commit, and optionally a push and a pull request | Leave `repo` out: the job gets a **fresh, empty workspace**, for ideas, Jira tickets, diagrams, documents, plans. No branch, no push. |
| **Created files** (`files`) | `"files": true`: every file the job created or changed comes back as its own artifact, `files/<path>` | `"files": false`: only `changes.patch` and `report.json` |

The default for `files` is **true without a repository** (the files are the result) and **false with one** (the branch is the result). `result.files` always lists the paths created or changed.

```json
{"task": "Draw the architecture of an order system as a Mermaid diagram in docs/orders.md"}
→ result.files: ["docs/orders.md"], artifact "files/docs/orders.md"
```

Download a file with `GET /v1/jobs/{id}/artifacts?name=files/docs/orders.md` (or with the path URL-encoded after `/artifacts/`).

**Workflows for every job:** `"workflows": {"default": {…}, "review": {…}}` in the server configuration. A job uses them by name (`"workflow": "review"`) when its repository has no workflow of that name, and always when it has no repository.

### 4.10 What the repository brings

Each job reads the repository's own `.swarmlab/` folder (on the job's branch): `policy.json` (agents, tools, folders), `prompts/`, `graph.json` (the `default` workflow) or `workflows/<name>.json`, and skills (`.swarmlab/skills/`, `.claude/skills/`). Configure agents in VS Code, commit `.swarmlab/`, and the server uses the same team. Memory (board and notes) is kept per repository in `dataDir/memory/`.

### 4.11 Decision model (optional)

A decision model such as Jev answers typed decisions (a choice, a score, a yes/no) instead of a full model reply: workflow `decide` steps, run mode `auto`, the cheaper model for simple messages, skipping code search, and a hint on command approvals. Off unless configured; when it is unsure (below `minConfidence`) or fails, jobs run exactly as without it. It never approves anything.

```json
"decisions": {
  "enabled": true,
  "provider": "openrouter",
  "model": "jev-latest",
  "apiKeyEnv": "OPENROUTER_API_KEY",
  "minConfidence": 0.5,
  "points": { "graph": true, "runMode": true, "cascade": true, "ragGate": true, "commandHint": true }
}
```

`provider`: `openrouter` (OpenRouter's System One API), `typesafe` (TypeSafe directly), `custom` (any System One server: set `baseUrl`, the part before `/v1/systemone`, for example a LiteLLM proxy), or `chat-model` (the worker model answers as JSON; no key). Workflow `decide` steps work without this section too: the worker model answers them. Every decision is an event (`kind: "decision"`) in the job's stream. `swarm-lab check` reports a missing key variable.

### 4.15 A job configured by its script

```json
{
  "repo": "app", "mode": "swarm", "task": "Map the structure of this project",
  "policy": { "agents": { "reviewer": { "model": "claude-sonnet-5-5", "tools": ["list_files", "read_file", "search_text"] }, "writer": { "editPaths": [".swarmlab/out/**"] } } },
  "prompts": { "roles": { "swarm-lead": "…" }, "agents": { "reviewer": "Be concrete: name files and lines." } },
  "memory": { "session": "q4-audit", "topics": ["auth"] },
  "settings": { "maxAgents": 4 }, "labels": { "team": "core" }
}
```

`policy` and `prompts` apply to this job only, over the repository's `.swarmlab/` files; they are checked when the job is submitted (an unknown role, a malformed agent, a prompt over 40,000 characters is refused with the reason). `memory`: jobs with the same `session` share memory (the progress note of the last job, its items, relevant topic and project items, within `memory.budgetTokens`); `false`: none. Server default: `"memory": { "mode": "notes" }` (the per-repository notes of earlier versions); `"scoped"` gives every job its own session (or the one it names); `"off"`. Scoped memory is kept per repository in `dataDir/memory-scoped/`.

### 4.17 Profiles, MCP, skills, checks, hooks per job

```json
"mcpAllowHosts": ["mcp.internal.example"],
"hooks": { "allowHosts": ["hooks.internal.example", "127.0.0.1"] }
```

`PUT /v1/profiles/{name}` (role `approve` or `admin`) saves a configuration; `GET /v1/profiles`, `GET /v1/profiles/{name}`, `DELETE /v1/profiles/{name}` (admin). A job with `"profile": "name"` is merged with it when submitted (the job wins; skills by name; hooks and MCP servers add up) and stored merged. Per job (or profile): `mcp` (`use`: servers of `mcp` in this configuration; `add`: by URL, host in `mcpAllowHosts`; a local `command` only with an admin key), `skills`, `checks` (`tests`, `verify`, `retry`), `models` (`auto`), `hooks` (URL hosts in `hooks.allowHosts`; MANUAL.md, section 33). Before-hooks run before the allow-list and before approvals: a deny always wins.

### 4.16 Reports

Each job writes `report.md` and `report.json` (artifacts): every step with its tokens, cost and time, totals by agent and by model, files, memory, the independent check; its result keeps `usage.byModel` and `usage.byAgent`. `GET /v1/jobs/{id}/report` returns the Markdown (`?format=json` the data). `GET /v1/reports?groupBy=day|mode|model|repo|key|status|all|label:<name>&from=&to=&label=name=value&repo=&format=json|csv|md` sums tokens, cost, successes and time across jobs (yours; everyone's with `admin` or `approve`). Costs use the prices of `models.pool`.

### 4.14 Experiments (optional limits)

```json
"experiments": { "maxConcurrency": 16, "maxRuns": 2000, "maxRunning": 2, "requireLimit": true }
```

`maxConcurrency`: the most runs at once in one experiment (default 16); `maxRuns`: the most runs in one experiment (default 2,000); `maxRunning`: experiments running together on this server (default 2); `requireLimit`: refuse experiments without `maxCostUsd` or `maxTokens`. Experiments run in the API process (`serve` or `api`) on repositories from `repos`; they are stored in `dataDir/experiments/` (one that was running when the server stopped is marked stopped). Each run's cost uses the prices of `models.pool`.

### 4.13 Actions that cannot be undone

Commands such as `rm -rf`, `git push --force`, `DROP TABLE`, `kubectl delete`, `terraform apply`, cloud deletes, deploys and package publishing (MANUAL.md, section 28.3) always wait for an approval, even with `"commands": "auto"` or on the allow-list; connected tools whose name says they delete, deploy, send or pay too, even with `"mcp": "auto"`. Cancelling a job closes its pending approvals at once.

### 4.12 Automatic model choice (optional)

```json
"models": {
  "auto": "cheapest",
  "pool": [
    { "id": "small-model-id", "tier": "small", "input": 0.15, "output": 0.6 },
    { "id": "big-model-id", "tier": "large", "input": 3, "output": 15 }
  ]
}
```

Each agent turn of a job uses the cheapest model of the size class its task needs (MANUAL.md, section 26). Without `pool`, the provider's worker model is small and its lead model large. Prices (USD per million tokens) let it pick the cheapest of a class and give jobs and benches their cost. `"escalate": false` turns off the move to a bigger model after a failure. In `swarm-lab bench`, setups with `"leadModel": "auto:cheapest"` (or `balanced`, `best`) use it.

---

### 4.18 Data for jobs

A job may name data its agents read, and a folder for results: `"data": { "inputs": ["data/labels.csv", "/srv/datasets/q3/"], "output": "results/" }`. Relative paths start in the job's workspace. Agents get `list_data`, `read_data` (CSV, Excel, Word, PDF, PowerPoint, notebooks, ZIP, pictures) and `write_output`, as in VS Code (MANUAL.md, section 34). Results saved inside the job's workspace come back with the job's files when `files` is on (the default for jobs without a repository).

Paths outside the job's workspace are refused unless they are inside one of the server's data folders:

```json
"data": { "roots": ["/srv/datasets"], "images": true, "write": "auto" }
```

`write`: `auto` (new files are saved; overwriting waits for an approval), `ask` (every save waits), `off`. A job with a path outside `roots` is refused when it is submitted (400), not later in a worker.

### 4.19 Workers and model calls, live

`workers.concurrency` (jobs at once in this process) and `workers.maxParallelCalls` (model calls at once across those jobs; 0 = no limit) change while the server runs:

```bash
curl -s $URL/v1/workers -H "Authorization: Bearer $ADMIN_KEY"                       # current limits, running and waiting calls
curl -s -X PUT $URL/v1/workers -H "Authorization: Bearer $ADMIN_KEY" -H "Content-Type: application/json" \
  -d '{"concurrency": 4, "maxParallelCalls": 6, "save": true}'                        # save: also write the configuration file
```

Admin keys only. Lowering a limit lets running jobs and calls finish. In VS Code: **Server** tab → **Jobs at once** / **Model calls at once**. A process started with `api` runs no workers and answers 409: change the limits on the worker processes.

### 4.20 Web research for jobs

```json
"web": { "enabled": true, "search": "duckduckgo" }
```

`search`: `duckduckgo` (no key), `brave` or `tavily` (`"keyEnv": "SEARCH_KEY"`, the environment variable with the key), `searxng` (`"searxngUrl"`). Jobs get `web_search` and `fetch_url` unless they send `"web": false`; a job sending `"web": true` to a server without it is refused (400). Private addresses stay blocked unless `"allowPrivate": true`; `"blockHosts"` lists hosts never read.

### 4.21 Environments: what jobs install and where their commands run

A job's commands (its agents' `run_command` and `run_tests`, a workflow's command steps) run in its **environment**,
prepared before the agents start: dependencies installed, a Python virtual environment, a container, a virtual screen
for VS Code or browser tests. A job gives it with `"environment"`; without one, the repository's
`.swarmlab/environment.json` is used, else the server's `environments.default`, else none.

```json
"environments": {
  "allowSetup": "submit",
  "runtimes": ["local", "docker"],
  "defaultRuntime": "local",
  "docker": { "binary": "docker", "allowImages": ["node:*", "python:3.*", "mcr.microsoft.com/devcontainers/*"], "extraArgs": ["--cpus", "4", "--memory", "8g"] },
  "presets": { "web-e2e": { "runtime": "docker", "image": "mcr.microsoft.com/playwright:v1.48.0-jammy", "preset": "node" } },
  "default": "auto"
}
```

- `allowSetup`: who may send setup commands in a job: `submit` (default; submitters can already let agents run commands), `admin`, or `off` (only presets, the server's `presets` and repository files).
- `runtimes` and `docker.allowImages` limit what jobs may ask for. `docker.binary` can be `podman`.
- `presets`: named environments; a job uses them with `"environment": "web-e2e"`.
- The setup's output is the job's `environment.log` artifact, its summary is `result.environment`. What the setup created (for example `node_modules/`) is kept out of the job's commit, and tracked files it rewrote are restored.

Every field, the presets and examples: [docs/ENVIRONMENTS.md](docs/ENVIRONMENTS.md).

---

## 5. API reference

All endpoints take and return JSON; send `Authorization: Bearer <key>`.

### Jobs

| Method and path | Role | What it does |
|---|---|---|
| `POST /v1/jobs` | submit | Create a job (201; 200 with the existing job for the same `idempotencyKey`) |
| `GET /v1/jobs?status=queued,running&repo=app&label=team=core&limit=50&before=<createdAt>` | read | List jobs, newest first; `next` is the cursor for `before` |
| `GET /v1/jobs/:id` | read | One job, with its spec and result |
| `POST /v1/jobs/:id/cancel` | submit | Cancel (a queued job at once; a running job at its next step) |
| `POST /v1/jobs/:id/retry` | submit | A new job with the same spec |
| `GET /v1/jobs/:id/events?after=0&limit=500` | read | Events in order (`seq`) |
| `GET /v1/jobs/:id/stream?after=0` | read | Live events (server-sent events); ends with `event: end`. Browsers can pass `?token=<key>`. |
| `GET /v1/jobs/:id/artifacts` and `/artifacts/:name` | read | `changes.patch` (the diff) and `report.json` (answer, metrics, every agent) |
| `GET /v1/jobs/:id/approvals` | read | The job's approvals |

**Job fields:**

| Field | Meaning |
|---|---|
| `task` (required) | What to do |
| `repo` | A name from `repos`; leave it out for a job without a repository |
| `files` | `true`: return each created or changed file as an artifact (default: true without a repository) |
| `mode` | `single` (default), `tree`, `swarm`, `graph` |
| `workflow` | Graph mode: `"default"` (`.swarmlab/graph.json`), a name (`.swarmlab/workflows/<name>.json`), or a whole workflow object |
| `agent` | Single mode: run as one of the repository's agents |
| `ref` | Start from this branch or commit |
| `priority` | Higher runs first (default 0) |
| `approvals` | This job's approval rules (section 4.5) |
| `settings` | Allowed engine settings |
| `labels` | Your own tags, for filtering (`{"team": "core", "ticket": "PAY-123"}`) |
| `webhook` | URL called with the result when the job ends |
| `idempotencyKey` | The same key from the same caller never creates a second job |
| `maxAttempts`, `timeoutSec` | Retries and time limit |

**Statuses:** `queued` → `running` ⇄ `waiting` (for a human) → `succeeded` · `failed` · `cancelled`. Infrastructure errors (Git, network, model API) are retried with a growing delay, up to `maxAttempts`.

### Approvals

| Method and path | Role | What it does |
|---|---|---|
| `GET /v1/approvals?status=pending` | approve | Every waiting request: title, reason, diff or command, choices |
| `POST /v1/approvals/:id` | approve | `{"decision": "approve"}` or `{"decision": "reject"}`; optional `"choice"` and `"text"` (an edited message or task). A request is decided only once (409 afterwards). |

### Others

| Method and path | What it does |
|---|---|
| `POST /v1/triggers/:name` | Webhook (section 4.7) |
| `GET /v1/repos` | Repository names |
| `GET /v1/capabilities` | What this server offers: version, modes, repositories, saved workflows, profiles, allowed settings, default approvals, limits, models, features, environments (presets, runtimes, whether docker is installed), your roles (role `read`) |
| `POST /v1/validate` | Check a job without queueing it, with the same rules as `POST /v1/jobs` (profile and saved workflow merged): `{"valid", "errors", "spec"}` (role `submit`) |

### Saved workflows

A saved workflow is a graph plus, if you like, its agents (`policy`), their `prompts`, its `environment`, `checks`,
`settings` and `approvals`. A job with `"workflow": "<name>"` runs it; the job's own fields win over the workflow's.
A bare graph (`{"start", "nodes"}`) is accepted too. Saved workflows are used before the server configuration's
`workflows` and before a repository's `.swarmlab/workflows/<name>.json` of the same name.

| Method and path | Role | What it does |
|---|---|---|
| `GET /v1/workflows` | read | Saved workflows (steps, agents, environment) and the configuration's |
| `GET /v1/workflows/:name` | read | One workflow |
| `PUT /v1/workflows/:name` | approve | Save it; checked like a job (graph, agents, environment, settings this server allows) |
| `DELETE /v1/workflows/:name` | admin | Delete it |
| `POST /v1/workflows/validate` | read | `{"valid", "errors"}` for a workflow, without saving it |
| `GET /v1/health` | Queue sizes; for load balancers |
| `GET /metrics` | Prometheus: jobs by status, tokens, cost, pending approvals, busy workers (role `read`) |
| `GET /` | The dashboard |

**Example: submit, follow, approve**

```bash
API=http://127.0.0.1:8787; H="Authorization: Bearer $KEY"
ID=$(curl -s -X POST $API/v1/jobs -H "$H" -H "content-type: application/json" \
  -d '{"repo":"app","mode":"graph","task":"Fix the failing date test","approvals":{"edits":"ask"}}' | jq -r .id)
curl -N -H "$H" $API/v1/jobs/$ID/stream                              # live events
curl -s -H "$H" "$API/v1/approvals?status=pending" | jq '.approvals[] | {id, title, diff}'
curl -s -X POST -H "$H" -H "content-type: application/json" $API/v1/approvals/<approval-id> -d '{"decision":"approve"}'
curl -s -H "$H" $API/v1/jobs/$ID | jq '{status, result: .result | {branch, diffStat, prUrl}}'
curl -s -H "$H" $API/v1/jobs/$ID/artifacts/changes.patch
```

---

**From your own application:** `clients/README.md` gives the exact request and response formats, error codes and webhook payload. `clients/python/` has the `swarmlab` Python library ([docs/PYTHON-LIBRARY.md](docs/PYTHON-LIBRARY.md): typed agents, workflows and environments, on a server or without one), the older single-file client (`swarmlab_client.py`, standard library only) and an example application (`example_app.py`) that submits a job, follows it live, answers approvals and saves the results.

## 6. The dashboard

Open the server's address in a browser and paste your API key (kept in that browser only).
- **Waiting for you:** every pending request with its diff or command, and **Apply / Run / Reject** (an editable box for messages and tasks).
- **New job:** repository, organization, workflow, priority, task.
- **Jobs:** status, filter by status; click one for its task, branch, pull request, diff summary, answer, error, tokens and cost, artifacts, **Cancel** or **Run again**, and the **live event log**.

---

## 7. Scale with PostgreSQL and Docker

### 7.1 Why PostgreSQL

The file store is for one process (`serve`). With PostgreSQL, any number of **API processes** and **worker processes**, on any number of machines, share one queue:
- jobs are claimed with `FOR UPDATE SKIP LOCKED`, so no job is ever taken twice;
- each job has its own ordered event numbers;
- an approval is decided exactly once, even if two people click at the same moment;
- if a worker dies, its jobs return to the queue after `staleSec`.

### 7.2 Run it

```bash
export SWARMLAB_DATABASE_URL=postgres://swarmlab:secret@db:5432/swarmlab
npx swarm-lab migrate        # creates the tables (the API also does it at start)
npx swarm-lab api            # on 1…n machines, behind a load balancer
npx swarm-lab worker         # on 1…n machines; each runs workers.concurrency jobs at a time
```

Capacity is **worker processes × `workers.concurrency`** jobs at the same time. Most of a job's time is spent waiting for the model, so 2–4 jobs per CPU core is a reasonable start; watch `swarmlab_worker_busy` and the queue size in `/metrics`.

### 7.3 Docker Compose

`docker-compose.yml` starts PostgreSQL, one API and two workers. Edit `deploy/swarmlab.server.json`, then:

```bash
export LLM_API_KEY=… SWARMLAB_KEY_ADMIN=… GITHUB_TOKEN=… GITHUB_WEBHOOK_SECRET=… POSTGRES_PASSWORD=…
docker compose up -d --build
docker compose up -d --scale worker=6        # more workers
docker compose logs -f worker
```

The image contains Node, Git and Python. Add your projects' toolchains (for example a JDK, Go, or your test dependencies) to the `Dockerfile`, so that `npm test`, `pytest` and the rest work inside the workers.

---

## 8. Running it safely in a company

- **Branches, not main:** every job's result is a branch (and a draft pull request); keep branch protection on `main`.
- **Isolation:** each job works in its own worktree, and agents cannot reach `.git` or paths outside it. Commands still run with the worker's permissions, so run workers in **containers** with only the tools, network access and credentials they need. Prefer `commands: "allowlist"`.
- **Untrusted input:** issue text and webhook payloads go into prompts; a malicious issue can try to steer agents (prompt injection). Use filters on triggers, keep pushes to draft pull requests, and keep `commands` on `allowlist`.
- **Secrets:** environment variables or your secret manager; never in `swarmlab.server.json`, `.swarmlab/` or repositories. Keys are compared by sha256.
- **Limits:** `limits` (queue, active jobs per key), per-job `tokenBudget` and `timeoutSec`, and `maxAttempts`.
- **Audit:** every job keeps who submitted it, every event, every approval (who decided, when) and the patch.

---

## 9. Monitoring

- `GET /metrics` (Prometheus): `swarmlab_jobs{status}`, `swarmlab_tokens_total`, `swarmlab_cost_usd_total`, `swarmlab_pending_approvals`, `swarmlab_worker_busy`.
- `GET /v1/health`: queue sizes, for load balancers and uptime checks.
- Logs: one line per job event on standard output.
- Alerts worth having: queue growing, approvals waiting more than a day, failure rate, cost per day.

---

## 10. Commands

| Command | What it does |
|---|---|
| `swarm-lab init [file]` | Example configuration |
| `swarm-lab check` | Check the configuration |
| `swarm-lab serve` | API + workers (file store or PostgreSQL) |
| `swarm-lab api` | API only (PostgreSQL) |
| `swarm-lab worker` | Workers only (PostgreSQL) |
| `swarm-lab run --task T [--repo R \| --repo-path P] [--spec FILE] [--env E] [--approve …] [--json \| --jsonl]` | One job now, no server (section 3) |
| `swarm-lab env [PATH] [--preset P] [--runtime docker --image I] [--setup C]… [--run C]… [--test]` | Prepare an environment and run commands in it, no agents |
| `swarm-lab workflow validate FILE` | Check a workflow file |
| `swarm-lab version` | The version |
| `swarm-lab migrate` | Create the PostgreSQL tables |
| `swarm-lab mcp list` / `mcp add NAME --command … \| --url …` / `mcp remove NAME` | Manage MCP servers (picked up without a restart) |
| `swarm-lab hash-key [key]` | A new API key and its sha256 |

`SIGTERM` (for example `docker stop`) stops taking jobs, waits up to 10 seconds, and returns unfinished jobs to the queue for another worker.

---

### swarm-lab experiment

```bash
swarm-lab experiment suite.json --repo app [--url http://127.0.0.1:8787] [--key KEY] [--concurrency N] [--max-cost USD] [--max-tokens N] [--label TEXT] [--no-wait]
```

Submits a bench suite to a running server as an experiment (MANUAL.md, section 31), prints its progress every few seconds and the summary per setup at the end (Ctrl+C stops it). The key (or `SWARMLAB_KEY`) needs the `submit` role. API: `POST /v1/experiments` `{ suite, repo, concurrency, maxCostUsd, maxTokens, label }` → 201; `GET /v1/experiments` (yours; all with `admin` or `approve`); `GET /v1/experiments/{id}` (progress and summary); `GET /v1/experiments/{id}/result` (every run with its checks); `POST /v1/experiments/{id}/cancel`.

### swarm-lab bench

```bash
swarm-lab bench .swarmlab/bench/parser.json [--repo PATH] [--set-baseline] [--max-drop POINTS] [--json] [--config FILE]
```

Runs a bench suite (MANUAL.md, section 25) on a repository (default: the current folder) with the configured provider and decision model: every task × setup × repeat in its own Git worktree, unattended. It prints one line per setup (passed, pass rate, tokens, cost, time, and the difference with the baseline), saves the result in `PATH/.swarmlab/bench/results/`, and **exits with 1** when a setup's pass rate drops more than `--max-drop` points (default 0) below the baseline: a regression gate for CI when prompts, `policy.json` or workflows change. `--set-baseline` saves this run as the new baseline.


## 11. Tests

```bash
npm test                                                     # everything below
SWARMLAB_TEST_PG=postgres://user@host:5432/db node out/test/pgSim.js
```

**Server tests (file store):**
- API keys and roles;
- an edit waiting for approval, approved through the API, committed on its own branch, with `main` untouched;
- artifacts, the live stream, idempotency, and cancelling a waiting job;
- 4 jobs on 2 workers;
- a signed GitHub webhook with a filter;
- metrics, retry, recovery from a dead worker, and the CLI.

**PostgreSQL tests:**
- 40 jobs claimed by 4 competing connections, none twice;
- concurrent events numbered without gaps;
- simultaneous approval decisions (one wins);
- a real deployment of **1 API process and 2 worker processes**.
