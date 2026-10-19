# Swarm Lab

**An AI coding assistant and teams of agents inside VS Code—with visible steps, reviewable edits, and command approvals.**

Start with a conversation about your project. Move to a single-agent task when you
want a bounded result, then explore teams or repeatable workflows when useful.
You do not need to configure agents, workflows, or a server to begin.

![Swarm Lab chat, with an answer and reviewable work](media/screenshot-chat.png)

## Public release: 0.38.0

This release is prepared for distribution as an installable VSIX, documentation,
and Python client/examples. **Extension source code will follow in a later update.**
Download assets will be available on GitHub once the release is published.

- [GitHub project](https://github.com/joeaelkhoury/SwarmLab)
- [Releases and VSIX downloads](https://github.com/joeaelkhoury/SwarmLab/releases)
- [Report a problem](https://github.com/joeaelkhoury/SwarmLab/issues)

The license remains MIT. Deferring source publication does not make the extension
confidential: a VSIX contains inspectable bundled JavaScript. See the
[public-release checklist](docs/PUBLIC-RELEASE.md) for distribution details.

## 1. Install and open

You need:

- VS Code 1.95 or later, or an editor compatible with that extension API.
- A small, preferably non-sensitive project folder for learning.
- A model connection for real AI answers, or the offline mock for an interface demo.
- Your project's test tools if you want to run its tests.

Download the VSIX from [Releases](https://github.com/joeaelkhoury/SwarmLab/releases).
In VS Code, open **Extensions → ⋯ → Install from VSIX…** and select the download.
The publisher ID is **joe-el-khoury**; it is different from the GitHub account name.

Alternatively, with VS Code's command-line launcher:

```sh
code --install-extension swarm-lab-0.38.0.vsix
```

Then:

1. Choose **File → Open Folder…** and open your practice project.
2. Open the Command Palette with **Ctrl+Shift+P** (macOS: **Cmd+Shift+P**).
3. Run **Swarm Lab: Open**.
4. If updating an existing installation, use **Developer: Reload Window** if needed.

No TypeScript source checkout or npm build is needed to use the installed extension.

## 2. Connect a model—or try the mock

Open **Setup**, choose a provider, save settings, then run **Test connection** and
**Test tool calling**.

| Choice | What you need |
|---|---|
| Anthropic API | Your Anthropic key and exact model IDs |
| OpenRouter | Your OpenRouter key, credits, and model IDs |
| OpenAI-compatible API | The service's API base URL, models, and any required key |
| Ollama / LM Studio | A running local API server with a model loaded |
| VS Code language models | Access through VS Code; a subscription may be required |
| Offline mock | No key; scripted demonstration responses, not real reasoning |

Use **Set API key** for provider credentials; extension keys use VS Code Secret
Storage. Never paste keys into tasks, rules, screenshots, or shared configuration.
Set the **Lead model** and **Worker model** to models offered by your provider.
Using the same model for both is fine initially.

Local model software and models are not installed by Swarm Lab. Start that service
first. Hosted providers may charge separately. If native tool calling fails, try
**Tool calling → Text**, or choose a model that supports tools.

## 3. Ask your first question

In **Chat**, start read-only:

```text
Explain what this project does. Read the relevant files first, name the files
you used, and do not change anything.
```

Next, ask for one small improvement:

```text
Find one missing edge-case test. Propose the test and explain why it matters.
Ask before running commands. Do not change unrelated files.
```

- **Enter** sends; **Shift+Enter** adds a line.
- Watch the activity to see which files and tools are used.
- Review **Waiting for you** before approving an edit or command.
- **Apply** accepts a proposed edit; **Reject** declines it.
- **Stop** interrupts work, but does not undo already applied changes or command effects.

A good task states the goal, relevant files, constraints, and a test for success.

## 4. Try a bounded run

A chat is a conversation. A run has a task, an organization of agents, limits,
and a result/usage report.

1. Save your files and preserve existing work, ideally with a Git commit.
2. Open **Run**, enter a small task, and select **Single agent**.
3. Review safety settings and token/step limits; click **Run task**.
4. Follow the steps and answer approvals.
5. Review the diff and tests before keeping or merging the result.

| Mode | Organization | Try it for |
|---|---|---|
| Single | One agent | A focused fix or explanation |
| Tree | Lead with temporary sub-agents | Independent investigations |
| Swarm | Lead with persistent workers and a shared board | Work requiring shared findings |
| Graph | Your configured workflow controls transitions | Repeatable plan, fix, test, review |

More agents do not automatically mean better answers or lower cost. Start small.
Graph needs a configured workflow. Chat can suggest an organization, but its choice
is not guaranteed optimal. [Read the mode-selection guide](docs/RUN-MODES.md).

## 5. Find your way around

| Area | Purpose |
|---|---|
| Chat | Conversation, attachments, history, and proposed actions |
| Run | Start runs; inspect steps, agents, results, and usage |
| Setup | Providers, models, limits, permissions, and optional routing/search |
| Project | Saved rules, requirements, plans, and bounded evidence |
| Agents / Prompts | Specialist instructions and permissions |
| Workflow | Create and save graph workflows |
| Tools | Optional MCP integrations and skills |
| Server | Start/connect a server, submit jobs, review remote approvals |
| Check | Validate setup and diagnose configuration problems |
| Bench | Compare repeatable tasks and configurations |

Code maps rely on your project's VS Code language support. Search indexing,
decision models, automatic model routing, MCP, and Bench are optional—not setup prerequisites.

## 6. Safety before speed

- Swarm Lab's native interactive edits are proposed as diffs; commands ask by default.
- Allow-listed commands can run without another click. A test script can execute arbitrary code.
- Destructive commands still require confirmation, including when allow-listed.
- Worktrees and run branches help review changes; they are **not an operating-system sandbox**.
- Git safety needs Git and a repository with a commit. Inspect Keep/Revert choices carefully.
- MCP, external engines, and unattended Bench have different permission paths; read the manual first.
- Scoped reads support bounded native single/chat read-only use, not general multi-agent isolation.
- Saved requirement status or a successful command is not proof of correctness or fresh test evidence.
- Model providers receive selected context; remote tools and services may receive additional data.
- Review code, run meaningful tests, and check provider costs before merging.

## 7. Python and background jobs (optional)

Python users can use the native server launched from the **installed extension's
Server tab**; no extension source checkout is required. Docker is optional.
A reachable server still needs a configured provider, permissions, and repositories.
VS Code language models cannot serve as a standalone server provider.

Download the separate Python starter files together; installing the VSIX does not
install them. Start with offline payload previews, then submit a small job to your
configured server. A mock can demonstrate the interface, not prove a real fix.

[Python workflows](docs/PYTHON-WORKFLOWS.md) covers downloads, server setup,
credentials, real command-line options, approval exits, and report handling.
The [complete four-mode repair demo](docs/PYTHON-WORKFLOWS.md#7-complete-four-mode-repair-demo)
includes a tiny broken fixture, baseline Git setup, exact preview/submission commands,
and independent single/tree/swarm/graph runs. Offline checks are not live-model verification.

## 8. Learn more and get help

- [Getting started](docs/GETTING-STARTED.md): a guided first session.
- [Run modes](docs/RUN-MODES.md): choosing an organization and understanding automatic choices.
- [Python workflows](docs/PYTHON-WORKFLOWS.md): source-free previews and server jobs.
- [Manual](MANUAL.md): the detailed feature/settings reference; retained in full.
- [Server quickstart](SERVER-QUICKSTART.md): public entry path plus developer-only source tests.
- [Public release checklist](docs/PUBLIC-RELEASE.md): exact upload scope and license cautions.

If something fails, open **Check → Check everything** and **View → Output → Swarm Lab**.
For an issue, include your extension version, editor/OS, provider type, sanitized
error, and reproduction steps. Never include keys, sensitive prompts, or private logs.

**License:** [MIT](LICENSE). Retain applicable third-party notices when redistributing.
