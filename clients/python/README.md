# Python starter files

## The `swarmlab` library (new in 0.39.0)

```sh
pip install .                      # from this folder; standard library only
python -m unittest test_swarmlab_package
```

```python
from swarmlab import SwarmLab, Agent, Workflow, Environment

sl = SwarmLab()                    # a server (SWARMLAB_URL, SWARMLAB_KEY), or SwarmLab.local("repo") without one
r = sl.run("Fix the failing test", repo="app", environment="auto", checks=True)
print(r.answer)
```

Agents, workflows (built in Python, checked offline, saved on the server), environments that install what a job
needs, approvals answered by your own functions, and `python -m swarmlab` on the command line. The full guide:
[PYTHON-LIBRARY.md](https://github.com/joeaelkhoury/SwarmLab/blob/main/docs/PYTHON-LIBRARY.md).

The files below (single-file client, examples, demos) still work as before.

---

Python 3.8+ and the standard library are sufficient. Extract the entire starter ZIP
into a dedicated folder; keep every Python neighbor and the demo_project directory.
The VSIX does not install these files. The ZIP uses paths relative to clients/python,
so the same commands work here and in the public repository's clients/python folder.

## Offline checks

```sh
python configuration_examples.py --list
python workflow_demos.py --list
python workflow_demos.py --mode single --repo demo-app --dry-run
python workflow_demos.py --mode tree --repo demo-app --dry-run
python workflow_demos.py --mode swarm --repo demo-app --dry-run
python workflow_demos.py --mode graph --repo demo-app --dry-run
python -m unittest -v test_workflow_demos
```

These checks require no server or model and do not prove a real repair. The public
test copies the deliberately broken fixture to a temporary folder: six fixture tests,
two expected failures. After a genuine repair, the unchanged six tests should pass.
Do not use unittest discovery in this kit: it also discovers the intentionally red fixture.

## Complete demos

Follow the [end-to-end demo guide](https://github.com/joeaelkhoury/SwarmLab/blob/main/docs/PYTHON-WORKFLOWS.md#7-complete-four-mode-repair-demo)
and the local demo_project/README.md. Create a fresh absolute demo folder outside
this kit and existing Git workspaces, then manually initialize, commit, and tag ONLY
that fixture repository. The initializer never runs Git. Each mode starts from the
same demo-baseline tag in an independent server worktree.

Submission needs a reachable configured server, a real provider, a registered
repository named demo-app, and suitable host permissions. Launch the bundled native
server from the installed extension's Server tab; Docker is optional. Credentials
belong in the host/environment, never scripts. workflow_demos submits once and prints
an ID; fix_job follows that ID with a fresh output directory. Neither answers approvals.
Review each request in Server/dashboard. Models may ignore delegation instructions;
a submitted or successful job is not proof of a correct fix.

References (external links work in both the public checkout and flat starter ZIP):
- [Python workflows](https://github.com/joeaelkhoury/SwarmLab/blob/main/docs/PYTHON-WORKFLOWS.md)
- [Manual](https://github.com/joeaelkhoury/SwarmLab/blob/main/MANUAL.md)
- [Public release checklist](https://github.com/joeaelkhoury/SwarmLab/blob/main/docs/PUBLIC-RELEASE.md)

The source-dependent full integration test and shell runner are not included.
