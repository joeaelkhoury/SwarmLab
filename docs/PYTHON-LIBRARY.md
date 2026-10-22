# The `swarmlab` Python library

Run Swarm Lab agents, teams and workflows from Python, as a library. The same code works **on a Swarm Lab server**
and **on your machine without one**. Python 3.8+, standard library only.

```python
from swarmlab import SwarmLab, Agent, Workflow, Environment

sl = SwarmLab()                                   # a server: $SWARMLAB_URL (default http://127.0.0.1:8787), $SWARMLAB_KEY
r = sl.run("Fix the failing date test", repo="app", environment="auto", checks=True)
print(r.answer)
r.save_patch("fix.patch")
```

## 1. Install

From the downloaded Python kit (or `clients/python` of the source):

```bash
pip install ./clients/python          # or: cd clients/python && pip install -e .
python -m swarmlab --help
```

Without installing, put the folder on `PYTHONPATH` (or run your script from it).

**A server or not?**

- `SwarmLab(url, api_key)`: jobs go to a Swarm Lab server (started from VS Code's **Server** tab, `swarm-lab serve`, or Docker). Many jobs in parallel, approvals in the dashboard, saved workflows shared with your team.
- `SwarmLab.local(repo)`: no server. Each job runs on this machine with the `swarm-lab` program of the installed VS Code extension (found automatically; or set `SWARMLAB_SERVER_JS` to `…/dist/server/main.js`). Node.js 18+ and Git are needed.

```python
sl = SwarmLab.local("path/to/repo", provider="anthropic", model="claude-sonnet-5-5")   # key from $ANTHROPIC_API_KEY
sl = SwarmLab.local("path/to/repo", provider="openai", base_url="http://localhost:11434/v1", model="qwen2.5-coder")
sl = SwarmLab.local("path/to/repo", config="swarmlab.server.json")   # everything from a server configuration file
sl = SwarmLab.local("path/to/repo", provider="mock")                 # offline, scripted answers (to try things)
```

The repository must be a Git repository with a commit: jobs work on a branch of it, so your files are not changed;
the result is a patch (and a branch) to review.


### The configuration from VS Code: `SwarmLab.from_config()`

In VS Code, **Server tab → 📄 Create run files** writes `swarmlab-run/` with `swarmlab.client.json`, the library
and `example.py`. Then:

```python
from swarmlab import SwarmLab
sl = SwarmLab.from_config()          # ./swarmlab.client.json, ./swarmlab-run/swarmlab.client.json, or $SWARMLAB_CLIENT_CONFIG
print(sl.defaults)                   # your Setup: mode, settings (models, limits, tool mode…), approvals
r = sl.run("Fix the failing test", max_agents=2)   # keywords win over the defaults; settings/approvals dicts are merged
```

The file: `{"url": "http://127.0.0.1:8787", "keyEnv": "SWARMLAB_KEY", "defaults": {"repo": "app", "mode": "swarm",
"settings": {...}, "approvals": {...}}}`. The key is read from the variable named by `keyEnv`.

## 2. Running a job

`run(task, **options)` submits a job, waits for it, and returns a `Result`. Every option of a job is a keyword:

```python
r = sl.run(
    "Add input validation to the signup form, with tests",
    repo="web",                          # a server's repository name (local: the repo of SwarmLab.local, or a path)
    mode="single",                       # single | tree | swarm | graph
    environment="auto",                  # install the project first (see section 4)
    checks=True,                         # run the tests, and check "done" independently at the end
    approvals="unattended",              # or "careful", or Approvals(...): what waits for a human
    approve="auto",                      # how *this script* answers approvals (section 5)
    max_steps=20, token_budget=300_000,  # any setting, by name
    labels={"ticket": "WEB-142"},
)
print(r.status, r.ok, r.tokens, r.cost_usd)
print(r.answer)        # the final answer
print(r.files)         # files created or changed
print(r.patch())       # the diff
print(r.report())      # every step with its tokens, cost and time (Markdown; report("json") for a dict)
print(r.environment)   # how the environment was prepared
r.raise_for_status()   # JobFailed unless it succeeded (or run(..., check=True))
```

| Keyword | Meaning |
|---|---|
| `repo`, `ref`, `files` | Repository (none: an empty workspace for ideas, documents, diagrams), start ref, return every changed file |
| `mode` | `single`, `tree`, `swarm`, `graph` |
| `agent` | One agent for a single-mode job: an `Agent(...)` or the name of one in the repository's policy |
| `agents` | Agents a lead may use (tree, swarm), with their models and permissions |
| `prompt` | The lead's instructions for this job |
| `workflow` | A `Workflow`, a saved workflow's name, a `.json` file, or a dict (graph mode) |
| `environment` | `"auto"`, a preset, a server environment's name, an `Environment(...)`, a dict, or `False` |
| `checks` | `True` (tests + verify), a test command (`"pytest -q"`), or `Checks(...)` |
| `approvals` | `"unattended"`, `"careful"`, or `Approvals(edits=…, commands=…, command_allow_list=[…], …)` |
| `settings` or any setting | `Settings(...)`, a dict, or keywords: `max_steps_per_agent` (`max_steps`), `max_agents`, `token_budget`, `max_tokens_per_call`, `cost_budget_usd`, `answer_length`, `answer_style`, `tool_mode`, `max_continuations`, `max_parallel_calls`, … (a server accepts those in its `allowedSettingOverrides`) |
| `memory` | A session name to share memory with other jobs, `Memory(session, topics)`, or `False` |
| `data` | Input files/folders (list) or `Data(inputs, output)` |
| `mcp`, `skills`, `hooks`, `models`, `providers` | MCP servers (`["github"]`), skills, HTTP hooks, `"cheapest"`/`"balanced"`/`"best"`, RAG/decision models |
| `rag`, `decision`, `web` | Turn code search, the decision model and web research on (`True`) or off (`False`) for this job |
| `profile` | A saved configuration to start from (the job's own fields win) |
| `labels`, `priority`, `webhook`, `max_attempts`, `timeout_sec`, `idempotency_key` | Bookkeeping and delivery |
| `extra` | A dict of fields sent as they are (for anything newer than this library) |

A wrong name or value is reported **before** anything is sent, with the list of valid ones. `sl.preview(task, …)`
returns the job's JSON without sending it; `sl.validate(task, …)` asks the server whether it would accept it.

**Not waiting:** `job = sl.submit(task, …)` returns at once; then `job.wait()`, `job.events()` (live, as flat dicts
with a `kind`), `job.cancel()`, `job.approvals()`. **Several at once:** `sl.run_many(["task 1", {"task": "task 2",
"mode": "tree"}], repo="app")` returns the results in order.

## 3. Agents

```python
fixer = Agent("fixer", "You fix bugs with the smallest possible change, and add a test.",
              model="lead",                    # "lead", "worker", or an exact model id
              edit=["src/**", "tests/**"],     # files it may change ([] = none)
              tools=["read_file", "search_text", "edit_file", "run_tests"])   # only these tools
reviewer = Agent("reviewer", "You review changes. You never edit.", edit=[], description="reviews diffs")

sl.run("Fix the date parsing bug", repo="app", agent=fixer)                    # one agent
sl.run("Audit the error handling", repo="app", mode="swarm", agents=[fixer, reviewer])   # a team
```

## 4. Environments

```python
Environment.auto()                                   # detect and install (package.json, pyproject.toml, go.mod, …)
Environment.python(setup=["pip install -e .[dev]"])
Environment.vscode_extension()                       # install, compile, virtual screen for the extension's tests
Environment.docker("node:22", setup=["npm ci"], network=False)                # any image
Environment(preset="node", pre_setup=["apt-get install -y xvfb"], env={"CI": "1"}, test="npm run test:unit")
Environment.named("web-e2e")                         # one of the server's environments
Environment.load(".swarmlab/environment.json")       # and .save(...) to write one for the repository
```

Every command of the job runs in it. Prepare one and run commands **without agents**:

```python
out = sl.env("path/to/project", Environment.vscode_extension(), test=True)
print(out["ok"], out["runs"][0]["output"])
```

**A real editor.** Swarm Lab can download VS Code (or Insiders, or VSCodium), install .vsix files and extensions,
start the editor, and test the extensions in it, on Linux, macOS, Windows or in a container:

```python
from swarmlab import VSCode

editor = VSCode(flavor="vscodium",                       # or "vscode" (default), "insiders", executable="cursor"
                install=["vendor/dependency.vsix"],      # plus the workspace's own extension, packaged
                commands=["myExt.hello", {"command": "myExt.add", "args": [41]}],   # must run without an error
                check="test/smoke-check.js",             # module.exports = async (vscode, report) => true
                require="regression")                    # the job fails if it breaks an extension that worked

r = sl.run("Add a 'Copy as Markdown' command, with a test", repo="my-extension",
           environment=Environment.vscode_extension(editor), checks=True, approve="auto")
print(r.vscode["baseline"]["ok"], r.vscode["final"]["ok"])   # before and after the job, in the real editor
print(r.editor_report())                                     # every extension, command result, error and log

# Only check a .vsix built elsewhere, no agents:
out = sl.env("build", Environment.editor(VSCode(install=["my-ext-1.2.0.vsix"], commands=["my.hello"])), run=["swarmlab-vscode smoke"])
```

In a workflow, `.command("check", "swarmlab-vscode check", on_fail="fix", max_visits=4)` loops until the extension
works in the editor. All fields and presets: [ENVIRONMENTS.md](ENVIRONMENTS.md), section 6.

## 5. Approvals from Python

When something waits for a human (an edit, a command, an MCP call), `run` and `wait` answer with `approve=`:

| `approve=` | What happens |
|---|---|
| `"ask"` | Asked in this terminal (the default when you run in a terminal) |
| `"auto"` / `"reject"` | Everything approved / rejected |
| `None` | Left for someone else (the server's dashboard); a local job rejects |
| a function | Called with the approval (`title`, `kind`, `detail`, `diff`, `choices`); return `True`, `False`, `None` (leave it), a choice, or `{"decision", "choice", "text"}` |

```python
def policy(a):
    if a["kind"] == "command":
        return a["diff"].startswith("$ pytest")      # tests yes, other commands no
    return True                                       # edits are fine: the result is a branch to review

sl.run("Fix it", repo="app", approvals={"edits": "ask", "commands": "ask"}, approve=policy)
```

## 6. Workflows

A workflow is a list of steps. Steps follow each other in the order you add them unless you say otherwise:

```python
fixer = Agent("fixer", "Make the smallest change that fixes the problem.", edit=["src/**"])
reviewer = Agent("reviewer", "Review strictly. End with DECISION: ok or DECISION: redo.", edit=[])

wf = (Workflow("fix-and-test", "Fix, test, review", environment=Environment.auto())
      .agent("fix", "Fix this: {task}\n\nLast test output, if any:\n{last}", agent=fixer)
      .command("test", "python -m pytest -q", on_fail="fix", max_visits=3)    # pass → next step
      .agent("review", "Review the change for: {task}", agent=reviewer, routes={"ok": "done", "redo": "fix"}))

wf.check()                 # every problem at once (the server's rules), before anything runs
print(wf.mermaid())        # a diagram (GitHub renders Mermaid in Markdown)

r = sl.run("The total ignores quantities", repo="shop", workflow=wf, approve="auto")
```

| Step | Use |
|---|---|
| `.agent(id, task, agent=…, routes=…, next=…, max_visits=…)` | An agent works. With `routes`, it ends its reply with `DECISION: <key>`. |
| `.command(id, command, on_pass=…, on_fail=…, max_visits=…)` | A shell command; exit 0 = pass (default: next step), else `on_fail` (default: done). |
| `.decide(id, question, yes=…, no=…)` | A yes/no question about the previous output, answered by the decision model. |
| `.choice(id, question, {"option": "meaning"}, routes=…)` | One of several options. |
| `.score(id, question, ["low", "mid", "high"], {0: …, 1: …, 2: …})` | A level on a scale. |

Placeholders in tasks: `{task}`, `{last}` (the previous step's output), `{node:<id>}`, `{data}`, `{output}`.
`max_visits` with `on_limit` stops loops. `"done"` ends the workflow.

**Save it once, use it everywhere**: a saved workflow carries its agents, prompts and environment.

```python
sl.save_workflow(wf)                                # server: PUT /v1/workflows/fix-and-test (local: in the data folder)
sl.run("Fix bug #12", repo="shop", workflow="fix-and-test")
sl.workflows(); sl.workflow("fix-and-test"); sl.delete_workflow("fix-and-test")
wf.save("fix-and-test.json"); Workflow.load("fix-and-test.json")
```

The same file runs from the command line, with or without a server:

```bash
python -m swarmlab run "Fix bug #12" --repo shop --workflow fix-and-test.json --approve auto
python -m swarmlab --local . --provider anthropic run "Fix bug #12" --workflow fix-and-test.json
swarm-lab run --repo-path . --task "Fix bug #12" --workflow fix-and-test.json      # the Node program itself
```

## 7. The command line

```bash
python -m swarmlab run "Explain the project" --repo app --approve none
python -m swarmlab run "Fix it" --repo app --env auto --checks --set max_steps=20 --patch fix.patch
python -m swarmlab preview "Fix it" --repo app --env python            # the JSON, nothing sent
python -m swarmlab validate "Fix it" --repo app                        # the server's verdict
python -m swarmlab workflow validate fix-and-test.json                 # offline (add --url for the server's rules)
python -m swarmlab workflow diagram fix-and-test.json
python -m swarmlab workflow push fix-and-test.json                     # save on the server
python -m swarmlab env . --test                                        # environment only, no agents
python -m swarmlab caps                                                # what the server allows
python -m swarmlab approvals ; python -m swarmlab decide <id> --reject
```

`--url`, `--key` (or `SWARMLAB_URL`, `SWARMLAB_KEY`) choose the server; `--local [REPO]` runs without one.

## 7b. Ready workflows, notebooks, gates, schedules

```python
sl.templates(category="Banking")                       # the gallery
r = sl.run_template("model-monitoring", repo="models", notebook="monitoring/pd.ipynb", thresholds="psi<0.2")
wf.notebook("train", "train.ipynb", {"max_depth": 4}).gate("targets", "metrics.json", "auc>=0.75", on_fail="improve")
wf.agent("card", "Write MODEL_CARD.md", model="worker", check="swarmlab-check files MODEL_CARD.md", retries=3)
sl.schedule("monthly", "0 7 1 * *", template="model-monitoring", repo="models", inputs={...}, timezone="Europe/Paris")
sl.outcomes()                                          # runs, success, cost, time saved
```

Everything about them: [WORKFLOWS.md](WORKFLOWS.md).

## 8. More

- `sl.capabilities()`: version, modes, repositories, saved workflows, profiles, allowed settings, environments, features, your roles.
- `sl.save_profile("team-defaults", approvals="careful", environment="auto", max_steps=15)`; then `profile="team-defaults"`.
- `sl.costs(group_by="model")`, `sl.jobs(status=["failed"])`, `sl.approvals()`, `sl.decide(id, "approve")`.
- `Result`: `answer`, `status`, `ok`, `error`, `files`, `branch`, `commit`, `diff_stat`, `tokens`, `cost_usd`, `environment`, `metrics`, `patch()`, `save_patch()`, `report()`, `environment_log()`, `artifact(name)`, `download_files(folder)`.
- The older single-file client `swarmlab_client.py` still works and now also has `environment=`, `capabilities()`, `validate()` and the workflow methods.
