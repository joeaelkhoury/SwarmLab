# Swarm Lab for beginners: run a server and the Studio


By the end of this guide you will have a Swarm Lab server running on your PC/Mac and you will have run jobs from VS Code, from the Studio in your browser, and from Python. It takes about 30 minutes the first time. Every command is written out: copy it, paste it into Terminal, press Return.

## Before you start:

| Word | What it means |
| --- | --- |
| **Server** | A program that runs AI agents for you in the background. It listens at the address `http://127.0.0.1:8787` (only your own computer can reach it). |
| **Job** | One piece of work you give the server, for example "fix the failing tests". It moves through *queued → running → succeeded* (or *failed*). |
| **Agent** | An AI worker inside a job. It can read files, change files and run commands, depending on what you allow. |
| **Project (repository)** | The folder the agents work on. It works best as a **Git** folder with at least one saved version (a *commit*). |
| **Approval** | A question the job asks you before doing something sensitive, such as running a command. The job waits until you answer. |
| **Studio** | A web page of the server with ready-made workflows ("review changes", "fix a bug", …) you start with a few clicks. |

You need: a PC/Mac, an internet connection, and an API key from your AI provider (OpenAI, Anthropic or OpenRouter).

## Part 1: Install what you need

You install three things once: VS Code, the developer tools (for Git), and the Swarm Lab extension.

1. **Install VS Code.** Download it from [code.visualstudio.com](https://code.visualstudio.com), open the downloaded file, and drag **Visual Studio Code** into **Applications**.
2. **Make the `code` command work in Terminal.** Open VS Code, press **Cmd+Shift+P**, type `shell command`, and choose **Shell Command: Install 'code' command in PATH**.
3. **Check Git and Python.** In Terminal:

   ```sh
   git --version
   python3 --version
   ```

   If a window asks to install the *command line developer tools*, click **Install**, wait until it finishes, then run `git --version` again. Both commands should print a version number.
4. **Install Swarm Lab.** Put `swarm-lab-0.40.4.vsix` in your **Downloads** folder, then:

   ```sh
   code --install-extension ~/Downloads/swarm-lab-0.40.4.vsix --force
   code --list-extensions --show-versions | grep swarm-lab
   ```

   The second line must print `joe-el-khoury.swarm-lab@0.40.4`.
5. **Quit VS Code completely** with **Cmd+Q**. Closing the window is not enough; quitting makes VS Code load the new version.


## Part 2: Prepare a project folder

The agents need a folder to work on. Use the small demo that comes with Swarm Lab: it has two bugs for the agents to fix. You give it a Git history so the agents can work on a branch and you can see exactly what they changed.

1. Copy the demo out of the downloaded ZIP folder:

   ```sh
   mkdir -p ~/SwarmLabProjects
   cp -R ~/Downloads/"SwarmLab-main 2"/clients/python/demo_project ~/SwarmLabProjects/demo-app
   cd ~/SwarmLabProjects/demo-app
   ```

   If your folder in Downloads has another name, use that name instead of `SwarmLab-main 2`.
2. Save a first version with Git:

   ```sh
   git init -b main
   echo "swarmlab-data/" >> .gitignore
   git add -A
   git -c user.name="Me" -c user.email="me@example.com" commit -m "start"
   ```

   The second line keeps the server's own data out of your project's history.
3. Run the tests once to see the bugs:

   ```sh
   python3 -m unittest -v
   ```

   You should see **2 failures**. That is expected: those are what the agents will fix.

Later, for your own project, do the same in its folder: `cd` into it, then `git init`, `git add -A` and `git commit`. A folder without Git still works, but only as a copy of its current files, with no history.

## Part 3: Set up Swarm Lab in VS Code

You tell Swarm Lab once which AI to use. The server copies these settings every time it starts, so the chat and the server always work the same way.

1. Open the project in VS Code:

   ```sh
   code ~/SwarmLabProjects/demo-app
   ```
2. If VS Code asks **"Do you trust the authors of the files in this folder?"**, click **Yes, I trust the authors**. The server only starts in a trusted folder.
3. Open Swarm Lab: press **Cmd+Shift+P**, type `Swarm Lab: Open`, press Return.
4. Click the **Setup** tab and fill in:

   | Field | What to choose |
   | --- | --- |
   | **Provider** | Your AI provider: OpenAI-compatible, Anthropic or OpenRouter |
   | **Lead model** | The stronger model (it plans and decides) |
   | **Worker model** | The model that does the work (can be cheaper) |
   | **Reasoning effort** | `none` (needed for OpenAI GPT-5 models with tools; safe for others) |
   | **Tool calling** | **Native: the model's tool calling**. Never *Off*: with Off, agents cannot read or change any file. |
5. Click **Set API key** and paste your provider's key. It is stored safely by VS Code, never in a file.
6. Click **Save settings**.

To check that the AI answers, type `hello` in the **Chat** tab. A reply means the provider, model and key are right.

## Part 4: Start the server and check it

One click starts the server; one Terminal command proves it is the new version.

1. **Stop any old server first** (only needed if you used Swarm Lab before). In Terminal:

   ```sh
   lsof -nP -iTCP:8787 -sTCP:LISTEN
   ```

   If it prints a line, note the number in the **PID** column and stop it with `kill <PID>`, for example `kill 4242`. No output means nothing is running.
2. In Swarm Lab, click the **Server** tab, then **Start local server**.
   - The first time, Swarm Lab creates `swarmlab.server.json` in your project from your Setup and opens it beside. You do not need to change it.
   - It also creates `swarmlab-data/`, where the server keeps its jobs and logs.
3. Check it in Terminal:

   ```sh
   curl -s http://127.0.0.1:8787/v1/health
   ```

   You should see `"ok":true` and `"version":"0.40.4"`. An older version number means an old server is still running: go back to step 1.
4. Back in the **Server** tab, the green label reads **connected**.

The server runs as long as VS Code is open. The server's log is in VS Code: **View → Output**, then choose **Swarm Lab** in the list.

## Part 5: Run your first job from VS Code

You describe the work, submit it, approve what it asks, and read the result: all in the **Server** tab.

1. Scroll down to **New job** and fill in:

   | Field | What to put |
   | --- | --- |
   | **Organization** | **Single agent** (the simplest; *Tree*, *Swarm* and *Graph* use several agents) |
   | **Repository** | `demo-app` |
   | **Commands** | Leave the default |
   | **Task** | `Fix the two failing tests in pricing.py and labels.py. Run python -m unittest -v before and after. Do not change test_demo.py.` |
2. Click **Submit job**. It appears under **Jobs** as *queued*, then *running*.
3. **Answer the approvals.** When an agent wants to run a command, the job shows **waiting** and the request appears under **Waiting for you on the server**. Read the command (for example `$ python -m unittest -v`), then click **Approve** (or **Reject**). The job continues at once.
4. **Read the result.** Click the job in the **Jobs** list. You see:
   - the **Answer**: what the agent did and the test results;
   - the **Branch**, for example `swarmlab/job-1a2b3c4d`, which holds the changes;
   - the **Events**: every step, in order.
5. **Look at the changes and keep them.** In Terminal:

   ```sh
   cd ~/SwarmLabProjects/demo-app
   git diff main swarmlab/job-1a2b3c4d
   git merge swarmlab/job-1a2b3c4d
   python3 -m unittest -v
   ```

   Use your own job's branch name. Your folder only changes when you merge, so nothing happens behind your back.

A job marked **succeeded · ⚠ not accepted** finished but its review rejected the work. Read its answer to see why, fix the cause, and run it again.

## Part 6: Run ready workflows in the Studio

The Studio is a web page of your server with ready-made workflows: you pick one, answer a few questions, and press **▶ Run it**. No VS Code knowledge needed.

1. **Open the Studio** in your browser (the server must be running):

   ```sh
   open http://127.0.0.1:8787/studio
   ```

   Or, in the **Server** tab, click **Open dashboard**, then **✦ Studio** at the top.
2. **Pick a workflow** on the **Start** page. Type in **Search workflows** (for example `bug`, `review`, `notebook`, `research`) and click a card.
3. **Fill in the form.** Each workflow asks its own questions. Under **Project (optional)**, choose `demo-app` to work on your project, or **No project (a fresh, empty workspace)** for work without code (documents, research, ideas).
4. Click **▶ Run it**. The run page opens and shows **Latest activity** as it moves.
5. **Answer questions.** When the run shows **Needs you: an answer is waiting below**, open **Waiting for you**, read the request, and answer it. The run continues.
6. **Read the result** on the run page when it is done. **My runs** (top left) lists every run; click one to open it again, or **↻ Run again** to repeat it.

To make your own workflow, click **Build** (top left), describe the steps, then **Save and run**. Saved workflows appear on the **Start** page.

If the Studio says it cannot reach the server, start the server again (Part 4). If it asks for a key, open **Settings** in the Studio and paste the server's access key (not needed for the local setup in this guide).

## Part 7: Run jobs from Python

One button writes everything Python needs; then a single command runs a job with your Setup.

1. In the **Server** tab, click **📄 Create run files**. A folder `swarmlab-run/` appears in your project with a `README.md` (it opens), start scripts, `swarmlab.client.json` (the server address and your settings) and `example.py`, plus the Python library itself: nothing to install.
2. Run a job (the server must be running):

   ```sh
   cd ~/SwarmLabProjects/demo-app
   python3 swarmlab-run/example.py "Fix the two failing tests in pricing.py and labels.py"
   ```
3. When the terminal asks to approve a command, type `y` and press Return. The answer prints at the end.

In your own script, three lines are enough:

```python
from swarmlab import SwarmLab
sl = SwarmLab.from_config("swarmlab-run/swarmlab.client.json")
print(sl.run("Add input validation to pricing.py", mode="single").answer)
```

Save it as `my_job.py` in the project folder and run it with `PYTHONPATH=swarmlab-run python3 my_job.py` (this tells Python where the library is).

**Without VS Code** (for example on another machine or in the background): copy `swarmlab-run/.env.example` to `swarmlab-run/.env`, put your API key in it, then run `./swarmlab-run/start-server.sh`. Never commit `.env`: it holds your key.

## Part 8: Stop, restart, and run several servers

All of these are buttons in the **Server** tab.

| You want to… | Click |
| --- | --- |
| Apply new Setup settings | **↻ Restart** (or **Start again (restart)**) |
| Stop the server | **Stop** |
| Stop an old server you started earlier or elsewhere | **✕ Kill old server** |
| Run a second server at the same time | Type a port such as `8788` under **Local servers**, then **Start on port** |
| Send jobs to another server in the list | **Use** on its row |
| Stop one server in the list | **Stop** (or **✕ Kill**) on its row |

Each extra server gets its own data folder (`swarmlab-data-8788/` for port 8788), so servers never mix their jobs. Its Studio is at `http://127.0.0.1:8788/studio`.

In the browser, the dashboard (`http://127.0.0.1:8787/`) also has **↻ Restart server** and **■ Stop server** at the top.

To work on more than one project with one server, open `swarmlab.server.json` and list each project under `"repos"` with its full path; then choose the project per job. After editing the file, click **↻ Restart**.

## Troubleshooting

Most problems come from an old server still running. Check the version first (`curl -s http://127.0.0.1:8787/v1/health`); it must say `0.40.4`.

| What you see | Why | What to do |
| --- | --- | --- |
| `code: command not found` | The `code` command is not installed | Part 1, step 2 |
| Health shows an older version, or nothing changes after an update | An old server still runs on port 8787 | `lsof -nP -iTCP:8787 -sTCP:LISTEN`, then `kill <PID>`; or **✕ Kill old server**. Then **Start local server** |
| "Port 8787 is already in use" | Another server or program holds the port | **✕ Kill old server**, or start on another port (Part 8) |
| Agents say "no workspace tools are available" | **Tool calling** is *Off* | Setup → **Tool calling** → **Native**, **Save settings**, **↻ Restart** |
| "Function tools with reasoning\_effort are not supported" | An OpenAI GPT-5 model with reasoning on | Setup → **Reasoning effort** → `none`, **Save settings**, **↻ Restart** |
| A job stays **waiting** | It is asking you something | **Waiting for you on the server** (VS Code), **Waiting for you** (Studio), or type `y` in the Python terminal |
| Test run "exited 127" or `python: command not found` | Old server without the `python` alias | Update to 0.40.4 and restart |
| "cannot resolve base reference HEAD" or a snapshot error | Old server; the folder has no Git history | Update to 0.40.4; better, give the folder a history (Part 2) |
| **succeeded · ⚠ not accepted** | The review rejected the work | Read the job's **Answer**, fix the cause, run again |
| Studio: "Cannot reach the Swarm Lab server" | The server is stopped | Start it (Part 4), then reload the page |

Still stuck? Save the job's events and send them along with the health line:

```sh
curl -s "http://127.0.0.1:8787/v1/jobs/<JOB_ID>/events?format=json" > ~/Desktop/job-events.txt
```

## Cheat sheet

The everyday routine is three steps: open the project in VS Code, click **Start local server**, run jobs from the Server tab, the Studio or Python.

| Task | Command or place |
| --- | --- |
| Open the project | `code ~/SwarmLabProjects/demo-app` |
| Open Swarm Lab | **Cmd+Shift+P** → `Swarm Lab: Open` |
| Start the server | **Server** tab → **Start local server** |
| Check the server | `curl -s http://127.0.0.1:8787/v1/health` |
| Find what holds port 8787 | `lsof -nP -iTCP:8787 -sTCP:LISTEN` |
| Stop a process | `kill <PID>` |
| Open the Studio | `open http://127.0.0.1:8787/studio` |
| Open the dashboard | `open http://127.0.0.1:8787/` |
| Run a job from Python | `python3 swarmlab-run/example.py "your task"` |
| See what a job changed | `git diff main <job branch>` |
| Keep a job's changes | `git merge <job branch>` |
| Run the tests yourself | `python3 -m unittest -v` |
| Update Swarm Lab | `code --install-extension ~/Downloads/<file>.vsix --force`, then **Cmd+Q**, stop the old server, **Start local server** |
