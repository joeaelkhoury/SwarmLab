# Tiny repair project (intentional red baseline)

Python 3.8+, stdlib only. No installs, credentials, or network needed for tests.
The baseline has **six tests, two failures**: quantities are ignored in pricing.py,
and repeated/mixed whitespace is mishandled in labels.py. This is not a passing app.

Contracts:
- total(lines): sum unit_price times quantity for each pair; empty input = 0.
- slug(text): trim/lowercase, split on whitespace, join words with one hyphen;
  blank input = empty string.

Only pricing.py and labels.py need repair. Do not weaken test_demo.py. Each bug can
be repaired independently; no dependencies or architecture work is needed.

## Fresh dedicated repository

From clients/python in the downloaded kit, choose a NEW absolute path outside the
kit and any existing Git workspace. Its parent must already exist. The copier
refuses existing destinations and never runs Git:

```sh
python workflow_demos.py --init-demo /absolute/practice/demo-app
```

Windows example (use the resulting path in every command below):

```powershell
python workflow_demos.py --init-demo C:/practice/demo-app
```

Run the following manually ONLY against that newly created demo folder. Replace
the absolute path consistently. Never run these commands on your real workspace.
Git must be installed. Identity is set only for this initial commit, not globally.

```sh
git -C /absolute/practice/demo-app init
git -C /absolute/practice/demo-app add README.md .gitignore pricing.py labels.py test_demo.py
git -C /absolute/practice/demo-app -c user.name="Demo User" -c user.email="demo@example.invalid" -c commit.gpgsign=false commit -m "Intentional two-regression baseline"
git -C /absolute/practice/demo-app tag demo-baseline
```

The demo-baseline tag makes the jobs independent of the default branch name.
To see the expected failure, change directory ONLY to your dedicated demo folder:

```sh
python -m unittest -v
```

Expected: exit code 1, six tests, FAILED (failures=2). A full repair should yield
exit code 0 and six tests OK. Do not interpret the intentional red baseline as a
kit failure. The separate kit tests assert this baseline behavior.

## Server use

Open this new folder in VS Code; configure/start the installed native server and
register it as demo-app (or your own name), with demo-baseline as a valid base ref.
The committed files must be on the SERVER filesystem; a client-local folder is
not enough for a remote server. Use ask/review approvals and host-configured real
models. Native file/edit/command tools must be permitted by the host. Worktrees
are not security sandboxes.

From the downloaded clients/python folder, preview then explicitly submit:

```sh
python workflow_demos.py --mode graph --repo demo-app --dry-run
python workflow_demos.py --mode graph --repo demo-app --submit
```

Repeat with single, tree, or swarm. Every mode starts from demo-baseline in its own
server worktree, not your uncommitted edits. The graph command is literally
python -m unittest -v on the SERVER PATH; choose --python-command python3 or
--python-command "py -3" if that is what the server can execute. There is no
server substitution of the client's sys.executable or {python} in this job.
Submission is not completion. Review approvals in Server/dashboard, then follow
with fix_job.py --job-id ID --out a-new-report-folder. Inspect test evidence,
branch/patch, and retry-limit warnings before merging or claiming a verified fix.
