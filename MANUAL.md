# Swarm Lab: the full manual

Swarm Lab is a VS Code extension for working on your code with AI agents, under your control. You can **chat** with an assistant that knows your project, **define your own agents**, and run them **alone, as a tree, as a swarm, or in your own fixed workflow (graph)**. Every file change is a diff you approve, every command waits for your click, and everything the agents are told and do is visible.

It works with **Anthropic, OpenRouter, any OpenAI-compatible server** (a company gateway, LiteLLM, vLLM, Ollama, LM Studio, a local model behind a proxy), **VS Code's own models**, or **Claude Code** as the engine of an agent. Models **without tool calling** work too.

## Explicit read scopes (bounded slice)

Agents merges policy names with saved/draft named prompts, without saving permissions merely on view. Edit a permission deliberately and Save. May read stores optional readPaths: missing inherits name/glob → role → legacy unrestricted; ** explicitly allows workspace files; none stores an empty list and denies file reads. Data inputs remain references, not access restrictions or read grants. Existing editPaths behavior is unchanged when no read scope exists.

Explicit scopes are currently native single/chat **read-only**: host-side filtered file lists/text search and scoped read_file/read_data, including existing document parsers. Only workspace documents are supported, not external assigned data. Paths containing traversal and symbolic-link components are rejected. Reads check paths immediately before opening, but concurrent hostile filesystem mutation is not sandboxed.

Unsupported tools (including edits, commands/tests, MCP, web, skills, code symbols/call graphs, semantic retrieval, memory and all delegation) are denied at dispatch, even if a model requests a hidden tool. Tree/swarm/graph scoped agents fail closed because hand-off context is not isolated. Automatic retrieval and memory recall are skipped for scoped chat; restored history, inline Attached files payloads and images are discarded. Start a new chat when changing permissions. Shared rules, requirements and configured role/agent prompts are necessarily visible. User-authored text and prompts may disclose arbitrary content; this is not OS isolation or general information-flow control. Agents offers a repository file/folder picker with search, optional document filtering, paging, removable selection chips and advanced glob text. Inherit, All, None and Custom remain drafts until Apply; Save permissions persists them. Cancel or Escape discards the picker draft. The paths-only administration list excludes dependency/build/cache folders and symlinks, and scans at most 20,000 entries / 2.5 seconds; it is not a complete repository index or a read grant. Scoped edits remain unsupported. Inherited role read scopes may make a named agent read-only depending on execution mode. Effective patterns and disabled routes appear in prompt preview.

**Highlights**
- **Chat with your codebase:** the assistant searches and reads your code, explains it, and proposes changes as diffs you approve.
- **Your own agents:** give each one instructions, a model, tools and the folders it may change; talk to them, or let them work together.
- **Four ways to organize agents:** one agent, a tree (a lead splits the task), a swarm (workers share a board and talk to each other), or your own fixed workflow (for example plan → fix → test → review).
- **Always in control:** a single "Waiting for you" bar for every edit, command and question; per-agent permissions; Git safety for every run.
- **Visual answers:** tables, ✅ ⚠️ 💡 callouts, syntax-colored code, and Mermaid diagrams you can save as **PNG, PDF or SVG**.
- **See the work:** a live step map of every model call, tool, edit and decision; Explorer badges and line highlights on what the agents touched; a code map of what calls what, from VS Code's own call hierarchy (sections 21 and 22).
- **Test and measure:** a `run_tests` tool with short failure reports, and a Bench that gives your own tasks to several setups and compares pass rate, tokens and cost with a baseline (sections 24 and 25).
- **Spend fewer tokens:** an optional decision model such as Jev (through OpenRouter) answers routing decisions in a fraction of the cost (section 23).
- **Extras:** code search by meaning, MCP tools, reusable skills, step-by-step mode, long answers continued automatically, and a built-in server to run many jobs in the background.

---

## Panel navigation (0.37.1)

The panel has two navigation levels: **Work** (Chat, Run, Project), **Build** (Agents, Workflow, Prompts), **Explore** (Codebase Graph, Code map), **Evaluate** (Bench, Check), and **Settings** (Setup, Tools, Server). Groups remember their last view until the webview reloads. Arrow keys, Home/End and Enter work on both rows; narrow panels scroll horizontally.

Chat keeps agent/model/New chat primary. **Conversations**, **Data**, **Memory** (or **Notes** when memory is off), **Activity / Steps**, **Context**, and **Costs** are inspectors, not another navigation level. Only one opens at a time; press it again to close. Messages, approvals and composer stay in place. Engine/Web are under **Chat settings**; **Actions** holds Reset view and Reload panel. The global **Chat · N waiting** button opens pending approvals even from another group.

## Project tab: shared context and requirements (phase 1)

Open **Project**, edit shared rules, or **Add requirement**. IDs are assigned as REQ-1, REQ-2, etc. and remain read-only when editing. Fill the title, description, priority, status and acceptance criteria (one per line), then click the corresponding **Save (confirm)** button. Only saved files affect future runs; an already-running agent keeps its original context. Switching tabs preserves drafts. **Reload saved context** asks before discarding drafts. Reload after external edits.

Rules save only `.swarmlab/rules.md`. Other rule files and role/agent prompts are not overwritten. Requirements save only `.swarmlab/project.json`:

```json
{
  "version": 1,
  "requirements": [
    {
      "id": "REQ-1",
      "title": "Preserve existing behavior",
      "description": "Keep legacy projects working.",
      "priority": "must",
      "acceptanceCriteria": ["Regression tests pass"],
      "status": "proposed"
    }
  ]
}
```

IDs must be unique, letter-prefixed and at most 64 characters (letters, digits, underscore, hyphen). Priorities: must, should, could. Statuses: proposed, planned, in_progress, blocked, implemented, verified. All fields are required; unknown fields are rejected. Maximum: 100 requirements, 200-character titles, 8000-character descriptions, 30 nonempty acceptance criteria of 2000 characters each, 200000 aggregate serialized requirement characters, and a 1 MB requirements file. No requirements file preserves legacy behavior. Invalid files block execution and display an error; repair them in VS Code, then reload. There is no requirement deletion/reordering UI in phase 1; use the file for those operations.

The preview displays the exact **saved shared project-context fragment** used by native and Claude Code prompts, with source references and warnings; it is not the entire role/tool/history/retrieval prompt. All mandatory rules and must requirements are retained, never silently truncated. Optional requirements exceeding the 12000-character context budget are omitted with individual warnings. Large mandatory context may exceed a model's context limit and fail; no token-count or model-capacity guarantee is made.

Saves require workspace trust and modal confirmation. Cancellation, validation errors, stale disk content and detected symbolic links are reported without discarding drafts. Trust, symlinks and stale content are rechecked after confirmation; filesystem-provider checks cannot guarantee atomic compare-and-swap against a simultaneous external writer or symlink swap. Use a normal trusted workspace and avoid concurrent external saves. Fixed paths only are accepted from the UI. Statuses are user reports, not independent test evidence, approved plans or automatic completion. The Project tab also provides a version-1 plan JSON editor with Save and Approve buttons. Each step includes id, title, links ({requirementId, criterion}, zero-based), command and claim. Approval uses a trusted host modal and a SecretStorage-backed signature bound to exact saved plan/project/shared-rule bytes and workspace; edits make it stale. Existing VS Code approved commands capture a pre-execution snapshot and save signed exit outcomes with exact-command requirement links. Reload Project to refresh outcomes. Forged receipts are untrusted; malformed receipts display an error. Exit zero is not requirement verification, code-freshness proof or automatic completion. Plan approval does not bypass command approval. Plan-to-prompt/context integration, Claude CLI/server command receipts, durable jobs and broader traceability remain deferred. Filesystem checks are not atomic against concurrent external writers.

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
19. [Background jobs: the Server tab](#19-background-jobs-the-server-tab)
20. [Privacy and data](#20-privacy-and-data)
21. [Step map and agent activity](#21-step-map-and-agent-activity)
22. [Code map](#22-code-map)
23. [Decision models (Jev and others)](#23-decision-models-jev-and-others)
24. [Tests: run_tests](#24-tests-run_tests)
25. [Bench: compare setups on your own tasks](#25-bench-compare-setups-on-your-own-tasks)
26. [Automatic model choice](#26-automatic-model-choice)
27. [Project management workflows](#27-project-management-workflows)
28. [Memory by conversation and topic, and checked "done"](#28-memory-by-conversation-and-topic-and-checked-done)
29. [Skills that earn their place, tidy memory, and what fills the context](#29-skills-that-earn-their-place-tidy-memory-and-what-fills-the-context)
30. [Your own workflow templates](#30-your-own-workflow-templates)
31. [Experiments on the server](#31-experiments-on-the-server)
32. [Scripted jobs on the server: your agents, prompts, memory, and reports](#32-scripted-jobs-on-the-server-your-agents-prompts-memory-and-reports)
33. [Your whole setup on the server: profiles, MCP, skills, checks, hooks](#33-your-whole-setup-on-the-server-profiles-mcp-skills-checks-hooks)
34. [Data: give agents files and folders](#34-data-give-agents-files-and-folders)
35. [Calibrate an LLM judge](#35-calibrate-an-llm-judge)
36. [How many model calls at once](#36-how-many-model-calls-at-once)
37. [Edit an answer, a code block or a diagram](#37-edit-an-answer-a-code-block-or-a-diagram)
38. [Edit a picture before you send it](#38-edit-a-picture-before-you-send-it)
39. [Web research (on or off)](#39-web-research-on-or-off)
52. [The Lab: GPU or CPU, apps, training runs and their results](#52-the-lab-gpu-or-cpu-apps-training-runs-and-their-results)
53. [Metadata filters on code search](#53-metadata-filters-on-code-search)
54. [Web pages: source type and dates](#54-web-pages-source-type-and-dates)
55. [Pasted text, the message editor and Access](#55-pasted-text-the-message-editor-and-access)
56. [The message box (0.45)](#56-the-message-box-045)
57. [Refine a harness](#57-refine-a-harness)
58. [The panel: sidebar, Details, groups and views](#58-the-panel-sidebar-details-groups-and-views)
59. [Language](#59-language)
60. [Certificates (trust store)](#60-certificates-trust-store)
61. [Review by conditions and inputs](#61-review-by-conditions-and-inputs)
62. [Pictures inside attached files](#62-pictures-inside-attached-files)
63. [Reminders and the Today page](#63-reminders-and-the-today-page)
64. [The Atlas of your documents](#64-the-atlas-of-your-documents)
65. [🩺 Check: why an answer is wrong](#65--check-why-an-answer-is-wrong)

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

**From Open VSX** (VSCodium, Cursor, Windsurf and other editors that use Open VSX): open the Extensions view (**Ctrl+Shift+X**, Mac **Cmd+Shift+X**), search for **Swarm Lab**, and click **Install**.

**From a `.vsix` file** (VS Code, or any editor):
1. Download `swarm-lab-<version>.vsix` from the extension's page on open-vsx.org.
2. Extensions view → **⋯** at the top → **Install from VSIX…**, and choose the file. Or in a terminal: `code --install-extension swarm-lab-<version>.vsix`.
3. Run **Developer: Reload Window** (Command Palette: **Ctrl+Shift+P**).

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

### 3.8 Several model servers: connections (0.49)

With **connections**, Swarm Lab uses several model servers side by side, each with its own address, settings and API
key: Ollama on this machine, a company gateway, vLLM on a GPU box, OpenRouter… Open *Setup → Connections* (or
**Swarm Lab: Connections**).

1. Choose a starting point (Ollama, LM Studio, vLLM, LiteLLM or a gateway, Azure OpenAI, OpenAI, Anthropic, OpenRouter,
   Groq, DeepSeek, Mistral, Together, Gemini, xAI, another server), **Add**, check the base URL, **Save connections**.
2. **Key**: kept in VS Code's secret storage on this machine (never in settings) and sent only to that address. A server
   on this machine needs none. Settings Sync copies connections, not keys: on another computer, Setup, the model picker
   and the status bar say “key missing on this machine”.
3. **⟳** asks the server for its models; keep the ones you use. They appear next to Send, grouped under the connection.
4. **Test** asks for the model list and makes one tiny call.
5. **⋯** shows the connection's proxy, key header (“api-key” for Azure-style gateways), reasoning effort, extra headers
   and extra request fields.

**Naming a model on a connection**: `@id/model`, for example `@ollama/qwen2.5-coder:7b` or
`@openrouter/anthropic/claude-sonnet-5-5`. It works for the lead and worker models, the chat's model, the model list of
automatic choice, the Atlas, embeddings (`swarmLab.rag.embeddingModel`), the decision model and fallbacks. A plain name
goes to the **default connection**. So a team can have a cheap local worker (`@ollama/qwen2.5-coder:7b`) and a cloud
lead (`@openrouter/…`). Prices, context windows and pictures go by the bare model name, and a server on this machine
costs $0.

**The default connection** is chosen next to Send (🔌), in the status bar, or in Setup, for every folder or *only for this
workspace*. “Setup” is the classic *Model provider* fields below: until you choose another default, nothing changes.
**Make the Setup fields a connection** copies them (key included) when you want to keep them as one of several.

**Fallbacks** (one per line): when a model is down (rate limit, server error, no connection) after its own retries, the
next is tried, and the chat says so. A real error, such as a refused key or an unknown model, is shown instead.

**The local server** uses the default connection; its key is passed only when the server's provider is that connection.
Models on other connections are sent with their bare name (and the log says so): the server has one provider.

**Sharing**: **Export…** writes the connections without keys; **Import…** adds them (same id: replaced; fields that look
like keys are refused). Migrating from Cline, Roo or Continue keeps every model server found in
`.swarmlab/connections.json` and offers to add them.

Connections are user settings only (`swarmLab.connections` cannot be set by a folder), so a cloned project cannot send
your saved key to another address. The default (`swarmLab.connection`) and `swarmLab.fallbacks` can be set per workspace.

### 3.9 Setup presets and the Essentials view (0.49)

*Setup → Setup presets* (or **Swarm Lab: Apply a setup preset**) changes a few settings at once; you see each change
before it applies:

| Preset | What it sets |
|---|---|
| 🖥 Local model (Ollama) | Adds an Ollama connection (no key) and makes it the default, asks it which models lead and work, helpers for small models, answers in steps for small windows, 3 agents |
| 💲 Cheap | Automatic choice “cheapest”, simple messages on the worker, short answers, $0.05 per message and $2 per day |
| 🔐 Careful | You approve every edit and command, no auto-approve, the lead reviews, changes verified with tests, risky ones thought through first |
| ↺ Back to the defaults | The settings above, back to Swarm Lab's defaults (connections and keys are kept) |

**Essentials / Everything** at the top of Setup shows only presets, connections, the model, the engine, isolation,
costs, safety and limits, or all settings.

Under the message box, a chip says **where commands run** (🧪 venv, 🐳 Docker · net on/off, ⚠ no sandbox): click it to
change it, turn Docker's network on or off, or reset the environments. **💲 This chat** shows what the conversation
cost so far; click it for today, the month and the limits.

### 3.10 One place for every model: Setup → Models (0.49.2)

**Setup → Models** lists every model of every connection, and the roles are chosen from that list.

1. **Connections** (above): add each server (OpenRouter, Ollama, a local gateway, your own URLs) and its key.
2. **Models → ⟳ Models on this server**: pick a connection, ask its server; tap the models you use (or **Add all**), or
   type a name and **Add**. **Save models**.
3. **Roles**: choose from the lists, grouped by connection:

| Role | What it does | Setting |
|---|---|---|
| Lead | Plans and leads runs; the single agent | `swarmLab.leadModel` |
| Worker | Workers, sub-agents, summaries | `swarmLab.workerModel` |
| Chat | The chat's model (also next to Send), or Auto · cheapest / balanced / best | `swarmLab.chat.model` |
| Decisions | Off; the worker model as JSON; any model as JSON; or Jev and other System One servers (Decision model) | `swarmLab.decisions.*`, `swarmLab.decisions.chatModel` |
| Embeddings | Code search by meaning (off: keywords only) | `swarmLab.rag.embeddingModel` |
| Atlas: entities and relations | The Atlas's model pass: rules only, ask at each build, or with the model you choose | `swarmLab.atlas.model`, `swarmLab.atlas.extractModel` |

4. **Automatic choice**: tick **Auto** on the models it may pick, check their size (or **Sizes by price**) and prices,
   choose the strategy. **Fallbacks** are tried in order when a model is down.

The classic *Model provider* fields are the built-in “Setup” connection, folded under Connections. A model on another
connection is named `@id/model` in settings; in Setup you only pick it.

### 3.11 Trying a reranker, and using it for code search (0.49.4)

A reranker takes a question and some texts and scores how well each text answers it. Nothing changes until you choose
one: code search works as before.

1. **Its server**: in *Connections*, add **Cohere**, **Jina**, **Voyage**, **Text Embeddings Inference** (on this
   machine), or your own server, and its key.
2. **The model**: in *Models*, pick that connection, type the model's name (for example `rerank-v3.5`,
   `jina-reranker-v2-base-multilingual`, `rerank-2`, or the model your TEI or vLLM server runs) and **Add**,
   **Save models**. Do not tick **Auto** for it: automatic choice is for chat models.
3. **Try it**: *Models → Try a reranker* (or **Swarm Lab: Try a reranker**). Choose the model, type a question, then
   either your own texts (a blank line or `---` between them) or **What code search finds**, and **Rank**:

| Column | What it shows |
|---|---|
| Rank | Its place in the reranker's order |
| Before | Its place before (your order, or code search's), with ↑ or ↓ |
| Score | The reranker's score, with a bar from the lowest to the highest |
| Text | The text (for code search: the file and line, and whether keywords or meaning found it) |

   Above the table: how many texts, how long it took, the model, how it was called and how many moved. *The server's
   answer* shows the raw reply; **Copy the results** copies the table.
4. **Use it** (optional): **Use it for code search**, or *Roles → Reranker*. The best *N* results of the usual search
   (30 by default) go to the reranker and come back in its order. If it fails, the usual order is used. *Off* stops it.

**How it is called**: *Cohere-style* (`query` and `documents` to `…/rerank`: Cohere, Jina, Voyage, vLLM, llama.cpp,
Infinity, LiteLLM) or *TEI-style* (`query` and `texts`: Hugging Face text-embeddings-inference). *Auto* tries the first,
then the second. The address is the connection's base URL followed by `/rerank` (a base that already ends in
`/rerank` is used as it is).

### 3.12 The reranker playground and campaigns (0.49.5)

**One question, for developers.** In *Try a reranker*, the texts can be a JSON list (`["…"]` or
`[{"id": "doc-12#3", "text": "…"}]`), JSON lines, a CSV with `id` and `text` columns, or paragraphs;
`{"id": "x", "file": "docs/policy.pdf"}` reads a file of the folder. The results keep your ids. **Request options**:
`top_n`, the longest text sent, `return_documents`, TEI's `raw_scores`, and more fields as JSON (none set: the request is
as before). Under the results: **The request sent** (the key shown as `$RERANK_API_KEY`), **The same call as code**
(curl, Python, JavaScript; **Copy as code**), **Copy as JSON** (`id`, `rank`, `before`, `index`, `score`) and **Scores
0–1**.

**Campaigns: many questions at once.** *Reranker campaign* (or **Swarm Lab: Reranker campaign**). A campaign is JSON:

```json
{
  "name": "Invoices",
  "documents": [{ "id": "round", "text": "The total is rounded to two decimals." }, { "id": "send", "file": "docs/billing.pdf" }],
  "queries": [{ "id": "q1", "query": "How is the total rounded?", "relevant": ["round"] }],
  "models": ["@cohere/rerank-v3.5"],
  "params": { "topN": 10 }
}
```

A question may have its own `documents`. **Import…** also reads JSON lines (one question per line) and a CSV of
questions (`query`, `relevant` with ids separated by `|`). *Ranked against* can be **what code search finds** for each
question (its best N): then `relevant` names files. **Cut files into chunks** cuts file texts as code search does (ids
`<id>#1`, `<id>#2`…; a relevant file id counts for all its chunks). Tick the rerankers, **Run the campaign**:

| Column | Meaning |
|---|---|
| Right first | Share of questions where a right text came first (hit@1) |
| Top 3 | Share where a right text is in the first three |
| MRR | Average of 1 / the rank of the first right text |
| nDCG@10 | How high all the right texts are in the first ten (1 = perfect) |
| Avg ms, p95 ms | Speed; Failed: calls that did not answer |

**As given** (the texts in their order, or code search's order) is the baseline; the best reranker is starred. Per
question you see where the right text came and the top 3. **Save** keeps the campaign in `.swarmlab/rerank/`;
**Report** saves Markdown, CSV or JSON in `.swarmlab/rerank/reports/`.

### 3.13 Chaining models: pipelines (0.50.0)

A **pipeline** runs several models one after another on the same input. *Setup → Models → Try a pipeline* (or
**Swarm Lab: Try a model pipeline**).

1. **Add steps** and drag them into order. Each step is a model of any connection:

| Step | What it does |
|---|---|
| Embeddings | Ranks the texts by meaning (an embedding model) |
| Reranker | Reorders the texts (a reranker) |
| Generate | Writes an answer from the top texts (any chat model) |
| Decide | Returns a JSON object from the top texts |
| Entities | Finds named entities in the top texts (NER) |

   A ranking step can **keep** only its best N for the next step; a writing step uses the **top N** texts and an
   instruction where `{context}` is those texts and `{query}` the question.
2. **Question**, and the texts (your own, or what code search finds).
3. **Run the pipeline**: you see each step's output — the order after it, or the answer it wrote — and the final answer.
   A step that fails stops the chain and says why; the earlier steps' output is still shown.

A common chain is **embeddings → reranker → generate**: embeddings narrow by meaning, the reranker reorders the best,
and the model writes the answer from the top few. **Add to the campaign** turns a pipeline into a column in a reranker
campaign (3.12), so you can compare, over many questions, a pipeline against a single reranker and against the texts as
given — on ranking (hit@1, MRR, nDCG@10) and, when the pipeline writes answers, on how many pass each question's check.

### 3.14 Comparing whole pipelines in the Playground (0.50.3)

Open **Settings → Playground** (or **Swarm Lab: Open the model Playground**) and choose **Pipelines**.

**Build.** Each pipeline is a chain drawn left to right: *Dataset → steps → Answer* (or *Ranking*). Add one from a
preset or empty; insert a step with the **+** between two steps; reorder by dragging a step's title or with ‹ ›; remove
with ×. Every step has a model (empty: the model of the matching Role), and a number: for embeddings and rerankers, how
many documents it passes on; for generate, decide and entities, how many of the top documents go into the prompt as
`{context}`. Generate and decide steps take an optional prompt with `{query}` and `{context}`.

**Data.** Pipelines use the same dataset as Retrieval — queries, documents and the relevant (✓) labels — plus an
optional **expected answer** per query: key words separated by commas (all must appear), expected JSON for a decide
step, or entity names for an entities step. The judge also reads it as the reference answer.

**Judge.** *Grade answers with an LLM judge* adds a 1–5 score and a one-line reason to every answer (one extra call per
answer). Empty model: your decision model. Available in Generation too.

**Results.** One row per pipeline: Hit@1, MRR, nDCG@k and Recall@k on the order the pipeline ends with (only for
pipelines that rank), the answer check, the judge's average, and latency. Pick a query to see each pipeline's trace:
every step with its time and the ids it kept (relevant in green), then the answer with its checks. *Data → Copy the
results (CSV)* exports one row per pipeline and query.

**Projects and history.** *Data → Save project as…* writes a `.playground.json` (default `.swarmlab/playground/`) with
the dataset, every model and pipeline, the judge settings and the run history; after that, changes are saved to it
automatically (Ctrl/Cmd+S saves too). Commit it to share or review changes. *Open a project or dataset…* reads it back,
or a `{ "queries": [...], "documents": [...] }` dataset, or any file of documents. Every run is kept in **Run history**;
the tables show the change since the previous run, or since any run you pick with *Compare*.


## 4. Chat

### 4.0 Seeing and fixing attached files, and moving in a long chat (0.49.3)

**Attached files.** Tap a file's name, in the message box or in a message you sent:

| The file | What you see | What you can do |
|---|---|---|
| Text (code, Markdown, CSV, JSON…) | Its contents, editable | **Save to file** (Ctrl+S), **Revert**, **Undo the save** |
| A document (PDF, Word, PowerPoint, Excel, notebook…) | What the model reads from it | **Open** it in its own program |
| A picture | The picture, large | **✎ Edit the picture** |

Files not sent yet also have **Replace…** and **Remove**; a message already sent has **Fix and resend** (change its
files or text and send it again). Saving changes the file in your folder. A file that changed since you opened it (in
the editor or by a run), or that has unsaved changes in an editor tab, is not overwritten.

**Moving in a long chat.** While you read earlier messages, new ones do not pull you down: **⤓ N new** shows what
arrived. Buttons at the bottom right: **☰** your messages to jump to, **⤒** top, **▲ ▼** one message up or down, **⤓**
latest. Keys: **Alt+↑ / Alt+↓**, **Alt+Home / Alt+End**.


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

### 4.2 From the editor

You do not have to copy code into the chat:
- **Right-click** in a file → **Swarm Lab** → **Explain this code**, **Fix this code**, **Write tests for this code**, **Suggest improvements**, **Ask about this code…**. They work on the selection, or on the whole file when nothing is selected. The chat opens beside your code, with the code and its location already in the message.
- **On a red or yellow underline**, the light bulb (**Ctrl+.**) offers **🤖 Fix with Swarm Lab**. The error message and the lines around it go to the chat; the fix comes back as a diff you approve.
- **Ctrl+Alt+I** (Mac **Cmd+Alt+I**): **Ask about this code…**.

### 4.2b Review a branch or your changes

Type `/review` in the chat, or run **Swarm Lab: Review my branch or changes** (also in the Source Control view's title bar):
- `/review` compares your branch with `main` (or `master`, `develop`); `/review release/2.0` with another base;
- `/review --working` reviews what you have not committed yet.

The answer is a table of findings by severity (🔴 high, 🟠 medium, 🟡 low) with file:line and the suggested fix, then a verdict (✅ ready, ⚠️ after fixes, ❌ needs rework). Nothing is edited. A very large diff is not pasted: the assistant reads the changed files instead.

### 4.2b2 Security scan (/scan)

`/scan` (the whole project), `/scan changed` (uncommitted changes) or `/scan <folder or file>`; also **Swarm Lab:
Security scan** in the command palette and the Explorer's and editor's menus. The 🛡 card shows the plan and its estimated
cost; **Start** runs it:

1. The cheapest models of Models → automatic choice, from different vendors (`swarmLab.security.scanModels`,
   `scanModelCount`, 2 by default), each read the code twice (`runsPerModel`) with severity criteria, a checklist of
   vulnerability types and checks before reporting, plus your rules from `.swarmlab/security-rules.md`.
2. Each model re-reads its own findings in a new conversation and may withdraw some (`selfCheck`).
3. The findings are merged (same file, lines 3 or fewer apart, same type).
4. A model from another vendor (`verifierModel`) confirms, rejects or is unsure about each one, withdrawn ones included,
   and cannot add any (`verify`, `maxVerify`).

On each finding: the file:line opens it; **🧪 Reproduce** (`reproduce`) has a model write a small test, opened beside the
chat; after you approve it, it runs in the chat's isolation environment (never **machine**), and *confirmed* means it ran,
exited 0 and printed the marker; **Dismiss…** asks why, and offers to add your reason as a project rule. Severity is the
model's estimate. Calls count in today's spend; `maxCostUsd` ($5) stops a scan. Small models (`smallModels`, or 40B or
fewer by name) also get call relationships (`callContext`). Files left out: `exclude`, generated or minified files, over
`maxFiles` (the files with the most places worth a look come first). **Copy report** gives Markdown; scans are kept in
`.swarmlab/security/`.

### 4.2c Attach files

Click **＋ Files** or type **`@`** in your message. A list appears: your open editors first, then the workspace. Type letters to filter in order (`@dat` finds `src/date.ts`), use the arrows and **Enter**, or click. Up to 8 files become 📎 chips and are sent with your message, read the way a person would: Word, PDF, PowerPoint, Excel, CSV (with column summaries), notebooks, ZIP contents, and pictures for models that can see (section 34).

**When a message stops early.** If the assistant reaches its step limit (**`swarmLab.chat.maxSteps`**, 20 by default), it is asked once more, without new tools, for its answer so far: what it did, what it found or changed, what is left. The answer starts with ⚠️ **Stopped at the step limit**, and a **Continue where you stopped** button picks the work up (the conversation keeps every step). If that extra call fails, or the message stops on an error, the token budget or **Stop**, you get a report instead of a bare error: **What it did** (each file read, change applied or rejected, command, test run) and **Its notes along the way**, with the reason it stopped. Nothing it did is lost. Turn the extra call off with `swarmLab.chat.answerAtLimit`.

**The steps of each answer.** At the top of every answer, a line sums up what it did: *▸ 6 steps · 3 model calls · read 4 files · 2 edits · tests ✓*. Click it to open the steps: the step map (one lane per agent) and the numbered list; click a step with a file to open it there. Click the line again to minimize. The steps are kept with the conversation, so older answers keep theirs; the **Steps** button in the top bar still follows the message being answered, live.

**What each answer costs.** Under every answer: its time (and the models' share of it), the number of model calls, tokens in and out, the cost and the model. **details** lists each call: which agent, which model, what step, tokens, time, cost (decision-model calls and runs started from the chat included). The **Today** chip in the top bar shows today's spend; click it for the **Costs** drawer: today, this month, this conversation, the last days, and the limits: **most per message ($)**, **most per day ($)** (chat, runs and benches together, in all workspaces), and **most tokens per message**. At a limit the message stops and shows what was done; send “continue” to go on. Costs use OpenRouter's price list automatically; for other providers, set your models' prices in **Setup → Costs** (unknown prices show “cost unknown”: tokens are still counted, nothing is guessed).

**Find a conversation.** **History** has a search box: **Keywords** (exact words, ranked), **By meaning** (finds a conversation from what it was about, even with other words; uses the embedding model of Setup → Code search, and remembers each passage so the next search is quick), or **Both**. Each result shows the best passages with the words highlighted; click one to open the conversation at that message.

**Code blocks stay whole.** A block ends only at a line with its closing fence, so code that itself contains three backticks (a Markdown example, a string with a code block) is shown, copied and saved in one piece. **Copy** on a message gives Markdown that stays valid anywhere: such blocks get a longer fence (````). **History → Export this chat as Markdown** (or **Swarm Lab: Export chat as Markdown**) writes the whole conversation to one `.md` file. Conversations are saved in full in `.swarmlab/chat/`.

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

**See each change in the diff editor.** When the assistant proposes an edit, the file opens **beside the chat** in VS Code's side-by-side diff (before | after), and the chat keeps the focus, so you read the change and click **Apply** without switching. Once applied, the diff shows the real file on the right, which you can keep editing. Choose when diffs open in **Context → Diffs**: when an edit is proposed (default), once applied, or never (`swarmLab.chat.diffView`).

**After each answer that changed files**, a **📝 Files changed** card lists them (✏️ edited, 🆕 created):
- **Review all changes**: every file of that answer in VS Code's multi-file diff view, one scrollable page;
- **Diff** next to a file: that file alone, before ↔ now;
- **↩️ Undo these changes**: puts the files back as they were before that answer (created files are deleted), after a confirmation. The assistant is told, so it does not assume the changes are still there.

To apply several proposed edits at once, use **Approve all** in the orange bar.

### 4.4 Options and recommendations

When there are several ways forward, the assistant shows a **question card** with 2 to 4 options, each with its trade-off, and one marked **recommended**. Click an option, or write your own answer. **Take the recommended** answers every waiting question with its recommended option. After most answers, **next-step chips** appear under the message (for example **Add a test for this**); one click sends it.

### 4.5 Code blocks

Every code block in an answer is **numbered** (**#4**), also when the answer came in several parts. On each block:
- **Copy**: to the clipboard.
- **Insert**: at the cursor of the active editor (**Ctrl+Z** undoes it).
- **Save to file…**: choose the place; a new file is created and opened; an existing file shows a diff first.

You can also just ask: *"save #4 as src/parse_date.py"*, or *"append #5 to tests/test_parse.py"*. The agent saves the block **by its number, without writing it again**, so long code is never cut.

### 4.6 Diagrams

Ask for a diagram, for example *"draw this module's flow as a Mermaid diagram"*. A ```` ```mermaid ```` block is **drawn**: flowcharts, sequence, class, state, Gantt and more. ```` ```svg ```` blocks are shown as images. Mermaid is bundled: it works offline.

Each diagram has:

| Button | What it does |
|---|---|
| **PNG** | Saves an image (white background, light theme, twice the screen resolution for sharp slides and documents) |
| **PDF** | Saves a one-page PDF of the diagram, page sized to the diagram |
| **SVG** | Saves the vector file (scales to any size; opens in browsers and design tools) |
| **Code / Diagram** · **Copy** · **Save code…** | Switch to the Mermaid source, copy it, or save it as a file |

You choose where to save (the `docs/` folder is suggested), then **Open** or **Show in folder**.

**When a diagram has a mistake.** The most common one, a label with brackets, parentheses or quotes that is not in quotes (`A[Load (cache)]`), is repaired for you: the diagram is drawn, its title says *labels auto-quoted*, and **Copy**, **Save** and the exports use the repaired code. Any other mistake shows ⚠️ with Mermaid's message, the code, and **Ask to fix it**, which puts a correction request in the message box. Mermaid's own "Syntax error" picture is never left in the panel.

**Reset view** and **Reload panel** (top bar of the Chat). **Reset view** redraws the conversation from what is saved: leftover pictures, stuck messages and half-drawn diagrams go away. **Reload panel** is the full reset: the whole panel, every tab, is loaded again (also the ⟳ button in the panel's title bar, or **Swarm Lab: Reload panel**). Nothing is lost with either: conversations, memory, runs and waiting approvals stay. If a script error ever breaks part of the panel, a red bar at the bottom says so and offers both.

### 4.7 Visual answers and colorful code

Answers are written to be easy to scan, and the chat displays them that way:
- **headings, numbered and bulleted lists, tables, links**;
- colored **callouts**: ✅ done or success, ⚠️ warning or risk, ❌ problem, 💡 tip, ℹ️ note;
- **code always in a block**, with its language, **syntax colors** that follow your dark or light theme, and a colored edge per language (blue TypeScript, yellow JavaScript, green Python, grey shell, orange Java…);
- diagrams when a picture is clearer than text.

Prefer plain text? **Context → Answer style → Plain text** (`swarmLab.answerStyle`). Code stays in colored blocks either way.

### 4.8 Copy, edit, history

- **Copy a whole message:** hover it, click **Copy** at the top right.
- **Edit an earlier message of yours:** hover it, click **Edit**, change the text, **Resend**. The chat goes back to just before that message (in the conversation and in what the model remembers) and sends the new text.
- **History:** **History** → **Open** a past conversation (the current one is saved first).

### 4.9 Talk to your agents

- **Talk to** menu: switch the whole chat to an agent.
- **`@name` in a message:** type `@`, pick the agent (agents are listed first), finish your message. That one message goes to the agent; the answer appears here and is kept in the agent's own conversation.
- The assistant also **consults your agents by itself** when their skill fits.

### 4.10 Memory

- The **conversation** is saved per agent and comes back after a restart.
- **Long-term notes** carry facts into every new chat. They are created when you add one in **Memory**, type `/remember <fact>`, or ask the assistant to remember something.

### 4.11 Slash commands

They work without the model:

| Command | What it does |
|---|---|
| `/single <task>`, `/tree <task>`, `/swarm <task>`, `/graph <task>` | Start a run; its answer comes back to the chat |
| `/ask <agent> <question>` | Ask an agent of the last run |
| `/remember <fact>` | Save a long-term note |
| `/review [base]` · `/review --working` | Review your branch against its base, or your uncommitted changes (4.2b) |
| `/remote <mode> [options] <task>` | Run on the Swarm Lab server; the answer and the created files come back here (see 4.12) |
| `/new` | New chat |
| `/help` | Short help |

### 4.12 Run things from the chat, get the answers in the chat

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

**Workflow** tab. Start from a **template**: choose one in **Start from a template**, then **Use this template**. Your project's test command is filled in for you (`npm test`, `yarn test`, `pytest`, `go test ./...`, `cargo test`, `mvn test`, `dotnet test`…, from the files at its root).

| Template | Steps |
|---|---|
| 🐞 Bug fix | plan → fix → test → review, back to fix until the tests pass and the review approves |
| 🧹 Safe refactor | plan → refactor → test → review; behavior must not change |
| 🧪 Write tests | find untested behaviors → write tests → run them, until they pass |
| 📚 Write docs | read the code → write Markdown docs (with a diagram) → check them against the code |
| ⬆️ Dependency upgrade | plan → upgrade and fix breakages → test |
| 🔍 Code review | review → a findings table by severity; no edits |

Check the steps, then **Save workflow**. **Load the example** gives the bug-fix workflow without filling the test command.

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

**The result of a run.** At the top of the Run tab, a **Result** card: how it ended, time, tokens, calls, cost, edits and commands; then sections you open or minimize: **Answer** (formatted), **Workflow** (each step in order: ✓ done or passed, ✕ failed, ◆ a decision with the route it took, ↻ stopped looping; open **output** under a step to read what it wrote), **Files it wrote** and **Files changed** (click to open), and **Steps** (every model call, tool, edit and command). Click the card's title to minimize it. The **Workflow** tab shows the same timeline under **Last run of a workflow**.

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

Inline code for an interpreter (`python -c`, `node -e`, `bash -c`…) always asks, and allow-list entries that would let any
code run (`python`, `bash`, `node`, `npx`, `env`, `sudo`…) are ignored: list the exact command instead (`python -m pytest`).
Where commands run (this machine, a temporary virtual environment or a Docker container): [section 51](#51-isolation-where-commands-run).

**Control files.** Agents never change Swarm Lab's own control files, whatever their **May edit** paths:
`.swarmlab/policy.json`, `mcp.json`, `graph.json`, `environment.json`, `project.json`, rules, prompts, workflows, hooks,
plans, `.claude/settings*.json` and `swarmlab.server.json`. You change them in the Agents, Prompts, Tools and Project
tabs (Setup → Isolation → *Agents may not change Swarm Lab's control files*, on by default).

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
| `.swarmlab/chat/changes/<turn>/…` | Each file as it was before a chat answer changed it (for Review all changes and Undo) |
| `.swarmlab/memory/board.md`, `agent-<name>.md` | Shared board and long-term notes |
| `.swarmlab/index/index.json` | Code search index |
| `.swarmlab/tasks/tasks.json` | The task list: each task, its thread and its status |
| `.swarmlab/learn/outcomes.jsonl` | One line per answer: models, helper actions, verified or not, tokens, cost (no text) |

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
| `swarmLab.chat.diffView` | `proposed` | Open the diff beside the chat when an edit is `proposed`, once `applied`, or `off` |
| `swarmLab.answerStyle` | `visual` | `visual` (headings, tables, ✅ ⚠️ 💡 callouts, diagrams) or `plain` |
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

**Decision model, maps and activity**

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.decisions.enabled` | `false` | Use a decision model (section 23) |
| `swarmLab.decisions.provider` | `openrouter` | `openrouter`, `typesafe`, `custom` (base URL), `chat-model` (the worker model) |
| `swarmLab.decisions.model` | `jev-latest` | Decision model id |
| `swarmLab.decisions.baseUrl` | empty | The part before `/v1/systemone`; empty = the provider's default |
| `swarmLab.decisions.minConfidence` | `0.5` | Below it, the answer is not used |
| `swarmLab.decisions.graph` / `runMode` / `cascade` / `ragGate` / `commandHint` | `true` | Where it is used (once enabled) |
| `swarmLab.activity.badges` / `activity.highlight` | `true` | Explorer badges; highlights on the lines agents read |
| `swarmLab.codeMap.agentTools` | `true` | The `code_symbols` and `call_graph` tools for agents |
| `swarmLab.memory.mode` | `session+topics` | Memory by conversation and topic (section 28); `session`; `off` (the older per-agent notes) |
| `swarmLab.memory.budgetTokens` / `memory.agentsWriteProject` | `1500` / `false` | Most memory per message; let agents write the project memory without you |
| `swarmLab.skills.suggest` / `skills.maxShown` | `true` / `6` | Offer long verified answers as skills; most skills listed to an agent (those that match) |
| `swarmLab.memory.suggest` | `ask` | After each answer: suggest what to remember and let you decide; `auto` (with Undo); `off` |
| `swarmLab.verify.enabled` / `verify.tests` / `verify.retry` | `true` | Check "done" independently; run the tests to check; one more try when it fails |
| `swarmLab.models.auto` | `off` | Automatic model choice: `off`, `cheapest`, `balanced`, `best` (section 26) |
| `swarmLab.models.pool` | `[]` | The models it picks from, with size classes (empty: worker small, lead large) |
| `swarmLab.models.difficultyBy` / `models.escalate` | `rules` / `true` | How it judges a task; a bigger model after a failure |
| `swarmLab.chat.model` | empty | The chat's model: empty (Setup), `auto:…`, or a model id |
| `swarmLab.prices` | `{}` | Model prices in USD per million tokens (OpenRouter's are automatic) |
| `swarmLab.chat.maxCostPerMessageUsd` | `0` | Chat: stop a message at this cost (0 = no limit) |
| `swarmLab.costs.dailyLimitUsd` | `0` | Stop chat, runs and benches at this cost per day (0 = no limit) |
| `swarmLab.chat.maxSteps` | `20` | Chat: steps per message before it must answer |
| `swarmLab.chat.answerAtLimit` | `true` | At the limit, ask once more for the answer so far (else a report) |
| `swarmLab.tests.tool` | `true` | The `run_tests` tool for agents (section 24) |
| `swarmLab.tests.command` | empty | Test command; empty = detected |

---

## 17. All commands

Command Palette (**Ctrl+Shift+P**):

| Command | What it does |
|---|---|
| **Swarm Lab: Open** | Open the panel |
| **Swarm Lab: Reload panel (full reset)** | Load the whole panel again (also ⟳ in its title bar); conversations, runs and approvals are kept |
| **Swarm Lab: Choose model provider** | Guided setup: provider, address, proxy, key, models |
| **Swarm Lab: Set API key** / **Clear API keys** | Keys in secret storage |
| **Swarm Lab: Test connection** | One small request to the model |
| **Swarm Lab: Pick OpenRouter models** / **Pick a VS Code language model** | Model pickers |
| **Swarm Lab: Edit prompts and permissions** | Create the starter files in `.swarmlab/` |
| **Swarm Lab: Build code index** | Build or update the code search index |
| **Swarm Lab: Explain / Fix / Write tests for / Suggest improvements / Ask about this code** | On the selection or the file (also in the editor's right-click menu) |
| **Swarm Lab: Review my branch or changes** | Branch review or uncommitted changes (also `/review`) |
| **Swarm Lab: Open memory** / **Clear memory** | The shared board and notes |
| **Swarm Lab: Show call map** / **Show the call map of this file** | The code map from the cursor or the file (also in the editor's right-click menu) |
| **Swarm Lab: Clear agent activity** | Empty the badges, highlights and the activity view |
| **Swarm Lab: Test decision model** | One sample decision: answers, confidence, time and cost |
| **Swarm Lab: Open Bench** | The Bench tab (section 25) |
| **Swarm Lab: Export chat as Markdown** | The whole conversation as one Markdown file |

---

## 18. Troubleshooting

| Problem | What to do |
|---|---|
| **"Swarm Lab: Open"** is missing | Check the extension is installed and VS Code is 1.95 or later; run **Developer: Reload Window** |
| The panel is empty or buttons do nothing | **Reload panel** (⟳ in the panel title bar, or **Swarm Lab: Reload panel**); if that does not help, **Developer: Reload Window**; then **Developer: Toggle Developer Tools → Console** and look for red errors |
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
| Server tab: "No server at …" | Click **Start local server**, or fix the address |
| Server: `401` / `403` | **Server → Set API key**; the key needs the role (`submit`, `read`, `approve`) |
| A `/remote` job stays waiting | It needs an approval: **Server → Waiting for you on the server** |
| A server job fails with "needs a workflow" | Graph mode needs `.swarmlab/graph.json` (Workflow tab → Save workflow), or `--workflow NAME` |
| Logs | **View → Output → Swarm Lab** (commands, Claude Code, Git, index, local server) |

---

## 19. Background jobs: the Server tab

For long or repeated work, send tasks to a **Swarm Lab server** instead of running them in the editor. Each job runs in its own sandbox; its changes go to a separate Git branch; every step is recorded; approvals wait for you. The server is **included in the extension**.

### 19.1 Start a local server

1. **Server** tab → **Start local server**.
2. The first click creates `swarmlab.server.json` in your folder, with this folder as the repository and your model from Setup. Check it, then click **Start local server** again.
3. The status shows **connected**. Logs are in **View → Output → Swarm Lab**.

To use a server set up by your team, type its address in **Server address**, click **Set API key**, then **Save**.

### 19.2 Send a job

In **New job**:
- **Organization:** single, tree, swarm or graph (and the workflow, or **Run as** an agent);
- **Repository**, or **No repository** for ideas, tickets, diagrams and documents;
- **Created files:** return each created file, or only the patch;
- **Edits** and **Commands:** automatic, ask me, or off;
- the **task**, then **Submit job**.

Follow it under **Jobs**: live events, the answer, the branch and diff summary; **Open** the patch or any created file in the editor; **Cancel** or **Run again**. Approvals appear under **Waiting for you on the server**.

### 19.3 From the chat

`/remote single|tree|swarm|graph [options] <task>` sends the task to the server; the chat stays free, and the answer and created files come back into the chat (section 4.12).

## 20. Privacy and data

- **Your code goes only to the model provider you choose** (Setup), and only what the agents read or what you attach. With a local model, nothing leaves your machine.
- **API keys** are stored in VS Code's secret storage, never in files.
- **Everything Swarm Lab keeps** (conversations, memory, prompts, workflows, the code index) is in the `.swarmlab/` folder of your project, as plain files you can read or delete (section 15).
- **No telemetry:** Swarm Lab does not collect or send usage data.
- MCP servers and the background server only run when you add or start them.
- **The decision model**, when you turn it on, receives the text it decides about (a step's output, your chat message, a command) and nothing else, at the provider you choose.


---

## 21. Step map and agent activity

**See every step.** In the **Run** tab, switch the map from **Agents** to **Steps**. In the **Chat**, click **Steps** in the top bar. Each agent gets a lane; each step is a mark, left to right, as it happens:

| Mark | Step |
|---|---|
| ○ circle | a model call (hover: tokens in and out) |
| ▪ small square | a tool (`read_file`, `search_text`, `call_graph`…) |
| ○ blue ring | code search |
| ■ green square / □ red outline | an edit applied / rejected or not applied |
| `$` box | a command |
| ◆ diamond | a decision by the decision model (dashed: it was not used) |
| vertical line | a message between agents (orange through the lead, blue peer to peer) |

Hover a mark to read it; **click** one with a file (a read, a search hit, an edit) to open that file at that line. A dashed lane is an agent that was deleted (a tree's sub-agent).

**In VS Code itself**, during a run or a chat message:
- **Explorer badges** on the files the agents touched: **R** read, **E** edited, **P** a change proposed but not applied. Hover a badge for who did it and which lines.
- **Line highlights** in open editors on the lines an agent read (with marks in the scroll bar).
- The **Swarm Lab: agent activity** view in the Explorer: one entry per agent, then each step; click to open the file at the line. **Clear agent activity** (its toolbar button) empties it.

Each new run or chat message starts fresh. Turn badges and highlights off in **Setup → Maps and activity**.

---

## 22. Code map

**What calls what**, drawn from your editor's own language support: the same data as VS Code's **Call Hierarchy** (`Shift+Alt+H`). Whatever language extension you use (TypeScript, Python, Java, Go, C#…) provides it; nothing is parsed by Swarm Lab.

1. Put the cursor on a function, then right-click → **Swarm Lab → Show call map** (or **Show the call map of this file**). Or open the **Code map** tab and click **Build map**.
2. **Start from**: the symbol under the cursor, the current file (all its functions and what they call), or the current file's folder (up to 25 files of the same type).
3. **Show**: what it calls, what calls it, or both. **Levels** and **Most functions** keep large code readable; the result says when the limit was reached.

Each function is a box colored by its file; callers are on the left, callees on the right; dashed arrows go back (loops, recursion). **Click** a box for its callers and callees, with **Open**, **VS Code call hierarchy** and **Who calls it (VS Code)**; **double-click** to open the code. **Find** dims everything that does not match. **Open as Mermaid** gives the map as a Mermaid flowchart to save or paste into docs.

**Call order.** With **Show call order** on, each function's calls are laid out top to bottom in the order they are written, and each arrow ends at a number: the call's place in its caller (1 is the first call in the function). The number sits at the arrow's tip, next to the function called, and its border has the color of the caller, so a function called from several places shows whose call each number is. Symbols inside the number say what the code around the call means: **↻** in a loop (it may run many times), **?** in an if (it may not run), **!** in a try or an error handler, **…** later (a callback, a promise, a timer); hover a number for the full text and the line. **Click a function** to see only its calls: the rest of the map fades (click it again, or Esc, to see everything). **Library calls** (off by default): calls into the standard library and installed packages are counted on each function (**+N lib**, names on hover) instead of drawn, so the map, and its function limit, go to your code; turn it on to draw them as dashed leaves. **Walk the calls** lists them depth first (1, then what 1 calls: 1.1, 1.2…, then 2); **Previous** / **Next** highlight each call on the map, and clicking a step opens the exact line of the call. A function's details list its calls in order, each opening its call line. The symbols are read from indentation and keywords: a reading guide, not a record of a real run. The `call_graph` tool gives agents the same order and lines (library calls summarized).

**Show what the agents touched** outlines the functions whose lines the agents read (orange) and the files they edited (green): the code map and the step map together show which part of your code a run actually worked on.

The last map is also in the Explorer, in the **Swarm Lab: call map** view (expand a function to see what it calls).

**For the agents:** with **Agents can use the call hierarchy** on (default), agents get two read-only tools, `code_symbols` (a file's classes, functions and line numbers) and `call_graph` (what a function calls, or what calls it). They follow the code for a few hundred tokens instead of reading whole files. On the server there are no language servers, so these tools are not offered there.

> ⚠️ Dynamic calls (callbacks, `obj[name]()`, dependency injection) are often missing from any call hierarchy, so treat the map as a guide, not proof.

---

## 23. Decision models (Jev and others)

Some steps need a **decision**, not a written answer: which way a workflow goes, which kind of run fits, whether a message needs code. A **decision model** such as **Jev** (TypeSafe AI's "System One" model) reads the situation and returns a typed answer with its probability: a **choice** among options, a **score** on a scale, or a **yes/no**. It writes no text, so it is fast and costs a small fraction of a lead-model call.

**It is optional and off by default.** When it is on and it is unsure (below **Minimum confidence**) or fails, Swarm Lab does exactly what it does without it. It never approves an edit or a command.

### 23.1 Set it up

1. **Setup → Decision model** → **Use a decision model**.
2. **Where**:
   - **OpenRouter**: uses your OpenRouter key (OpenRouter serves Jev through its System One API). Model `jev-latest` or `jev-1.13`.
   - **TypeSafe directly**: **Set decision model key** → TypeSafe key.
   - **Another System One server**: a LiteLLM proxy, a company gateway, or another host of the same API. **Base URL** is the part before `/v1/systemone`, for example `http://localhost:4000/typesafe`.
   - **No decision model**: the worker model answers the same typed questions as JSON. Useful to compare, or where only chat models are allowed.
3. **Save settings** → **Test decision model**: it asks about a sample support ticket and shows the three answers, their confidence, the time and the cost.

### 23.2 Where it is used

Each one has its own switch:

| Switch | What changes | Saves |
|---|---|---|
| **Workflow decision steps** | `decide` steps in your workflow are answered by the decision model | a model call per decision |
| **Pick the run mode** | the assistant can start a run with mode `auto`; the decision model picks single, tree, swarm or graph | a wrong-sized run |
| **Simple messages on the worker model** | a greeting or a short question is answered by the worker model, for that message only | lead-model tokens |
| **Skip code search when not needed** | no automatic code context for messages like "thanks!" | input tokens on every such message |
| **Hint on command approvals** | the approval card says whether the command looks read-only | nothing; it informs you |

The two chat checks share **one** decision call per message. Every decision appears in the step map (◆), the activity view and the log, with its answer, confidence, whether it was used, and its cost. The **Runs compared** table counts decisions, fallbacks and cheap turns.

### 23.3 Decision steps in a workflow

In the **Workflow** tab, **Add a decision step**. It has a question, what it reads (default `{last}`, the previous step's output), and its answers:

- **Choice**: options as `name: what it means`; each option routes to a step.
- **Yes or no**: routes `yes` and `no`; **Yes when at least** sets the threshold (default 0.5).
- **Score**: levels described in words, lowest first (2 to 10); each level number routes to a step (the score is rounded).
- **else** catches the case where there is no good answer.

```json
"triage": {
  "decide": { "type": "choice", "instructions": "Did the tests reveal a real bug?",
              "criteria": { "fix": "A real failure to fix", "done": "All passing or only flaky" } },
  "state": "{last}",
  "routes": { "fix": "fixer", "done": "done", "else": "done" }
}
```

A decision step works even with the decision model off: the worker model answers it. With the decision model on, it costs no lead- or worker-model call.

> 💡 Write criteria that describe each option in words; avoid bare numbers as score levels. Confidence says how concentrated the answer is, not that it is right.

---

---

## 24. Tests: run_tests

Agents get a **run_tests** tool (setting **Tests → Agents use run_tests**, on by default). It runs your test command, all tests, some files or folders, or only the tests whose name matches. Instead of the whole output, the agent gets a short report:

```text
FAILED: 1 failed, 2 passed of 3 (pytest, exit 1) — $ pytest -q tests/test_avg.py
1. tests/test_avg.py::test_empty
   tests/test_avg.py:9 — ZeroDivisionError: division by zero
```

It reads **pytest, Jest, Vitest, Mocha, node --test, go test, cargo test and dotnet test**; for any other runner it keeps the exit code and the last 40 lines. The test command is detected from your project, or set in **Setup → Tests → Test command**. Paths and test names are checked character by character, so nothing can be chained or redirected. It goes through the same approval as any command: add the test command to the allow-list to run it without asking.

In the step map, each test run is a circle with ✓ or ✕.

---

## 25. Bench: compare setups on your own tasks

Give the same tasks to several **setups** and compare them: one agent or your workflow, a strong or a cheap model, the decision model on or off.

1. **Bench** tab → **New starter suite** (creates `.swarmlab/bench/starter.json`), or save real tasks with **Save as bench case** (the Run tab, or the button on your messages in the chat; they go to `.swarmlab/bench/my-tasks.json`, starting from the current commit).
2. Edit the suite: its tasks, their **checks**, and the setups.
3. **Run bench**. The grid fills in as runs finish: ✓ passed, ✕ failed (with the share of checks that passed). Click a cell for its checks, tokens, time, the files it changed, its answer, and how its own test runs went.
4. **By setup**: passed, pass rate, tokens and time per run, cost, how many runs **repaired** a failure (tests failing first, passing at the end), and commands refused. **Set this result as the baseline**, and every later run shows its difference: pass rate in points, tokens and time in percent (green is better).

**Each run is isolated.** It works in a fresh Git worktree of the suite's base commit (default: your last commit, so commit what you want tested), unattended: edits are applied there; commands run only from the suite's allow-list and the test command, anything else is refused (nothing waits for you). Your folder and branches are never changed; worktrees are removed after each run.

```json
{
  "name": "parser",
  "repeats": 2,
  "commands": "allowlist",
  "allowList": ["npm run lint"],
  "testCommand": "npm test",
  "setups": [
    { "name": "single", "mode": "single" },
    { "name": "cheap", "mode": "single", "leadModel": "claude-haiku-5-5" },
    { "name": "workflow + decisions", "mode": "graph", "decisions": true }
  ],
  "tasks": [
    { "id": "empty-input", "task": "parseDate('') throws. Make it return null, with a test.",
      "checks": [
        { "type": "tests" },
        { "type": "files", "changed": ["src/**"], "unchanged": ["package.json"] },
        { "type": "judge", "instructions": "Is the fix correct and minimal?", "levels": ["No", "Partly", "Yes", "Yes, cleanly"], "pass": 2 }
      ] }
  ]
}
```

**Checks**: `tests` (the test command passes), `command` (any command, with `expectExit`), `files` (`changed` / `unchanged` globs), `answer` (`contains`, `notContains`, `matches`), and `judge`: a rubric scored by the decision model (or the worker model when none is set), levels described in words, lowest first, and `pass`, the lowest level that passes. A run passes when all its checks pass. Task options: `base` (a commit), `setup` (a command before the run, for example `npm ci`). Suite options: `repeats` (models vary: 2 or 3 gives a fairer picture), `parallel` (runs at the same time), `timeoutSec` per run.

Results are kept in `.swarmlab/bench/results/`, the baseline in `.swarmlab/bench/baselines/`. **Earlier results** lists them, with **Show** and **Set as baseline**.

**In CI**, the same suite runs from the command line (SERVER.md, section 10): `swarm-lab bench .swarmlab/bench/parser.json --max-drop 5` exits with 1 when a setup's pass rate drops more than 5 points below the baseline.

> 💡 Setups with `"decisions": true` use the decision model (Setup → Decision model) even when it is off for everyday work, so you can measure what it saves before you turn it on.

---

## 26. Automatic model choice

For each task, Swarm Lab can pick **the cheapest model from your list that is good enough**, instead of always the lead model.

1. **Setup → Automatic model choice → Strategy**:
   - **Cheapest**: small models unless the task is hard (then medium).
   - **Balanced**: small for simple tasks, medium for ordinary ones, large for hard ones.
   - **Best**: large models unless the task is simple (then medium).
2. **The model list**: each model with a size class (small, medium, large). **Add the lead and worker**, add others, and **Size classes by price** sorts them for you (cheapest third small, the middle medium, the rest large). Prices come from OpenRouter's list, or the ones you type; uncheck **Tools** for a model that cannot call tools; give its **Context** when you know it. With an empty list, the worker model is small and the lead model is large.
3. **How hard a task is**: **by rules** (free: words like refactor, debug, design; the length; the amount of code; leads always plan on hard), or **by the decision model** (Setup → Decision model).

Then the choice is narrowed: agents that use tools only get models that can; a conversation longer than a model's context skips it; when the next call would pass the **cost limit**, a smaller model that fits is used (the biggest class that fits). **Move to a bigger model after a failure** (on by default): a failed call is retried on the next class, and after a message that stopped early (step limit, error) the next message starts one class up; "continue" keeps the same model.

**Where it applies.** The **chat**: its **Model** picker (top bar) says *Default (Setup)*, *Auto · cheapest / balanced / best*, or one model for this chat. **Runs**: the Setup strategy. **Benches**: setups with `"leadModel": "auto:cheapest"` (or `balanced`, `best`), next to fixed setups, to measure what it saves on your own tasks. **The server**: a `models` section in `swarmlab.server.json` (SERVER.md 4.12). A model you set for an agent (`policy.json`) or a workflow step is never changed; Claude Code agents keep theirs.

**What it did.** Each choice appears in the step map (◆ auto model), the chat activity and the activity view; under the answer: *auto: small for a simple task · saved ~$0.019 vs your lead model* (when the prices are known), and **details** gives the reason of each choice.

---

## 27. Project management workflows

The **Workflow** tab → **Project management** runs ready-made workflows that read your project and write plans, tickets and reports into `.swarmlab/out/`. They run as they are, without replacing your own workflow (**Load into the editor** copies one into the editor to change it).

| Workflow | What it writes |
|---|---|
| 📋 **Jira tickets from a task** | `tickets/tickets.md` (epics, stories with Given/When/Then acceptance criteria, estimates, dependencies, risks) and `tickets/tickets.csv` for Jira's CSV import (Issue Id / Parent Id keep the hierarchy). A review step sends them back until they are right. With a Jira MCP server connected (Tools tab), a last step creates the issues in Jira, each call approved by you; otherwise it says how to import the CSV. |
| 🗓️ **Sprint plan** | `sprint-plan.md`: sprints within your capacity, in dependency order, with goals, a Mermaid gantt timeline, the critical path, risks and what to cut first. Reads the tickets if they exist. |
| 📈 **Project optimization review** | `optimization-review.md`: improvements found in the project (tests, CI, dependencies, TODOs, large files, docs, build) with evidence, scored by impact, confidence and effort (ICE), quick wins first; and `tickets/optimization-tickets.csv` for the top 10. |
| 🚀 **Release notes** | `release-notes.md` from the commit history: new, fixed, breaking changes, upgrade notes, in words for users. |
| 📊 **Status report** | `status-report.md` from the last three weeks of commits, TODOs and tests: done, in progress, blocked, numbers, next steps. |
| ⚠️ **Risk register** | `risk-register.md`: risks with likelihood, impact, score, mitigation, owner and early warning sign, and the top actions. |

Pick one, write what to work on (each one suggests what to write), and **Run it**: the Run tab shows its progress and its result. Under **Files it wrote**, each file opens in a click, and a Jira CSV is checked: **ready for Jira import** with its totals (issues, epics, stories, sub-tasks, points), or the exact lines to fix (a wrong header, an unquoted comma, a Parent Id that does not exist, a sub-task without a parent, an unknown issue type).

To import the CSV: Jira → **Settings → System → External system import → CSV**, and map **Issue Id** and **Parent Id** so epics, stories and sub-tasks keep their hierarchy.

---

## 28. Memory by conversation and topic, and checked "done"

### 28.1 Memory

Agents no longer share one memory for everything. Memory has three scopes, stored as readable Markdown in `.swarmlab/memory/` (open, edit and commit it like any file):

| Scope | Used by | Written by |
|---|---|---|
| **This conversation** (`sessions/`) | this conversation only | the agents (by default), you |
| **Topic** (`topics/auth.md`…) | every conversation about that topic | agents that name the topic, you, or a promotion |
| **Project** (`project.md`) | every conversation | you; agents only **propose** (you approve), unless Setup allows them |

**Topics.** A conversation's topics are found in your messages (a topic named in the message, or one whose memory shares several words with it) and shown on the **Memory** button of the chat. Open it to remove a topic that does not fit, or add one; your choice sticks for the conversation.

**What goes into a message**, in this order and within a budget (**Most memory per message**, 1,500 tokens): the conversation's **progress note** (what the last message did, what changed, whether it stopped early: "continue" starts from it), the conversation's own items, then only the topic and project items **relevant to the message**. Items marked wrong, archived or not yet approved are never used. Memory goes in as data, not instructions, and is removed from the history at the next message, so it does not pile up. Each answer's steps (▸ at its top) list **Memory used**, with a **wrong** button for each item.

**After each answer: "Remember this?"** (Setup → Memory and checks → **After each answer**). The worker model reads the exchange and suggests at most 3 things worth keeping (a decision, a preference, a fact that was hard to find) and new topics; what the assistant asked to remember during the answer waits on the same card. Each line can be edited, ticked or not, and sent where you choose (this conversation, a topic, the project); then **Keep selected** or **Skip**. **Nothing is saved or used before you keep it.** Short exchanges ("thanks") cost no call; what is already remembered is not suggested again. *Remember the suggestions* saves them at once, with **Undo** on the card; *Nothing* lets agents remember on their own, as before.

**The Memory panel** (chat → Memory) lists the items of this conversation, its topics and the project, with where each came from, how far to trust it, and how often it was used: **Edit**, **Wrong** (never used again, kept in the file), **→ topic** / **→ project** (share it; it becomes yours), **Approve** (a project item an agent proposed), **Delete**; and a box to add your own.

**Trust.** Every item records its source. What an agent saves right after reading a web page or a connected (MCP) server is marked **from an outside source**, shown as such in the prompt, and never goes to the project memory without you: memory that can be taught can be poisoned.

Setup → **Memory and checks** → **Memory**: *this conversation + its topics + project* (default), *this conversation + project*, or *off* (the per-agent notes of earlier versions; the chat then shows a **Notes** button instead).

### 28.2 "Done" is checked by Swarm Lab, not by the agent

An agent saying it is done is a claim. When an answer or a run **changed files**, Swarm Lab checks it independently:

- **complete edits**: no placeholders left instead of code ("// … rest of the code unchanged") and no merge-conflict markers in the changed files;
- **tests**: if the agent ran the tests after its last change and they passed, that counts (the test program decided); otherwise the check runs them (it asks you unless the test command is on the allow-list).

The answer shows **✓ verified** (tests passed after the last change), **✕ check failed**, or **◌ not verified** (no test could be run: it never says verified without evidence); hover it for each check. When the check fails, the agent gets **one more turn** with what failed. Runs show the same on their result card. Answers that changed nothing have nothing to check and show no badge.

### 28.3 Actions that cannot be undone

An allow-list says a command is usual, not that it can be undone. These always ask, even when allow-listed, with **⚠ cannot be undone** and why, and a warning when they seem to target production: deleting files recursively, force push, `git reset --hard`, `git clean`, discarding work, `DROP` / `TRUNCATE`, `DELETE` or `UPDATE` without `WHERE`, deleting databases, `kubectl delete`, `terraform apply/destroy`, cloud deletes (AWS, Google Cloud, Azure), removing container volumes, publishing packages, deploys, HTTP `DELETE`/`PUT`/`PATCH`, erasing disks, shutting down. Connected tools whose name says they delete, drop, deploy, publish, send, pay, refund or transfer ask too, even when their server is set to "allow". On the server, they always wait for an approval; an unattended bench refuses them.

---

## 29. Skills that earn their place, tidy memory, and what fills the context

### 29.1 Skills: trial, trusted, retired

Every skill in `.swarmlab/skills/` has a status and a track record (`record.json` next to its `SKILL.md`):

- **trial**: drafted by an agent or from an answer's steps. Agents see it marked *(trial skill: check its result)*.
- **trusted**: written by you, approved by you (**Trust**), or shown by the bench to help.
- **retired**: never shown to agents again (kept on disk; **Restore** brings it back as a trial).

Skills from elsewhere (`.claude/skills`) count as yours. **Only the skills that match the task** are listed to an agent (at most **Most skills shown to an agent**, 6), trusted first, and a good record helps; retired skills never. Each use is recorded with how that answer turned out under the independent check (✓ verified, ✕ failed, ◌ not verified), shown in **Tools → Skills**.

**From what really happened.** Open an answer's steps (▸ at its top) → **Save these steps as a skill**: the worker model drafts a skill from the actual steps (only what the record shows), and a card lets you edit its name, when to use it and its instructions, then **Save as a trial skill** or **Dismiss**. After a **verified** answer that took 6 steps or more (and used no skill), the same card is offered on its own (Setup → Memory and checks → *Offer to save long verified answers as skills*).

**Test with the bench** (Tools → Skills) runs your saved tasks (at least 3, from **Save as bench case**) twice: with the skill and without it. It becomes **trusted only on a clear margin** (at least 2 more tasks passed, and at least 20% of the runs); if it makes things worse, retiring it is suggested; otherwise it stays a trial. In a bench suite, `"skills": "all"`, `"none"` or a list of names sets which skills a setup may use.

### 29.2 Tidy the memory

**Memory → Tidy up…** proposes, for this conversation, its topics and the project:

- **Merge** items that say the same thing (the one you wrote, or the most used, stays);
- **May contradict**: two items that say almost the same thing with different values (30 s / 60 s) or one negated: choose which to keep;
- **Archive** items never used in 30 days (yours are never proposed);
- **Share with the topic** a conversation item used in 3 messages or more.

Nothing changes until you tick what you want and **Apply selected**; a full copy of `.swarmlab/memory` is saved first in `.swarmlab/memory/.backup/`.

**Session state.** The progress note of a conversation keeps its **goal** (your first message) and **every file changed so far**, then what the last message did: "continue" starts from there.

### 29.3 What fills the context

The **Context** drawer of the chat shows what the last message sent, part by part: instructions, tools, history, your message, attached files, code found and memory, in tokens and as a bar; each answer's steps list it too. When one part dominates, you know what to trim (attach less, lower the memory budget, start a new chat).

### 29.4 Checking the checker

When a bench task is graded by both the **tests** and a **judge**, the result says how often they agreed; below 80%, the judge alone should not be trusted: review its rubric. A checker that nobody checks is only an assumption.

---

## 30. Your own workflow templates

Put templates in **`.swarmlab/templates/*.json`** (commit them to share with your team). They appear in the Workflow tab's **Start from a template** list (marked *yours*) and, for `"category": "management"`, in **Project management**, where they run as they are:

```json
{
  "title": "🔎 Triage a bug",
  "description": "reproduce → find the cause → write a failing test → plan the fix",
  "category": "management",
  "hint": "The bug report, for example: Login fails after a password reset.",
  "outputs": [".swarmlab/out/triage.md"],
  "graph": {
    "start": "reproduce", "maxSteps": 10,
    "nodes": {
      "reproduce": { "agent": "investigator", "model": "lead", "task": "Bug: {task}\nReproduce it and find the cause. Do not edit.", "next": "test" },
      "test": { "agent": "tester", "task": "Cause:\n{node:reproduce}\n\nWrite a failing test for it.", "next": "plan" },
      "plan": { "agent": "writer", "task": "Write .swarmlab/out/triage.md: the cause, the failing test, the fix plan.", "next": "done" }
    }
  }
}
```

`title`, `description` and `graph` are required; `category` is `code` (the default: loads into the editor) or `management`; `outputs` lists files under `.swarmlab/out/` (opened and checked after the run). The graph follows the same rules as the Workflow editor. A file that cannot be used is listed under the template picker with the reason, and left out.

**A template that makes templates.** *Project management → 🧩 New workflow template*: describe a process; a planner designs the steps, a writer writes `.swarmlab/out/new-template.json` and checks it with **`check_workflow`** (a tool that validates a workflow or template file with the editor's rules) until it is valid, and a reviewer approves it or sends it back. On the result card the file shows **valid template** and **Add to my templates**, which copies it into `.swarmlab/templates/` under a name from its title.

---

## 31. Experiments on the server

An **experiment** is a bench suite (section 25) run by the server at scale: every task × setup × repeat in its own Git worktree, many at once, graded like the bench, and bounded: **at once** (concurrency), **most $** and **most tokens** stop it cleanly. Hundreds of agents in total come from many runs in parallel (each run has its own few agents), not from one giant swarm.

- **Dashboard** (the server's page) → **Experiments** → *New experiment*: paste the suite, pick the repository, set the limits, **Start**. The list shows progress and cost live; click one for the summary per setup; **Stop** ends it.
- **Command line**: `swarm-lab experiment suite.json --repo app --concurrency 16 --max-cost 20` submits it to a running server, follows it, and prints the summary (SERVER.md, section 10).

Setups can compare modes (single, tree, swarm, workflows), models (including `"leadModel": "auto:cheapest"`), the decision model (`"decisions": true`) and skills (`"skills"`); the summary gives the pass rate, tokens, cost and time of each, and how often the judge agreed with the tests.

---

## 32. Scripted jobs on the server: your agents, prompts, memory, and reports

From a script you can configure a job completely, run it in any mode, and read everything it did.

**Configure the job itself** (no commit needed): `policy` (agents: models, tools, edit paths, engines; merged over the repository's `.swarmlab/policy.json`), `prompts` (`roles` by role, `agents` by name; over `prompts/`), `memory` (`{ "session": "name", "topics": [...] }`: jobs with the same session share memory; `false` for none), plus `mode` (`single`, `tree`, `swarm`, `graph` with an inline `workflow`), `settings`, `labels`.

**Memory on the server.** With `memory` in the job (or `"memory": { "mode": "scoped" }` in the server configuration), a job starts from its session's memory: the progress note of the session's last job, its items, and the relevant topic and project items, as data, within a budget. At its end it writes the session's progress note, so the next job of the session knows what happened. Each session is separate.

**Reports.** Every job writes `report.md` and `report.json`: every step (agent, model call with tokens, cost and time, tool, edit, command, test, decision, model choice, memory, check), totals by agent and by model, files changed, memory used and saved. `GET /v1/jobs/{id}/report` (Markdown, or `?format=json`). Across jobs: `GET /v1/reports?groupBy=day|mode|model|repo|key|status|label:<name>&from=YYYY-MM-DD&to=…&format=json|csv|md`, and the **Reports** section of the dashboard.

**The Python client** (`clients/python/swarmlab_client.py`): `submit(..., policy=, prompts=, memory=)`, `wait()`, `report(id, "md" | "json")`, `costs(group_by=, fmt=, label=)`, `submit_experiment()`, `wait_experiment()`.

**The full test script**: `clients/python/full_test.py` configures agents and prompts, runs a single job, then a swarm and a graph job that share its memory, saves every report, then the usage by mode, model and label (and, with `--experiment`, a small experiment). `bash clients/python/run_full_test.sh` runs it against a throwaway local server with the offline fake model (no key, no cost), to see everything work in a minute.

---

## 33. Your whole setup on the server: profiles, MCP, skills, checks, hooks

**Profiles.** Server tab → **Your setup on the server** → **Export to the server** saves this setup as a named profile on the server: agents and prompts, the workflow, models and limits, automatic model choice, tests and the check of "done", memory, your skills (not retired ones) and MCP servers. Never your keys. A job or script then says `"profile": "name"`; anything in the job itself wins (agents, prompts and settings merge key by key; skills by name; hooks and MCP servers add up). The job is merged when it is submitted and stored that way, so editing a profile later never changes jobs already queued. Writing a profile needs a key with the `approve` or `admin` role; it is checked with the same rules as a job.

**What a job (or profile) can carry**, besides agents, prompts, memory, mode, workflow and settings:

- `mcp`: `{ "use": ["github"] }` picks servers from the server's configuration; `{ "add": { "facts": { "url": "http://…" } } }` adds one by URL (its host must be in the server's `mcpAllowHosts`); a local program (`"command"`) needs an admin key, so a script can never start programs on your server. The job's servers are started for it and closed at its end.
- `skills`: `[{ "name", "description", "instructions", "status": "trial" | "trusted" }]`, next to the repository's skills (theirs win on the same name).
- `checks`: `{ "tests": true }` (detects the test command) or `"pytest -q"` gives agents `run_tests`; `"verify": true` adds the independent check of "done" at the end of the job.
- `models`: `{ "auto": "cheapest" | "balanced" | "best" | "off" }`: automatic model choice for this job.
- `hooks`: `[{ "url", "events", "tools", "secret", "timeoutMs", "onTimeout" }]`: your endpoint is called with JSON (signed with HMAC-SHA256 in `X-SwarmLab-Signature` when a secret is set).
  - **before** a command (`before:command`, including workflow command steps), an edit (`before:edit`) or any other tool (`before:tool`, optionally only the `tools` you list, like `mcp__*`): answer `{ "decision": "allow" }`, `{ "decision": "deny", "note": "why" }` or `{ "decision": "allow", "note": "for the agent" }`. A deny wins over everything, the allow-list included; the agent gets the reason (a denied workflow command step stops the workflow, as when you reject it). A hook that does not answer in time denies an action that cannot be undone; for the rest, `onTimeout` decides (default `allow`).
  - **after** a model call, an edit, a command, the check of "done" (`after:call`, `after:edit`, `after:command`, `after:verify`) and at the end (`job:end`: status, tokens, cost, files): for logs, alerts or counters. The job's report lists what the hooks allowed and blocked.

  Hook URLs must be on the server's `hooks.allowHosts` (default `127.0.0.1` and `localhost`) unless the key is admin.

**What stays in VS Code**: the code map and call hierarchy (they need VS Code's language support), the approval cards in the editor (the server uses its API and dashboard), and models that come through VS Code (Copilot).

**Step by step:** **SERVER-QUICKSTART.md** (in the source package) builds the server, runs the offline test in five minutes, then your own server with a real model.

**The test script** (`clients/python/full_test.py`) shows all of it: it starts a small MCP server and a hook receiver inside the script, saves a profile with agents, prompts, a skill, checks, the hooks and the MCP server, runs a single, a swarm and a graph job from it (sharing memory), and prints the reports, what the hooks saw and blocked, and what the MCP server served. `bash clients/python/run_full_test.sh` runs it against a throwaway local server.



## 34. Data: give agents files and folders

Any run (single, tree, swarm, graph), the chat and server jobs can use **data**: files or folders the agents read to solve a task, and a folder where they save results. You give the data; **each agent decides when it helps**.

**Where you give it** (inputs add up; for the output folder, the most specific wins):

| Where | What | Saved in |
|---|---|---|
| **Run** tab → **Data** | For every agent of every run and for the chat: inputs (**Add folder…**, **Add files…**, or type paths) and the **Output folder** | `swarmLab.data.inputs`, `swarmLab.data.output` (workspace settings) |
| **Agents** tab → an agent → **Data inputs** / **Save results in** | Only for that agent, in every mode | `.swarmlab/policy.json`: `"data": { "inputs": [...], "output": "..." }` |
| **Workflow** tab → a step → **Data for this step** | Only for that step (agent or command step) | `.swarmlab/graph.json`: the step's `"data"` |
| A lead (tree, swarm) | Hands some of its data paths to the agent it creates (`data` in `delegate` / `create_agent`), never anything else | — |

Paths can be absolute, relative to the workspace, or `~/…`. The Run tab shows what each input holds (*folder: 12 files, 3.4 MB: table ×5, pdf ×2*) and warns about paths that do not exist.

**Data files attached in the chat (0.43.15).** A CSV, TSV, Excel, JSON or Parquet file attached to a message reaches the
model as a summary: its size, one line per column (type, missing values, range or most common values) and the first 50
rows. So that no analysis comes from that sample, the message then carries a rule. With *Allow commands* on, the agent
writes a script that reads the whole files (Python with pandas, or the csv module), runs it, answers from its output,
fixes and reruns it when it fails, says which script produced each result, and saves new tables or charts to new files.
With commands off, its answer starts by saying it rests on the summaries and the first rows only. The chat shows which
applies (*data files attached: …*). Each command still needs your approval unless it is on your allow-list or *Work on
its own* is *Everything*.

**How agents use it.** Their instructions list their data with absolute paths, and they get three tools:

| Tool | What it does |
|---|---|
| `list_data` | The agent's data and output folder; or the files of a data folder (kinds and sizes; `glob` to filter) |
| `read_data` | Reads a file the way a person would (see the table below); `from` and `count` read a part (rows, pages, slides, cells or lines), `sheet` an Excel sheet, `entry` a file inside a ZIP |
| `write_output` | Saves a result (table, report, JSON, SVG) in the agent's output folder |

To compute on data (statistics, joins, plots), agents write a script and run it with `run_command`, using the absolute paths: the prompt tells them so. In a **command step** of a workflow, `{data}` becomes the step's data paths (quoted) and `{output}` its output folder, for example `python analyze.py {data} --out {output}`; in an agent step's task, `{data}` and `{output}` are filled in the same way.

**What can be read** (by `read_data`, and by files attached in the chat with **＋ Files** or `@`):

| Kind | What the agent gets |
|---|---|
| CSV, TSV | Rows × columns, a summary of every column (numbers: min, mean, max; text: distinct values, most common), then rows as a table |
| Excel (.xlsx, .xlsm), OpenDocument | Every sheet with its summary and rows; `sheet` for one; pictures placed on the sheets |
| Word (.docx), .odt | The text with headings, lists and tables, and the pictures in it (for models that can see) |
| PDF | The text page by page (pages in order, fonts with Unicode maps, LaTeX ligatures), and the pictures on the pages read; a scanned PDF's pages go as pictures |
| PowerPoint (.pptx) | Slide by slide: title, bullets, speaker notes, and each slide's pictures |
| Jupyter notebooks | Cells with their language, outputs and errors; picture outputs are shown to the model |
| JSON, JSONL, text and code | The content (JSON with its structure) |
| ZIP, .gz, .tar | The list of files; `entry` reads one with the right reader (a Word file in a ZIP is read as Word) |
| Pictures (PNG, JPEG, GIF, WebP) | The picture itself, for models that can see |
| Legacy .doc, .xls, .ppt; Parquet, SQLite… | A clear message (save as .docx…, or read it with a script) |

**Pictures.** Pictures go to the models that can see them, automatically (see [62](#62-pictures-inside-attached-files)); older pictures in a conversation become a one-line note so they do not cost tokens on every call. VS Code's models and models in text tool mode get a note instead. Turn pictures off with `swarmLab.data.images`.

**Safety.** An agent reads only inside the workspace, its own data, and its output folder (symbolic links cannot lead outside them). It writes only inside its output folder: new files are saved, **overwriting asks you** (`swarmLab.data.write`: `auto`, `ask` for every save, or `off`). Big files are capped (150 MB to read, 20 MB to save through the tool); ZIP and PDF unpacking is capped against zip bombs.

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.data.inputs` | `[]` | Files or folders for every agent (Run tab) |
| `swarmLab.data.output` | `.swarmlab/out/data` | Where agents save results |
| `swarmLab.data.write` | `auto` | `auto`: new files saved, overwriting asks · `ask`: every save asks · `off` |
| `swarmLab.data.images` | `true` | Send pictures to models that can see (automatic) |
| `swarmLab.data.visionModels` | `[]` | Models that see (`name`) or do not (`!name`), over what their names say |
| `swarmLab.data.maxImages` | `8` | Most pictures with one message (0–20) |
| `swarmLab.python` | empty | Python for the bundled scripts (`python3`, `py -3`, a venv's python) |

On the **server**, a job takes `"data": { "inputs": [...], "output": "..." }`; paths outside the job's workspace must be inside the server's `data.roots` (see SERVER.md, 4.18).

## 35. Calibrate an LLM judge

**Workflow → Start from a template → ⚖️ Calibrate an LLM judge** (also in **Project management**). For a judge that gives a binary label (hallucinated or not, toxic or not, pass or fail), it estimates the **true rate** on the items you care about, corrected for the judge's mistakes, with confidence intervals.

**What you need:** a **calibration set** (items labelled by humans *and* by the judge) and a **target set** (the judge's labels on the items to estimate). Give them as **Data** in the Run tab, or name the files in the task.

**The steps:** *plan* (finds the files, columns and positive value) → *compute* (runs the bundled script) → *check* (a command step that checks the script's output is consistent; back to compute if not) → *review* (inputs, and the assumptions that may fail) → *report* (`.swarmlab/out/llmaaj/report.md`). **No agent computes a number:** every number comes from the script.

**What the script computes** (`media/scripts/llmaaj_calibrate.py`, standard-library Python; NumPy makes the bootstrap faster):

| | |
|---|---|
| Se, Sp, q | Sensitivity and specificity of the judge on the calibration set, the raw judged rate on the target, each with a **Wilson** interval |
| Corrected rate | **Rogan–Gladen**: p = (q + Sp − 1) / (Se + Sp − 1), clipped to [0, 1] |
| Delta | First-order delta-method interval (fast approximation) |
| Bootstrap | Percentile bootstrap, positives, negatives and target resampled separately (**the main interval**) |
| 8 corners | p at every combination of the Wilson bounds of q, Se and Sp, each at 1 − α/3 (Bonferroni): a cautious bound |
| Warnings | J = Se + Sp − 1 below 0.2 (unstable) or ≤ 0 (impossible), small classes, clipping, Se or Sp exactly 0 or 1, delta and bootstrap that disagree |

Run it yourself: `python3 media/scripts/llmaaj_calibrate.py --calibration cal.csv --target prod.csv --out results/`, or with counts: `--tp 45 --fn 5 --tn 40 --fp 10 --target-positives 120 --target-n 400`. Its tests (`test_llmaaj_calibrate.py`) include a simulation that checks the intervals cover the true rate as often as they should.


## 36. How many model calls at once

**Run** tab (next to **Run task**), **Setup → Limits**, or `swarmLab.maxParallelCalls`: **Model calls at once**. Agents that want to call the model while that many calls are running wait their turn (first come, first served). It is one limit for the whole window: the chat, every run, tree and swarm workers, parallel tool calls and Claude Code turns. `0` (or empty) means no limit. It changes live: raising it lets waiting calls go at once; lowering it lets running calls finish and holds new ones. The Run tab shows how many calls are running and waiting.

Use it for provider rate limits, or a local model that serves one request at a time. **Workers per run** (`swarmLab.maxAgents`) still caps how many agents a lead may create.

**On the server:** the **Server** tab has **Jobs at once** and **Model calls at once** (with − and +), changed live on the connected server; tick **Save** to also write them into its configuration file. This needs an admin key, and calls `PUT /v1/workers` (SERVER.md).

## 37. Edit an answer, a code block or a diagram

Every answer has **Edit** (top right, on hover), and every code block and diagram has its own **Edit** button.

| What | How |
|---|---|
| The whole answer | A Markdown editor with a live preview (text, code blocks, diagrams) |
| One code block | That block only, in place; the rest of the answer is kept exactly as it was |
| A diagram (Mermaid, SVG) | Its code, with the diagram redrawn as you type |

Then:

- **Save**: your version replaces the model's. The model reads **your version** from now on (it is written into the conversation the model sees, and numbered blocks such as `#2` follow, so `save_block` saves your code). The answer shows *✎ edited*.
- **Save & ask…**: the same, then a message goes to the model with **your changes as a diff** and what you want, for example *"explain why my fix works"* or *"continue from my version"*, so it reasons from your version.

When the conversation was summarized, or with the Claude Code engine (which keeps its own history), your version is sent with your next message instead.

**Proposed file changes.** In the **Waiting for you** bar, **Edit before applying** opens the proposed file in an editor beside the current one: change it, then **Apply**. Your version is applied, and the agent is told exactly what you changed (as a diff) and to build on it. **Commands** can be changed in the approval card before **Run**; the agent is told what you ran instead.

## 38. Edit a picture before you send it

**✎** on an attached picture (in the message box), on a picture in a message, or **✎ Edit** under a picture in an answer, opens the picture editor: **Pen**, **Highlight**, **Arrow**, **Box**, **Text**, **Crop**, a colour and a thickness, **Undo / Redo** (Ctrl+Z / Ctrl+Y) and **Reset**. **Attach edited picture** saves a copy (`.swarmlab/uploads/…-edited-….png`; the original is not changed) and attaches it to your next message, in place of the original when you edited an attachment. Models that can see read the edited picture.

## 39. Web research (on or off)

**🌐 Web** in the chat bar turns it on or off (`swarmLab.web.enabled`; off by default). When on, every agent that reads files, in every mode and in the chat, gets:

| Tool | What it does |
|---|---|
| `web_search` | Titles, addresses and snippets for a query |
| `fetch_url` | A page as readable text (headings, lists, tables, its links at the end; menus and scripts dropped), or a PDF, Word or sheet at an address, read with the document readers; long pages continue with `from` |

Agents are told to read pages before relying on them, and to cite them.

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.web.search` | `duckduckgo` | `duckduckgo` (no key), `brave` or `tavily` (key: **Swarm Lab: Set web search key**), `searxng` (your own) |
| `swarmLab.web.searxngUrl` | empty | Your SearXNG address |
| `swarmLab.web.allowPrivate` | `false` | Allow private and local addresses (an intranet wiki) |
| `swarmLab.web.blockHosts` | `[]` | Hosts never read |

**Safety.** Only `http` and `https`, and only public addresses: private, loopback and link-local addresses (your network, `localhost`, the cloud metadata service) are refused, and every redirect is checked again. Pages are capped at 8 MB. Everything read from the web is marked for the model as written by others, never to be obeyed, and the agent is treated as having read outside content (as with MCP tools). Allow a tool per agent as usual (`tools` in `.swarmlab/policy.json`).

---

**Third-party software:** Mermaid (MIT license) for diagrams and highlight.js (BSD-3-Clause license) for code colors are bundled; undici (MIT) is used for network proxies.

**License:** MIT.

---

## 40. Helpers for smaller models

Smaller and open models (Mistral, Gemma, Llama, Qwen, Phi…) are cheap and fast, but they make typical mistakes in an
agent loop: broken tool calls, edits that do not match the file, the same call again and again. **Setup → Helpers for
smaller models** fixes these automatically. It is **off by default**, and each helper has its own switch.

**Use helpers**: **Off**; **Recommended** (only models whose id contains a line of **Models that get helpers**, for
example `mistral`, `gemma`, `devstral`; `*` stands for anything); or **For every model**.

| Helper | What it does | Default |
|---|---|---|
| **Repair tool calls** | Fixes broken JSON and near-miss tool names instead of failing the call | on |
| **Simple working rules** | Six short, numbered rules in the instructions: small steps, exact edits, no repeats | on |
| **Shorter tool descriptions** | Tool descriptions cut to their first sentences | off |
| **Stop repeated calls** | The same call with the same input is not run a third time (until a file changes) | on |
| **Forgiving edits** | An edit that differs only in spaces or indentation finds its one place; new text re-indented | on |
| **Bigger model after N failed tool calls** | In one message; Automatic model choice, or the lead model. 0 = never | 3 |
| **Quick check after edits** | A fast lint or type check after each round of edits; errors go back at once | empty (off) |

Approvals do not change: every edit and command still asks you as usual. Put the quick check command on the
allow-list (Setup → Commands) so it does not ask each time. Each helper action appears in the log as a note
(*helpers: tool name "readFile" → read_file*), and a move to a bigger model as ◆ in the step map.

**Measure it.** In a bench suite, give two setups the same model, one with `"helpers": "recommended"` and one with
`"helpers": "off"`, and compare pass rate, tokens and time (section 25).

---

## 41. Metadata: what each answer did, and what your files say

**Under each answer.** The line under an answer shows time, calls, tokens, cost and models, and now what the helpers
for smaller models did: *helpers: 2 repaired, 1 repeat stopped, 1 edit matched, 1 quick check*. **details** lists
each action. The Bench grid shows the number of helper actions per run.

**File details.** Swarm Lab reads the details a file keeps about itself: title, author, created and modified dates,
pages, slides, sheets, words, picture size (PDF, Word, PowerPoint, Excel, OpenDocument, pictures, Markdown front
matter). Click **ⓘ** on an attached file to see them all, the citation line (*Jane Doe (2025). Pump maintenance
manual. [PDF, 2 pages]. manual.pdf*), and which details go to the model.

**What the model gets** (Setup → Quality and learning → **File details to the model**):

| Choice | Sent with attached files and the first `read_data` of a file |
|---|---|
| **What a citation needs** (default) | type, title, author, subject, dates, pages, slides, sheets, words, language |
| **All details** | also who last changed it, the company, the program that made it, keywords |
| **None** | nothing (you still see the details with ⓘ) |

**Record answer outcomes** (on by default): one line per answer in `.swarmlab/learn/outcomes.jsonl`, with the models,
helper actions, verified or not, tokens, cost and time. It contains no message text and no file content. Use it to
compare models and helpers on your own work; turn it off in Setup → Quality and learning.

---

## 42. Long ASD-STE100 reports

Attach the files the report is based on (＋ Files or @), then send:

```
/stereport pump P-101 maintenance
/stereport 8 pump P-101 maintenance      (8 sections instead of the default 6)
```

**How it is written.** In steps, so that each model call has one clear job (this also suits smaller models):

1. **Notes** from each file, part by part, with where each fact is (page, slide). Short files are used as they are.
2. **Outline**: the title and the sections, with the sources and the diagram each one needs.
3. **Sections**, in parallel: ASD-STE100 rules, only facts from the notes, a citation after each fact (`[S1]`,
   `[S1, p. 4]`), tables for numbers, numbered lists for procedures, a Mermaid diagram where it helps.
4. **STE check** of each section (sentence length, passive voice, -ing forms, approved words, phrasal verbs) and one
   repair pass that changes only the wording. The repair is kept only when it has fewer findings.
5. **Summary**, **References** (from the files' own details: *Jane Doe (2025). Pump maintenance manual. [PDF, 12
   pages]*), and an **ASD-STE100 check** table: findings before and after for each section, sources cited, diagrams,
   and the STE score of the whole report.

**Sources you can trust.** A citation to a source that does not exist is removed and reported; a source that is never
cited is listed under the references. A diagram that is not valid Mermaid is removed, so the export never breaks.
With **web research** on (section 39), up to 3 web pages are sources too (`[W1]`), marked as written by others.

**After.** The report is the answer: **Save as…** Word or PDF with the template **ASD-STE100 technical** exports it
with its diagrams. It is also saved in `.swarmlab/out/reports/`. Ask for changes in the chat (*make the summary
shorter*). **Stop** ends it at once. The cost shows under the answer.

**Setup → Long ASD-STE100 reports**: sections (3 to 12), repair passes (0 to 2), web pages as sources, author.

> ⚠️ The STE checker is a help, not a certification: the STE dictionary and the specification (asd-ste100.org) stay
> the reference, and a trained STE writer makes the final check.

---

## 43. Live presentations: change the slides while they are written

```
/livedeck pump P-101 maintenance            (about 10 slides, from your attached files if any)
/livedeck 14 pump P-101 maintenance         (about 14 slides)
/livedeck ste pump P-101 maintenance        (the slides in ASD-STE100)
```

A panel opens above the chat input. First the **plan** appears (the slide titles), then each slide is written, one at
a time. **While it writes, you can change everything:**

| You do | What happens |
|---|---|
| Type in a slide's title, content or speaker notes | The slide becomes **yours** as you type; it is never written over |
| Change the title of a slide still **to write** | It is written with your title |
| **Lock** | The slide stays exactly as it is |
| **Rewrite…** with an instruction | The slide is written again, with your instruction and its current version |
| **Add slide** | It is written next, in the place you chose |
| **↑ ↓** and **🗑** | Order and deletions count before the next slide |
| **⏸ Pause** / **▶ Resume** | The writing waits between slides |
| **Stop** | Ends at once; the slide being written goes back to *to write* |

Before each slide the whole deck is read again, so the model sees your slides (and follows their style without
repeating them). With attached files, facts are cited (`[S1, p. 4]`), and citations to no source are removed.

**At the end** the deck is an answer in the chat, with **Save as PowerPoint** (speaker notes included), and a file in
`.swarmlab/out/decks/`. You can keep changing it in the panel: **Put this version in the chat** gives the new version;
after adding slides, **Write the rest** writes them.

---

## 44. Tasks: one chat, many tasks

Keep talking to the assistant in **Chat**. When you ask for separate pieces of work (*make cover art for the game,
add a settings menu, and get a Windows build*), it puts each one on the **Tasks** tab. Each task runs on its own
thread: its own conversation, with the same tools, permissions and approvals as the chat. You keep talking meanwhile.

**The Tasks tab**

| List | What is in it |
|---|---|
| **Active** | **Working** (with what it is doing now), **Ready for review** (with its last line or question), **Failed**, **Stopped**. Tasks that need you come first. |
| **Up next** | Tasks the assistant suggests on its own. **Go ahead** starts one; ✕ dismisses it. |
| **Done** | Tasks you checked. Uncheck one to put it back in review. |

The badge on the tab counts the tasks ready for review. **＋ Task** adds one yourself (**Start now** or **Up next**).

**Three ways to make tasks:**

1. **Ask in the chat**, as usual: *make cover art for the game, add a settings menu, and get a Windows build*. The
   assistant puts each piece of work on the list (one task each) and keeps talking with you. You can also say
   *put these on the task list: …*. It suggests its own ideas as **Up next** tasks.
2. **Type it**: `/task Fix the login bug: users with a + in their email cannot sign in` starts it now;
   `/task later Write the press kit` puts it in Up next. `/tasks` opens the Tasks tab.
3. **＋ Task** in the Tasks tab, or the **A task** card in Make.

**Open a task** to read its thread, follow its steps live, and send it a message: an answer to its question, a
change, the go-ahead. The message goes to the same thread, so the task remembers everything it did. **Stop**,
**Run again**, **Mark done** and **Delete** are at the top; the files it changed, whether its result was verified,
its calls and cost are at the end.

**Approvals** of every task (edits, commands, questions) come to the Chat tab, as usual; each says which task asks.

**Setup → Tasks**: whether the assistant may create tasks, and **Tasks working at once** (1 by default, up to 4).
Tasks share your workspace: with more than one at once, keep them on different files.

**Make.** The **Make** tab has a card for each kind of document: a long ASD-STE100 report, a live presentation (also
in STE), a quick report, an analysis, an STE procedure, and a task. Each card puts its command in the chat input.

---

## 45. Work on its own, live tokens, and “No answer” explained

**Work on its own.** The **⚡ Auto** button next to Send switches between reviewing everything and working on its
own. The chat settings (and Setup → Chat and tasks) have three choices:

| Work on its own | Edits and file changes | Commands, runs, Claude Code, MCP | Questions (choose) | At the step limit |
|---|---|---|---|---|
| **Off** (default) | you approve | you approve | you answer | it stops and asks |
| **Edits** | applied | you approve | you answer | it stops and asks |
| **Everything** | applied | run | the recommended option | continues on its own (up to 3 times) |

Each automatic action is written in the chat (*✓ auto: Apply — assistant wants to change src/app.ts*), so you can
read everything it did. **Anything marked as impossible to undo still asks you**, in every mode. Your permissions
and blocked commands still apply: Work on its own only answers the questions that would have been asked. With Git
safety on, every change can be undone. Stop ends it at any time.

**Live tokens.** While the model writes, a line under the chat shows the model, the tokens written so far (and its
thinking), tokens per second and time, and this message's finished calls, tokens in and out and cost. Task threads
show the same. Counts while writing are estimated (about 4 characters a token); the totals use the provider's count
when it sends one. Setup → Chat and tasks → **Show tokens live** turns streaming off, for a server that has trouble
with it.

**No answer, explained.** When a message ends without answer text, the chat says why and what to do, for example:

> ⚠️ **No answer.** The model spent all its output tokens (4,000 of 4,000) on thinking and stopped before the answer.
> **What to do:** Raise Max output tokens per call, or lower Setup → Reasoning effort, then send “continue”.

Below it: the model, the stop reason, the tokens, what the reply contained, the model's thinking and its raw text.

---

## 46. Cited answers: every statement with a link to its exact source

Turn it on in the chat settings (or Setup → Chat and tasks → **Cited answers**):

| Cited answers | What is cited |
|---|---|
| **Off** (default) | answers as usual |
| **Code** | files of your project, with lines: `[src/auth.ts:42-58]` |
| **Everything** | also document pages and slides, `[docs/manual.pdf, p. 4]`, `[deck.pptx, slide 3]`, and web pages, `[https://example.com/page]` |

Answers then explain **step by step**, and each statement ends with its source. Each citation is a **link to the
exact place**: a file opens with those lines selected; a PDF opens at its page (if your PDF viewer follows `#page`)
and the page or slide is named; a web page opens in your browser.

**Every citation is checked** against what was really read in that answer, because a link only helps if it is right:

| Mark | Meaning |
|---|---|
| **✓** | read in this answer: the model saw these lines or this page |
| **⚠** | the file exists, but these lines (or this page) were not read in this answer: open it to check |
| **✕** | no such file, or past its end: struck through and not clickable |

**Citation check**, under the answer, lists every source with two buttons that guide the model:
**Wrong source** (it finds the right source, reads it, and corrects the answer) and **Use this** (points your next
message at that place, for example *Look at [src/auth.ts:42-58]: why is the role checked twice?*).

With cited answers on, files are read with line numbers so that citations point to the right lines; answers are
longer and cost more output tokens. Smaller models follow the format less reliably: the check shows when they miss.

---

## 47. Browser, screenshots and /build

Swarm Lab uses **your own Chrome, Edge or Chromium** in headless mode: nothing is downloaded. If it is not found,
set Setup → Browser → **Browser path** (or the `CHROME_PATH` environment variable). Each page opens in a fresh,
temporary browser profile, without your cookies, logins or passwords, and that profile is deleted afterwards.

**From the chat, yourself:**

```
/screenshot site/index.html                 (the whole page)
/screenshot site/index.html phone           (390 px wide, like a phone)
/screenshot http://localhost:3000 window    (only the window, of your dev server)
/screenshot https://example.com
```

**Agents** get two tools when the browser is on:

| Tool | What it does |
|---|---|
| `screenshot_page` | A picture of a workspace file, a local server or a web page: full page or window, any width. Saved in `.swarmlab/screenshots`, shown to models that can see, and in the answer. Console errors, failed files and uncaught exceptions are listed. |
| `browse_page` | The page read after its JavaScript ran: title, visible text, links, console errors. For pages that `fetch_url` cannot read. |

Ask for example: *take a screenshot of site/index.html at phone size and fix what overlaps*.

**Safety.** Files outside your workspace are refused. Internet pages ask once per site and session (⚡ Auto answers
it), and their text is marked as written by others, so instructions in it are not followed. Setup → Browser →
**Internet pages too** off keeps it to workspace files and local servers.

**/build: a whole file, part by part.**

```
/build site/index.html a landing page for our pump service, with prices and a contact form
/build docs/guide.md a user guide for the export feature
```

1. **Plan**: the parts of the file, in order.
2. **Skeleton**: the file's structure, with one marker line for each part.
3. **Parts**, one by one: each is written with the file so far in view, so names, classes and style match.
4. **HTML: a look in the browser** (Setup → /build → browser checks, 1 by default): the screenshot and the console
   go to the model, which names the parts to fix; only those parts are written again. The page is shown from its
   real folder, so its relative styles, scripts and pictures load.
5. **One change to approve**: the whole file, with its diff, as for any edit. The answer lists the parts and the
   checks, with the last screenshot.

Attach files (＋ Files or @) to have them followed, for example your style sheet or a page to match. An existing
file is improved, not ignored. **Stop** ends it.

---

## 48. Context windows per model (self-hosted models)

Many self-hosted models (through LiteLLM, vLLM, Ollama…) have a small **context window** that the prompt and the
answer **share**: with an 8,192-token window, a 6,000-token prompt leaves about 2,000 tokens for the answer. If more is
asked, the server cuts the answer or refuses the call; some servers silently drop the start of the prompt.

**You do not need to change the server.** By default (*Learn from the answers*), Swarm Lab learns each model's real
window from its own answers (an answer cut short after a long prompt, a prompt the server counted shorter than it was,
a "maximum context length is N" error), and from then on works **in steps**, as you would by hand in the chat:

- **A long answer is written in steps.** When the answer is cut, the rest is asked for with a short prompt (the request
  and the end of what is written), so each step has room again; the steps are joined into one answer (up to *Longest
  answer, in steps*, 12 by default). This also finishes a tool call cut in the middle, so agents work in text-tool mode.
- **A long input is read in parts, never cut.** A text that does not fit is read part by part: a request to change the
  whole text (rewrite, translate, convert, fix, comment…) is done on each part in turn and the results are joined; any
  other request gets notes from each part (code, names and numbers copied exactly) and is answered from the notes.
- Calls that fit are sent unchanged. In the chat, *in steps:* lines show what happens. **Check the limits** lists each
  model's window and where it came from; **Forget what was learned** starts again.
- Text-tool mode also understands the tool-call formats models write on their own:
  `<tool_call>name <arg_key>…</arg_key><arg_value>…</arg_value></tool_call>`, and `<tool_call>{json}</tool_call>`
  (Qwen, Hermes and others).

**Servers that say nothing (no token counts, no model info).** Learning from the answers needs the server's token
counts. When the server sends none, Swarm Lab finds the limits itself and answers the way you would in the chat:

- **A smoke test before the first use** (*Test new models*: before their first use, on by default; not done for
  api.openai.com). The model is asked to write: first a numbered list after a short prompt (how far it gets is its
  longest answer), then a word at the very start and one at the very end of texts of growing length, asked back in one
  line (the longest text whose two words both come back is the longest prompt it really reads), then the list again
  after a long prompt (a much shorter list means the prompt and the answer share one window). It takes about ten
  short calls, once per model; the result is kept. **Test the limits** (Setup) or *Swarm Lab: Test model limits*
  runs it again. *Test prompts up to* (32,768 tokens by default) is the largest text sent.
- **Read first, then answer in parts** (*Answer long prompts in parts*: when needed). When the prompt is long for the
  window, the model first reads it and says in one line what is asked, with the parts of its answer; then it writes the
  answer part by part, each reply short enough to fit, ending with a mark that says whether more follows. The parts are
  joined into one answer. A part that is cut is finished as the next part; a part that fails (502, timeout, empty
  answer) is asked again in halves: part 1 → 1.1 and 1.2 → 1.1.1 … *Always* does this for every answer without tools.
- **Tried again, smaller, until it fits** (*Tries when a call fails*, 4). A call that fails because of its size (502,
  504, 413, timeout, "context too long", an empty answer) is not sent again unchanged: first a shorter answer is asked,
  then the prompt is made smaller (long texts read in parts), and the smaller size is kept for next time. Rate limits
  (429) are waited out. A wrong key or a bad request stops at once.
- **Models that think first, and what is not a limit (0.43.12).** Many models think before they answer, and their
  thinking uses the same answer room (*max_tokens*). Only an answer the server cuts, with no thinking in it, counts as
  an answer limit; a model that thinks first or stops a list early is not limited by it. A model seen thinking gets
  room for its thinking on every call (plans, notes, parts), and an empty answer that comes with thinking is asked once
  more with more room. A failure well inside a tested window (a 502 from a busy gateway, an empty answer) is sent again
  as it is: it never makes the window smaller. Only a size error from the server ("context length", 413), or a 502 at a
  size the test did not show to be fine, does. Windows kept by 0.43.10–0.43.11 are forgotten once on update, because
  they could be far too small (down to 768 tokens); each model is tested again when used.
- **Timeouts (0.43.13).** A 504 or a timeout means the server took too long, not that the request was too big: the
  call is made quicker (the answer in parts in the chat, a shorter answer for agents, then a smaller prompt for that
  call only), never sent again unchanged, and the window is kept. In Setup, *Longest answer* says **no cut seen** when
  the test saw no cut, and **not measured (it thinks first)** when the model thought through all the room it was given.
- **Defaults (0.43.14).** *Answer long prompts in parts* is **Never** (one reply, continued in steps when it is cut)
  and *Test new models* is **Only with the button**. With *When needed* or *Always*, each part is asked with the request
  and the answer so far in the prompt, plus a reminder of what is asked, the parts, and how the last part ended. An
  empty answer is never sent again unchanged: it is asked again with more room (a model may think without showing it).
- **The test runs in Setup.** *Test the limits* shows each step live under the button: the model being tested, the
  step, the time, each finished model's row, and a **Stop** button. The test log stays below the table. Tests started
  from Setup no longer write their steps in the chat.

For the OpenAI-compatible provider (self-hosted servers), in the extension and the server.

**Files larger than the window, for agents (0.43.11).** An agent does not get notes of a long file: notes lose the
detail a fix needs. A code file, notebook or pasted code too long for the window is kept whole and replaced in the
prompt by its **map**, for example:

```
src/billing.py: 4,816 lines, 604 symbols (lines start–end):
  4–4169  helper_0 … helper_520 (521 functions like it)
  4172–4182  class Billing
    4173–4174  def __init__(self, rate)
    4176–4178  def compute_tax(self, amount)
    4180–4182  def invoice(self, amount)
  4185–4814  helper_521 … helper_599 (79 functions like it)
Read the exact lines you need with read_file (path "src/billing.py", start_line, line_count); ...
```

The agent then reads the exact lines (`read_file` with `start_line` and `line_count`; each read is sized to the
window and ends with `next: start_line=N`), finds names with `search_text`, and follows calls with `call_graph`.
Names the request mentions always stay in the map. Pasted code is kept as a read-only `@input/pasted.py` (or `.txt`)
that these tools accept; attached workspace files stay where they are, so the agent can change them.

- **Notebooks**: read as cells (`# %% [cell 12] code`), one header line per cell; the map lists every cell (markdown
  cells with their first line or heading) and the functions and classes defined in each code cell.
- **Without the editor** (server, jobs, notebooks): `code_symbols` and `call_graph` work from the text of the files;
  callers are found by text search, so calls through another name can be missing.
- **Long sessions**: earlier reads become one-line pointers ("read earlier: … lines 4176–4178 …"); the last two stay
  whole. The agent reads again what it needs.
- Prose (reports, notes) is still read in parts. *Long inputs for agents* → **Notes from each part** gives the
  behaviour of 0.43.10.

**Setup → Context windows per model**:

| Choice | Where the limits come from |
|---|---|
| **Learn from the answers** (default) | your list first, then what the model's answers showed |
| **Off** | nowhere: Max input tokens and Max tokens per call apply to every model, as before 0.43.9 |
| **Ask the server, and use my list first** | your list, then the server (and what was learned): LiteLLM `/model/info` (`max_input_tokens`, `max_output_tokens`), vLLM `/v1/models` (`max_model_len`), LM Studio, OpenRouter, Ollama `/api/show` (`num_ctx`) |
| **Only my list** | your list |

**My list**, one rule per line, first match wins: `model=window[/max answer]`, `k` for thousands, `*` for anything:

```
llama-3-8b=8192/2048
qwen*=32k/4k
*-7b=4096
```

**What happens on each call** of a model with a known window:

1. The prompt gets the window minus the room kept for the answer (a third of the window, or less if Max tokens per
   call or the model's own limit is lower) and a 5% margin. A longer chat is summarized, then old tool outputs and
   attachments are trimmed, as with Max input tokens.
2. The answer asks for the room that is left, within the model's own output limit.
3. An answer cut by that limit continues in parts and is joined (Max continuations: 4 or 5 is good for small windows).
   Some servers and proxies say “stop” when they cut. **Continue a cut answer when** decides what counts as cut:
   *the server says it was cut* (default), *it used all its tokens* (about all its output tokens, or a full window;
   used on its own for models with a known window), or *it also looks unfinished* (open code block, mid-sentence).
4. File reads get smaller for small windows (about a quarter of the window).
5. Big attached files: files attached to earlier messages are removed first; the files of your current message are
   **shortened to fit** (each keeps its beginning and says where it was cut), and the model reads the rest from the
   file. For work on a whole long document, `/stereport` reads it part by part with notes, and Code search (RAG)
   finds the relevant parts.

A model with no known window is never limited. **Check the limits** shows each model in use with its window, its
longest answer and where it came from. In LiteLLM, set the limits in your config's `model_info` if the server does
not report them:

```yaml
model_list:
  - model_name: llama-3-8b
    litellm_params: { model: openai/meta-llama/Meta-Llama-3-8B-Instruct, api_base: http://vllm:8000/v1 }
    model_info: { max_input_tokens: 8192, max_output_tokens: 2048 }
```

---

## 49. Long jobs: notebooks and repositories, step by step

For work that does not fit in one answer: a whole notebook updated or rewritten, a refactor across many files, a
conversion of a repository.

```
/job rewrite this notebook with polars instead of pandas, and add a chart for each section   (notebook attached)
/job rename the User model to Account everywhere, with its tests                              (no file: the repository)
/job resume        continue the last job that did not finish
/job status        list the jobs
```

You can also just ask in the chat; for a long rewrite, the assistant starts the job itself.

**How it works**

1. **Plan** (lead model): for a notebook, the cells to edit, insert or delete; for a repository, the files to modify,
   create or delete. Big files are split into parts (Setup → Long jobs → lines per part).
2. **Steps** (worker model), in order: each step sees the goal, the plan with what is done, the **journal** (one
   note from each finished step: what it did and the names it introduced), and only its own cell, file or part with
   its neighbours. That is why the job is not limited by the model's context or output.
3. **Checks and retries**: Python syntax, valid JSON, nothing empty, nothing shortened with “…” or “rest unchanged”.
   An invalid result is tried again with the error (Setup → tries per step); a cut output continues in parts.
4. **Review** (lead model): it reads what each step did and can send steps back with a fix.
5. **Result**: the changes are shown as diffs to approve (⚡ Auto applies them), with a table of every step.

**State and resume.** The job is saved after every step in `.swarmlab/jobs/<id>.json` (the plan, each step's
status and result, the journal). If it stops (Stop, an error, a limit, VS Code closing), `/job resume` continues
from the next step; finished steps are not redone, failed ones are tried again. A failed step leaves its cell, file
or part as it was.

**What each step sees.** The goal, the plan with what is done, the journal, and its own cell, file or part. In a
notebook, also: the names defined in **all** earlier cells (from their new versions, with the cell that defines each),
a one-line outline of every earlier cell, the last two cells in full, and what the cell showed last time. Outputs are
never cells: they are never written; raw cells are left alone.

**The plan first.** The plan is checked (duplicates and contradictions fixed, then the lead model looks for missing,
needless or misplaced steps; Setup → Check the plan), then shown in the Run tab: untick the steps you do not want and
press **Start** (Setup → Show the plan before starting). With ⚡ Auto: everything, it starts at once, and the result
is applied without asking. Neighbouring cell edits are done together (**Notebook: cells per step**, 3 by default).

**Run the code** (Setup → Long jobs; off by default). *After each step*, the notebook up to that step is run; *at
the end*, the whole notebook. It runs with Python in the notebook's folder (relative data files work), with a time
limit; charts do not open windows. An error is traced to its cell, and the step that made that cell is done again
with the traceback. It asks once per job; ⚡ Auto answers it. Running the code runs your code: data it writes or
services it calls are real.

**Live preview.** While a step writes, its text appears in the Job view; click a finished step to see its diff.

**Understand the code first** (Setup → Long jobs; *auto*: repository jobs of more than 3 files). Before planning,
the worker model writes a short card for each file (what it does, what it gives, what it uses, what to know before
changing it), and Swarm Lab maps which file imports which (Python, JavaScript, TypeScript). The plan is made from
this map; each step gets the cards of the files its file uses and of the files that use it. Cards are kept between
jobs, by the file's content: the next job on the same code only describes the files that changed.

**Files the job may read** (one pattern per line, for example `src/**`, `tests/**`, `*.md`; empty: the whole
workspace). The file list, the code base map and agent steps stay inside them, and the job cannot change, create or
delete a file outside them. Include what your code imports, its configuration and its tests.

**Only what changes.** The planner first sees where the goal's names and words are (each matching cell or file, with
the line), and plans only the cells or files the goal needs. A step that changes a cell, file or part of 30 lines or more
answers with **find/replace blocks** (only the changed lines), or **NO CHANGE**; shorter ones are written whole (Setup →
Long jobs → *How steps change cells and files*: Auto, Patch, Rewrite; also in the Job view). In big files, only the
parts that contain what the plan says the change touches become steps; the other lines stay as they are.

**Context per step.** Plain steps never call tools or explore: each is one call with exactly its context, which you
choose: *Lean* (the plan around the step, a few notes, the names defined before, one related cell or three related
files), *Balanced* (the default) or *Full* (the whole plan, more notes, a long outline, more related cells and
files). Each step's estimated tokens show in the Job view.

**The job's settings.** The Job view shows the settings this job runs with (cells per step, run the code, kernel or
script, review rounds, tries, agent steps, tests, check command, models, review before applying). They are saved with
the job, so a resumed job runs the same way, and can be changed while the plan waits for **Start**.

**A live Jupyter kernel.** With Run the code on and **Use a live Jupyter kernel** (Setup → Long jobs, on), the
notebook runs in a real kernel that stays loaded: after a step, only the new or changed cells run, and a change to an
earlier cell restarts the kernel and replays. It needs `jupyter_client` and `ipykernel` in your Python
(`pip install jupyter_client ipykernel`); without them, the notebook is run as a script.

**Review before applying.** When the steps are done, the Job view lists them, each with its diff: **Undo** leaves a
step out (its cell or file stays as it was), **Redo…** does it again with your instruction; then **Apply** or
**Discard** (Setup → Review the result before applying; ⚡ Auto: everything applies at once).

**Tests.** With **Add test steps to the plan**, the plan ends with an assert cell (notebooks) or test files
(repositories). For repositories, a **check command** (for example `pytest -q`) runs at the end; a failure goes to
the review, which sends the steps to fix back, up to 2 rounds. In repositories, each step also waits for the files
it needs first.

**Follow it in the Run tab.** The **Job** view shows the goal, a progress bar, what happens now, steps done, calls,
cost and time, **Stop** and **Resume**, and every step with its status (✓ done, → now, · to do, ✕ failed), its
tries, and its note or error.

**Provider trouble.** A job does not fail because the provider is busy. Rate limits, overload, server errors and
network drops are waited through, longer each time (30 s, 1, 2, 5 min) or as long as the server asks; these waits do
not count as tries, and the Job view shows them. After **Wait for a busy provider up to** (Setup → Long jobs, 10 min
by default), the job **pauses**, saved; `/job resume` or **Resume** continues from the next step. An error that
waiting cannot fix (a wrong key, a model that does not exist) stops the job with its message.

**Context too long.** If the provider says a step is too long, the step is made smaller (a shorter journal and less
of the neighbours), up to 3 times, without counting as a try; a whole file that is still too long is split in parts.

**Agent steps** (optional). With **Agent steps** on, each step is an agent turn that can read other files, search the
code and run a check command (for example the tests, or the code) before it answers. It never changes files itself:
its answer is the step's result. It has its own limits (tool turns, tokens, time); if it gives nothing, the step is
done with one plain call.

**Order and speed.** Notebook cells and the parts of one file are always done in order. With **steps at once**
above 1, steps on different files run at the same time (only for independent files).

---

## 50. What the assistant can access

**🔐 Access**, in the chat's toolbar, shows what the assistant can do right now: the workspace, what it can read and
change (from Configure → Agents and your project policy), whether commands are allowed (and which run without asking),
web research, the browser, data folders, MCP tools, Work on its own, and the files attached to your message.

---

## 51. Isolation: where commands run

**Setup → Isolation** chooses where the agents' commands, tests and code run, separately for the **chat** and for
**long jobs and runs**:

| Choice | Where | Deleted |
|---|---|---|
| **machine** | Your folder, your PATH, HOME and installed packages, as before 0.43.6 (the environment VS Code started with) | Nothing to delete |
| **existing** | Your folder, inside the virtual or conda environment you already use, as if activated: **Your environment** (`.venv`, `~/envs/proj`, or its Python), else VS Code's selected Python interpreter (a venv or conda one), else `.venv`, `venv`, `env`, `.conda` | Never: nothing is created or deleted; what the agent installs stays in your environment |
| **venv** (default; recommended for the chat) | Your folder on this machine, with its own Python virtual environment first on PATH (what the agent installs lands there, not in your Python), its own temporary folder and caches. Your installed packages stay visible (*see the machine's Python packages*, on) | With the conversation (chat), at the end (job, run) |
| **docker** (recommended for jobs and runs when Docker is installed) | A container (`python:3.12` or `node:22` from the project, or your image), your folder mounted at `/workspace`; nothing else of the machine is shared. The project's dependencies are installed first | Same |

- **Chat**: one environment per conversation, kept while you talk (packages installed in one message are there in the
  next). Deleting the conversation deletes it; **New chat** stops its container and keeps its folder until the
  conversation is deleted.
- **/job and runs**: one environment per job or run, deleted when it ends (also when it stops, pauses or is
  discarded; `/job resume` makes a new one). Isolated notebook checks run as a script in the environment (the live
  Jupyter kernel is for *machine*).
- **VS Code closes**: containers stop; folders left behind are removed at the next start.
- **Swarm Lab: Delete isolated environments** (command) deletes them all now.
- The approval card of each command says where it will run. If the environment cannot be prepared (no Python, no
  Docker, a failed install), nothing runs: choose another isolation or fix the cause.
- What isolation is not: a venv runs with your user's permissions in your folder; Docker shares your folder (the agent
  can still change your files there, through the usual approvals). Keep Git safety on.

Server jobs: `"isolation"` in the job, or the server configuration's `isolation` (SERVER.md, section 4.5).

## 52. The Lab: GPU or CPU, apps, training runs and their results

Activity → **Lab** (or *Swarm Lab: Open Lab*).

**Compute.** The top of the tab says what runs use, for example *GPU · NVIDIA GeForce RTX 4090 (24 GB) · CUDA 12.4*, or
*CPU · … (16 cores, 64 GB RAM)*. It is detected once (nvidia-smi, rocm-smi, the Apple chip, Python, PyTorch, package
managers) and kept for every project; press *Detect again* after installing a driver or PyTorch. *Everything detected*
lists the facts, and *Python to use* sets the interpreter (a venv's python works).

Choose **Auto**, **GPU** or **CPU**. Every command an agent runs then gets:

| Variable | Value |
|---|---|
| `SWARMLAB_DEVICE` | `cuda`, `mps` or `cpu` (AMD ROCm builds of PyTorch use `cuda`) |
| `MPLBACKEND` | `Agg` (charts are saved without a window) |
| `PYTHONUNBUFFERED` | `1` (logs arrive line by line) |
| `CUDA_VISIBLE_DEVICES` | empty, only when you chose CPU |

In code: `device = os.environ.get("SWARMLAB_DEVICE", "cpu")`. When there is a GPU but PyTorch cannot use it (the
CPU-only build), the Lab says so and agents propose the matching build, asking first.

**Processes.** Type a command (`streamlit run app.py`, `python train.py`), an optional name and address, and *Start*.
It runs in the background with no time limit; the card shows its last lines, the address it printed, 📷 for a
screenshot (needs the browser of section 47), *Log* for the whole log (`.swarmlab/lab/processes/`) and *Stop*, which
stops its child processes too. Agents start processes with `start_process`; each one is approved like a command (you
can change it first), and Work on its own applies as usual.

**Results.** Agents put finished work on the board with `lab_record`: a metrics file (`metrics.jsonl`, one JSON object
per line, or a CSV with a header) becomes one small chart per series with its last, smallest and largest value,
redrawn every few seconds while a process runs; final numbers become tiles; pictures show as thumbnails. Removing a
card leaves the files. The board is `.swarmlab/lab/records.json`.

**Search the project, with filters.** The code index (section 10), searched with a folder or glob, extensions, a kind
(code, docs, data, config), how recently the file changed, and what to leave out.

### Tools agents get

| Tool | What it does | Needs |
|---|---|---|
| `system_info` | The facts above and the device to use | Lab on |
| `install_packages` | pip (the detected Python), uv, conda, npm, brew, winget, choco or apt; names only, no shell characters | Allow commands |
| `start_process` | A long command in the background; waits for its address; screenshot when ready | Allow commands |
| `process` | status, logs, wait (up to 600 s), stop, screenshot, list | Allow commands |
| `lab_record` | A result on the board | Lab on |

Leads never get the tools that run things. Settings: *swarmLab.lab.enabled*, *lab.device*, *lab.python*,
*lab.installTimeoutSec* (default 1200 s).

## 53. Metadata filters on code search

*swarmLab.rag.filters* (`agent`, the default, or `off`). With `agent`, `search_code` takes optional filters:

| Filter | Example |
|---|---|
| `path` | `src`, `docs/**/*.md` (a folder means everything under it) |
| `exclude` | `tests/**, *.min.js` |
| `ext` | `ts,tsx` |
| `kind` | `code`, `docs`, `data`, `config` |
| `modified_after`, `modified_before` | `2026-10-01`, or `7d`, `12h`, `2w`, `3m` |

Files are filtered before ranking, so a filtered search still returns its best matches. Is it recommended? As an
option, yes; as a default, no. A filter helps when the question names where the answer is ("in the docs", "tests only",
"changed this week") and hides the answer when it is wrong. So agents are told to use filters only then, and a filtered
search that finds nothing says to search again without the filter.

## 54. Web pages: source type and dates

Each page an agent reads with `fetch_url` starts with a line such as:

> Source record: 👥 Anyone can post (reddit.com) · published: 2026-10-20 · updated: not found on the page.

The type comes from the address (official or docs, government, news, anyone can post, research, reference, code,
other); the dates come only from the page itself (meta tags, JSON-LD, `<time>`), never from a guess. A type says what to
check first, not whether a page is true. The skill *ai-search-citation-record* turns this into a full record:
the same question asked twice, cited pages compared, concentration on one site or on posting sites, and what a person
checked.

## 55. Pasted text, the message editor and Access

**Pasted text becomes a file** in `.swarmlab/uploads`, named by its type (`pasted-142501.csv`, `.json`, `.py`,
`.log`…). *swarmLab.chat.pasteAsFile*: `always` (two lines or more, or longer than *chat.pasteAsFileMinChars*, 200),
`long` (only long text) or `never`. The chip shows 📋 with the type and the lines; ⤶ puts the text back in the message.
Ctrl+Shift+V (Cmd+Shift+V) always pastes as text.

**Editing a sent message** (✎ on your message) opens a full-size editor: the conversation before it on the left
(*Context* hides it), the message on the right, its files below. Remove a file with ✕; add one with *＋ Image or file*,
*@ Workspace file*, or by pasting or dropping it. *Resend* (Ctrl+Enter) replaces the messages after it.

**🔐 Access** (Chat) now changes what it shows: file changes, commands and the allow-list, web research, browser, Lab
tools, device, search filters, work on its own, pasted text, and the files attached to the next message.

## 56. The message box (0.45)

```
[🌐 Web on] [🖥 GPU · CUDA] [🔐 You approve changes]
Ask about your code, describe a change, or type / for commands and @ for files
 ＋   🛠 Agent ▾   Default (Setup) ▾              ⚡ Auto   [ Send ]
```

| Control | What it does |
|---|---|
| ＋ | Upload a file or picture, pick a workspace file, screenshot a page, paste the next one as text, anything from the Make tab, open the Lab or Access |
| Mode ▾ | 💬 Chat (answers only, no tools) · 🛠 Agent (reads, edits, runs; starts a team when needed) · 👤 Single · 🌳 Tree · 🐝 Swarm · 🔀 Graph |
| Model ▾ | Which model answers (as before) |
| ⚡ Auto | Work on its own: off, edits, everything |
| Send / Start / ■ Stop | Sends; *Start* in a run mode; *■ Stop* while the assistant works and the box is empty |
| Chips | What the assistant may do now; each opens 🔐 Access |

A run mode adds its command to your next message: with 🌳 Tree, "fix the date bug" is sent as `/tree fix the date bug`.
Type your own command (`/review working`) and it is sent as typed. Chat and Agent are the same setting as
🔌 Sending → Mode.

Type **/** at the start of the box for the list of commands. ↑ and ↓ choose, Enter or Tab fills it in, Escape closes it.
**@** still attaches a file or sends the message to one of your agents. Enter sends, Shift+Enter adds a line.

## 57. Refine a harness

Configure → **Harness**. Fill the harness (or load one), write the **Task** to refine it on, then open **Refine this
harness**.

| Option | Choices |
|---|---|
| Edits to try | 1, 2 or 3 of each kind (general, and for this kind of task) |
| How | **Wide:** try every edit, then combine once (2 + 2k runs) · **Deep:** rounds, each starting from the last kept harness (1 + 3k runs) |
| Probe runs | **Read-only** (no edits, no commands: the default) · **As the harness allows** (each change still asks you) |
| A good answer contains / never says | Optional words, comma-separated: they become checks |

Press **Refine…** and approve the number of runs. Each run appears in the table as it ends: what changed, whether it
finished (and its own check and tests), tool calls, tokens, errors and loops, checks, and a score that orders the
table (checks first, then finishing, then fewer errors, loops and tokens). Open *Answer* to read each one. The composer
reads the runs themselves, not only the score.

At the end a card shows the composed harness: its instructions, guardrails, tool guidance, skills and settings, its
score against the harness as it was, and the lessons kept. **Save as name-r2** stores it as a new version (the
original stays); **Load into the form** lets you change it first. When the composed harness did not beat the base,
the card says keeping the current one is safer.

What a refinement may change: the harness instructions, these settings (steps per agent, agents, token budget,
tokens per call, code search results, continuations, answer length and style, one tool call at a time, automatic code
search, a final answer at the step limit) and the mode between single, tree and swarm. It never changes what agents may
read, change or run, the provider or the model, and never switches a workflow (graph) harness to another mode.

**Lessons** (`.swarmlab/harness-lessons.md`): one line each, with the date, the harness and the task; the newest 80
are kept and read by the next refinement. *Lessons* shows them; *Open the file* edits them.

**Instructions for every agent** (Harness tab): Instructions, Guardrails, Tool guidance and Skills to load first.
They are added after each agent's own prompt in every run with this harness. Server jobs read them from the job's
`harness`, or from `"instructions": { "system", "guardrails", "toolGuidance", "skills" }` in the job (the job's win).

## 58. The panel: sidebar, Details, groups and views

- **☰** (top left of Chat): your conversations as a sidebar, with search, *＋ New chat* and export. Click outside or
  press Escape to close it.
- **ⓘ Details** (top right): Context, Sending, Memory, Notes (when memory is off), Steps, Data, Access and Costs as tabs
  of one panel; ← and → move between them, ✕ closes. Today's cost is shown beside the button; click it for Costs.
- **Groups:** Chat (Chat, Make) · Activity (Tasks, Runs, Lab) · Configure (Agents, Workflow, Prompts, Harness,
  Project) · Insights (Codebase Graph, Code map, Bench, Check) · Settings (Setup, Tools, Server). The Activity badge
  counts what is running: a run, tasks and Lab processes.
- **Views** (*swarmLab.ui.view*, or Actions → View): *Simple* shows Chat, Activity and Settings; *Coding agent* adds
  Configure; *Everything* shows all groups. The first time the panel opens it asks which one you want (*Decide
  later* keeps Everything). Views only hide tabs: commands, settings and agents work the same in every view.

## 59. Language

*swarmLab.language*: `auto` (French when VS Code's display language is French, else English), `en` or `fr`. The panel is
drawn again when it changes. Settings and commands follow VS Code's display language (**Configure Display Language**),
not this setting. Technical terms stay in English. *swarmLab.language.answers* (on): with the panel in French, agents
write to you in French, keeping code, commands, file, tool and setting names and technical terms in English. Messages
written by the extension itself (pop-ups, some notes and progress lines) and this manual are in English. The French
README is `README.fr.md`.

## 60. Certificates (trust store)

| Setting | What it does |
|---|---|
| `swarmLab.tls.caFiles` | CA files to trust (PEM, or DER `.cer`): absolute, relative to the workspace, `~/…` or `${workspaceFolder}/…` |
| `swarmLab.tls.systemCertificates` | Also trust the operating system's store: Windows (Root and CA, machine and user), macOS (System and System Roots keychains), Linux (the first of `/etc/ssl/certs/ca-certificates.crt`, `/etc/pki/tls/certs/ca-bundle.crt`, …) |
| `swarmLab.tls.forCommands` (on) | The same authorities for commands agents run and the local server, as one bundle in the extension's storage (`tls/ca-bundle.pem`) given as `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `PIP_CERT`, `GIT_SSL_CAINFO`, `AWS_CA_BUNDLE`, `npm_config_cafile`, `DENO_CERT`. The local server uses it after a restart |
| `swarmLab.tls.allowInvalid` (off) | **Unsafe.** No certificate check for Swarm Lab's requests (and, with *forCommands*, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `GIT_SSL_NO_VERIFY=1`, `npm_config_strict_ssl=false` for commands) |

Certificates are added to Node's own authorities. Changes apply at once to model calls, `web_search` and `fetch_url`,
the decision model and embeddings, direct or through `swarmLab.proxy`. **Setup → Certificates → Check certificates**
lists what is trusted, each file that gave no certificate and why, and tries one HTTPS request to the provider's
address. To get your company's CA: ask IT, or in a browser open any HTTPS site, view the certificate, select the top
(root) certificate of the chain and export it (Base-64 / PEM).

## 61. Review by conditions and inputs

**Conditions.** `edit_file` and `write_file` take `applies_when`, `not_when` and `edge_inputs` (`[{"input": "shipping_fee(5000)", "expected": "0"}]`, or lines `f(1) → 2`). The edit card shows *Applies when*, *Does not apply when* and *Checked with* under the reason. A change to logic (conditions, comparisons, branches, returns) in a code file that states none shows *⚠ Conditions not stated*.

**Check with an input…** (Python `.py`, JavaScript `.js/.mjs/.cjs`, TypeScript `.ts/.mts/.cts` with the project's `typescript` package): give an expression with the file's names and the result the specification expects (a value in the file's language: `0`, `"ok"`, `[1, 2]`). The proposed version, then the current one, are written next to the original as hidden temporary files (`.<name>.swarmlab-check-…`, deleted at once), loaded, and the expression is evaluated; equal values (deep equality in JavaScript) count as expected. 15 s at most. Python is *swarmLab.lab.python*, else `python3`/`python`. The first check of a window asks before running code. **Run its N checks** runs the agent's `edge_inputs`. Your checks, and your think-first note, are added to the message the agent gets after Apply or Reject.

**Think first** (`swarmLab.review.thinkFirst`): `off`, `risky` (logic in a code file that touches money, access, limits, dates or counts, or three changed lines or more) or `always`. Show the explanation is enabled after 8 characters; Skip shows it without a note.

**/practice [folder or file]** sends a read-only request (in the panel's language): find one change made with an AI that a later fix, pull request or test shows to be a bug; show the request or specification and the code before the fix; wait for your answer; then show the fix and its evidence, marking what is not confirmed.

**Reviewer check** asks, before the answer, why the line is wrong and the input you would test, and after it, what you noticed only then. **My AI reliance report** adds: edits checked with an input, edits with a note before the explanation, checks explained first and how many of those were found, notes noticed only after the answer, and a hint when the median time to answer in the last week is 1.5 times that of the first.

## 62. Pictures inside attached files

Attached files (**＋ Files**, `@`, drag and drop) and files read with `read_data` give the model their pictures as well
as their text, when the model can see:

| File | Pictures taken |
|---|---|
| Word (.docx), OpenDocument | Every picture, in reading order (pictures in headers and footers after the others) |
| PowerPoint (.pptx) | Each slide's pictures, labelled with the slide; with `from` / `count`, only those slides |
| Excel (.xlsx) | Pictures placed on the sheets (charts drawn by Excel itself are data, not pictures) |
| PDF | The pictures drawn on the pages read: JPEG as it is; grey, RGB, CMYK, palette and 1–16-bit pictures, and black-and-white fax scans (CCITT Group 3 and 4), as PNG. JPEG 2000 and JBIG2 are counted, not shown |
| Scanned PDF | No text layer: the page pictures go instead, so a model that sees can read them |

Pictures under 48 pixels on a side (bullets, icons) are left out; pictures over about 4.5 MB, and EMF, WMF, TIFF, BMP
and SVG pictures, are counted with a note. The text tells the model how many pictures there are, which ones are
attached and in what order, and how to read the others (`read_data` with `from` / `count`).

**Which model sees: automatic.** In order: your list (`swarmLab.data.visionModels`: `my-model` sees, `!my-model` does
not, `*` is a wildcard, the last match wins), then what the provider answered before, then the model's name (Claude,
GPT-4o, 4.1 and 5, o1, o3, Gemini, Gemma 3, Llava, Llama 3.2 Vision and Llama 4, Qwen-VL, Pixtral, Mistral Small 3.1,
MiniCPM-V…; GPT-3.5, o3-mini, DeepSeek R1 and V3, Codestral, Llama 3.1, Mixtral and embedding models do not). A model of
unknown sight is sent the pictures once: if the provider refuses them, the same request goes again without them, and
the answer is remembered (**Swarm Lab: Forget which models take pictures** clears it). A model that does not see gets a
short note in place of each picture. The same applies to agents, runs and the server (`provider.visionModels`; the local
server gets your list).

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.data.images` | `true` | Pictures to the models that can see them; off: never |
| `swarmLab.data.visionModels` | `[]` | Models that see (`name`) or do not (`!name`) |
| `swarmLab.data.maxImages` | `8` | Most pictures sent with one message, from all its files together (0–20) |

In **Setup → Model provider**, under the models. **Setup → Certificates (trust store)** now comes right after it.

## 63. Reminders and the Today page

**Add one** in the chat: `/remind <when> <what>`, or **Swarm Lab: Add a reminder** (the box shows the time it
understood as you type), or the box at the top of the Today page.

| You type | Due |
|---|---|
| `in 20 min check the build`, `in 1h30 leave`, `in 2 hours call back` | That long from now |
| `tomorrow 9:00 call Sara`, `tonight call mom`, `today 17:30 …` | That day (a day without a time: 9:00) |
| `friday 2pm send the report`, `next friday …`, `at 9:30 …` | The next such day or time (a time already past: tomorrow) |
| `2026-11-03 14:00 dentist` | That date |
| `every weekday 8:30 stand-up`, `every day 18:00 …`, `every monday …`, `every month 10:00 …` | Repeats: **Done** moves it to its next time |
| `demain 9h appeler Sara`, `lundi 14h30 …`, `dans 20 minutes …`, `tous les jours 18h …`, `en semaine 8h30 …`, `ce soir …` | The same, in French |

Times are this computer's. **When it is due**, VS Code shows a notice: **Done** (for a repeating one: **Done, next
time**), **+10 min**, **Tomorrow 9:00**, **Open Today**. Each due time is announced once, also with several windows open;
reminders more than 6 hours overdue (VS Code was closed) are listed, not announced one by one. The 🔔 in the status bar
shows how many are due today (yellow when one is overdue) and, with ☑, the agents' tasks waiting for you.

`/reminders` lists them with numbers; `/reminders done 2` and `/reminders delete 2` act on one.

**The Today page**: start the local server (**Server** tab → **Start local server**), then **Swarm Lab: Open Today**
or a click on the 🔔 opens **http://127.0.0.1:8787/today** with your key (passed in the address's `#` part, which never
reaches the server, and removed at once). Without a server, the same click shows the list in VS Code.

- **Reminders**: due now, later today, the next 7 days, later, done today; **Done**, **+10 min**, **+1 h**,
  **Tomorrow**, **✕**.
- **Agents' tasks** (the Tasks tab's list): waiting for you (ready for review, waiting for your go-ahead), working,
  problems (failed, stopped), done today. Titles and status only; the threads stay in VS Code.
- Refreshed every 30 seconds and when you come back to it. **🔔 Turn on alerts** gives browser notifications; browsers
  allow them on `127.0.0.1` and `localhost`. From a phone on your network the page works, highlights what is due, but
  cannot notify.

Everything is in `.swarmlab/reminders/reminders.json` in the project folder (done reminders are kept 30 days). Nothing is
sent to a model or outside this computer. The API, with a key that has `read` (to view) or `submit` (to change):
`GET /v1/today[?repo=]`, `POST /v1/reminders` (`{"text": "tomorrow 9:00 call Sara"}`, or `text`, `due`, `repeat`),
`POST /v1/reminders/<id>/done`, `/undo`, `/snooze` (`{"minutes": 10}` or `{"until": "…"}`), `DELETE /v1/reminders/<id>`.

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.reminders.notify` | `true` | A notice in VS Code when a reminder is due |
| `swarmLab.reminders.statusBar` | `true` | The 🔔 in the status bar |

## 64. The Atlas of your documents

The Atlas reads a folder of documents and finds who and what they are about: organizations, people, projects,
contracts, meetings… with their facts, the links between them, a timeline, and the places where sources disagree.
Every item keeps where it was read (file and page, slide, sheet or line). It is **off by default**: **Setup → Atlas**,
or `swarmLab.atlas.enabled`.

**Build it**: **Swarm Lab: Build Atlas**, `/atlas build`, or **Build now** on the Atlas page. Only files that changed
are read again; with **Update when documents change** it updates itself 20 seconds after a save (rules only).

| What it reads | What it finds (rules, free) |
|---|---|
| Word, PDF, Excel, PowerPoint, OpenDocument, e-mails (`.eml`), Markdown, text, CSV | Companies (by their suffix: Inc, Ltd, SA, GmbH, Group, Industries…, and by e-mail domains), people (e-mail headers, titles, “Name, Role”, attendee lists), projects (“Project X”), contracts and meetings (by file name), tickets (`OPS-142`), Obsidian `[[links]]`, `#tags` and front matter |
| Every sentence | Amounts (`240 k€`, `$1.2M`), dates (`1 Jan 2027`, `1er janvier 2027`, `Q3 2026`), payment terms (`30 days`, `net 45`), roles, e-mails, phones, links; each fact goes to the names in its sentence, or to the contract or meeting the file is |
| Across files | Every later mention of a known name (“ACME” after “ACME Industries SA”), merged names, “mentioned together” links, a timeline, and **conflicts**: one entity (or its contract), one key, different values in different places |

**The model pass** (optional, `swarmLab.atlas.model`: `off`, `ask`, `on`): passages of about 1,500 characters go to
your worker model, which returns entities, relations (“Lina Martin owns Project Orion”) and facts, each with a quote.
**What its quote does not show in the text is dropped**, and so are names that are not in the passage. Answers are
cached per passage and model; at most `swarmLab.atlas.modelChunks` new passages per build (the next build goes on).

**Use it**
- **Agents** (chat, runs, server jobs) get `atlas_search` (a question → the entities named, their facts, conflicts,
  links, timeline and the sentences, with sources), `atlas_entity`, `atlas_related` (optionally one type) and
  `atlas_timeline` (optionally between dates). They are told to read the file before relying on a detail.
- **The chat** (0.48.2): `/atlas` shows the Atlas as a card: counts per type (tap to filter), conflicts, a mini-graph
  (hover, drag, click), the most mentioned entities and a search box (type, arrows, Enter). `/atlas <name>` opens an
  entity card: key facts as tiles, conflicts, and tabs **Facts**, **Links**, **Timeline**, **Mentions**, **Graph**; each
  source opens the file at its line, each link or node moves to that entity inside the card (**Back**, or Backspace).
  **Ask about it** asks the assistant; ⤢ opens the Atlas page; ⧉ copies the Markdown note. `/atlas <question>` is
  answered by the assistant from the Atlas. Answers that name entities of the Atlas get **chips** under them: a tap
  opens the card in place. `/atlas build`, `/atlas open`, and `/atlas text <name>` for the plain-text version.
- **The Atlas page** of the local server, **http://127.0.0.1:8787/atlas** (**Swarm Lab: Open Atlas**): overview (counts
  per type, conflicts, latest dates), entity pages (facts with sources, conflicts, links with their evidence, timeline,
  mentions, files, its Markdown note), a graph you can drag and click, a table per type (facts as columns: contracts
  with value, renewal and terms), and the timeline. It loads nothing from the network. Without a server, **Open
  Atlas** lists the entities in VS Code and shows one as a note.
- **Obsidian**: **Swarm Lab: Export Atlas as notes** writes one Markdown note per entity in `Atlas/`
  (`swarmLab.atlas.notesFolder`): front matter, facts with sources, `[[links]]`, a warning callout for conflicts. Open
  the folder as a vault. Notes you wrote there yourself are never replaced. Your own notes with `type:` and `aliases:`
  in their front matter are read as entities too.

**Your control** (0.48.3, all optional): **⚙ Manage**, opened by *Setup → Atlas → ⚙ My entities and colours*, the
command **Swarm Lab: Atlas: my entities, types and colours**, or ⚙ in the chat's Atlas card (`/atlas`). Since 0.49.1 it
works before the Atlas is on or built, so you can set up types, colours and names first. The same list as a file:
**{ } As a file**, or **Swarm Lab: Atlas: my entities as a file (JSON)** (a new file is empty).

**Many names at once** (0.49.1): ⚙ Manage → My entities → **📋 Paste a list, cells from Excel, or a CSV**. One name per
line, or columns *name*, *type*, *aliases* (several with `|`) and *match case*, with or without a header row (English or
French), separated by tabs (cells copied from Excel), `;` or `,`. A type is found by its id, its name or another word
(*organisation*, *société*, *personne*, *produit*…); one that does not exist is created (untick **Create the types it
names** to give those rows the type you choose instead). Before anything is added you see how many names, which are
already in your list (they are updated and keep their aliases), the new types, the skipped lines and why, and the first
rows; **Add N** adds them. **From a file…** reads a CSV, TSV or text file. For an Excel workbook, copy the cells (with
the header row) and paste them, or save it as CSV.

**Your own question** (0.49.1): on an entity card, **Ask about …** asks the usual question (key facts, open issues, dates
coming up, where the sources disagree); **Or ask your own question about …** sends yours, about that entity, with the
Atlas; the six ideas under it fill the box; **✎ Edit the question** puts the usual question in the message box so you
can change it first.

| What | Where | What it does |
|---|---|---|
| Types and colours | ⚙ Manage, or `types` in `.swarmlab/atlas/entities.json` | Your types (`{"id": "supplier", "label": "Supplier", "color": "#e0565b"}`); a built-in type's id changes only its name or colour. Used by every dot, chip, avatar and node, in the chat and on the Atlas page |
| Your entities | ⚙ Manage, 📌 on a card, or `entities` | Exact names and aliases, found whatever their length or case (or with case, `caseSensitive`); they keep your type |
| Patterns | ⚙ Manage (tested while you type), or `patterns` | Regular expressions for codes; each match is an entity of that type; a group `( )` keeps only that part |
| Only my entities | ⚙ Manage, or `options.onlyListed` | No automatic guesses: only your list and patterns |
| Corrections | ✎ on any entity card, or `.swarmlab/atlas/corrections.json` | `rename`, `retype`, `merge`, `removeAlias`, `reject`; by name, kept on every rebuild; **Undo** in ⚙ Manage |

**Exact search**: the **=** button next to the search box, or a name in “quotes”, finds only entities whose name or an
alias is exactly that. A change to your list or corrections links the Atlas again in about a second without reading
any file; editing the two files by hand gives completion and checks (their JSON schemas), and saving them applies them.

The API, with a key that has `read` (to view) or `submit` (to build): `GET /v1/atlas`, `/v1/atlas/search?q=&type=`,
`/v1/atlas/entity/<id>`, `/v1/atlas/note/<id>`, `/v1/atlas/graph?center=&depth=`, `/v1/atlas/table?type=`,
`/v1/atlas/timeline?entity=`, `POST /v1/atlas/build`.

**Limits.** Rules find names written the usual way; a model finds more but can be wrong, so every item points to its
source. People are not merged by first name alone. Dates like `03/04/2026` are read day first. Everything stays in
`.swarmlab/atlas/` in the folder; nothing is sent anywhere unless you turn the model pass on.

| Setting | Default | Meaning |
|---|---|---|
| `swarmLab.atlas.enabled` | `false` | The Atlas on |
| `swarmLab.atlas.preset` | `business` | `business`, `research` or `general` |
| `swarmLab.atlas.model` | `ask` | The model pass: `off`, `ask`, `on` |
| `swarmLab.atlas.modelChunks` | `200` | Most new passages per build for the model |
| `swarmLab.atlas.folders` | `[]` | Folders to read (empty: all) |
| `swarmLab.atlas.autoUpdate` | `true` | Update after documents change |
| `swarmLab.atlas.includeCode` | `false` | Also read code files |
| `swarmLab.atlas.notesFolder` | `Atlas` | Where notes are exported |

## 65. 🩺 Check: why an answer is wrong

`/check` in the chat (or **Swarm Lab: Check**, or *Setup → Code search → 🩺 Check*) opens a card with three tools.
They only read and report; nothing is changed unless you press a fix.

**Trace a question** (`/trace [question]`, or **Is this answer wrong?** in the trace under any answer, below). Give the question and a few
words the right answer contains, exactly as the document writes them; optionally the file. Each stage is checked in
order, and the verdict names the first one that loses the words:

| Stage | Checked | Typical finding |
|---|---|---|
| Read from the file | The file as Swarm Lab's readers see it (Word, PDF, Excel… included) | “00123 lost its leading zeros: it appears as 123.0”; a scanned PDF |
| In the search index | The chunks of the code index | Word, PDF and Excel are not in the code index (read when attached, with `read_data`, or by the Atlas); left out by Include / Exclude |
| Found by search | The rank of the right chunk for this question | “Ranked #7: agents read 6, the chat adds 4”; not in the first 50 (other words: add an embedding model) |
| In the Atlas | Facts and sentences of the Atlas | Not attached to any entity (add the name in ⚙ Manage) |
| Reached the model | Your last message, the automatic context and the tool results of the last turn | Never got it; got it but did not use it |

Each stage shows what was found (your words highlighted; a source opens at its line) and what to do. **Copy the
report** gives Markdown to paste in an issue: the question, the stages, the settings that differ from the defaults; no
keys.

**Settings in effect.** Every setting that decides what the model reads (model, code search, reading files, Atlas),
with its value and where it comes from: *default*, *user*, *workspace* or *folder*. Then what the index on disk was
built with, compared with the settings in use (chunk size, embedding model, how many chunks have vectors, their
dimensions), the same for the Atlas (preset, rules, your list), and **names in your settings files that are not
settings**, ignored without a word by VS Code, with the closest real name. **Test** checks the embedding model alone.

**Reading and search check.** Small files made by hand with known content (Word, Excel, PDF, CSV, e-mail, Markdown)
go through every stage, and the content is compared with what went in: “00123” stays “00123”, an empty cell stays
empty (not “nan”), accents and amounts as written, each value whole in a chunk, the right passage first for a
question, found by meaning too (with an embedding model), the company, its contact and its payment terms in the
Atlas. **Also check the model** asks one small question from a passage. It takes about a second and sends nothing
anywhere without that button. With `swarmLab.check.afterUpdates` (on), it runs again on its own after an update of
Swarm Lab, a change of model or embedding model or chunk size, and you are told only if something fails.


### Under every answer: what it was based on (0.48.5)

One line under each answer says what it was based on: **🧭 Based on 3 files and 1 web page**, or **Based on the model’s
own knowledge: no file was read** (fine for a general question; for one about your documents, it means they were not
used). A **1 cited source not read** flag appears when the answer cites a source it never read. Tap the line to open the trace in
place, under that answer; tap it again, press ✕, Esc, or **Close** at the bottom to close it. Nothing is sent anywhere:
the trace is made from the steps the answer already recorded.

| Part | What it shows | What to do with it |
|---|---|---|
| The sentence at the top | The one thing to take from it (nothing read, an unread citation, a search that found nothing, a failed step) | Act on it before reading the rest |
| Sources | Every file, document and page the model got, as chips | Open one at its line and check the answer against it |
| 1 You asked | Your message and its attached files | — |
| 2 Added on its own | The passages Swarm Lab added before the model started, and memory used; or why nothing was added (code search off, adding off, skipped, nothing matched) | If the right file is missing here, use the document's words or attach it |
| 3 It looked up | What the model chose to search, read or run, in order, with “nothing found” flagged | A search that found nothing points at the index or the words used |
| 4 The model read | A bar of what was in front of the model (instructions, history, your message, your files and passages, memory), the model, the calls, the check and the citations | Only what is here can be in the answer |

The first step with a problem opens first (arrows move between steps). **Is this answer wrong or incomplete?** at the
bottom runs *Trace a question* for this answer's own turn, not only the last one: type a few words the right answer
should contain, optionally pick one of the files it used, and the stages are shown in place. ⧉ copies the trace as
Markdown; **🩺 Full check** opens the Check card.

How it differs from the **citation check**: the citation check looks at what the answer *says* (is each `[source]` it
cites real, and was it read?). The trace looks at what the answer was *given* (everything read, added and looked up,
cited or not), so it also shows an answer that cites nothing and read nothing, and where the right text was lost.
**Open the citation check** in step 4 opens the citation check of the same answer.
