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



In case of problems runnign the studio jobs


Open *Terminal* and run these in order.

### 1. Check the tools
sh
python3 --version
git --version

If git asks you to install the developer tools, accept, wait for it to finish, then run git --version again. You do *not* need a python command; 0.40.2 provides it for jobs.

### 2. Install the new extension
sh
code --install-extension ~/Downloads/swarm-lab-0.40.2.vsix --force
code --list-extensions --show-versions | grep swarm-lab

The second command must print joe-el-khoury.swarm-lab@0.40.2.

If you get code: command not found: open VS Code, press *Cmd+Shift+P, choose **Shell Command: Install 'code' command in PATH*, then repeat this step.

Then *quit VS Code completely with Cmd+Q*. Closing the window is not enough.

### 3. Stop every old server
sh
lsof -nP -iTCP:8787 -sTCP:LISTEN

If this prints a line, stop it using the number in the PID column:
sh
kill <PID>

Check that nothing answers anymore:
sh
curl -s http://127.0.0.1:8787/v1/health || echo "port is free"


### 4. Make a real project folder with Git history
Use a copy of the demo outside the downloaded ZIP:
sh
mkdir -p ~/SwarmLabProjects
cp -R ~/Downloads/"SwarmLab-main 2"/clients/python/demo_project ~/SwarmLabProjects/demo-app
cd ~/SwarmLabProjects/demo-app
git init -b main
git add -A
git -c user.name="Me" -c user.email="me@example.com" commit -m "start"
python3 -m unittest -v

The last command should show *2 failing tests*. Those are the bugs the agents will fix.

### 5. Open it in VS Code and set it up
sh
code ~/SwarmLabProjects/demo-app

1. When VS Code asks, choose *Yes, I trust the authors*.
2. In Swarm Lab's *Setup* tab, choose your provider and the lead and worker models.
3. Set *Reasoning effort* to *none*.
4. Enter your API key, then click *Save*.

### 6. Start the server and check its version
In the *Server* tab, click *Start local server*. Then in Terminal:
sh
curl -s http://127.0.0.1:8787/v1/health

It must contain "version":"0.40.2". If it shows anything older, an old server is still running: go back to step 3.

### 7. Create the run files and run the job from Python
In the *Server* tab, click *📄 Create run files*. Then:
sh
cd ~/SwarmLabProjects/demo-app
python3 swarmlab-run/example.py "Repair the two regressions in pricing.py and labels.py so that python -m unittest -v passes. Do not edit test_demo.py."


When the terminal asks you to approve a command such as python -m unittest -v, type *y*. The answer appears when the job is done.

You don't need the .env file when the server is started from VS Code. It's only for swarmlab-run/start-server.sh.

### 8. If it still fails, send me these
The job id is printed by the script and shown in the Server tab.
sh
curl -s http://127.0.0.1:8787/v1/health
curl -s "http://127.0.0.1:8787/v1/jobs/<JOB_ID>/events?format=json" > ~/Desktop/job-events.txt

Attach job-events.txt and paste the health line. Together they show the exact step where it stops.
