# Swarm Lab

Swarm Lab is a VS Code extension for working on your code with AI agents, under your control. You can **chat** with an assistant that knows your project, **define your own agents**, and run them **alone, as a tree, as a swarm, or in your own fixed workflow (graph)**. Every file change is a diff you approve, every command waits for your click, and everything the agents are told and do is visible.

It works with **Anthropic, OpenRouter, any OpenAI-compatible server** (a company gateway, LiteLLM, vLLM, Ollama, LM Studio, a local model behind a proxy), **VS Code's own models**, or **Claude Code** as the engine of an agent. Models **without tool calling** work too.

**Three parts, one engine:**

| Part | For | Where |
|---|---|---|
| **The VS Code extension** | Working with agents on the project open in VS Code: chat, runs, approvals as you go | This guide, sections 1–18 |
| **The server** (`swarm-lab`) | Many jobs at once, history, triggers, several machines: an API with a queue and workers; jobs with or without a repository | Section 19, and SERVER.md for everything |
| **The clients** | Your own applications: a Python client and an example app, and the API guide for any language | `clients/README.md`, `clients/python/` |

The extension can also drive the server: the **Server** tab, and `/remote` in the chat (the answer and the files come back into the chat).

---

## Contents

1. [The big picture](#1-the-big-picture)
2. [Install and open](#2-install-and-open)
3. [Connect a model](#3-connect-a-model)
4. [Chat](#4-chat)
5. [Your own agents](#5-your-own-agents)
6. [Runs: single, tree, swarm, graph](#6-runs-single-tree-swarm-graph)
7. [Workflows (graph mode)](#7-workflows-graph-mode)
8. [Prompts](#8-prompts)
9. [Tools: MCP servers and skills](#9-tools-mcp-servers-and-skills)
10. [Code search (RAG)](#10-code-search-rag)
11. [Claude Code as an engine](#11-claude-code-as-an-engine)
12. [Safety and control](#12-safety-and-control)
13. [Context, limits and long answers](#13-context-limits-and-long-answers)
14. [Check everything](#14-check-everything)
15. [Files Swarm Lab keeps in your project](#15-files-swarm-lab-keeps-in-your-project)
16. [All settings](#16-all-settings)
17. [All commands](#17-all-commands)
18. [Troubleshooting](#18-troubleshooting)
19. [Run it as a service (API, queue, workers)](#19-run-it-as-a-service-api-queue-workers)
20. [Build, test and publish](#20-build-test-and-publish)

---

## 1. The big picture

The panel has nine tabs:

| Tab | What you do there |
|---|---|
| **Chat** | Talk to the assistant or to one of your agents: questions, changes, runs, files, diagrams. This is the home tab. |
| **Run** | Give one task to a single agent, a tree, a swarm or your workflow, watch it live, and compare runs. |
| **Setup** | Model provider, models, proxy, engine, code search, safety and limits, with a test button for each. |
| **Agents** | Your agents: instructions, model, engine, tool calling, tools, folders they may edit. |
| **Workflow** | Your fixed workflow for graph mode (for example plan → fix → test → review), with a live drawing and a dry run. |
| **Prompts** | Every prompt the agents receive, editable, with a preview of the final prompt. |
| **Tools** | MCP servers (extra tools) and skills (reusable instructions). |
| **Server** | Send jobs to a Swarm Lab server (with or without a repository), follow them live, answer its approvals, or start a local server. |
| **Check** | One button that checks the whole setup before you work. |

**How a typical session goes:** you ask in the Chat. The assistant searches and reads your code, proposes changes, and every proposal appears in the orange **"Waiting for you"** bar above the message box with its diff. You click **Apply** or **Reject**. For bigger work it starts a run (a swarm, or your workflow), or you send it to the server with `/remote`: in both cases the answer comes back to the chat.

---

## 2. Install and open

### 2.1 Install

**From a `.vsix` file:**
1. In VS Code, open the Extensions view (**Ctrl+Shift+X**, Mac **Cmd+Shift+X**).
2. Click **⋯** at the top of the view, then **Install from VSIX…**, and choose `swarm-lab-<version>.vsix`.
3. Run **Developer: Reload Window** (Command Palette: **Ctrl+Shift+P**).

Or in a terminal: `code --install-extension swarm-lab-<version>.vsix`

**From Open VSX** (VSCodium, Cursor and other editors): search for **Swarm Lab**.

Needs **VS Code 1.95 or later**.

### 2.2 Open

1. **File → Open Folder…** and open your project. The agents work on this folder.
2. Command Palette → **Swarm Lab: Open**. The panel opens as an editor tab, on the **Chat** tab.

### 2.3 First five minutes

1. **Setup** tab → choose your provider, models and key ([section 3](#3-connect-a-model)) → **Save settings**.
2. Click **Test connection**, then **Test tool calling**.
3. **Check** tab → **Check everything** → fix anything marked ✕.
4. **Chat** tab → ask *"What does this project do?"*.

Without any key, Swarm Lab uses an **offline mock**: no cost, a fixed script, good for discovering the interface.

---

## 3. Connect a model

Everything is in the **Setup** tab, in the **Model provider** group. Always finish with **Save settings**, then **Test connection** and **Test tool calling**.

### 3.1 Choose a provider

| Provider | Use it for | Key |
|---|---|---|
| **Anthropic API** | Claude models directly | Anthropic key |
| **OpenAI-compatible** | OpenAI, company gateways, LiteLLM, vLLM, Ollama, LM Studio, Azure-style endpoints, any local model | Optional for local servers |
| **OpenRouter** | Many providers' models with one key | OpenRouter key (`sk-or-…`) |
| **VS Code language models** | Models VS Code already has (for example GitHub Copilot) | None; VS Code asks once |
| **Offline mock** | Trying the interface, demos | None |

**Keys** are stored in VS Code's secret storage, never in a settings file. Click **Set API key**, choose **which provider the key is for**, and paste it. A chip shows which providers have a key (`openrouter key ✓`). If a key looks like it belongs to another provider (for example `sk-or-…` saved for Anthropic), Swarm Lab warns you and offers to fix it.

### 3.2 OpenRouter, step by step

1. On **openrouter.ai**: **Keys** → create a key (`sk-or-…`). Make sure the account has credits.
2. **Setup** → Provider **OpenRouter** → leave **Base URL** empty → **Save settings**.
3. **Set API key** → choose **OpenRouter** → paste.
4. **Pick OpenRouter models**: the list shows only models that support tools, with prices. Pick a strong **lead** model, then a cheaper **worker** model.
5. **Test connection** → **Test tool calling**.

### 3.3 A local model, or a model behind a gateway

1. Find the address: open `http://localhost:PORT/v1/models` in a browser. If you see JSON with your model, note its `"id"`.
   Usual ports: Ollama **11434**, LM Studio **1234**, vLLM **8000**, llama.cpp **8080**.
2. **Setup** → Provider **OpenAI-compatible**.
3. **Base URL**: `http://localhost:PORT/v1`. Include `http://` and, usually, `/v1`. A company gateway: `https://llm-gateway.company.com/v1`. Query strings are kept (Azure-style `…?api-version=…`).
4. **Lead model** and **Worker model**: the exact `id`.
5. **Key header**: leave `authorization` (sends `Bearer <key>`); use `api-key` for Azure-style gateways.
6. **Save settings** → **Test connection** → **Test tool calling**.

**API key:** most local servers need none. If yours does, **Set API key** → **OpenAI-compatible**.

### 3.4 Through a company network proxy

Set **Network proxy** to `http://proxy.company.com:8080` (or `http://user:pass@proxy:8080`). Empty uses VS Code's `http.proxy` setting, then `HTTPS_PROXY` / `HTTP_PROXY`. `localhost`, `127.0.0.1` and the hosts in `NO_PROXY` are always reached directly. If your company inspects TLS with its own certificate, start VS Code with `NODE_EXTRA_CA_CERTS=path\to\company-ca.pem`.

### 3.5 Special server options

- **Reasoning effort** (`none` … `high`): sent as `reasoning_effort`. Choose **none** if your model rejects tools together with reasoning (an error like *"function tools with reasoning effort not supported"*).
- **Extra request fields (JSON)**: any other field your server needs, for example `{"temperature": 0.2}` or `{"reasoning": {"effort": "none"}}`.
- **Extra headers**: in VS Code settings (`swarmLab.extraHeaders`), for a gateway's tenant or project header. No secrets there.

### 3.6 Tool calling: native, text, or off

Agents work through tools (read files, edit, run tests…). If **Test tool calling** fails, your model or server has no tool calling. Choose **Setup → Tool calling**:

| Mode | How it works |
|---|---|
| **Native** | The model's own tool calling. |
| **Text** | For models **without** tool calling. The tools are described in the prompt, the model writes each call as a small JSON block, and Swarm Lab runs it like a normal tool call: same approvals, permissions and diffs. |
| **Off** | Plain chat, no tools. |

Each agent can override it (Agents tab).

### 3.7 Lead and worker models

The **lead model** is used by the chat assistant, the single agent and the leads of trees and swarms: use your strongest model. The **worker model** is used by workers, sub-agents and workflow steps: it can be cheaper. Each of your agents can have its own model.

---

## 4. Chat

### 4.1 Talk

Type in the message box and press **Enter** (**Shift+Enter** for a new line). The assistant searches and reads your code before answering, and names the files it used. Activity lines under the conversation show what it does (`search_code`, `read_file`…).

**The top bar of the chat:**

| Control | What it does |
|---|---|
| **Talk to** | Who you talk to: the assistant, or one of your agents. Each has its own conversation and memory. |
| **Engine** | The assistant's engine: Swarm Lab loop (edits are diffs you approve) or Claude Code. |
| **History** | Your saved conversations: **Open** one, or delete it. |
| **Context NN%** | How full the context is, and every context and limit control ([section 13](#13-context-limits-and-long-answers)). |
| **Memory** | Long-term notes: see, add, delete. |
| **New chat** | Start fresh. The old chat is kept in History; long-term notes are kept. |

### 4.2 Attach files

Click **＋ Files** or type **`@`** in your message. A list appears: your open editors first, then the workspace. Type letters to filter in order (`@dat` finds `src/date.ts`), use the arrows and **Enter**, or click. Up to 8 files become 📎 chips and are sent with your message.

### 4.3 Approve or reject: the orange bar

Everything that needs your OK appears **together** in the **"Waiting for you"** bar, right above the message box. The Chat tab shows **"Chat (3 waiting)"**.

| Request | Buttons |
|---|---|
| ✎ Edit a file (the diff is shown: red removed, green added) | **Apply** · **Reject** · **Open diff** (side-by-side in VS Code) |
| ▶ Run a command | **Run** · **Reject** |
| 🗂 Delete or rename a file | **Delete / Rename** · **Reject** |
| ⚙ Start a run (you can edit the task first) | **Start** · **Reject** |
| ❓ A question with options | click an option · **Send my answer** · **Skip** |
| MCP tool call, new skill, Claude Code, an agent's message | **Allow / Create / Send** · **Reject** |

**Approve all N** and **Reject all N** answer everything at once. Approved edits and commands run in order, one after another. **Stop** cancels the waiting requests and always frees the chat. While the assistant works you can still type: **Send later** sends your message when it finishes.

### 4.4 Options and recommendations

When there are several ways forward, the assistant shows a **question card** with 2 to 4 options, each with its trade-off, and one marked **recommended**. Click an option, or write your own answer. **Take the recommended** answers every waiting question with its recommended option. After most answers, **next-step chips** appear under the message (for example **Add a test for this**); one click sends it.

### 4.5 Code blocks

Every code block in an answer is **numbered** (**#4**), also when the answer came in several parts. On each block:
- **Copy**: to the clipboard.
- **Insert**: at the cursor of the active editor (**Ctrl+Z** undoes it).
- **Save to file…**: choose the place; a new file is created and opened; an existing file shows a diff first.

You can also just ask: *"save #4 as src/parse_date.py"*, or *"append #5 to tests/test_parse.py"*. The agent saves the block **by its number, without writing it again**, so long code is never cut.

### 4.6 Diagrams

Ask for a diagram, for example *"draw this module's flow as a Mermaid diagram"*. A ```` ```mermaid ```` block is **drawn**: flowcharts, sequence, class, state, Gantt and more. Each diagram has **Code / Diagram**, **Copy** and **Save to file…**. ```` ```svg ```` blocks are shown as images. Mermaid is bundled: it works offline.

### 4.7 Copy, edit, history

- **Copy a whole message:** hover it, click **Copy** at the top right.
- **Edit an earlier message of yours:** hover it, click **Edit**, change the text, **Resend**. The chat goes back to just before that message (in the conversation and in what the model remembers) and sends the new text.
- **History:** **History** → **Open** a past conversation (the current one is saved first).

### 4.8 Talk to your agents

- **Talk to** menu: switch the whole chat to an agent.
- **`@name` in a message:** type `@`, pick the agent (agents are listed first), finish your message. That one message goes to the agent; the answer appears here and is kept in the agent's own conversation.
- The assistant also **consults your agents by itself** when their skill fits.

### 4.9 Memory

- The **conversation** is saved per agent and comes back after a restart.
- **Long-term notes** carry facts into every new chat. They are created when you add one in **Memory**, type `/remember <fact>`, or ask the assistant to remember something.

### 4.10 Slash commands

They work without the model:

| Command | What it does |
|---|---|
| `/single <task>`, `/tree <task>`, `/swarm <task>`, `/graph <task>` | Start a run; its answer comes back to the chat |
| `/ask <agent> <question>` | Ask an agent of the last run |
| `/remember <fact>` | Save a long-term note |
| `/remote <mode> [options] <task>` | Run on the Swarm Lab server; the answer and the created files come back here (see 4.11) |
| `/new` | New chat |
| `/help` | Short help |

### 4.11 Run things from the chat, get the answers in the chat

| You type | Where it runs | What comes back into the chat |
|---|---|---|
| A normal message | The assistant, here | Its answer; edits and commands as approvals in the orange bar |
| `/single <task>` · `/tree` · `/swarm` · `/graph` | A local run (follow it in the Run tab) | The run's answer, its numbers (tokens, calls, edits), the agents you can still ask |
| `/ask <agent> <question>` | An agent of the last run | Its answer, from its memory of the run |
| `@reviewer <message>` | One of your agents | Its answer (also kept in its own conversation) |
| `/remote <mode> <task>` | The Swarm Lab server | The answer, the branch and diff summary, **and the files it created**: shown in the chat, so diagrams are drawn and code blocks get **Save to file…** and a number (`save #12 as docs/flow.md`) |

**`/remote` options**, written before the task:

| Option | Meaning |
|---|---|
| `--no-repo` | No repository: a fresh empty workspace (ideas, Jira tickets, diagrams, documents); files come back by default |
| `--repo NAME` | Another repository than the default (Server tab → Default repository) |
| `--files` / `--no-files` | Return the created files, or not |
| `--workflow NAME` | Graph mode: which workflow (default: `default`) |
| `--agent NAME` | Single mode: run as one of your agents |

Examples:

```
/remote single --no-repo Draw the order flow as a Mermaid diagram in docs/orders.md
/remote graph Fix the failing date test
/remote swarm --no-repo Propose 5 ideas to reduce checkout latency, with effort and risk
/remote single --agent reviewer --files Review src/payments and write the findings in docs/review.md
```

While a `/remote` job runs, **the chat stays free**: keep talking. If the job needs an approval, a note says so; answer it in **Server → Waiting for you on the server**. When it ends, the result appears as an assistant message, with next-step chips. The result also goes into the conversation's history, so you can then ask *"explain this result"* or *"save the files to my project"*.

---

## 5. Your own agents

### 5.1 Create an agent

1. **Agents** tab → **Add an agent**.
2. Fill in the card:
   - **Name**: letters, digits, `-`, `_` (for example `reviewer`).
   - **Description (shown to leads)**: *when* to use it, for example *"reviews Python code for bugs and security"*.
   - **Instructions**: the agent's own prompt, for example *"You review Python code for bugs and security issues. Answer with a numbered list, most serious first."*
   - **Model**: `lead`, `worker`, or an exact model id (for example `mistral-large-latest`). Empty = by role.
   - **Engine**: Swarm Lab loop or Claude Code.
   - **Tool calling**: Native, Text or Off (empty = the Setup default).
   - **May edit**: glob patterns such as `src/**, tests/**`, `none` for no edits, empty for all files.
   - **Tools**: untick **Default tools for the role** and choose the tools it may use.
3. **Save permissions**. The permissions go to `.swarmlab/policy.json`, the instructions to `.swarmlab/prompts/agent-<name>.md`.

**Role rules** (bottom of the tab) give defaults to every agent of a role, for example *swarm workers may edit only `src/**`*. A named agent's rule wins over its role rule.

An agent that only has a prompt file (`agent-<name>.md`, created in the Prompts tab) is a full agent too.

### 5.2 Use your agents

| Where | How |
|---|---|
| Chat, its own conversation | **Talk to** → the agent |
| Chat, one message | `@name your message` |
| Inside the assistant's work | The assistant consults it by itself (`consult_agent`) |
| Run tab | **Single agent** → **Run as** → the agent |
| Workflow | A step's **Agent** field (it suggests your agents) |
| Swarm | Leads see your named agents and their descriptions, and create workers with those names |

### 5.3 A good starting team

| Agent | Settings |
|---|---|
| `planner` | Description *"reads the code and writes a plan"*, May edit `none` |
| `fixer` | *"changes code under src/"*, May edit `src/**` |
| `checker` | *"runs the tests; never edits"*, tools: read, search, `run_command`; May edit `none` |
| `reviewer` | *"reviews changes"*, Tool calling **Off** if your model is weak with tools |

---

## 6. Runs: single, tree, swarm, graph

**Run** tab → write the task → choose the organization → **Run task**.

| Organization | How it works | Use it when |
|---|---|---|
| **Single agent** | One agent: read, check, answer, change. **Run as** chooses which of your agents. | Most tasks |
| **Tree** | A lead splits the task; sub-agents answer once and are deleted. | Independent sub-questions |
| **Swarm** | A lead creates persistent workers; they share a board and ask each other directly. | Open exploration, larger investigations |
| **Graph** | Your fixed workflow ([section 7](#7-workflows-graph-mode)). | Repeated, auditable work (fix → test → review) |

**What you see:**
- **Map**: agents as hexagons; messages flash orange (through the lead), blue (peer to peer), green (to the board). Graph mode draws your workflow and lights each step (orange running, green done, grey at its limit).
- **Log**: every model call (tokens), tool call, message, edit and command.
- **Inspect an agent**: the exact prompt it received, its tools, the folders it may edit, every message to and from it.
- **Runs compared**: tokens, calls, messages, notes, edits, commands, Claude Code cost, time, how it ended. Run the same task in each organization and compare.
- **Ask an agent after the run**: persistent agents answer from their memory (tree sub-agents are deleted, so they cannot).

---

## 7. Workflows (graph mode)

**Workflow** tab. Start with **Load the example**: plan → fix → test → review.

**Steps:**
- **Agent step**: an agent (one of yours or a new name), a model (worker or lead), a **task**, and where to go next:
  - **Always the same step**, or
  - **The agent decides**: decisions such as `approve → done`, `reject → fix`. The agent ends its reply with `DECISION: <word>`; `else` catches any other word.
- **Command step**: a command such as `npm test`; **If it passes** / **If it fails** go to different steps. Approval and allow-list rules apply.
- **Stop looping after N visits**, then go to another step; **Step limit** caps the whole workflow.

**Placeholders in a task:** `{task}` (your task), `{last}` (the previous step's output), `{node:<step>}` (that step's latest output, for example the failing test output).

**Buttons:**
- **Dry run**: walks the workflow with the offline mock (the first test fails, then passes) and shows the path.
- **Save workflow**: writes `.swarmlab/graph.json`.
- **Show JSON**: the raw file.

The drawing updates as you edit; renaming a step updates every reference to it. The same agent keeps its memory between visits (the fixer remembers its earlier attempts).

---

## 8. Prompts

**Prompts** tab:
- **Roles**: the built-in prompt of each role (single, tree-lead, tree-worker, swarm-lead, swarm-worker, graph-node, chat). Edit and **Save** to replace it; **Use the default** removes your file.
- **Agents**: instructions for one agent name, added after its role prompt. **Add** creates one.
- **Placeholders**: `{name}`, `{role}`, `{teammates}`, `{maxAgents}`, `{profiles}` (leads: your agents and their descriptions), `{rules}` (tool rules and allowed folders; added at the end if you leave it out). Unknown placeholders are flagged.
- **Preview the final prompt**: choose a role and an agent name → exactly what that agent would receive, with its engine, tools and folders.

---

## 9. Tools: MCP servers and skills

### 9.1 MCP servers

MCP servers give agents more tools (GitHub, databases, browsers, documentation, company APIs…).

1. **Tools** tab → **Add a local server (command)** or **Add a remote server (URL)**.
2. **Local server:** **Command** (for example `npx`), **Arguments** one per line (for example `-y` and `@modelcontextprotocol/server-github`), **Environment** as JSON (for example `{"GITHUB_TOKEN": "…"}`).
   **Remote server:** **URL** of the MCP endpoint, **Headers** as JSON (for example `{"Authorization": "Bearer …"}`).
3. **Calls**: **Ask me before each call** (default) or **Allow without asking**.
4. **Save servers** → **Connect and list tools**. Each server shows its tools or its error; a broken server does not stop the others.

Agents receive the tools as `mcp__<server>__<tool>`. In an agent's tools you can allow some with wildcards, for example `mcp__github__*`. The configuration is `.swarmlab/mcp.json` (the common `"mcpServers"` format is accepted). Environment and headers are stored in that file: do not commit secrets.

### 9.2 Skills

A skill is a folder with a `SKILL.md`: a name, a one-line description of **when** to use it, and instructions. Other files in the folder (scripts, templates) can be referred to.

```markdown
---
name: review-python
description: Use when reviewing Python code for bugs and security
---

1. Read the changed files with read_file.
2. Check error handling, input validation and secrets in code.
3. Answer with a numbered list, most serious first.
```

- **Create one:** Tools tab → **New or edit a skill** → name, *when to use it*, instructions → **Save skill**. Or ask the assistant: *"make a skill of what we just did"*; you approve it in the orange bar.
- **Use them:** agents see the list and load a skill with `use_skill` when a task matches.
- **Where:** `.swarmlab/skills/<name>/SKILL.md`, and also `.claude/skills/<name>/SKILL.md` (Claude Code's format, so the same skills work in both).

---

## 10. Code search (RAG)

Agents get a **`search_code`** tool that finds the code relevant to a question, even when the code uses other words (*"where are expired tokens handled?"*).

**Setup → Code search (RAG):**
1. **Code search on** (default).
2. **Embedding model** (optional, for search by meaning): for example `text-embedding-3-small`, `nomic-embed-text`, `bge-m3`. Empty = keyword search only, which works with any provider.
3. **Embeddings address**: an OpenAI-compatible `/embeddings` endpoint, for example `http://localhost:11434/v1`. Empty = the chat provider's address (OpenAI-compatible or OpenRouter). Anthropic has no embeddings endpoint: set an address, or stay keyword-only.
4. **Chat: add relevant code to each message**: the most relevant chunks are added to each chat message. Older retrieved code is removed from the history, since it can be found again.
5. **Results per search**, **Chunks added per chat message**, **Lines per chunk**, **Only these files** / **Also skip** (globs).
6. **Build index now**, then try the **Search** box.

**How it works:** files are cut into chunks at functions, classes and headings, and stored in `.swarmlab/index/index.json`. Search combines **keywords** (BM25, with code names split: `parseDate` → *parse date*) and **meaning** (embeddings), merged into one ranking. Results give the file, the line range and the code; the agent then reads the exact lines. The index updates by itself after you save, create, rename or delete files: only changed files are re-indexed.

---

## 11. Claude Code as an engine

Any agent except the leads can run on **Claude Code** (`claude -p`) instead of the Swarm Lab loop. It gets Claude Code's own tools, and its session is resumed on every turn, so it remembers.

1. Install Claude Code; `claude` must work in a terminal. Otherwise set **Claude Code path**.
2. **Setup → Agent engine**: **Default engine** (Swarm Lab loop or Claude Code), **Ask before Claude Code runs** (first time per agent / every time / never), **Budget per turn ($)**, **Time limit per turn**, **Bare mode** (skips the folder's hooks, plugins, MCP servers and CLAUDE.md; needs an Anthropic API key).
3. Per agent: **Agents** tab → **Engine: Claude Code**, with its own budget, model, permission mode and allowed tools. Allowed tools are built from **May edit** and the command allow-list, unless you write them yourself (for example `Read,Grep,Glob,Edit,Bash(npm test *)`).
4. **Test Claude Code** (Setup).

Claude Code edits files itself, so keep **Git safety** on ([12.4](#124-git-safety)): changes outside an agent's folders are reverted automatically, and you **Keep** or **Revert** the rest after each turn. While Git safety is on, Claude Code turns run one at a time.

Claude Code needs Claude models: directly, or through a gateway that speaks the Anthropic format (`/v1/messages`). It does not work with a Mistral or OpenAI-only endpoint; use the Swarm Lab loop for those agents.

---

## 12. Safety and control

### 12.1 Edits

**Setup → Safety → Edits**: **Each edit is a diff you approve** (default) or **Off** (read-only agents). Agents edit with exact replacements, write whole files in parts, save numbered code blocks, delete and rename, always within the folders they may edit. Edits outside those folders are blocked before you see them. Leads never edit.

### 12.2 Commands

**Commands:**
- **Ask every time** (default): a card shows the command, the reason and the folder.
- **Allow-list runs without asking**: commands in the **Allow-list** (default `npm test`, `pytest`, `go test`, `cargo test`…) run directly. A command with `;` `&` `|` `` ` `` `$` `<` `>` never matches, so `npm test && rm -rf /` still asks.
- **Off**.

**Will it ask?** tells you what would happen for any command. Output goes to **View → Output → Swarm Lab**.

### 12.3 Agent-to-agent messages

**Review agent-to-agent messages:** **Off**, **Tasks and questions from leads** (you can edit each one before it is sent), or **All**, including peer questions.

### 12.4 Git safety

**Git safety: Own branch per run** (in a Git repository with at least one commit):
1. Each run works on its own branch `swarmlab/run-<n>-<time>`. Uncommitted work is stashed first, if you agree.
2. Around each Claude Code turn: a checkpoint; afterwards, out-of-scope changes are reverted, and you **Keep** or **Revert**.
3. At the end of the run: **Keep** (a commit on the run branch, for you to merge) or **Revert all** (back to your branch, run branch deleted, stash restored).

`.swarmlab/` is never committed, stashed or reverted. Add `.swarmlab/` to `.gitignore` if you do not want it in the repository.

### 12.5 Limits

**Setup → Limits**: model calls per agent turn, workers per run, token budget per run, max tokens per call.

---

## 13. Context, limits and long answers

Open **Context NN%** at the top of the chat.

| Control | What it does |
|---|---|
| Meter | Tokens sent on each call, against your limit; messages, tool outputs, attached files |
| **Summarize when the chat passes (tokens)** | Older messages become a short summary |
| **Keep the last messages word for word** | Recent messages are never summarized |
| **Max tokens per answer part** | Your provider's output limit per call |
| **Provider input limit (tokens)** | Every call is kept under it (summarize, then trim); a clear message if it cannot fit |
| **Continue cut answers up to N times** | A cut answer is continued and the parts are joined into one answer; a cut code block continues inside the same block |
| **Answer length** | Short, Normal, Detailed |
| **Add relevant code automatically** | Code search adds the matching code to each message |
| **Step mode** | Pause before each model call, each tool call, or both: **Continue**, **Run to the end**, **Stop / Skip** |
| **Run tool calls one at a time** | The tools of one answer run in order instead of together |
| **Summarize now** · **Remove old tool outputs** · **Remove attached files** | Shrink the context by hand |
| **View context** | Opens exactly what the model receives, in an editor tab |

Every prompt requires closed, language-tagged code blocks; an answer that leaves a block open is closed automatically. A tool call cut by the output limit is not run, and the agent is asked for smaller steps (long files are then written in parts).

---

## 14. Check everything

**Check** tab → **Check everything**. It checks your provider and key, URLs and proxy, models, folder and Git, `policy.json`, `graph.json`, prompts, code search and embeddings, Claude Code, MCP and the safety settings. Each line is ✓ ok, i info, ! warning or ✕ error, with what to do. **Test connection**, **Test tool calling** and **Test Claude Code** are also there.

---

## 15. Files Swarm Lab keeps in your project

Everything lives in `.swarmlab/`, as plain files you can read and edit:

| Path | Contents |
|---|---|
| `.swarmlab/policy.json` | Agents and role rules: tools, folders, engine, model, tool calling |
| `.swarmlab/prompts/<role>.md`, `agent-<name>.md` | Prompts |
| `.swarmlab/graph.json` | Your workflow |
| `.swarmlab/mcp.json` | MCP servers |
| `.swarmlab/skills/<name>/SKILL.md` | Skills (also read from `.claude/skills/`) |
| `.swarmlab/chat/conversation.json`, `conversation-<date>.json` | The assistant's conversations |
| `.swarmlab/chat/agents/<name>.json` | Each agent's own conversation |
| `.swarmlab/memory/board.md`, `agent-<name>.md` | Shared board and long-term notes |
| `.swarmlab/index/index.json` | Code search index |

API keys are **not** in these files: they are in VS Code's secret storage.

---

## 16. All settings

All of these are in **Setup** (or the chat's Context drawer). They are also in VS Code settings under **Swarm Lab**.

**Models and network**

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.provider` | `anthropic` | `anthropic`, `openai` (OpenAI-compatible), `openrouter`, `vscode-lm`, `mock` |
| `swarmLab.baseUrl` | empty | API address; empty = provider default |
| `swarmLab.proxy` | empty | HTTP(S) proxy; empty = `http.proxy`, then `HTTPS_PROXY` |
| `swarmLab.keyHeader` | `authorization` | Header for an OpenAI-compatible key (`api-key` for Azure-style) |
| `swarmLab.extraHeaders` | `{}` | Extra headers on every request (no secrets) |
| `swarmLab.reasoningEffort` | not sent | `none` … `high` |
| `swarmLab.extraBody` | `{}` | Extra fields in every request body |
| `swarmLab.leadModel` | `claude-sonnet-5-5` | Assistant, single agent, leads |
| `swarmLab.workerModel` | `claude-haiku-5-5` | Workers, sub-agents, workflow steps |
| `swarmLab.vscodeLmVendor` | empty | VS Code models: only this vendor (for example `copilot`) |
| `swarmLab.toolMode` | `native` | `native`, `text`, `none` |

**Engines**

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.chatEngine` | `native` | The chat assistant's engine |
| `swarmLab.defaultEngine` | `native` | Agents without an engine in `policy.json` |
| `swarmLab.claudeCode.path` | `claude` | Claude Code executable |
| `swarmLab.claudeCode.confirm` | `first` | `first`, `every`, `never` |
| `swarmLab.claudeCode.bare` | `false` | `--bare` |
| `swarmLab.claudeCode.maxBudgetUsd` | `1` | Per turn (0 = no cap) |
| `swarmLab.claudeCode.timeoutSec` | `900` | Per turn |

**Safety**

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.git` | `branch` | Git safety: `branch` or `off` |
| `swarmLab.edits` | `ask` | `ask` or `off` |
| `swarmLab.commands` | `ask` | `ask`, `allowlist`, `off` |
| `swarmLab.commandAllowList` | `npm test`, `pytest`, … | Commands that run without asking with `allowlist` |
| `swarmLab.commandTimeoutSec` | `120` | Per command |
| `swarmLab.reviewMessages` | `off` | `off`, `lead`, `all` |
| `swarmLab.memory` | `true` | Board and long-term notes across runs |

**Limits, context and long answers**

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.maxStepsPerAgent` | `8` | Model calls per agent turn |
| `swarmLab.maxAgents` | `5` | Workers per run |
| `swarmLab.tokenBudget` | `300000` | Tokens per run |
| `swarmLab.maxTokensPerCall` | `1500` | Output limit per call |
| `swarmLab.maxInputTokens` | `0` | Provider input limit (0 = none) |
| `swarmLab.maxContinuations` | `3` | Continue cut answers up to N times |
| `swarmLab.answerLength` | `normal` | `short`, `normal`, `long` |
| `swarmLab.chatContextTokens` | `40000` | Summarize past this |
| `swarmLab.chatKeepMessages` | `6` | Kept word for word |
| `swarmLab.stepMode` | `off` | `off`, `model`, `tools`, `both` |
| `swarmLab.sequentialTools` | `false` | Tool calls one at a time |

**Code search**

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.rag.enabled` | `true` | `search_code` for agents |
| `swarmLab.rag.autoContext` | `true` | Chat: add relevant code to each message |
| `swarmLab.rag.topK` | `6` | Results per search |
| `swarmLab.rag.autoK` | `4` | Chunks per chat message |
| `swarmLab.rag.chunkLines` | `60` | Lines per chunk |
| `swarmLab.rag.include` / `rag.exclude` | empty | Globs |
| `swarmLab.rag.maxFiles` | `5000` | Files indexed |
| `swarmLab.rag.embeddingModel` | empty | Empty = keywords only |
| `swarmLab.rag.embeddingBaseUrl` | empty | Empty = the chat provider's address |

---

## 17. All commands

Command Palette (**Ctrl+Shift+P**):

| Command | What it does |
|---|---|
| **Swarm Lab: Open** | Open the panel |
| **Swarm Lab: Choose model provider** | Guided setup: provider, address, proxy, key, models |
| **Swarm Lab: Set API key** / **Clear API keys** | Keys in secret storage |
| **Swarm Lab: Test connection** | One small request to the model |
| **Swarm Lab: Pick OpenRouter models** / **Pick a VS Code language model** | Model pickers |
| **Swarm Lab: Edit prompts and permissions** | Create the starter files in `.swarmlab/` |
| **Swarm Lab: Build code index** | Build or update the code search index |
| **Swarm Lab: Open memory** / **Clear memory** | The shared board and notes |

---

## 18. Troubleshooting

| Problem | What to do |
|---|---|
| **"Swarm Lab: Open"** is missing | Check the extension is installed and VS Code is 1.95 or later; run **Developer: Reload Window** |
| The panel is empty or buttons do nothing | **Developer: Reload Window**; then **Developer: Toggle Developer Tools → Console** and look for red errors |
| `401 invalid x-api-key` or `401` | The key was saved for another provider. **Clear API keys**, then **Set API key** and choose the right provider |
| Runs say "offline mock" | No key for the chosen provider, or the base URL is not valid (it needs `http://` or `https://`) |
| **Test tool calling** fails | Turn tool calling on in your server, or set **Tool calling: Text** |
| *"function tools with reasoning effort not supported"* | **Reasoning effort: none** |
| A local model is not reached behind a proxy | Fixed: `localhost` and `NO_PROXY` hosts go direct. Check the port and `/v1` |
| The chat seems stuck | Look at the orange bar: requests may be waiting for you. **Stop** always frees the chat |
| Answers are cut | Raise **Max tokens per answer part**, or **Continue cut answers**; ask to save code with `save #N` instead of rewriting it |
| *"larger than the provider's input limit"* | **New chat**, attach fewer files, **Remove old tool outputs**, or raise the limit |
| An MCP server shows an error | **Open** the error: command not found, wrong token, or HTTP 401; fix and **Connect** again |
| Code search finds nothing by meaning | Set an embedding model and address, then **Build index now** |
| Claude Code is not found | Install it, or set **Claude Code path**; **Test Claude Code** |
| Git safety is off | The folder must be a Git repository with at least one commit |
| Server tab: "No server at …" | Start one (**Start local server**, or `npx swarm-lab serve`), or fix the address |
| Server: `401` / `403` | **Server → Set API key**; the key needs the role (`submit`, `read`, `approve`) |
| A `/remote` job stays waiting | It needs an approval: **Server → Waiting for you on the server** |
| A server job fails with "needs a workflow" | Graph mode: add `.swarmlab/graph.json` to the repository, `"workflows"` to the server configuration, or `--workflow NAME` |
| Logs | **View → Output → Swarm Lab** (commands, Claude Code, Git, index, local server) |

---

## 19. Run it as a service (API, queue, workers)

For real, continuous use (many tasks, history, triggers, several machines), run the same engine as a **server**.

**How it works:**
1. You send a job: `POST /v1/jobs {"repo": "app", "task": "…", "mode": "graph"}`.
2. A worker runs it in its own sandbox.
3. Every event is stored, and approvals wait for a human.
4. The result comes back: an answer, a branch, a patch, files.

The store is files (one machine) or PostgreSQL (many API and worker processes). The repository's `.swarmlab/` folder (agents, prompts, workflows, skills) is used as is.

### 19.1 Start

```bash
npx swarm-lab init      # writes swarmlab.server.json: set your repository and model
npx swarm-lab check
npx swarm-lab serve     # API + workers + dashboard on http://127.0.0.1:8787
```

Or from VS Code: **Server** tab → **Start local server**. The first click creates `swarmlab.server.json` with this folder as the repository; the second starts the server.

### 19.2 Two options per job

| Option | With | Without |
|---|---|---|
| **Repository** (`repo`) | Works on your code, in a worktree on its own branch; result = a commit, optionally pushed with a draft pull request | A fresh empty workspace: ideas, tickets, diagrams, documents |
| **Created files** (`files`) | Each created or changed file is downloadable on its own (`files/<path>`) | Only `changes.patch` and `report.json` |

The default for files is *yes* without a repository, *no* with one.

### 19.3 MCP on the server, in one command

```bash
npx swarm-lab mcp add jira --command npx --arg -y --arg <jira-mcp-package> --env JIRA_TOKEN='${JIRA_TOKEN}'
npx swarm-lab mcp list
npx swarm-lab mcp remove jira
```

Each server is checked when added. Workers use it from their next job, without a restart. Each call is an approval unless the job sets `"approvals": {"mcp": "auto"}`.

### 19.4 Use it from VS Code: the Server tab

- **Connection:** address, **Set API key** (secret storage), **Test**, **Open dashboard**, **Start local server** / **Stop** (logs in **View → Output → Swarm Lab**).
- **New job:**
  - organization, workflow, **Run as**, and the edits and commands rules;
  - **Repository** (or **No repository**) and **Created files**;
  - priority, then the task.
- **Waiting for you on the server:** the server's approvals, with diffs.
- **Jobs:** live events, answer, branch, diff summary, files; **Open** any artifact in the editor; **Cancel** / **Run again**.
- **From the chat:** `/remote` (section 4.11).

### 19.5 Use it from your own application

`clients/README.md` gives the exact JSON to send and to expect, events, approvals, errors and the webhook payload. `clients/python/` has a client (standard library only) and an example app:

```python
from swarmlab_client import SwarmLabClient
sl = SwarmLabClient("http://127.0.0.1:8787", api_key="sl_...")
job = sl.run(None, "Draw the order flow as a Mermaid diagram in docs/orders.md")   # no repository
print(job["result"]["answer"]); sl.download_files(job["id"], "out/")
```

### 19.6 Scale

PostgreSQL (`SWARMLAB_DATABASE_URL`), then `swarm-lab api` and `swarm-lab worker` on as many machines as needed, or `docker compose up -d --scale worker=6`. **SERVER.md**, next to this README in the source code, covers everything: configuration, approval rules, API reference, GitHub webhooks, PostgreSQL, Docker, security and monitoring.

## 20. Build, test and publish

```bash
npm install
npm test            # all logic tests (engine, tools, MCP, code search, chat, Git on a real temporary repository…)
npm run package     # builds swarm-lab-<version>.vsix (needs @vscode/vsce)
```

Press **F5** in VS Code to start an Extension Development Host.

**Publish on Open VSX:**
1. Create an Eclipse account (accounts.eclipse.org) with your **GitHub username** in its profile.
2. On open-vsx.org: sign in with GitHub → profile → **Log in with Eclipse** → **Show Publisher Agreement** → accept.
3. **Settings → Access Tokens** → create a token.
4. Once: `npx ovsx create-namespace <publisher> -p <token>` (the `publisher` of `package.json`).
5. Each version: `npx ovsx publish swarm-lab-<version>.vsix -p <token>` (Windows: `npx.cmd` if scripts are blocked).

**Code map:**

| Path | Contents |
|---|---|
| `src/core/engine.ts` | Agents, organizations, tools, approvals, limits, memory, chat |
| `src/core/llm.ts` | Anthropic, OpenAI-compatible, OpenRouter clients; embeddings; proxy |
| `src/core/textTools.ts` | Text tool calling for models without tool calling |
| `src/core/rag.ts` | Code search: chunks, BM25, embeddings, fusion, incremental index |
| `src/core/mcp.ts`, `src/core/skills.ts` | MCP client (stdio and HTTP), skills |
| `src/core/chatContext.ts` | Context measuring, trimming, code blocks, fences |
| `src/extension.ts` | Commands, chat controller, runs |
| `src/panel.ts`, `src/panelWorkbench.ts` | The panel and its tabs |
| `src/vscode*.ts`, `src/workbench.ts` | VS Code layers: files, Git, Claude Code, code index, tools, setup |
| `src/server/` | The server: configuration, stores (files, PostgreSQL), sandbox, Git, runner, workers, API, dashboard, CLI |
| `src/test/` | Tests |

**Third-party:** Mermaid (MIT) bundled in `media/mermaid.min.js`; undici (MIT) for proxies.

**License:** MIT.
