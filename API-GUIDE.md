# Using the Swarm Lab server from your application

Your application talks to the server over **HTTP with JSON**. The cycle is always the same:

```
1. SEND     POST /v1/jobs                    {"repo": "app", "task": "...", "mode": "graph"}
2. RECEIVE  201                              {"id": "…", "status": "queued", …}
3. FOLLOW   GET /v1/jobs/{id}/stream         live events, until "end"   (or poll GET /v1/jobs/{id})
4. ANSWER   GET /v1/approvals?status=pending → POST /v1/approvals/{id} {"decision": "approve"}   (only if the job waits)
5. RESULT   GET /v1/jobs/{id}                status, answer, branch, diff summary, pull request
            GET /v1/jobs/{id}/artifacts/changes.patch   the diff
```

Every request carries `Authorization: Bearer <your API key>` (see SERVER.md, section 4.6, to create keys).

---

## 1. What to send

`POST /v1/jobs`

```json
{
  "repo": "app",
  "task": "Fix the failing date test in src/date.ts",
  "mode": "graph",
  "workflow": "default",
  "priority": 5,
  "approvals": { "edits": "auto", "commands": "allowlist" },
  "labels": { "ticket": "PAY-123", "team": "payments" },
  "webhook": "https://your-app.example.com/swarmlab/done",
  "idempotencyKey": "PAY-123-fix"
}
```

| Field | Required | Meaning |
|---|---|---|
| `repo` | | A repository name from the server's configuration (`GET /v1/repos`). **Leave it out** for work without code (ideas, tickets, diagrams, documents): the job gets an empty workspace |
| `files` | | `true`: every created or changed file comes back as its own artifact `files/<path>` (default: true without a repository, false with one) |
| `task` | yes | What to do, in plain words |
| `mode` | | `single` (default), `tree`, `swarm`, `graph` |
| `workflow` | graph | `"default"` (the repository's `.swarmlab/graph.json`), a name (`.swarmlab/workflows/<name>.json`), or a whole workflow object |
| `agent` | | Single mode: one of the repository's agents |
| `ref` | | Branch or commit to start from |
| `priority` | | Higher runs first |
| `approvals` | | This job's rules: `edits`, `fileOps`, `commands`, `mcp`: `"auto"`, `"ask"`, `"off"` (commands also `"allowlist"`) |
| `settings` | | Engine limits allowed by the server, for example `{"tokenBudget": 200000}` |
| `labels` | | Your own tags, to find jobs later (`GET /v1/jobs?label=ticket=PAY-123`) |
| `webhook` | | The server POSTs the finished job here (see 5) |
| `idempotencyKey` | | Sending the same key again returns the same job instead of a new one: safe retries |

---

## 2. What you receive

**Right away**: `201 Created` (or `200` with the existing job for a repeated `idempotencyKey`):

```json
{ "id": "2988e584-da89-4635-b828-3397681b28cd", "status": "queued", "task": "Fix the failing date test…",
  "repo": "app", "mode": "graph", "priority": 5, "attempts": 0, "maxAttempts": 2,
  "createdAt": "2026-10-16T09:12:00.000Z", "submittedBy": "my-app", "labels": { "ticket": "PAY-123" } }
```

**While it runs**: events, one per line of the live stream (`GET /v1/jobs/{id}/stream`, server-sent events), or as a list (`GET /v1/jobs/{id}/events?after=N`):

```json
{ "jobId": "2988e584-…", "seq": 9, "at": "2026-10-16T09:12:16.000Z",
  "event": { "kind": "approval", "id": "f77b…", "title": "fixer wants to change src/date.ts", "approvalKind": "edit" } }
```

| `event.kind` | Meaning |
|---|---|
| `status` | `queued`, `running`, `succeeded`, `failed`, `cancelled` |
| `sandbox` | The job's branch, for example `swarmlab/job-2988e584` |
| `call` | A model call (agent, tokens in and out) |
| `tool` | A tool call (agent, tool, input) |
| `message` | A message between agents |
| `node` | Graph mode: a step started or finished, and where it goes next |
| `edit`, `command` | A file change or a command, and whether it happened |
| `approval`, `approval-decided` | The job waits for a human / the human answered |
| `final` | The answer is ready |
| `retry`, `warning`, `pushed`, `pull-request` | Infrastructure news |

**At the end**: `GET /v1/jobs/{id}`

```json
{
  "id": "2988e584-…", "status": "succeeded", "attempts": 1, "tokens": 18450, "costUsd": 0,
  "result": {
    "answer": "Fixed parseDate: inputs without a time zone are read as UTC. The tests pass and the checker approved.",
    "stoppedBy": "done",
    "branch": "swarmlab/job-2988e584",
    "commit": "9f2c…",
    "diffStat": " src/date.ts | 2 +-\n 1 file changed, 1 insertion(+), 1 deletion(-)",
    "pushed": true,
    "prUrl": "https://github.com/your-org/app/pull/128",
    "metrics": { "inputTokens": 17000, "outputTokens": 1450, "calls": 13, "toolCalls": 9, "editsApplied": 1, "commandsRun": 2, "graphSteps": 6 }
  }
}
```

If `status` is `failed`, `error` says why. `result.files` lists the files created or changed. Artifacts: `changes.patch` (plain diff), `report.json` (answer, metrics, every agent's numbers), and with `files: true` one `files/<path>` per file: `GET /v1/jobs/{id}/artifacts?name=files/docs/orders.md`.

**Without a repository** (`{"task": "Draw the order flow as a Mermaid diagram in docs/orders.md"}`), `result` has no `branch`: the result is `answer` and the files.

---

## 3. Answer approvals (only for what your rules send to a human)

```
GET  /v1/approvals?status=pending
→ { "approvals": [ { "id": "f77b…", "jobId": "2988…", "kind": "edit", "title": "fixer wants to change src/date.ts",
                     "detail": "Convert input to UTC", "diff": "@@ src/date.ts line 2 @@\n- …\n+ …", "choices": ["Apply", "Reject"],
                     "status": "pending", "expiresAt": "…" } ] }

POST /v1/approvals/f77b…   {"decision": "approve"}          → 200
POST /v1/approvals/f77b…   {"decision": "reject"}           → 200
                            again                            → 409 (already decided)
```

For messages and tasks (`editable`), send `{"decision": "approve", "text": "the edited text"}`. The key needs the `approve` role.

---

## 4. Errors

| Code | Meaning | What to do |
|---|---|---|
| 400 | The request is wrong (unknown repo, mode, bad workflow…) | Read `error` and fix the request |
| 401 / 403 | Missing or unknown key / the key lacks the role | Check the key and its roles |
| 404 | No such job (or not yours) | |
| 409 | Already finished / already decided | Nothing to do |
| 429 | Queue full or too many active jobs for your key | Retry later, with backoff |
| 5xx | Server problem | Retry with the same `idempotencyKey` |

Errors are JSON: `{"error": "…"}`.

---

## 5. Without polling: webhooks

With `"webhook": "https://your-app/…"`, the server POSTs this when the job ends:

```json
{ "id": "2988e584-…", "status": "succeeded", "result": { "answer": "…", "branch": "…", "prUrl": "…" }, "error": null, "labels": { "ticket": "PAY-123" } }
```

Use `labels` to match it to your own records.

---

## 6. The Python client and example app (in `clients/python/`)

Standard library only, Python 3.8+.

```python
from swarmlab_client import SwarmLabClient

sl = SwarmLabClient("https://swarmlab.example.com", api_key="sl_...")

# Send, follow live, get the result
job = sl.submit("app", "Fix the failing date test", "graph", workflow="default", labels={"ticket": "PAY-123"})
for ev in sl.stream(job["id"]):
    print(ev["event"]["kind"])
job = sl.get(job["id"])
print(job["status"], job["result"]["answer"], job["result"]["branch"])
patch = sl.artifact(job["id"], "changes.patch")

# Without a repository: a diagram, saved locally with its path
job = sl.run(None, "Draw the order flow as a Mermaid diagram in docs/orders.md")
sl.download_files(job["id"], "out/")          # → out/docs/orders.md

# Or in one call, answering approvals with your own rule
job = sl.run("app", "Update the README", "single",
             approvals={"edits": "ask"},
             on_approval=lambda a: {"decision": "approve"} if a["kind"] == "edit" and "README" in a["title"] else {"decision": "reject"})
```

The example application does the whole cycle from a terminal:

```bash
export SWARMLAB_URL=http://127.0.0.1:8787 SWARMLAB_KEY=sl_...
python example_app.py --repo app --mode graph --task "Fix the failing date test" --out results/
python example_app.py --repo app --mode swarm --task-file task.md --approve ask      # you answer approvals in the terminal
python example_app.py --repo app --task "Explain the project" --approve auto --label ticket=PAY-123
python example_app.py --no-repo --task "Write 3 Jira tickets as JSON for…" --out results/   # no repository
python example_app.py --repo app --task "Add docs/api.md" --files --out results/             # repository + each file
python example_app.py --list
```

It prints the live events, shows each approval with its diff (and answers it: `--approve ask | auto | reject`), prints the answer, branch, diff summary and files, and saves `answer.md`, `job.json`, `changes.patch`, `report.json` and the created files under `files/`. Exit code: 0 if the job succeeded.

---

## 7. From other languages

**curl**

```bash
curl -s -X POST $URL/v1/jobs -H "Authorization: Bearer $KEY" -H "content-type: application/json" \
     -d '{"repo":"app","mode":"swarm","task":"Review the payment module"}'
curl -N -H "Authorization: Bearer $KEY" $URL/v1/jobs/$ID/stream
```

**JavaScript / TypeScript (Node 18+ or a browser)**

```ts
const H = { "content-type": "application/json", authorization: `Bearer ${KEY}` };
const job = await (await fetch(`${URL}/v1/jobs`, { method: "POST", headers: H,
  body: JSON.stringify({ repo: "app", mode: "graph", workflow: "default", task: "Fix the failing date test" }) })).json();
let cur;
do { await new Promise((r) => setTimeout(r, 2000)); cur = await (await fetch(`${URL}/v1/jobs/${job.id}`, { headers: H })).json(); }
while (!["succeeded", "failed", "cancelled"].includes(cur.status));
console.log(cur.status, cur.result?.answer, cur.result?.branch);
```

In a browser, `EventSource` cannot send headers: use `…/stream?token=<key>` with a read-only key, or call the server from your back end.
