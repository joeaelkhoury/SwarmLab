# Python workflows without extension source

[README](../README.md) · [Run modes](RUN-MODES.md) · [Manual](../MANUAL.md) ·
[Server quickstart](../SERVER-QUICKSTART.md)

## 1. Download the starter files together

Use Python 3.8 or newer; only the standard library is needed. Download these files
from the public repository into the **same local folder**, preserving their names:

- [swarmlab_client.py](../clients/python/swarmlab_client.py): API client.
- [fix_job.py](../clients/python/fix_job.py): bounded job submission/follow-up, no approval answering.
- [configuration_examples.py](../clients/python/configuration_examples.py): offline-first payload examples.
- [example_app.py](../clients/python/example_app.py): optional interactive streaming application.

For the complete repair demo, also download workflow_demos.py, test_workflow_demos.py,
and the entire demo_project directory (README.md, .gitignore, pricing.py, labels.py,
and test_demo.py). Prefer the starter ZIP so these relative paths stay intact.

The examples import their neighbors: configuration_examples needs fix_job and
swarmlab_client; fix_job and example_app need swarmlab_client. No TypeScript source
or pip install is needed. The VSIX does not install these Python files.
Run the commands below from that download folder; use python3 where appropriate.

## 2. Source-free offline smoke check

```sh
python configuration_examples.py --list
python configuration_examples.py --example single --dry-run
python configuration_examples.py --example tree --dry-run
python configuration_examples.py --example swarm --dry-run
python configuration_examples.py --example graph --dry-run
python fix_job.py --repo demo-app --mode single --task "Explain the test setup; do not edit" --out preview-01 --dry-run
```

These commands print choices/JSON without networking or model calls. Dry-run is
also configuration_examples' default; only its explicit submit option uses the
network. Previews do not validate remote models, policy, repositories, or workflows
and do not demonstrate a real fix. Source-dependent full-test scripts are developer
integration tests, not prerequisites for these public examples.

## 3. Start a reachable native server

1. Install/open the extension and open your practice Git project in VS Code.
2. In Setup, save a supported API provider or local endpoint, models, and provider key.
   Offline mock is suitable only for scripted demonstrations. VS Code language models
   cannot be used by the standalone server.
3. Choose **Server → Start local server**. On first use it creates/opens configuration;
   review it and click again to start. The installed VSIX supplies the bundled server.
   No extension source build is needed; Docker is optional.
4. Review the server's repository paths, base references, approvals, and permissions.
   Restart after changing provider/model settings. The launcher forwards supported
   saved provider credentials to the child without writing them to configuration.
5. Save/test the server connection in the Server tab. Keep local learning on loopback.

The generated repository name matches the open folder basename. Example payloads
use **demo-app**: configure that name on the host, or override it with a JSON config
using your actual registered name. The repository must have a real existing Git
commit and valid base reference; an extracted ZIP alone is insufficient. Worktrees
use committed files, not unsaved edits. Install project dependencies/test tools
on the server. A reachable remote server works too when properly configured.

The generated local configuration has no access keys: keep it loopback-only.
Before sharing remotely, configure authentication, TLS/reverse-proxy protection,
network restrictions, and a dedicated runtime account. Worktrees are not a sandbox.

## 4. Keep credentials outside scripts

The Python client uses the **server access key**, not the model-provider key.
Supply it through the environment (or omit it for unauthenticated loopback-only use).
Use submit/read roles for the bounded client; review approvals with a separately
authorized Server/dashboard session. Obtain real secrets privately, not in shared
shell history, committed files, job JSON, or transcripts. Placeholder examples:

```powershell
$env:SWARMLAB_URL = 'http://127.0.0.1:8787'
$env:SWARMLAB_KEY = '<server-access-key>'
```

```sh
export SWARMLAB_URL='http://127.0.0.1:8787'
export SWARMLAB_KEY='<server-access-key>'
```

Provider credentials belong in the host's secret/environment setup. Never put
credentials or headers in job configuration.

## 5. Submit one small job

After registering demo-app (or substituting the actual server repo name):

```sh
python fix_job.py --repo demo-app --mode single --task "Explain the test setup without changing files" --token-budget 12000 --max-steps 6 --wait 180 --out run-01
```

To submit an example payload, deliberately opt into networking:

```sh
python configuration_examples.py --example single --submit
```

That example asks to fix a date test in a specific file: adapt the task/repo to
real files first. Configuration examples submit and print an ID; they do not wait,
fetch reports, or answer approvals. Review/follow the job in Server/dashboard.

For JSON configuration, use API camelCase fields; CLI settings merge by key:

```json
{
  "repo": "demo-app",
  "task": "Explain the test setup without changing files",
  "mode": "single",
  "settings": { "tokenBudget": 12000, "maxStepsPerAgent": 6 }
}
```

Save that as a local job JSON, then:

```sh
python fix_job.py --config job.json --out run-02 --dry-run
python fix_job.py --config job.json --out run-02
```

Local defaults < JSON < explicit CLI. No implicit mode is sent by fix_job, so a
profile/harness may select it. Server validation is authoritative. Profiles merge
first; harness settings/providers sit below explicit job settings/providers.
Harness RAG/decision switches can replace top-level flags; avoid conflicting flags.
Graph needs a saved workflow name or valid inline graph; named agent is single-only.

## 6. Approvals, deadlines, and reports

fix_job never approves edits or commands. Host policy may already permit actions.
At waiting status it exits with review instructions; use Server/dashboard to decide.
Then follow the existing ID with a fresh output directory:

```sh
python fix_job.py --job-id JOB_ID --out followup-01 --wait 180
```

| Exit | Meaning |
|---|---|
| 0 | Succeeded, or dry-run |
| 1 | Failed job |
| 2 | Input, HTTP/network, or report I/O error |
| 3 | Cancelled |
| 4 | Waiting for human approval; none sent by this script |
| 5 | Local deadline; job continues, no cancellation sent |

Completion saves fixed job.json, report.md, and report.json filenames; waiting
saves only job.json. Existing files are never overwritten. Use a new directory for
each follow-up. It does not download server artifact paths. Missing reports can
return 2 even after a successful job, and partial files may remain.

There are no automatic submission retries. Inspect Server before resubmitting;
a stable idempotency key supports retries of the same submission, not a new task.
Review the branch/patch, reports, and tests before merging. Success is not proof
of a correct fix, full VS Code host parity, or sandboxing.

## 7. Complete four-mode repair demo

This is a concrete stdlib repair exercise, not a claim of live-model verification.
The same five-file fixture drives every mode. The committed baseline has six tests
and **two intentional failures**; a successful repair means the unchanged six tests
run with exit code 0 and OK, plus source review confirms both contracts.

### Create and commit only a new fixture repository

Run from the extracted Python kit (or clients/python). Choose a NEW absolute path
outside the kit and all existing Git workspaces; its parent must already exist.
Replace the example path everywhere. On Windows use C:/practice/demo-app instead.
The initializer copies known files only and never runs Git:

```sh
python workflow_demos.py --init-demo /absolute/practice/demo-app
```

Manually run the following ONLY on that newly created fixture folder, never your
real workspace. Git must be installed; the identity applies only to this commit:

```sh
git -C /absolute/practice/demo-app init
git -C /absolute/practice/demo-app add README.md .gitignore pricing.py labels.py test_demo.py
git -C /absolute/practice/demo-app -c user.name="Demo User" -c user.email="demo@example.invalid" -c commit.gpgsign=false commit -m "Intentional two-regression baseline"
git -C /absolute/practice/demo-app tag demo-baseline
```

In a separate terminal, change to that new fixture folder and run:

```sh
python -m unittest -v
```

Expected baseline: exit 1, Ran 6 tests, FAILED (failures=2): test_quantities and
test_mixed_whitespace. Do not repair the baseline or move the tag between modes.
The required fixes are quantity multiplication in pricing.total and whitespace
splitting/joining in labels.slug; the job must not edit tests.

### Start the bundled server against this fixture

1. Open the new demo-app folder in VS Code, not the kit or extension source.
2. Configure a real API/local provider and working lead/worker models in Setup;
   test connection and tool calling. Mock output is not repair evidence, and VS Code
   language models are not a standalone server provider.
3. Choose Server → Start local server in the installed extension. Review the
   generated configuration, then start again. No source build or Docker is needed.
4. Register the absolute fixture path as demo-app and allow demo-baseline as its
   base ref. The generated repo name should match the folder; verify rather than
   assume. The committed repo must exist on the server filesystem for remote use.
5. Permit native file reads, edits, delegation tools and Python test commands with
   human review/ask approvals; keep loopback learning local. Do not enable blanket
   automatic approval. Restart after host configuration/provider changes and test
   the connection. See the [server reference](../SERVER.md) for exact host fields.
6. Return your client terminal to the Python kit. Set SWARMLAB_URL and, when
   required, SWARMLAB_KEY as described above; this is the server access key, not the
   provider key. Python must be on the server PATH.

### Preview all four payloads, without networking

```sh
python workflow_demos.py --mode single --repo demo-app --dry-run
python workflow_demos.py --mode tree --repo demo-app --dry-run
python workflow_demos.py --mode swarm --repo demo-app --dry-run
python workflow_demos.py --mode graph --repo demo-app --dry-run
python -m unittest -v test_workflow_demos
```

Default behavior is preview too. The public suite checks offline payloads, safe
fixture creation, expected red baseline, and mocked submission; it is not a live
server/model test. If the server uses python3 or the Windows launcher, append
--python-command python3 or --python-command "py -3" to BOTH preview and submission.
Only these three fixed command choices are accepted; no arbitrary shell input.
The graph command is a literal server-side command, not the client's interpreter.

### Submit independently, then follow each actual ID

Each command below explicitly submits one job and prints its ID; it does not wait,
answer approvals, or prove success. Run and review one mode before the next:

```sh
python workflow_demos.py --mode single --repo demo-app --submit
python workflow_demos.py --mode tree --repo demo-app --submit
python workflow_demos.py --mode swarm --repo demo-app --submit
python workflow_demos.py --mode graph --repo demo-app --submit
```

Every payload uses ref demo-baseline, maxAttempts 1, a 900-second timeout,
80,000-token budget, 24 steps per agent, and at most four agents including the lead.
The server creates an independent job worktree at the same tag; one mode's repair
must not become another's starting point. These are limits, not cost guarantees.

Replace the placeholders with the printed IDs, keeping report folders distinct:

```sh
python fix_job.py --job-id SINGLE_JOB_ID --out demo-single-01 --wait 180
python fix_job.py --job-id TREE_JOB_ID --out demo-tree-01 --wait 180
python fix_job.py --job-id SWARM_JOB_ID --out demo-swarm-01 --wait 180
python fix_job.py --job-id GRAPH_JOB_ID --out demo-graph-01 --wait 180
```

On exit 4, inspect and decide each pending request in Server/dashboard; neither
script approves anything. Then follow the SAME ID into a fresh folder:

```sh
python fix_job.py --job-id GRAPH_JOB_ID --out demo-graph-02 --wait 180
```

Exit 5 means only the local wait expired; do not resubmit. Follow the same job
again with another unused folder. Reports never overwrite previous files. Review
the actual branch/patch, baseline and final command evidence, approvals and limits.
A repaired suite should say Ran 6 tests and OK with exit 0; server status alone is
not enough. No live-provider repair has been verified by this documentation.

| Mode | Concrete organization and evidence |
|---|---|
| Single | One agent reads both contracts, reproduces failures, repairs only pricing.py and labels.py, and reruns the full suite. |
| Tree | Lead delegates independent pricing/labels workers with separate file ownership, then asks a read-only verifier for the full suite after both handoffs. |
| Swarm | Persistent pricing/labels workers read_board, post_note cause and test evidence; verifier uses ask_peer, waits for both READY handoffs, then tests; lead resolves blockers with ask_agent. |
| Graph | Inline plan → implement → test command → review; failed tests or rejected review return to implement, bounded by visits and total steps. |

The graph test node executes the chosen Python unittest command. Implementation
and test allow at most three visits each, review two, and the graph twelve total
steps. Exhaustion may end without a verified repair: inspect latest test evidence
and NOT VERIFIED notes rather than treating termination as approval. Graph commands
still obey host permissions/approvals. Tree/swarm organization is a model instruction,
not a guarantee that a model will delegate or obey ownership; inspect actual tools
and handoffs. Worktrees are not sandboxes. Never merge without reviewing the result.

## 8. Advanced controls and the interactive example

Exact lead/worker model CLI overrides disable automatic model selection. The host
must explicitly add leadModel/workerModel to allowedSettingOverrides: **they are
not default-allowed**. Named-agent and workflow node models can still override role
defaults. The examples filter reference settings to the default allowlist; those
reference values are not discovered host defaults.

Optional providers.rag.model and providers.decision.model bind models to existing
host services, not arbitrary URLs/keys. RAG requires enabled/configured embeddings;
decisions require an enabled usable decision client. The API field is singular
**decision**. MCP, hooks, data roots, settings, and feature gates remain host-controlled.

The optional example_app streams events and can answer approvals interactively:

```sh
python example_app.py --repo demo-app --mode single --task "Explain the test setup" --approve ask
```

Keep interactive approval mode. Its automatic approval option approves everything;
do not use it as a beginner safety default. Unlike fix_job, this application has
an approval-answering background thread and optional artifact downloads. Inspect
it before use; do not treat it as the bounded client's exit/report contract.

For advanced field tables, see [Programmatic configuration](PROGRAMMATIC-CONFIGURATION.md)
and the [Manual](../MANUAL.md). Source build/full integration instructions in the
[Server quickstart](../SERVER-QUICKSTART.md) are developer-only.
