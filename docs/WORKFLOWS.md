# Workflows: ready to use, built without code, checked by numbers

Swarm Lab runs **workflows**: steps done by agents, notebooks, commands and checks, with a person deciding only what
matters. This guide covers the ready workflows (the gallery), building your own in the **Studio** without code,
the **banking and model lifecycle** workflows, how checks let **small, cheap models** do reliable work, and
**schedules**.

## 1. The Studio (no code)

Open `http://<server>/studio` (the server's address; on your machine `http://127.0.0.1:8787/studio`), or click
**✦ Studio** at the top of the dashboard. The server prints the Studio address when it starts.

1. **What do you want done?** Pick a card in the gallery (🐞 Fix a bug, 📓 Run a notebook, 🧪 Validate a model…),
   search by words, or filter by category.
2. **Fill in the form.** Each field says what it wants, with an example. Choose the project (repository) when the
   workflow needs one. Nothing runs until you press **Run**.
3. **Follow it.** Each step shows as it runs. When something needs you (an approval, a decision line), it appears
   in your **inbox**.
4. **Read the results** in the page: reports as formatted text, CSV files as tables, notebooks with their charts.

**Build your own** with the builder: add steps with the buttons, in order, and the diagram updates as you go.

| Step | Use it to |
|---|---|
| 🤖 Agent step | have an agent do something: write, analyse, fix. Choose 🧠 a capable model or ⚡ a fast, cheap one, and add **✅ a check of its result** (section 4). |
| ✅ Check | stop or go back when a result is not right: files exist, every claim has a link, no prices written, a text is present, not too long, the tests pass, the extension works in VS Code. |
| 📓 Notebook | run a Jupyter notebook cell by cell, with parameters. A failing cell fails the step, with its error. |
| 🎯 Numbers gate | let numbers decide: a metrics file and targets (`auc >= 0.75`, `psi < 0.2`). |
| ⚙️ Command | run any command of the project (`npm run build`, `make report`). |

For each check, gate, notebook and command you choose **what happens if it does not pass**: stop and report, or go
back to an earlier step (for example the agent step that wrote the result) and try again, a number of times. Save
the workflow and it joins the gallery for everyone on the server.

## 2. The gallery

| Category | Workflows |
|---|---|
| Software | 🐞 Fix a bug · 📦 Update dependencies safely · 🔍 Review a change · 📝 Write or update the README · 🧩 Change a VS Code extension, tested in VS Code |
| Data | 📓 Run a notebook and explain the results · 📊 Answer a question with your data |
| Research | 🔎 Research brief with sources |
| Business | 📄 Draft a client proposal · 🎯 Find and qualify prospects (nothing sent) · ✅ Meeting notes → actions · 🗓️ Weekly project update · 💬 Draft replies to customer messages (nothing sent) |
| Banking | 🏋️ Train a model until it meets its targets · 🧪 Independent model validation pack · 🚀 Go-live readiness (mise en production) · 📉 Monthly model monitoring · 💳 Credit memo draft · 🧾 AML / fraud alert review pack · 🧮 Reconcile two files and list the breaks |

Every workflow checks its own result before it ends. From Python: `sl.templates()`, `sl.run_template(name, ...)`;
over HTTP: `GET /v1/templates`, `POST /v1/templates/<name>/run` with `{"inputs": {...}, "repo": "..."}`
(`"preview": true` shows the job without running it).

## 3. Banking: the model lifecycle, then operations

The model workflows follow the life of a model: **train → validate independently → put in production → monitor**,
then train again. Notebooks do the computing, gates check the numbers, agents only repair, explain and write. Every
decision that matters stays with a named person: the workflows prepare it completely and leave the decision line
blank (`[DECISION]`, `Approved by: [NAME]`), like a price left for the salesperson.

| Workflow | What it does | What a person decides |
|---|---|---|
| 🏋️ Train a model until it meets its targets | Runs your training notebook with parameters; a gate checks `metrics.json` against your targets (AUC, KS, Gini…); if short, an agent improves it **within the limits you write** (for example "hyperparameters only, never the test set") and it trains again; then `MODEL_CARD.md`, checked to have its metrics and limitations. | Whether the model goes to validation. |
| 🧪 Independent model validation pack | Reproduces the model from its own notebook (a failure is a finding, never fixed by the validator); writes and runs a separate `validation.ipynb` (AUC, KS, Gini, PSI by score band, the same per segment, charts); a gate against your thresholds; `VALIDATION_REPORT.md` with findings and severities. A check refuses any sentence saying the model is approved. | `Validator decision: [DECISION]`. |
| 🚀 Go-live readiness (mise en production) | The project's tests; champion / challenger: the new version is not worse than the one in production on each metric by more than the drop you accept (latency: lower is better); an optional scoring notebook run end to end; then `CHANGE_REQUEST.md` with evidence, risks, monitoring and a rollback plan. Any failed check gives `READINESS.md` (what failed, what to do) instead. It never deploys. | `Approved by: [NAME], date: [DATE]`, then your own deployment process. |
| 📉 Monthly model monitoring | Runs the monitoring notebook for the period; a gate on drift and performance; `MONITORING.md` is an all-clear with the numbers, or an alert: which thresholds broke, by how much, likely causes, and the options (watch, recalibrate, retrain) without choosing. Schedule it (section 5). | What to do about an alert. |
| 💳 Credit memo draft | `ratios.ipynb` computes growth, EBITDA margin, net debt / EBITDA, DSCR, current ratio, equity ratio per year (missing lines stay missing, never estimated); `CREDIT_MEMO.md` uses only those numbers. A check refuses "we recommend approving / declining". | `Credit decision: [DECISION]`, `Conditions: [CONDITIONS]`. |
| 🧾 AML / fraud alert review pack | For each alert, the facts from the case data with their file and row; a suggested disposition (escalate, needs more information, likely false positive) with its reason and confidence; `review.csv` is checked for its columns, and for not closing or reporting anything. | Every alert's disposition. |
| 🧮 Reconcile two files | A notebook matches the files exactly (your matching rule, your tolerance) and writes `breaks.csv` (missing, amount differs, duplicate); `RECONCILIATION.md` totals and explains the largest breaks. | What to correct. |

**What this changes for a team.** The work that fills days (reproducing, computing, comparing, writing up) is done
and checked before anyone looks; the person spends their time on the decision, with everything needed in one report.
The outcomes report (`/v1/outcomes`, `sl.outcomes()`) shows runs, success, cost and the time saved against doing it
by hand (`manualMinutes` per workflow).

**What it is not.** These workflows support a model risk practice; they do not make one compliant by themselves.
Thresholds, segment choices, the independence of validation and the sign-off remain your institution's policy.
Run them on a server inside your network (or `SwarmLab.local`) when the data must not leave it, and choose a model
provider your institution allows.

**Your notebooks.** The model workflows expect your notebooks to have a cell tagged `parameters` (the parameters
are injected after it) and to write their numbers to a JSON file (`metrics.json` by default), for example:

```python
import json
json.dump({"auc": auc, "ks": ks, "gini": 2 * auc - 1, "psi": psi}, open("metrics.json", "w"))
```

## 4. Small, cheap models: let checks judge, not the model

A weak model fails mostly in two ways: it believes it is done when it is not, and it cannot find its own mistake.
Swarm Lab removes both from the model's job:

- **A check on the step.** Any agent step can carry a `check`: a command that judges the result (exit 0 = good).
  When it fails, the same agent receives exactly what the check printed ("missing columns: source", "auc = 0.71
  does not meet >= 0.75", "no source for: Installers…") and tries again, up to `retries` times (default 2, at most
  5). Still failing, the step goes to `onFail` (or on, with the failure noted). The model only has to fix one named
  problem at a time, which small models do well.
- **Gates decide with numbers.** `swarmlab-check metrics metrics.json auc>=0.75 psi<0.2` decides, not a model's
  opinion; `compare` decides champion against challenger.
- **Small steps.** The gallery's workflows give each agent one clear job with its inputs written in, rather than one
  long open task.
- **The right model per step.** Choose ⚡ a fast, cheap model for simple, checked steps and 🧠 a capable one for
  the hard thinking (`"model": "worker"` or `"lead"` on a step).

```json
"write": { "task": "Write review.csv …", "model": "worker",
           "check": "swarmlab-check csv review.csv --columns alert_id,summary,evidence --min-rows 1",
           "retries": 3, "onFail": "escalate" }
```

**The checks** (`swarmlab-check`, on every job's PATH): `files`, `sources` (every claim has a link), `contains`,
`absent`, `prices` (no amount of money), `csv` (columns, rows), `json`, `words`, `test` (the project's tests),
`metrics FILE RULE…` (rules like `auc>=0.75`, or `auc:ge:0.75`), `compare NEW CURRENT METRIC… --max-drop X`. Each
prints what failed in plain words, which the next step reads as `{last}`.

**Notebooks** (`swarmlab-nb`, in environments with `"notebooks": true`): `swarmlab-nb run NOTEBOOK -p name=value`
runs every cell, injects the parameters after the cell tagged `parameters`, keeps outputs and charts in
`NOTEBOOK.out.ipynb` (or `--in-place`), and reports each failing cell with its error; `--optional` passes when no
notebook is given. `"notebooks": { "packages": ["pandas", "scikit-learn"] }` installs packages for them.

## 5. Schedules: run it again without anyone starting it

```python
sl.schedule("pd-monitoring", "0 7 1 * *", template="model-monitoring", repo="models", timezone="Europe/Paris",
            inputs={"notebook": "monitoring/pd.ipynb", "parameters": "month=\"latest\"", "thresholds": "psi<0.2\nauc>=0.70"})
sl.schedules(); sl.run_schedule_now("pd-monitoring"); sl.delete_schedule("pd-monitoring")
```

Cron syntax (minute hour day month weekday) in the time zone you give. Over HTTP: `PUT /v1/schedules/<name>` with
`{"cron", "timezone", "job"}`, `POST /v1/schedules/validate` shows the next five times. Setting a schedule needs the
`approve` role, because it runs unattended again and again.

## 6. From Python

```python
from swarmlab import SwarmLab, Workflow, Agent, Environment

sl = SwarmLab()
r = sl.run_template("model-validation", repo="models", notebook="models/pd.ipynb", recent="data/2026q2.csv",
                    thresholds="auc>=0.70\npsi<0.25")
print(r.status, r.files)

wf = (Workflow("score-and-report", environment=Environment.notebooks_env(["pandas", "matplotlib"]))
      .notebook("score", "score.ipynb", {"month": "2026-09"}, on_fail="repair")
      .gate("quality", "metrics.json", "auc>=0.75", "psi<0.2", on_fail="explain")
      .agent("explain", "Explain the results for the risk committee.", model="worker",
             check="swarmlab-check contains REPORT.md \"## Recommendation\"", retries=3)
      .agent("repair", "Fix the failing cell: {last}", next="score"))
sl.save_workflow(wf)
```
