# Changelog

## 0.59.1 — Fix: Setup crashed when opened

- Opening **Setup** showed "Something went wrong in the panel: Cannot read properties of null (reading 'value')" and
  left the model provider fields missing. The proxy's **Remove** buttons (0.58) were looked up in the page before their
  group was added to it; that stopped Setup's layout halfway. They are now found inside their own group, a layout error
  can no longer leave Setup half arranged, and the provider check tolerates a missing field.
- New checks in proxyClearSim; Setup was also checked by opening the real panel in a simulated browser (load, settings,
  the proxy's Remove, the sections, Save).

## 0.59.0 — Safer runs: checkpoints and rewind, a worktree per agent, a cost forecast, a public benchmark

- **Checkpoints and ⟲ Rewind.** Before each chat message, Swarm Lab snapshots your folder in a shadow Git repository
  kept outside it (VS Code's storage for this workspace), so every change counts: agent edits, commands, files created
  or deleted, even your own. **⟲ Rewind** on a message shows what will go back and asks: *files only*, or *files and
  conversation* (the message returns to the input box). Your folder as it was is saved first, so **↩ Undo rewind**
  brings it back. Your own repository, branches and index are never touched; `.gitignore`d files, dependencies, build
  output and virtual environments are neither saved nor touched. A snapshot never holds up a message for more than
  `swarmLab.checkpoints.waitSeconds` (10). Off with `swarmLab.checkpoints.enabled`.
- **A Git worktree per agent (optional, off by default: `swarmLab.worktrees.perAgent`).** In Tree and Swarm runs each
  worker edits its own worktree, outside your folder, made from your commit plus your uncommitted changes, so parallel
  agents cannot overwrite each other. Commands still ask, and run in the agent's worktree. At the end (also when a run
  stops early) each changed file comes to you as one review card in your folder, the agents' versions merged three ways
  with yours; where they disagree, the card shows conflict markers to fix. Then the worktrees and their branches go.
  Not with Docker isolation, which only sees your folder.
- **Cost forecast and a hard stop.** Before Tree, Swarm and workflow runs (`swarmLab.runs.costForecast`: *multiAgent*,
  *always* or *off*), a modal shows a likely cost and an upper bound, in tokens and dollars, from the agents, the steps
  each may take, the task and your models' prices; nothing runs before **Start**. Every run stops at
  `swarmLab.runs.maxCostUsd` ($5; 0: only `costBudgetUsd` and the daily limit).
- **Public benchmark.** **Bench → Public benchmark…** (or **Swarm Lab: Set up the public benchmark**) writes a small
  Python project with known bugs and five tasks, the same for Single, Tree and Swarm, graded by tests, some hidden from
  the agents. The report lists setups, models, versions, every run's result, tokens, cost and time, and how to rerun it,
  ready to publish: it shows when more agents help, and what they cost.
- New test: runSafetySim (42 checks, with real Git).

## 0.58.0 — Easier to adopt: your existing rules, a way back from a proxy, keys, a first-run guide

- **Setup → Network proxy: Remove.** Under the field, Setup now says which proxy model calls use and where it comes from
  (Swarm Lab's setting, VS Code's `http.proxy`, the `HTTPS_PROXY` variable, or none). **Remove proxy: back to the
  default** deletes Swarm Lab's proxy at every level it is saved (user, workspace, folder), after you confirm; calls then
  use VS Code's `http.proxy`, then `HTTPS_PROXY`, or go direct. Connections with a proxy of their own are named, since
  they keep it.
- **Other assistants' instruction files are project rules too:** `AGENTS.md`, `CLAUDE.md`, `.cursorrules` and
  `.github/copilot-instructions.md` at the root of the folder, after `.swarmlab/rules.md`, up to 20,000 characters each
  (`swarmLab.rules.agentFiles`, on by default; Setup → Chat and tasks). Moving a project to Swarm Lab keeps its conventions.
- **Learn from rejections.** When you reject a change, a command or a file operation, the record in the conversation asks
  why; **Save as a project rule** adds your reason to `.swarmlab/rules.md`, which every agent reads from the next message on.
- **Keys.** In the chat, **Alt+Enter** approves the first waiting request and **Alt+Backspace** rejects it (a Think-first
  request only moves the focus to your note). In VS Code, **Ctrl+Alt+W** then **O** opens Swarm Lab, **S** starts a
  security scan, **R** reviews your branch, **L** opens the Lab, and in an editor **E** explains and **F** fixes the selection.
- **Get started with Swarm Lab**, a walkthrough on VS Code's Welcome page: connect a model, ask a first question,
  approve a first change, run a security scan.
- **Only in a trusted folder.** The manifest now declares that Swarm Lab does not run in Restricted Mode or on virtual
  file systems: its agents read your files, edit them after your approval, run commands and read instruction files.
- **Package and README:** the changelog now ships inside the VSIX; the README says to install from Open VSX or a GitHub
  Release and to compare the `.sha256`; the install example no longer names an old version; a stray row in the tabs table
  is gone; sections 5b, 5c and 5d are in order.
- New tests: adoptionSim (40 checks), proxyClearSim (20 checks).

## 0.57.0 — 🛡 /scan: a security scan with several cheap models, a verifier, and your project's rules

- **`/scan`** (the whole project), **`/scan changed`** (your uncommitted changes) or **`/scan <folder or file>`**; also
  **Swarm Lab: Security scan** (command palette, the Explorer's and the editor's menus). A 🛡 card in the chat shows the
  plan first: the files, those left out and why, the models, and the **estimated cost**. Nothing runs before **Start**.
- **A structured prompt**, in our own words: severity levels (critical, high, medium, bug), a checklist of about 30
  vulnerability types, and checks before reporting (is the input escaped, does middleware protect it, can an attacker
  reach it, is auth on the handler and not only at the proxy, is the redirect target checked). `dist/`, `node_modules/`,
  tests, minified and generated files are left out (`swarmLab.security.exclude`); files with the most places worth a
  look (input, queries, commands, redirects) come first when there are more than `security.maxFiles`.
- **Several cheap models, two runs each, merged.** By default the 2 cheapest models of Models → automatic choice, from
  different vendors (`security.scanModels`, `security.scanModelCount`, `security.runsPerModel`). The same problem found
  by several runs (same file, lines close, same type) is one finding, with *found by 3 of 4 runs*.
- **A verifier that can only confirm or reject.** Each model first re-reads its own findings in a new conversation and
  may withdraw some (`security.selfCheck`). Withdrawn findings are **not** thrown away: a model from **another vendor**
  (`security.verifierModel`, else chosen for you) re-checks every finding, without being told which were withdrawn;
  answers for anything it was not given are ignored. Findings show as **confirmed**, **unsure**, **not verified** or
  **rejected**, and *withdrawn by the model that found it, then confirmed* when that happens.
- **🧪 Reproduce** (optional, `security.reproduce`): a model writes a small test for one finding; it opens beside the chat
  for you to read; it runs only after you approve it, in the chat's isolation environment (venv, docker or your own; never
  on **machine**). **Confirmed** means it ran, exited 0 and printed the confirmation marker.
- **Project rules against false positives:** `.swarmlab/security-rules.md`, one fact per line (*auth is always done by
  `requireUser`*, *`/internal/*` is only reachable from the VPN*), added to the checks of the scanners and the verifier.
  **Dismiss…** on a finding asks why; your reason can become a rule in one click. **Swarm Lab: Edit the project's
  security rules** opens the file.
- **Extra context only for small models** (`security.callContext`, default *smallModels*): no config files or docs are
  ever sent; call relationships from VS Code's language features go only to small models (a name with 40B parameters or
  fewer, a small model on a local server, or `security.smallModels`).
- **Cost:** every call counts in today's spend; a scan stops at `security.maxCostUsd` ($5) or the daily limit, keeping
  what it found. Severity is always shown as the model's **estimate**. **Copy report** gives Markdown. Scans are saved in
  `.swarmlab/security/` and come back with the conversation.
- The built-in **security-review** skill now uses the same checklist, checks and rules file, and suggests `/scan`.
- Setup → Safety and limits → **Security scan (/scan)**; 17 new settings, in English and French.
- New tests: secScanSim (84 checks), secScanVscodeSim (18 checks).

## 0.56.0 — ↩ Discard and ↪ reapply the agent's changes, as often as you like

- **Per file and per turn.** The *Files changed* card under an answer now has **↩ Discard** and **↪ Reapply** on each
  file, and **↩️ Discard all changes** / **↪️ Reapply all changes** for the turn (*Discard the rest* / *Reapply the
  others* when only some are discarded). A discarded file is struck through and marked *discarded*.
- **Nothing is lost.** Discarding first keeps the agent's version (in `.swarmlab/chat/changes/<turn>~redo`), so
  Reapply puts it back; you can go back and forth. Reapplying asks only when you edited the file since discarding.
  Both go through a VS Code edit, so Ctrl+Z also works in the editor, and the model is told which version the files
  have. Cards from before 0.56 that were undone show as discarded (their agent version was not kept then).
- **Setup: Save automatically** (optional, off by default), under the search in Setup's navigation: each change is
  saved a moment after you make it, without the Save button. Remembered for next time.
- New test: changesRedoSim (12 checks).

## 0.55.0 — ↻ Regenerate in the chat, and Setup reorganized

- **↻ Regenerate.** Ask the same question again in one click: under the latest answer (always visible), on any
  other answer when the pointer is over it, and as **↻ Send again** on your own messages. The conversation goes back to
  that question, as Edit does. On an older answer it first says how many later messages would go
  (*Regenerate from here? The 2 messages after it will go*), with Regenerate and Cancel.
- **Versions of an answer.** The earlier answers are kept as versions of the new one (up to 6): **‹ 1 / 2 ›** under the
  answer shows them in place, and **Use this version** makes one the answer the model reads from then on (the current
  one becomes a version). Saved with the conversation.
- **Setup, reorganized** (same settings, same keys, same save). Seven sections with a sticky side navigation (a bar
  of tabs on narrow panels): *Connection and models*, *Network and certificates*, *Model routing and costs*, *Agents
  and chat*, *Knowledge and context*, *Tools and outputs*, *Safety and limits*. **Search settings** finds any setting by
  its name, help or key. The **save bar** stays at the bottom of the screen while there are unsaved changes: how many,
  which ones, **Discard** and **Save changes** (Ctrl+S / Cmd+S); changed fields and their sections are marked.
  *Model provider* comes in three parts (where the calls go, models, advanced request options), and fields that do not
  apply to the chosen provider are hidden (key header for OpenAI-compatible, vendor for VS Code models…). The
  **network proxy** has its own group next to the certificates; pictures moved to *Knowledge and context*.
- New tests: setupUxSim (9 checks), regenSim (12 checks).

## 0.54.0 — 🗺 The Run Map in the chat, and 🎯 Auto run mode in the chat bar

- **Run Map.** A run started from the chat (the mode picker next to Send, `/tree …`, or the assistant's `start_run`)
  is drawn live in the conversation, from the run's own events: nothing extra is asked of the models.
  - **Tree and Single:** the lead on top, sub-agents branching below as they are created, each with a status ring
    (working, waiting, done, failed), what it is doing now (`read_file src/reports.ts`, `edited …`) and its tokens.
  - **Swarm:** the workers around their shared board; the line between two workers lights up when one writes to the
    other.
  - **Graph:** your workflow's steps in order; the active one glows, steps not reached yet say so, and a loop back
    (test → fix) is an arc with a counter (↺ ×2).
  - A strip with time, agents, tokens, cost, calls, files changed and checks, ticking live, with **Stop**. Click an
    agent for what it did, the files it changed, its messages and its answer. ▴ folds the card to one line.
  - When the run ends, the card stays in the conversation with its summary (*Tree run · 4 agents · 2m 10s · 12k tokens
    · $0.08 · 3 files · checks 5/5*), **▶ Replay** (the whole run again in about six seconds) and **Open in Runs**. It is
    saved with the conversation and comes back when you reopen it. Runs started from the Runs tab are unchanged.
  - Calm by default: VS Code colours, motion only where something happens, and none with reduced motion.
- **🎯 Auto run mode** (`swarmLab.chat.autoRunMode`). A chip in the chat bar in Agent mode, and a choice in Setup →
  Decisions. **On:** when the assistant starts a run, a model picks single, tree, swarm or graph for the task; without
  a decision model your worker model does (`decisions.chatModel` if set), with the higher confidence bar for chat models,
  and for this choice only (other decision points stay as they are). **Off:** the assistant picks the mode itself.
  **As in Setup** (the default): as before, auto only with a decision model.
- New test: runMapSim (26 checks).

## 0.53.0 — 🧱 Playground: Build & test, a no-code workbench for pipelines

The Playground opens on **Build & test** (now the first tab; a choice you saved is kept). Same data, same engine and
same project files as 0.50.3; Retrieval and Generation are unchanged.

- **Try it, live.** Ask one question (or pick one of the dataset) and press Enter: every pipeline that is on runs on
  your documents at once. Blocks pulse while they work, then turn green or red with their time; each arrow shows how
  many documents flow through it (*12 docs → 5 docs → answer*); the answer appears on the last block and in full under
  the pipeline. **Inspect** on a block shows exactly what it passed on (the documents it kept, best first, ✓ green when
  marked relevant in the dataset) or what it wrote.
- **Blocks you drag.** A palette of blocks (Embeddings, Reranker, Generate, Decide, Entities): drag one onto any arrow
  of a pipeline to insert it there, or click it to add it at the end. Moving, removing and setting blocks work as before.
- **Templates.** A gallery as the empty state, and a **Templates** button: *Answer from your documents*, *Answer,
  simple*, *Search only*, *No retrieval (baseline)*, *Decide as JSON*, *Find entities*, and *With vs without retrieval*
  (two pipelines at once). With an empty dataset, the example data is loaded too.
- **Before you run.** A block without a model (and no role to fall back on) is flagged on the block; a custom prompt
  without `{context}` is flagged too. The full run is estimated in model calls, and **▶ Run on 5 questions** gives a
  quick, cheap first result before **▶ Run**.
- **Variants and a winner.** In a copy of a pipeline (⧉), the blocks that differ from the first pipeline are marked;
  after a run, the pipeline that is best on the most measures gets a 🏆.
- Engine: each step now reports how many documents it passes on; Try it asks for the step details only, so full runs
  stay as small as before.
- New test: playgroundStudioSim (22 checks).

## 0.52.0 — 🏷 Labels and names for your conversations, and search by label

In **☰ Conversations**:
- **Labels on every conversation**, the current one too. **＋ Label** (or **Edit labels**) opens a small editor: the
  labels it has (✕ removes one, Backspace the last), a box that completes from the labels you already use (Enter or a
  comma adds), and **suggestions to tap**: labels you use that its first messages mention, its topics, your other labels,
  then common kinds of work (Bug, Feature, Refactor, Question, Review, Docs, Data, Research, Important, To follow up).
  No model call. Case does not matter (`bug` joins `Bug`); at most 12 labels of 32 characters.
- **✎ Rename** a conversation (Enter saves, Esc cancels; empty goes back to its first message).
- **A bar of every label** with how many conversations use it: click to show only those, click more to combine (all
  must match), **All** to clear.
- **Search by label**: the bar writes `#label` in the search box, and you can type it: `#bug` filters at once,
  `#bug timeout` searches *timeout* (keywords or meaning) only in conversations labelled Bug; `#"to follow up"` for a
  label with spaces. Results show their labels.
- Kept in each conversation's own file (`session.labels`, `session.title` in `.swarmlab/chat/`), so they stay with it
  when you start a new chat, reopen an old one, or move the folder.
- New test: convLabelsSim (32 checks).

## 0.51.0 — 🎯 Understanding mode: understand a change without stopping the agent

Optional, **off by default** (*Setup → Understanding mode*, `swarmLab.understanding`). With it off, nothing changes: no
item, no chip, no check, nothing added to a message. Based on two studies of people working with coding agents: tests
passing is not understanding (Qiao, Haque and Hundhausen, 2026, arXiv:2609.33712: one developer passed 112 of 136 tests
and explained 0 of 14), and label leakage went unnoticed in 11 of 15 models built with agents (Ma et al., 2026,
arXiv:2610.14660).

- **Brief** (＋ → Brief): your approach in one line, inputs with the result you expect (`save_task('   ')` → `False`), and
  what is still unknown. About 40–60 words are added to the message, only when a brief is attached; unknowns are
  investigated read-only and the agent asks instead of guessing. The active brief shows as a 🎯 chip; click to change it.
- **Your inputs run while the agent works** (*Checks only*, 0 tokens): on each proposed change to a Python, JavaScript or
  TypeScript file that defines the function they call, with the runner of **Check with an input…**, in the background.
  The agent never waits. A quiet rail in the working card shows the results; **only a failed one** shows a card, with
  **Send to the agent** (a normal message, queued while it works) or **My expectation was wrong**. Your inputs also come
  first in the edit card's checks. The first run asks before running code (*Run* or *Always for this workspace*).
- **Explain this change** (*Checks + explain on demand*): a button on the Files changed card. One call to the worker
  model, only when pressed, with the diff only (cut to 6,000 characters), then cached in `.swarmlab/understanding/`. The
  change is shown as a path (goes in → handled → stopped → comes back), each step with its `file:line` and checked on the
  files (✓ found at this line / ⚠ not found), and one question about a boundary input.
- **Data guard** (0 tokens): when a Python file or notebook the agent changes builds the target from columns that are
  also features (`df['likely_quit'] = df['overtime_hours'] > 20` and `X` keeps `overtime_hours`), a note says so once, with
  **Show where** and **It's intended**.
- **Counter** (off by default, 0 tokens): a ◐ chip with the applied changes neither checked with your input nor
  explained (`.swarmlab/understanding/ledger.json`); click to review them. It never blocks anything.
- Fixed while building it: inputs keep the spaces inside quotes (`'   '` is not `''`).
- New test: understandingSim (69 checks, with real Python and JavaScript runs).

## 0.50.3 — 🔗 Playground: pipelines end to end, an LLM judge, project files and run history

The Playground becomes a place to build and compare whole systems, not only single models.

- **New: Pipelines mode.** A third switch next to *Retrieval* and *Generation*. Each pipeline is drawn as a chain of
  steps — *Dataset → Embeddings → Reranker → Generate → Answer* — and any mix of steps works: embeddings, reranker,
  generate, decide (JSON) and entities. Insert a step anywhere with the **+** between two steps, reorder by dragging a
  step's title (or with ‹ ›), set each step's model, how many documents it keeps (or reads into the prompt), and a
  custom prompt with `{query}` and `{context}`. Start from a preset (*retrieve → rerank → answer*, *retrieve → answer*,
  *retrieve → rerank*) or from empty. Every pipeline runs on every query of the **same dataset as Retrieval** (one
  editor, shared), so you compare end-to-end RAG against no-retrieval baselines on identical data. Results show
  ranking metrics on the order each pipeline ends with (Hit@1, MRR, nDCG@k, Recall@k), an answer check against the
  query's new optional **expected answer**, the judge's score, and latency; per query you see each step's time and the
  ids it kept (relevant ones in green), then the answer. **{ }** copies a pipeline as JSON (the campaign format).
- **New: an LLM judge** for Generation and Pipelines. Turn on *Grade answers with an LLM judge*, pick the judge model
  (default: your decision model), and each answer gets a 1–5 score with a one-line reason — graded against the expected
  answer when there is one, otherwise for correctness and grounding in the texts it was given.
- **New: project files in the workspace.** *Data → Save project as…* writes everything — dataset, retrieval and
  generation models, pipelines, judge settings and run history — to a `.playground.json` file (default
  `playground/` at the workspace root — outside `.swarmlab/`, which is usually git-ignored). From then on every change is **saved automatically** to it (Ctrl/Cmd+S also saves), so the
  project can be committed, diffed and shared. *Open a project or dataset…* opens such a file, a dataset JSON, or any
  file of documents; *Add documents from a file…* reads JSON, JSONL, CSV, TSV, Markdown or plain text (up to 25 MB).
  The Playground only writes to files you picked in a dialog.
- **New: run history.** Every run is recorded with its scores. The results tables show small **deltas** against the
  previous run (or any run you pick with *Compare*), so you see at a glance whether a change helped. Copy the history
  as CSV.
- **Large corpora.** The document list renders 150 at a time with *Show more*, so thousands of documents stay fast.
- **Fixed: Generation runs never finished.** In 0.50.2 the panel did not pick up the answers to generation calls, so a
  run stayed at "Running 0 / N". Every request the Playground makes now resolves.
- **Fixed:** after drawing retrieval results, the Retrieval / Generation switch could show neither as selected.

Everything saved by 0.50.1/0.50.2 (dataset, models, prompts) is read as before.

## 0.50.2 — 🧪 Playground: compare generative models too

The Playground now compares **generative** models, not only retrieval ones. A new **Retrieval / Generation** switch
sits at the top.

- **Generation mode.** Write a set of prompts (with an optional shared *context* given to every model as `{context}`),
  add any mix of **contenders** — an **LLM (generate)**, a **Decision** model (returns JSON), or an **Entities (NER)**
  extractor — and **Run**. Each model answers every prompt; you read the answers **side by side** per prompt, with
  measured **latency** and output size. These run through the exact same step engine as pipelines, so behaviour matches.
- **The models you already chose.** **+ My current models** adds your Roles (lead, chat, decision, Atlas) as contenders
  in one click, and each new card pre-fills with the matching role model — so comparing "my current setup" against
  alternatives is immediate. Every card is optional and can be switched off. **Use for lead / decision / Atlas** sets
  the role from a card you like.
- **Optional scoring.** Give an *expected answer* and each contender is scored: keyword coverage for generate, field
  match against expected JSON for decide, and precision/recall **F1** for entities. Leave it blank to just compare
  answers, latency and size. Export the inputs or the full results as CSV. Inputs are remembered between sessions.

Retrieval mode (embeddings, rerankers, chains, IR metrics) is unchanged.

## 0.50.1 — 🛠 Fix: the protected build opened, and an embedding playground

A small release on top of 0.50.0.

- **Fixed: "kA is not defined" in the panel.** The protected (obfuscated) build shipped in 0.50.0 crashed the panel on open:
  the chat view is given the engine's own fenced-code parser as source, and after obfuscation that source referred to an
  internal name that only exists in the extension, not in the panel. The parser's source is now injected clean at build
  time, so the panel opens normally. Only the build changed; the parser behaves exactly as before.
- **New: a Playground tab for comparing models.** The testers now live in their own **Playground** tab (under
  *Settings*, next to *Setup*), so *Setup → Models* holds only model setup. The Playground is a comparison workbench:
  build a small test set (queries, one shared corpus, and which documents are *relevant* to each query — by hand,
  pasted, imported as JSON, or pulled from code search), add any mix of **contenders** (an *as-given* baseline, any
  embedding model, any reranker, or an *embedding → reranker* two-stage chain), and **Run**. You get a **leaderboard**
  (Hit@1, MRR, nDCG@k, Recall@k, latency, best in each column starred), a **side-by-side** view of every ranking with
  per-document score bars and rank movement, and a **rank-flow** diagram; click any document to follow it across all
  models. Metrics are computed from the returned order, so toggling a relevance label rescores every model instantly
  with no new calls. Export the dataset or the full results (CSV). The dataset is remembered between sessions. Deeper
  single-call tools — inspecting one reranker request, pipelines, and campaigns — are collapsible below. Open it with
  **Swarm Lab: Open the model Playground** or **Try an embedding model** from the command palette.

## 0.50.0 — 🔗 Model pipelines: chain any models one after another, and one protected build

Added on top of everything before it. The reranker and pipelines stay off for code search until you choose them.

**Chain models** (*Setup → Models → Try a pipeline*, or **Swarm Lab: Try a model pipeline**):

- Build a chain of steps run in order on the same input, each step a model of any connection: **Embeddings** and
  **Reranker** reorder the texts, **Generate** writes an answer from the top ones, **Decide** returns JSON, **Entities**
  finds named entities. Drag to reorder; each step picks its own model, how many texts to keep, and (for generate/decide)
  the instruction with `{context}` and `{query}`.
- Run it on your texts or on what code search finds, and see **every step's output** and the final answer. A broken step
  stops the chain and says why. **Copy the result (JSON)**.
- **Add to the campaign**: a whole pipeline becomes a column in a reranker campaign, compared with single rerankers and
  **as given**. Chains that write answers are scored by a pass rate against each question's check (`contains`, a regex,
  or valid JSON), beside the ranking metrics (hit@1, top 3, MRR, nDCG@10) and speed.
- New step kinds reuse your existing connections, keys, headers and proxies; nothing new to configure.

**A protected build.** The shipped extension is now obfuscated: the bundle carries no readable source (mangled names, a
hidden string table), behind a tiny loader so VS Code loads it normally. The published source stays available for review;
only the packaged `.vsix` is obfuscated.

## 0.49.5 — 🧪 Reranker playground for developers, and campaigns of many questions

Added on top: the reranker is still off until you choose one, and code search works as before.

**For one question** (*Setup → Models → Try a reranker*):

- **Your texts with your own ids**: a JSON list (`["…"]` or `[{"id": "doc-12#3", "text": "…"}]`), JSON lines, a CSV with
  `id` and `text` columns, or paragraphs as before. `{"id": "x", "file": "docs/policy.pdf"}` reads a file of the folder
  (documents too: PDF, Word, Excel…). The results keep your ids.
- **Request options**: `top_n`, the longest text sent, `return_documents`, TEI's `raw_scores`, and any more fields your
  provider documents (JSON). With none set, the request is exactly as in 0.49.4.
- **The request sent** (address, headers, body; the key shown as `$RERANK_API_KEY`) and **the same call as code**:
  curl, Python (requests) or JavaScript (fetch), ready to paste. The key is never copied.
- **Copy as JSON**: `[{id, rank, before, index, score}]`; **Scores 0–1** to compare providers on one scale.

**Campaigns** (*Try a reranker → Reranker campaign*, or **Swarm Lab: Reranker campaign**):

- Many questions, each ranked against shared texts, its own texts, or **what code search finds** for it, on several
  rerankers at once, with **as given** (no reranker) as the baseline.
- Say which texts are right (`relevant`) to get **right first (hit@1)**, **top 3**, **MRR** and **nDCG@10** per
  reranker (the best one starred), plus average and p95 time and failures; per question, where the right text came
  and the top 3. Without `relevant`, you still see the orders and the speed.
- Write it as JSON (**Example** shows the format), or **Import…** JSON, JSON lines or a CSV of questions (`query`,
  `relevant`). Files can be **cut into chunks** the way code search does; a relevant file counts for all its chunks.
  Pictures are left out (these rerankers take text), and the notes say so.
- **Save** keeps it in `.swarmlab/rerank/`; **Run**, **Stop**, progress; **Report** as Markdown, CSV or JSON in
  `.swarmlab/rerank/reports/`.

Also: **Test** on a reranker-only connection (TEI, a rerank API) now makes a tiny ranking instead of a chat call it
cannot answer.

## 0.49.4 — 🎯 Try a reranker, then use it for code search (off until you choose)

Nothing changes until you choose a reranker: code search works exactly as before.

- **Setup → Models → Try a reranker**: choose a reranker model from your list, type a question, give your own texts
  (separated by a blank line or a line of `---`) or take **what code search finds** for the question, and **Rank**.
  You see each text's new rank, its rank before (↑ ↓), its score (with a bar), how long it took, how it was called,
  and the server's raw answer. **Copy the results**. Also **Swarm Lab: Try a reranker**.
- **Use it for code search** (or *Roles → Reranker*): the best results of the usual search (keywords and meaning) go
  to the reranker and come back in its order; *best N results* sets how many (30). If the reranker fails, the usual
  order is used and the log says why. *Roles → Reranker → Off* stops it.
- **Both ways rerankers are called**: Cohere-style (`query` and `documents` to `…/rerank`: Cohere, Jina, Voyage,
  vLLM, llama.cpp, Infinity, LiteLLM) and TEI-style (`query` and `texts`: Hugging Face text-embeddings-inference).
  **Auto** tries the first, then the second, and remembers which worked.
- The reranker uses its connection's address, key, headers and proxy. New connection starting points: **Cohere**,
  **Jina**, **Voyage** and **Text Embeddings Inference** on this machine.
- A model with *rerank* in its name is not offered next to Send (it cannot answer a chat).
- New settings: `swarmLab.rag.reranker` (empty: off), `swarmLab.rag.rerankFormat` (auto), `swarmLab.rag.rerankTop` (30).

## 0.49.3 — 📎 See and fix what you attach · ⤓ moving in a long chat

**Attached files you can see and fix**

- Tap an attached file, in the message box or in a message already sent, to see it right there:
  - **a text file** (code, Markdown, CSV, JSON…) opens **editable**: fix it and **Save to file** (or Ctrl+S), **Revert**,
    **Undo the save**. A file changed meanwhile (in the editor or by a run) is not overwritten: it says so. A file with
    unsaved changes in an editor tab is not overwritten either.
  - **a document** (PDF, Word, PowerPoint, Excel, notebook…) shows **what the model reads** from it;
  - **a picture** is shown large, with **✎ Edit the picture**.
- **Open** (in the editor, or its own program), and for files not sent yet **Replace…** and **Remove**.
- Sent messages have **Fix and resend**: change their files or text and send again.
- Each file shows what it is (📄 📕 📝 📊 📽 📓 🖼). Closing with unsaved changes asks for a second ✕.

**Moving in a long chat**

- **New messages no longer pull you down** while you read earlier ones; **⤓ 3 new** says what arrived and takes you
  there. At the bottom, the chat follows as before, also while an answer is being written.
- Buttons at the bottom right of the chat: **☰** your messages (with their attached files) to jump to, **⤒** top, **▲ ▼**
  one message up or down, **⤓** latest. They appear when the chat is longer than the window.
- Keys: **Alt+↑ / Alt+↓** one message, **Alt+Home / Alt+End** top and latest.

## 0.49.2 — 🧩 Setup → Models: every model in one list, every role chosen from it

Connections, the model provider and automatic model choice were three places for one thing. Now there is one.

- **Setup → Models**: every model of every connection in one list (Setup's plain names too), with a search box and a
  connection filter. Tick **Auto** for the models automatic choice picks from; their size, prices, tool support and
  context window are on the same row (known prices shown in grey). **Sizes by price** sets the sizes; **Save models**.
- **⟳ Models on this server** (or ⟳ on a connection) asks the server which models it has: they appear as chips, **tap to
  add** or **Add all**; or type a name and **Add**.
- **Roles**, each a list of those models, grouped by connection (no `@id/model` to type; **Type a name…** is still there):
  **Lead**, **Worker**, **Chat** (or Auto · cheapest / balanced / best), **Decisions** (off, the worker model, any model
  as JSON, or Jev and other System One servers), **Embeddings** (code search by meaning; off = keywords) and **Atlas:
  entities and relations** (the model pass, like a named-entity model: rules only, ask, or with the model you choose).
  The list shows which model has which role. Every role is written into the Setup form and saved with it.
- **Automatic choice** (strategy, how difficulty is judged, move to a bigger model) and **Fallbacks** are in Models too.
- **The classic Model provider fields are the “Setup” connection**, folded under Connections; nothing changes for
  setups that use them. Lead and worker are chosen in Roles.
- New settings: `swarmLab.decisions.chatModel` (the decision model when decisions are answered as JSON; empty: the
  worker) and `swarmLab.atlas.extractModel` (the Atlas's model pass; empty: the worker).

## 0.49.1 — ◎ Atlas: your entities and colours where they are easy, a pasted list, your own question

- **⚙ Manage opens where it is easy**: *Setup → Atlas → ⚙ My entities and colours* and **Swarm Lab: Atlas: my entities,
  types and colours** now open the visual ⚙ Manage card in the chat (types and colours with a colour picker, your names,
  patterns tested as you type, options, corrections with Undo), not the JSON file. The file is one click away:
  **{ } As a file** in Setup, **{ }** in the card, or **Swarm Lab: Atlas: my entities as a file (JSON)**.
- **⚙ Manage works before the Atlas is on or built**: set up types, colours and names first; it says the Atlas is off
  (**Turn on and build**) or not built yet (**Build now**).
- **No sample in your list**: a new `.swarmlab/atlas/entities.json` is created empty (0.48.3 to 0.49.0 put a sample
  type and entity, “Northwind Consulting”, in it, and they became part of your Atlas; remove them in ⚙ Manage if you
  have them).
- **📋 Paste a list, cells from Excel, or a CSV** (⚙ Manage → My entities): one name per line, or columns *name*, *type*,
  *aliases* (several with `|`), *match case*, with or without a header row (English or French), tabs, `;` or `,`
  between columns. Types by id, name or another word (*organisation*, *société*, *personne*…); types it names that do
  not exist are created (or given the default type). **You see what will be added first** (how many, which are already
  in your list, new types, skipped lines and why, the first rows); **Add N** adds them; names already in your list are
  updated and keep their aliases. **From a file…** reads a CSV, TSV or text file (UTF-8 or Windows-1252). Up to 5,000
  names at once.
- **Ask your own question about an entity**: the entity card keeps **Ask about …** (the usual question: key facts, open
  issues, dates, conflicts) and adds a box **Or ask your own question about …** (Enter or **Ask**), six ideas that fill
  it (summary, key dates, who is involved, amounts and terms, where sources disagree, what changed), and **✎ Edit the
  question**, which puts the usual question in the message box to change before you send it.

## 0.49.0 — 🔌 Connections: as many model servers as you like

Use several model servers side by side, each with its own address, settings and API key: Ollama on this machine, a
company gateway, vLLM on a GPU box, OpenRouter… Everything is added to what exists: with no connection, nothing changes.

- **Connections** (*Setup → Connections*, **Swarm Lab: Connections**, `swarmLab.connections`): kind (OpenAI-compatible,
  Anthropic, OpenRouter), base URL, proxy, key header, extra headers, extra request fields, reasoning effort and the
  models you use. 15 starting points (Ollama, LM Studio, vLLM, LiteLLM, Azure, Groq, DeepSeek, Mistral, Gemini…).
  **Test** asks for the model list and makes one tiny call; **⟳** fetches the models; **⧉** duplicates; **✕** deletes the
  connection *and* its key.
- **Keys stay out of settings**: each in VS Code's secret storage as `swarmLab.key.conn.<id>`, sent only to that
  address. A key that looks like another provider's is caught (sk-or-, sk-ant-). Settings Sync copies connections, not
  keys: “key missing on this machine” is said in Setup, the picker and the status bar. `swarmLab.connections` is a user
  setting only, so a cloned folder cannot point your saved key at another address. *Clear API keys* clears them too.
- **`@id/model` everywhere a model is chosen**: lead, worker, the chat's model, the model list of automatic choice,
  Atlas, embeddings (`swarmLab.rag.embeddingModel`), the decision model and fallbacks. A cheap local worker and a strong
  cloud lead in one team. Plain names go to the **default connection**; an unknown `@…` stays a plain name (Cloudflare's
  `@cf/…` still works). Prices, windows and pictures use the bare model name; a server on this machine costs $0.
- **Default connection** (`swarmLab.connection`): next to Send, in the status bar (🔌), or in Setup; per workspace if you
  like (*only for this workspace*). Empty: the classic *Model provider* fields, shown as the built-in “Setup” connection,
  so nothing is copied and nothing goes stale. **Make the Setup fields a connection** copies them, key included.
- **Fallbacks** (`swarmLab.fallbacks`): when a model is down (429, 5xx, no connection) after its own retries, the next
  one is tried, and the chat says so. A real error (a refused key, an unknown model) is shown, not hidden.
- **The local server** uses the default connection (its address, headers and fields); its key is passed only when the
  server's provider is that connection.
- **Import and export** without keys, to share a team's setup (fields that look like keys are refused). **Migrating from
  Cline, Roo or Continue** now keeps every model server found (all Roo profiles, every Continue model) in
  `.swarmlab/connections.json` and offers to add them.

Also:

- **Setup presets**: 🖥 Local model (Ollama), 💲 Cheap, 🔐 Careful, ↺ Back to the defaults. You see every change before it
  applies; the local one adds Ollama and asks it which models to use. **Swarm Lab: Apply a setup preset**.
- **Setup → Essentials / Everything**: presets, connections, the model, safety, costs and limits, or all ~230 settings.
- **Two chips under the message box**: where commands run (🧪 venv, 🐳 Docker · net on/off, ⚠ no sandbox), which opens a
  menu to change it, turn Docker's network on or off, or reset the environments; and 💲 what this conversation cost.
- The model picker next to Send groups each connection's models under its name.

## 0.48.5 — 🧭 Under every answer: what it was based on

A line under each answer says what it was based on, and opens in place, under that answer, to show how. Everything is
made from the steps the answer already recorded: nothing is sent, nothing changes unless you open it.

- **The line**: “🧭 Based on 3 files and 1 web page”, or “Based on the model’s own knowledge: no file was read” when no
  file, document or page was read (fine for a general question, worth knowing for one about your documents); a
  “1 cited source not read” flag when the answer cites a source it never read. It replaces “🩺 Why this answer?”.
- **Opens and closes in place**: tap the line (again to close), ✕, Esc, or **Close** at the bottom; it stays open when
  the chat is shown again. Keyboard, screen readers, narrow panels and reduced motion are handled.
- **Inside**: one sentence with what to take from it; the **sources** as chips, each opening at its line; and four
  steps in order, as tabs (the first with a problem opens first): **You asked** (with attachments) → **Added on its
  own** (the passages added before the model started, memory used, or *why* nothing was added: code search off, adding
  off, skipped, nothing matched) → **It looked up** (searches, reads, commands and tests, “nothing found” flagged) →
  **The model read** (a bar of what was in front of the model, the model, calls, the check and the citations). Attached
  files are among the sources too.
- **Is this answer wrong or incomplete?** runs *Trace a question* for **that answer's own turn** (0.48.4 could only check
  the last one); pick one of the files it used in one tap. ⧉ copies the trace as Markdown; **🩺 Full check** opens the
  Check card.
- **Different from the citation check**, which checks what the answer *cites* (was each `[source]` read?): the trace
  shows what it was *given*, cited or not, so it also catches an answer that cites nothing and read nothing. The trace
  links to the citation check of the same answer (**Open the citation check**), and the citation check says so on hover.

## 0.48.4 — 🩺 Check: why an answer is wrong, stage by stage

When an answer is wrong, find the stage where the right text was lost instead of changing the prompt by guesswork
(after *Configuring RAG Systems: What Breaks, Where Originates, and How to Fix*, arXiv:2610.18567, which found that
about a third of setup problems show up in a later stage than their cause). `/check` in the chat, **Swarm Lab: Check**,
or *Setup → Code search → 🩺 Check*. Everything is added to what exists; nothing changes unless you open it.

- **Trace a question** (`/trace`, or **🩺 Why this answer?** under every answer, with its question filled in): you give
  a few words the right answer contains; each stage gets ✓, ✗ or !, with what was found (your words highlighted, the
  source opening at its line) and what to do:
  **Read from the file** (and if the reader changed it: “00123 lost its leading zeros: it appears as 123.0”) →
  **In the search index** (Word, PDF and Excel files are not in the code index: said plainly, with where they are read
  instead) → **Found by search** (at which rank, against the 4 chunks the chat adds on its own and the 6 agents read) →
  **In the Atlas** → **Reached the model** (in your message, the automatic context or a tool result, and whether the
  answer used it). The verdict names the first stage that lost it. **Copy the report** gives a Markdown report to paste
  in an issue or send to whoever runs the setup (no keys).
- **Settings in effect**: every setting that decides what the model reads, with its value and where it comes from
  (default, user, workspace, folder); what the index on disk was really built with (chunk size, embedding model,
  vectors and their dimensions) against the settings in use; the Atlas likewise; **misspelled settings** in your
  settings files, which VS Code ignores silently (“swarmLab.rag.chunkSize is not a setting: did you mean
  rag.chunkLines?”); and a test of the embedding model alone (does it answer, how many dimensions, how fast). Each
  finding has its one-click fix (Build index now, Build Atlas, Open the file).
- **Reading and search check** (the canary): small Word, Excel, PDF, CSV, e-mail and Markdown files, made by hand
  with known content, go through the readers, the cutting into chunks, keyword search, search by meaning (with an
  embedding model) and the Atlas, and the *content* is checked: “00123” stays “00123”, an empty cell stays empty,
  accents and amounts stay as written. **Also check the model** adds one small call. It runs again on its own after an
  update of Swarm Lab, the model or the embedding model (`swarmLab.check.afterUpdates`, on), and tells you only if
  something fails.

## 0.48.3 — Your control of the Atlas: your entities, types, colours and corrections

All optional: with no list and no corrections, the Atlas works exactly as in 0.48.2.

- **⚙ Manage** in the chat's Atlas card (or **Swarm Lab: Atlas: my entities, types and colours**, or *Setup → Atlas →
  My entities and colours*):
  - **Your types and colours**: add a type (Supplier, Drug, Part…) with a colour picker; change the colour or the name
    of any type, built-in ones too. Every dot, chip, avatar and graph node uses them, in the chat and on the Atlas page.
  - **Your entities**: exact names with aliases, found everywhere whatever their length or case (`NWC`, `apap`), or
    with case (`ACE` is not `ace`); they keep the type you give them, and are marked 📌.
  - **Patterns** for codes (`\bPN-\d{5}\b`): tested on your documents while you type (how many matches, examples,
    or the error), each match an entity of that type; a group `( )` keeps only that part as the name.
  - **Only my entities**: no automatic guesses; **Match case** by default.
- **Corrections that stick**, from ✎ on any entity card: rename, change type, merge into another (typeahead), remove a
  wrong alias, pin to my list, **Not an entity** (asks once more). Kept by name in `.swarmlab/atlas/corrections.json`,
  applied on every rebuild, each one with **Undo** in ⚙ Manage.
- **Exact search**: the **=** button, or “quotes”, finds only entities whose name or alias is exactly that (and says
  which alias matched).
- Changes apply in about a second: the Atlas is linked again without reading any file. Both files can be edited by
  hand too, with completion and checks in VS Code (JSON schemas), and are picked up when saved.

## 0.48.2 — The Atlas in the chat

- **`/atlas`** shows the Atlas as a card in the conversation: counts per type (tap one to filter), where sources
  disagree, a mini-graph (hover lights a node and its neighbours, drag to move, click to open), the most mentioned
  entities, and a search box that answers while you type (arrows and Enter).
- **`/atlas <name>`** opens an entity card: its key facts as tiles, the conflicts, and tabs for **Facts**, **Links**
  (with the sentence that links them), **Timeline**, **Mentions** and **Graph**. Every source opens the file at its
  line; links, chips and graph nodes move to that entity inside the same card, with **Back**. **Ask about it** sends a
  ready question to the assistant; ⤢ opens the full Atlas page; ⧉ copies the entity as a Markdown note.
- **`/atlas <question>`** goes to the assistant, which answers from the Atlas and the files it cites.
- **Chips under answers**: when an answer names clients, people, projects or contracts of the Atlas, they appear under
  it; a tap opens their card right there, a second tap closes it.
- Cards fetch fresh data each time they are shown (a saved conversation never shows an old Atlas), update themselves
  after a rebuild, show progress while building, and offer **Turn on and build** when the Atlas is off. They follow the
  VS Code theme, work with the keyboard, and respect reduced motion.

## 0.48.1 — Pictures inside attached files; reminders and a Today page; the Atlas of your documents

- **Pictures inside documents.** Attached Word, PowerPoint, Excel and OpenDocument files, and PDFs, now give the model
  their pictures as well as their text: in reading order, each PowerPoint picture with its slide, each PDF picture with
  its page. Small pictures (icons, bullets) are left out; the text says how many there are and which are attached.
- **Scanned PDFs are read.** A PDF without a text layer sends its page pictures instead of only saying "OCR is
  needed". JPEG pages go as they are; grey, RGB, CMYK, palette and 1–16-bit pages are written as PNG, and
  black-and-white fax scans (CCITT Group 4, Group 3 one- and two-dimensional) are decoded, all without dependencies.
- **Automatic, by model.** Which model sees is known from its name (Claude, GPT-4o/4.1/5, Gemini, Llava, Qwen-VL,
  Pixtral, Llama 3.2 Vision…), from your list (`swarmLab.data.visionModels`: `name` or `!name`) and from the provider's
  answers: an unknown model refusing pictures gets the same request again without them, and that is remembered
  (**Swarm Lab: Forget which models take pictures**). A model that does not see gets a note in place of each picture.
  Applies to the chat, agents, runs and the server (`provider.visionModels`).
- **`swarmLab.data.maxImages`** (default 8, was a fixed 6): the most pictures with one message.
- **Setup:** the picture settings are in **Model provider**, and **Certificates (trust store)** now comes right after it.
- **Reminders.** `/remind tomorrow 9:00 call Sara`, `/remind in 20 min check the build`, `/remind every weekday 8:30
  stand-up`, also in French (`/remind demain 9h appeler Sara`). When one is due, VS Code shows a notice with **Done**,
  **+10 min**, **Tomorrow 9:00** and **Open Today**; a 🔔 in the status bar counts today's reminders and the agents' tasks
  waiting for you. `/reminders` lists them (`/reminders done 2`). Kept in `.swarmlab/reminders/reminders.json`; nothing
  is sent anywhere.
- **The Atlas** (optional, *Setup → Atlas*): a folder of documents (Word, PDF, Excel, slides, e-mails, Markdown)
  turned into a graph of who and what they are about. Presets: `business` (organizations, people, projects,
  contracts, meetings, products, places, tickets), `research`, `general`. Rules first, free and instant: company names,
  people in e-mail headers, titles and attendee lists, ticket IDs, Obsidian `[[links]]`, `#tags` and front matter, then
  every later mention of a known name; facts (amounts, dates, payment terms, roles, e-mails), links, a timeline, and
  the places where **sources disagree** (30 days in the contract, 60 in a meeting). An optional model pass adds the
  relations the text states, kept only when its quote is really in the text; cached, within a budget. Only changed
  files are read again. Agents get `atlas_search`, `atlas_entity`, `atlas_related`, `atlas_timeline` (chat, runs and
  server jobs); `/atlas <name or question>` in the chat; **http://127.0.0.1:8787/atlas** shows entity pages, a graph,
  tables per type and the timeline, with no network; **Export Atlas as notes** writes an Obsidian vault.
- **The Today page** of the local server, **http://127.0.0.1:8787/today** (**Swarm Lab: Open Today**, or a click on the
  🔔): your reminders (due now, later today, the next 7 days) and the agents' tasks (waiting for you, working,
  problems, done today), refreshed every 30 seconds, with browser notifications. Add, finish, snooze or delete from
  there; made for a phone, like `/inbox`. API: `GET /v1/today`, `POST /v1/reminders`,
  `POST /v1/reminders/<id>/done|undo|snooze`, `DELETE /v1/reminders/<id>`.

## 0.48.0 — Review by conditions and your own inputs; README links fixed

- **Every change to logic states its conditions.** `edit_file` and `write_file` take `applies_when`, `not_when` and
  `edge_inputs` (inputs at the boundaries with the result the request expects), and agents are told to fill them in
  and to test the boundary itself (`>` and `>=` differ exactly there). The edit card shows them under the reason; a
  change to logic in code that states none shows **⚠ Conditions not stated**.
- **Check with an input…** on edit cards (Python, JavaScript, TypeScript with the project's `typescript`): your input and
  the result the specification expects; the proposed version and the current one are run next to the original file
  (so its imports work) and compared: `✓ shipping_fee(5000): with the change returns 0, as expected (now: 500)`.
  **Run its N checks** runs the agent's own inputs. Asked once per window before running code. Your checks go to the
  agent with your answer; a failed one comes first.
- **Think first** (*swarmLab.review.thinkFirst*: off · risky · always): the explanation stays hidden until you write what
  could be wrong and how you would check it (or skip); the note goes to the agent. *Risky*: logic in code touching
  money, access, limits or dates, or several lines.
- **/practice [folder]**: a read-only exercise from the project's git history (an AI change later fixed as a bug,
  confirmed by a fix, pull request or test; "No candidate" when none); the fix is shown only after your answer.
- **Reviewer check**: before the answer, you write why the line is wrong and the input you would test; after it, what
  you only noticed then. **Reliance report**: edits checked with an input, notes written first, checks explained first
  and found, and a hint when your reviews take 1.5× longer than in your first week.
- Code is shown without ligatures: `>=` stays two characters in diffs, code blocks and text boxes.
- **README fixed:** relative links opened "Extension Not Found: joe-el-khoury.LICENSE" in VS Code (it reads a relative
  link as an extension id). Every link and image now points to https://github.com/joeaelkhoury/SwarmLab (branch `main`),
  and the address is `joeaelkhoury/SwarmLab` everywhere again.
- Tests: reviewSim (27 checks, with real Python and JavaScript runs of the shipping-fee example); i18nSim checks that the
  READMEs have no relative link.

## 0.47.0 — French, a trust store for company certificates, and github.com/joeaelkhoury/SwarmLab

- **French.** The panel is in French when VS Code is in French, or with *Settings → Setup → Language* (*swarmLab.language*:
  auto, en, fr). Technical terms stay in English (Chat, Agent, Tree, Swarm, Graph, Lab, harness, prompt, token, RAG,
  GPU, diff, allow-list…). About 1,500 interface texts (`media/i18n/fr.json`), applied as they appear: the page, texts
  that scripts add later, and titles, placeholders and labels; numbers are kept ("2 running" → "2 en cours"). What
  people and models write is never translated: messages, answers, code, file names. Settings and commands (371 texts)
  use VS Code's own language files (`package.nls.json`, `package.nls.fr.json`) and follow VS Code's display language.
  With the panel in French, agents write to you in French and keep code, commands and technical terms in English
  (*swarmLab.language.answers*). README in French: `README.fr.md`, with French screenshots.
- **Trust store** (*Settings → Setup → Certificates*), for networks whose proxy or gateway re-signs HTTPS traffic
  ("unable to get local issuer certificate", "self-signed certificate in certificate chain"):
  *swarmLab.tls.caFiles* (your CA files, PEM or DER `.cer`, absolute, relative, `~/…`), *swarmLab.tls.systemCertificates*
  (the Windows certificate store, the macOS keychains, the Linux CA bundle), *swarmLab.tls.forCommands* (on: the same
  bundle for the commands agents run and for the local server: `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE`,
  `REQUESTS_CA_BUNDLE`, `PIP_CERT`, `CURL_CA_BUNDLE`, `GIT_SSL_CAINFO`, `npm_config_cafile`…, so `pip install`,
  `npm install`, `git` and `curl` work too) and *swarmLab.tls.allowInvalid* (unsafe, last resort: no check). Certificates
  are added to Node's own authorities, never instead of them, and apply at once to model calls, web pages, the decision
  model and the server client, direct or through the proxy. *Check certificates* says what is trusted and tries one
  HTTPS request to your provider. A certificate error now says where to fix it.
- **GitHub:** every link now points to https://github.com/joeaelkhoury/SwarmLab.
- Fixed (found by the French screenshots): the cost beside ⓘ Details and the translation could rewrite each other
  forever; the cost is now compared with what was written, and a safety net limits how often one text is translated.
  Texts with a name inside (process cards, the Refine result) keep the name apart so they translate.
- Tests: i18nSim (57 checks), tlsSim (26 checks, with a real HTTPS server and a self-signed certificate: refused without
  the trust store, trusted with the CA file, trusted by a child process through `NODE_EXTRA_CA_CERTS`).

## 0.46.2 — Release build of 0.46.1

- The same extension as 0.46.1: the PowerPoint fix, the README with screenshots of the current panel, and the display
  fixes. The README's version table and install command name 0.46.2.
- Built and checked again from a clean disk: the whole test suite, the VSIX contents (README links relative, the 11
  screenshots inside) and the PowerPoint fix in the bundle.

## 0.46.1 — PowerPoint export fixed, the README with screenshots of the current panel, and four display fixes

- **Fixed: *Save as PowerPoint* failed with `duplicate ZIP entry ppt/media/diagram-…-1.png`** when several slides had a
  diagram (since 0.43). Each slide numbered its pictures from 1 and the name used the current time, so two slides
  built in the same millisecond got the same name. Pictures are now numbered across the deck (`diagram-1.png`,
  `diagram-2.png`…). New check in docExportSim: three diagram slides in one millisecond, each slide pointing at its own
  picture.
- **README rewritten** with 11 screenshots of the 0.46 panel (chat, modes, ＋, "/", Details → Access, sidebar, message
  editor, Lab, Refine options and results, views); *Which version should I install?* compares 0.44.0, 0.45.0, 0.46.0
  and 0.46.1 with the known issues of each; tables say when to use each mode, each Access row and each Refine option.
  The screenshots are in `media/readme/` and show inside VS Code without a network connection (the VSIX keeps the
  README's links relative).
- Fixed: the ☰ conversations sidebar stopped after 240 pixels; it now runs the full height of the chat, with a visible
  backdrop.
- Fixed: the `hidden` attribute now always hides. In 0.46.0 an empty progress bar showed under *Refine…* and an empty
  badge left a gap after *Activity*.
- Fixed: the Refine progress bar looked empty even when full (its fill took the track's transparency).
- Fixed: the message editor's context showed each answer's *Save as* row; Access said *Build → Agents* for
  *Configure → Agents*.

## 0.46.0 — Refine a harness on your task (Propose–Probe–Compose), and a clearer panel: sidebar, Details, Activity, views

- **Harness → Refine this harness.** Adapted from the Propose–Probe–Compose step of Harness² (Xu et al., 2026,
  arXiv:2610.14224). With a harness and a Task:
  1. the task runs with the harness as it is;
  2. the lead model proposes up to k *general* edits (planning, checking, using tools, finishing) and k *domain* edits
     (for this kind of task), each aimed at something the run showed;
  3. each edit runs on the same task;
  4. the composer keeps the edits whose runs did better on the evidence, combines them, and that harness runs too.
  - **Wide** (try them all, combine once: 2 + 2k runs) or **Deep** (rounds that build on the last: 1 + 3k runs; a
    round is kept only when its run was at least as good). k is 1, 2 or 3.
  - **Evidence, not an answer key:** finished or not, tool calls, tokens, errors, loops, the run's own check and tests,
    and optional "a good answer contains / never says". A table shows every run, its change and its answer; the best
    run is marked.
  - **Safe by default:** one approval says how many runs it will make; probe runs are read-only unless you choose
    "as the harness allows" (then each edit and command still asks); edits never change access, the provider or the
    model, and never switch a workflow (graph). Nothing is saved until you press *Save as name-r2* (or load it into
    the form). A refined harness that did not beat the base says so.
  - **Lessons for next time:** what the evidence supported is kept in `.swarmlab/harness-lessons.md` (dated, with the
    harness and task; editable) and read by the next refinement.
- **Harness instructions** (Harness → Instructions for every agent): text, guardrails, tool guidance and skills to load
  first, added after each agent's own prompt in runs with the harness. Refine writes them; you can edit them.
  **Server jobs** use them too: a job's `harness.instructions`, or `instructions` in the job itself (which wins).
- **☰ Conversations** open as a sidebar, with *＋ New chat*.
- **ⓘ Details** replaces the eight inspector buttons: Context · Sending · Memory · Notes · Steps · Data · Access · Costs,
  as tabs of one panel (← → move between them). Today's cost is shown next to it. Each section works as before.
- **Tabs regrouped:** **Chat** (Chat, Make) · **Activity** (Tasks, Runs, Lab: everything running or finished, with a
  badge counting what runs now) · **Configure** (Agents, Workflow, Prompts, Harness, Project) · **Insights** (Codebase
  Graph, Code map, Bench, Check) · **Settings**. No tab was removed.
- **Views** (*swarmLab.ui.view*): *Simple* (Chat, Activity, Settings, like ChatGPT or Claude), *Coding agent* (also
  Configure, like Cursor or Copilot), *Everything*. Chosen once on first open, changed any time in Actions → View. A
  view only hides tabs; every feature keeps working.
- Fixed: the code search format of 0.44.0 broke an existing test (dates are now shown only for searches by date).
- Tests: refineSim (57 checks); navigationSim follows the new groups.

## 0.45.0 — A composer like the AI tools you know: modes next to Send, ＋, "/", status chips, Send or Stop

Everything works as before; the chat's message box is reorganized around what people expect from ChatGPT, Claude,
Cursor and Copilot.

- **One message box**, rounded, with the controls under the text: ＋, the mode, the model, ⚡ Auto, and Send.
- **Mode next to Send:** 💬 *Chat* (no tools), 🛠 *Agent* (reads, edits, runs, and starts a team on its own when the task
  needs one), and the runs 👤 *Single*, 🌳 *Tree*, 🐝 *Swarm*, 🔀 *Graph*. Chat and Agent are the same setting as
  🔌 Sending → Mode. A run mode adds its command to the next message (`/tree fix the date bug`) and the button says
  *Start*; a message that starts with a command is sent as typed. The mode is kept when the panel reloads.
- **＋ menu:** upload a file or picture, a file of this workspace, a screenshot of a page, paste the next one as text,
  every card of the Make tab, the Lab, and Access. Arrow keys and Escape work in it.
- **Type "/"** for every command (24), with what it does and what it takes; ↑ ↓ choose, Enter or Tab fills it in,
  Enter on a command without arguments (/new, /gpu, /tasks…) sends it.
- **Status chips** above the text: 🌐 Web on/off, 🖥 the device runs use, and 🔐 *You approve changes* or ⚡ *Works on
  its own*; a run mode shows *Next message starts a tree run*. Each chip opens Access.
- **One button sends or stops:** while the assistant works with an empty box it is *■ Stop*; with text it is *Send later*
  (sent when the assistant finishes) and a small ■ stops.
- The **model picker** moved from the top bar into the message box. The ＋ Files button is now in ＋.
- Fixed: *＋ Workspace file* in 🔐 Access opened the file list and closed it at once.
- New test: composerSim (61 checks).

## 0.44.0 — The Lab (GPU or CPU, apps, training, results), pasted text as files, a full message editor, Access you can change

- **Lab tab** (Work → Lab), one place to run things on this machine and see what came out:
  - **Compute:** NVIDIA (nvidia-smi, CUDA version), AMD (rocm-smi) and Apple Silicon GPUs, CPU, RAM, Python, PyTorch (does it
    see CUDA or MPS?), pip, uv, conda, npm, Docker, nvcc, brew, winget, choco, apt. Detected once and kept; *Detect again*
    after installing drivers. **Auto / GPU / CPU** (*swarmLab.lab.device*): every command an agent runs gets
    `SWARMLAB_DEVICE` (cuda, mps or cpu), `MPLBACKEND=Agg` and `PYTHONUNBUFFERED=1`; CPU empties `CUDA_VISIBLE_DEVICES`.
    A GPU that PyTorch cannot use (the CPU-only build) is named, with the build to install.
  - **Processes:** apps, servers and training runs in the background, with no time limit, a live log tail, the address
    they print, 📷 screenshots, Log and Stop. Start one yourself from the tab, or let agents do it.
  - **Results board** (`.swarmlab/lab/records.json`): metrics files become one small chart per series (loss, accuracy…),
    redrawn while a run is going; final numbers as tiles; screenshots and charts as pictures; filters by kind.
  - **Search the project, with filters:** the code index searched with folder or glob, extension, kind, changed within,
    leave out; each hit shows how it was found and when the file changed.
  - **Start something:** six one-click starts (train a model, run an app and screenshot it, build a RAG pipeline, charts
    from data, check the GPU setup, install what the project needs) that put a full request in the chat.
- **New agent tools:** `system_info`, `install_packages` (pip with the detected Python, uv, conda, npm, brew, winget, choco,
  apt; names only, never shell characters; approved like any command; *lab.installTimeoutSec*, default 1200 s),
  `start_process` (background, waits for the address, optional screenshot), `process` (status, logs, wait, stop,
  screenshot, list) and `lab_record`. Leads never get them; without *Allow commands* only `system_info` and
  `lab_record` remain. *swarmLab.lab.enabled* turns the Lab off.
- **Metadata filters on code search** (*swarmLab.rag.filters*: agent / off). `search_code` takes optional `path`, `exclude`,
  `ext`, `kind` (code, docs, data, config), `modified_after` and `modified_before` (2026-10-01 or 7d). Files are filtered
  before ranking, on keywords and embeddings alike. Agents are told to filter only when the task names a folder, a kind or
  a time, and to search again without the filter when nothing is found (the result says so). Hits show when the file changed.
- **Citation record for web pages:** every page read with `fetch_url` gets a *Source record* line: its type (official or
  docs, government, news, anyone can post, research, reference, code) and the published and updated dates as written on
  the page (meta tags, JSON-LD, `<time>`), or "not found on the page": dates are never guessed. Core helpers measure how
  concentrated citations are (one site, posting sites, no primary source) and how two runs of the same question differ.
- **Pasted text is a file** (*swarmLab.chat.pasteAsFile*: always / long / never). Text of two lines or more, or longer
  than *chat.pasteAsFileMinChars* (200), is saved in `.swarmlab/uploads` with its type found from the content (JSON, JSON
  lines, notebook, CSV, TSV, Python, TypeScript, JavaScript, SQL, shell, YAML, Markdown, HTML, SVG, diff, log, text). The
  chip says 📋 *type · lines*; ⤶ puts it back in the message as text. Ctrl+Shift+V always pastes as text.
- **Editing a sent message** opens a full-size editor: the conversation before it beside the text (the last 8, or all),
  its files and pictures, which you can remove, and *＋ Image or file*, *@ Workspace file*, paste or drop to add more.
  Ctrl+Enter resends. Before, the message became a small box and its files could not change.
- **🔐 Access changes things now:** file changes, commands (ask, allow-list, off) and the allow-list itself as chips, web
  research, browser (off, local, internet), Lab tools, device, search filters, work on its own, pasted text, and the
  files attached to this message (remove, add, upload). Each change is saved in the settings at once.
- **8 new built-in skills** (24 in all): track-entity-states-over-time, ai-search-citation-record,
  gpu-cpu-environment-setup, train-model-and-report, build-rag-pipeline, data-visualization, run-app-and-screenshot,
  install-software-safely.
- Command *Swarm Lab: Open Lab*. New test: labSim (121 checks); skillsDefaultsSim: 96 checks.

## 0.43.17 — Skills for every project: 16 built in, and your own folder for all projects

- **16 built-in skills** come with Swarm Lab (`media/skills`): debug-from-error, code-review, write-unit-tests,
  fix-failing-tests, refactor-safely, explain-codebase, security-review, performance-investigation,
  pandas-data-analysis, jupyter-notebook-work, sql-query-writing, write-readme-docs, git-commit-and-pr,
  dependency-upgrade, api-client-integration (timeouts, retries, 429, 502/504) and long-files-small-window. Agents
  still see only the skills that match the task (at most *Skills shown to an agent*, 6), so prompts do not grow.
- **Skills for all your projects** in one folder, `~/.swarmlab/skills` by default (*swarmLab.skills.globalFolder*;
  "off" for none). Save a new skill there with *For all my projects*, or press *Use in all projects* on a project skill.
- **Order:** this project (.swarmlab/skills, .claude/skills), then all projects, then built-in; the first of each name
  wins, and the list says what it replaces. *Copy to this project* makes an editable copy of a built-in or
  all-projects skill.
- **Turn off** a built-in or all-projects skill by name (*swarmLab.skills.hidden*), or all built-in skills at once
  (*swarmLab.skills.builtIn*). Nothing is deleted.
- Tools → Skills: filters (All, This project, All projects, Built-in) with counts.
- Server jobs read the same folders (`SWARMLAB_SKILLS`, `SWARMLAB_BUILTIN_SKILLS=off`); the built-in and all-projects
  skills are offered only when they match the job's task.
- New test: skillsDefaultsSim (72 checks).

## 0.43.16 — Sending: chat or agent, one reply or in parts, and what to do on 502, 504 and 429

- **Chat → 🔌 Sending**, one place for how your messages are sent. The button always shows the mode and the way of
  sending (for example *💬 Chat only · Safe for gateways*), and *⚠ n* when there were problems in the last 10 minutes.
  - **Mode:** *💬 Chat only* (no tools: smaller requests, answers can come in parts) or *🛠 Agent* (reads, edits, runs).
  - **One reply or in parts**, three choices instead of five settings: *Direct* (as before 0.43.9: one call, sent as
    it is), *Safe for gateways* (sent as it is; when a call fails or times out, the answer is written in short parts),
    *Always in parts*. Each sets Context windows, Answer long prompts in parts and the new tool fallback.
  - **The last request**, by part: instructions, tools, history, your message, attached files, code found, memory
    (counted before, never shown), with buttons to make it smaller and to see the whole prompt.
  - **When the server fails:** tries for 502/503/504 and dropped connections, the first wait, tries and longest wait
    for 429 (Retry-After is used), how long to wait for an answer, and the fallback for agents. **Recent problems**
    lists each retry and error.
- **↻ buttons under a failed answer:** *Try again*, *In parts (chat only)* (this message only: no tools, read first,
  written in short parts) and *Only this message* (without the earlier conversation, which is kept). The failed attempt
  is taken out of the history first. Before, *Continue where you stopped* after an error added the new text to the
  failed message, so the whole failed prompt was sent again, larger.
- **An error inside a stream has its status.** A gateway that answers 200 and then sends "504 Server Error: Gateway
  Timeout" (or 502, 429) inside the stream is now tried again and handled like the same status; before, it ended the
  answer at once.
- **429 and server errors are counted apart** (*retry.rateLimits*, *retry.rateLimitMaxWaitSeconds*,
  *retry.serverErrors*, *retry.waitSeconds*). Each wait is written in the chat and the log. The forced single retry
  with Context windows on is gone (the setting decides).
- **"fetch failed" says why:** no answer in time, connection reset, refused, name not found, certificate.
  *requestTimeoutSeconds* (default 600) replaces Node's fixed 300 s wait for the first byte.
- **Agents still get an answer** when a call with tools keeps failing for a reason other than its size (502, 504,
  timeout): after a shorter answer was asked, that answer is written once without tools, in parts (*toolFallback*:
  parts / off). Before, the prompt was read in parts on a server that was failing anyway.
- **A timeout is never kept as a model's window**, also for a model that was not tested.
- The log line "reading it in 1 parts" says what happens: notes taken in one call.
- New test: retrySim (21 checks). studioSim needs a sandbox with its local services (unchanged).

## 0.43.15 — Attached data is analysed on the whole files

- **Data files attached in the chat** (CSV, TSV, Excel, JSON, Parquet…) reach the model as a summary: the size, one line
  per column and the first 50 rows. An answer must not come from that sample. Now, when a message has data files:
  - with *Allow commands* on, the agent is told to compute with a script (Python with pandas, or the csv module) that
    reads the whole files, run it, answer from its output, fix and rerun it when it fails, say which script produced
    each result, and save new tables or charts to new files (never over the attached ones);
  - with commands off, it is told to say at the start of its answer that it rests on the column summaries and the
    first rows only, and never to give a number from those rows as true for the whole file.
  The chat shows which applies. Questions only about the columns or the format are still answered from the summary.
  Messages without data files are unchanged. Before, this rule was only given for data in an agent's data folders.
- New test: dataRuleSim (12 checks).

## 0.43.14 — One reply by default; empty answers never resent unchanged; better prompts for each part

- **New defaults.** *Answer long prompts in parts* is **Never**: the answer comes as one reply, and a cut answer is
  still continued in steps (*Longest answer, in steps*). *Test new models* is **Only with the button** (Setup → Test
  the limits). Choose *When needed* / *Before their first use* to get the earlier behaviour. Settings you saved
  yourself are kept.
- **The same empty call is no longer sent again.** In 0.43.13 the reading step of an answer in parts could get an empty
  answer and send the very same call up to five times ("trying again … the window is kept"). Your server sends no token
  counts and says "stop" even when its thinking used all the room, so the hidden thinking could not be seen. Now an
  empty answer to a short call (the reading step, notes, a part) is asked again with more room; the reading step grows
  from 220 to 1,024, then 4,096 tokens; if it still has no answer, the answer is written without a plan. An empty part
  is asked once more with 4,096 tokens more room, then in halves. An empty answer is never sent again as it was.
- **Each part is prompted like you did by hand.** After each call, the prompt of the next part restates what is asked
  (the one line of the reading step), the parts of the answer, how many are written and how the last one ended, with
  the request itself and the answer so far still in the prompt.
- thinkingSim: 33 checks (your server: a 504, then empty answers with no counts; the prompt of each part).

## 0.43.13 — Timeouts, and answer limits of models that think first

- **A 504 (gateway timeout) is a matter of time, not size.** 0.43.12 sent a request that timed out well inside the
  tested window again as it was, so it timed out again. Now a timeout makes each call quicker: the answer is written in
  parts (chat), or a shorter answer is asked (agents), then the prompt is made smaller for that call only. The window is
  kept. A 502/503 well inside the window is sent again once as it is, then handled the same way.
- **Answer limits of models that think first.** "The room left" in Setup could mean "not measured": the thinking used
  the answer room, so no cut was seen. Now the test asks once more with room for the thinking. An answer that then
  finishes shows "no cut seen"; one that is cut by the server gives a real limit; a model that still thinks through
  all the room shows "not measured (it thinks first)". An empty answer with thinking is given more room, not less (the
  test used to ask for less). Models that think are marked "thinks first", and every call to them gets room for it.
- **Thinking the server does not give apart.** Thinking inside the answer (<think> … </think>, also a block left open
  when the room ran out) is taken out of the answer. An empty answer the server cut ("length") or counted output tokens
  for, with no thinking shown, is taken as thinking hidden by the gateway: it gets more room, not smaller parts.
- thinkingSim: 26 checks (a 504 well inside the window, a model that thinks past all room).

## 0.43.12 — Models that think first; the limit test in Setup

Fixes a window that collapsed to 768 tokens on a model with a very large window (seen with a model that thinks before
it answers, behind a gateway that sometimes answers 502).

- **The limit test no longer takes thinking for a limit.** A short list was read as "answers up to 128 tokens" and gave
  parts of 96 tokens. Now only an answer the server cuts (finish reason "length") with no thinking in it is an answer
  limit; a model that thinks first or stops early is not limited by it. Parts are at least 1,024 tokens when the
  window allows. The one-line answers of the prompt test get room for thinking when the model thinks.
- **Failures that are not about size keep the window.** A 502, a timeout or an empty answer well inside a window the
  test measured is sent again as it is; it is never kept as a smaller window. Before, every empty answer cut the kept
  window by a third, down to 768 tokens. A short answer after thinking, or one with thinking left out of the count, no
  longer teaches "the window is full" either. Real size errors ("maximum context length", 413) are still learned.
- **Room for thinking.** A model seen thinking gets room for it on every call (the plan, notes and parts of a long
  answer); an empty answer with thinking is asked once more with more room.
- **Pasted notebooks** (their .ipynb JSON) are mapped by cells, like an attached notebook, not as code; other pasted
  JSON is not mapped as code.
- **Test the limits, live in Setup:** the model, the step, the time, each finished row and a Stop button, with the test
  log below the table. Its steps no longer go to the chat.
- **Windows kept by 0.43.10–0.43.11 are forgotten once** on update (they could be far too small); each model is tested
  again with the fixed test when used.
- New test: thinkingSim (a thinking model with a large window, empty answers and 502s).

## 0.43.11 — Files larger than the window: a map, then exact reads (agents, notebooks)

- **A map instead of notes.** For an agent with a small window, a code file, notebook or pasted code too long for the
  window is kept whole and given as a **map**: its classes, functions, methods (and the cells of a notebook) with their
  line ranges. The agent reads the exact lines it needs, so no detail is lost in a summary. A workspace file stays where
  it is (the agent can change it); pasted code becomes a read-only `@input/…` file that `read_file`, `search_text`,
  `code_symbols` and `call_graph` all accept. The names the request mentions are always kept in the map; runs of
  similar names are folded (`helper_0 … helper_599`). Prose (reports, notes) is still read in parts.
- **Reads sized to the window.** With a window up to 64K tokens, `read_file` returns as many numbered lines as fit and
  ends with where to go on (`next: start_line=N`); a whole read of a long code file returns its map.
- **Notebooks as cells.** `.ipynb` files are read as a cell view (`# %% [cell 3] code`), the same line numbers in
  the map and in every read; the map lists each cell (with the heading of markdown cells) and what each code cell
  defines.
- **Code tools without the editor.** `code_symbols` and `call_graph` now work on the server, in jobs and for notebooks:
  from the text of the files (callers found by text search) when the editor's language support is not there.
- **Old reads become pointers.** In a long session, earlier reads are replaced by one line ("read earlier:
  billing.py lines 4176–4178 of 4,816 …"), the last two kept whole, so every call fits without summaries.
- **Untested models are tested before their first prompt is fitted**, so the first call already fits the window.
- Setting *Long inputs for agents* (`swarmLab.agentInputs`: map / notes); notes = the behaviour of 0.43.10.

## 0.43.10 — Servers that say nothing: test first, then answer in parts, like in the chat

- **Smoke test of each new model** (Setup → Context windows → *Test new models*: before their first use, on by
  default). For servers that send no token counts and no model info: the model is asked to write a numbered list
  (its longest answer), to give back a word from the start and the end of texts of growing length (its longest prompt,
  read whole), and to write the list after a long prompt (a shared window). About ten short calls, once; the result is
  kept. **Test the limits** in Setup and the command *Swarm Lab: Test model limits* run it on demand.
- **Read first, then answer in parts** (*Answer long prompts in parts*: when needed / always / off). When the prompt
  is long for the window, the model first says in one line what is asked (and lists the parts of its answer), then
  writes the answer part by part, each reply short enough to fit, with a `[[NEXT]]` / `[[END]]` mark; the parts are
  joined. A cut part is finished as the next part; a failing part is asked again in halves (1 → 1.1 → 1.1.1).
- **Retry smaller until it fits** (*Tries when a call fails*, 4). A 502, 504, 413, timeout, "context too long" error
  or empty answer makes the call smaller instead of sending it again unchanged: a shorter answer first, then a smaller
  prompt (long texts read in parts). The smaller size is kept. In steps, a 502/504 is tried once by the HTTP client,
  then made smaller here. Rate limits are waited out; other errors stop at once.
- Server: the same, with `answerInParts` and `testModels` in the run settings.
- Docs and comments no longer name specific models.

## 0.43.9 — Small windows: read and write in steps, without changing the server

- **Learned, not configured.** Each model's real window (prompt and answer together) is learned from its own answers:
  an answer cut short after a long prompt, a prompt the server counted much shorter than it was (it dropped the start),
  or a "maximum context length is N" error. Setup → Context windows → *Learn from the answers* is the new default;
  **Check the limits** shows what was learned, **Forget what was learned** starts again.
- **Long answers in steps.** A cut answer is continued with a short prompt (the request and the end of the answer so
  far), so each step has room, and the steps are joined (up to 12; *Longest answer, in steps*). Before, each
  continuation sent the whole conversation again, so it had less and less room (one line after a long prompt). With an
  unknown window, a cut before the limit asked for sizes the next steps too.
- **Long inputs read in parts, never cut.** A text that does not fit is read part by part: requests that change the
  whole text (rewrite, translate, convert, fix, comment, format…) are done on each part in turn and joined; other
  requests are answered from notes taken from each part (code, names, numbers copied exactly). Notes are kept, so the
  next message does not read the same text again. When the server dropped the start of a prompt, the call is done
  again in parts. *Read long texts in parts instead of cutting them* (on).
- **Agents with text tools:** a tool call cut by the output limit is finished in a step and then run; the
  `<tool_call>name <arg_key>…</arg_key>…</tool_call>` and `<tool_call>{json}</tool_call>` formats some models write are understood; tool calls written while thinking
  are ignored.
- The chat, agents, runs, `/job` and the server (OpenAI-compatible provider) all use it.

## 0.43.8 — Long jobs change only what the goal needs, and write only the changed lines

- **The places first.** Before planning, Swarm Lab looks for the goal's names and words (`code`, identifiers such as
  `load_data` or `pd.read_csv`, other words) in the notebook's cells or the repository's files, and shows the planner
  each match with its cell or file and line. The planner is told to plan **only** the cells or files the goal needs
  (no clean-ups or improvements it does not ask for), with an instruction that says exactly what to change; the plan
  check now removes unneeded steps first.
- **Only the changed lines** (Setup → Long jobs → *How steps change cells and files*, and in the Job view): a step that
  changes an existing cell, file or part of 30 lines or more answers with find/replace blocks, not the whole text again.
  A step that finds nothing to change answers **NO CHANGE** (the cell stays as it is). Blocks are matched exactly, then
  ignoring indentation and trailing spaces; blocks that do not match go back with the reason, and after two the last
  try writes the whole text. A model that writes the whole text anyway is accepted as a rewrite (no second call). *Auto*
  (default): patch 30+ lines, rewrite shorter ones; *Patch*: always; *Rewrite*: as before.
- **Big files: only the parts that change.** The plan names what each file change touches (`"where"`); only the parts
  of a big file that contain it become steps, and the other lines are kept as they are (before, every part of the file
  was rewritten).
- **No more "rewrite every cell".** When the planner gives no plan it can read, the job no longer edits every code cell
  with the goal: it uses the cells where the goal's names appear, or stops and asks for a more precise goal.
- Fix: the blank lines that end a part of a big file are kept when the parts are joined again.

## 0.43.7 — Run in your own environment

- **existing**, a fourth isolation choice (Setup → Isolation, for the chat and for jobs and runs): commands run on this
  machine, in your folder, inside the virtual or conda environment **you already use**, as if it were activated (its
  folders first on PATH, `VIRTUAL_ENV` or `CONDA_PREFIX` set). Nothing is created, copied or deleted: packages the agent
  installs stay in your environment.
- Which environment: **Your environment** (a folder such as `.venv` or `~/envs/proj`, or its Python, such as
  `.venv/bin/python`), else the Python interpreter selected in VS Code (only when it is a venv or conda environment, never
  the system Python), else `.venv`, `venv`, `env` or `.conda` in the workspace. Looked up for every command, so a changed
  interpreter applies at once. None found: nothing runs, with a clear message (no fallback).
- `/job` with Run the code: the live Jupyter kernel runs with your environment's Python.
- **machine** stays as it was: the environment VS Code started with (which is not your terminal's activated venv).
- Server: `"isolation": "existing"` uses the configuration's `isolation.existingPath` (relative to the repository's own
  folder; empty: `.venv`, `venv`, `env`, `.conda` there). It runs on the worker itself, so it needs an admin key like
  `machine` (unless `isolation.machine` is `"submit"`).

## 0.43.6 — Choose where commands run (machine, venv, Docker), cleaned up afterwards; safer permissions

**Isolation: where the agents' commands, tests and code run** (Setup → Isolation; server jobs: `"isolation"`).

- **machine**: as before: your folder, your PATH, HOME and installed packages. Nothing to clean up.
- **venv** (default, recommended for the chat): still this machine and your folder, but with its own Python virtual
  environment first on PATH (`pip install` lands there, never in your Python), its own temporary folder, package
  caches and tools folder. The machine's packages stay visible by default, so nothing needs reinstalling; the venv is
  made in about 0.1 s (it borrows the machine's pip). Optional: its own empty HOME.
- **docker** (recommended for long jobs, runs and server jobs when Docker is installed): a container of an image
  (`python:3.12` or `node:22` from the project, or yours), with only your folder shared at `/workspace`; the project's
  dependencies are installed first by default; network can be turned off.
- **Cleaned up automatically**: a chat's environment is deleted when the conversation is deleted (New chat stops its
  container and keeps its folder until then); a `/job`'s and a run's when it ends (finished, stopped, paused or
  discarded); a server job's at its end, as before. Containers stop when VS Code closes; folders left behind are
  removed at the next start. **Swarm Lab: Delete isolated environments** removes them all now.
- Approval cards say where a command will run. An environment that cannot be prepared runs nothing (no silent
  fallback to the machine).
- `/job` with Run the code, isolated: the notebook runs as a script in the environment (the live kernel is for
  *machine*).
- **Server**: a job may say `"isolation": "machine" | "venv" | "docker"`; the configuration's `isolation` sets the
  default (`venv`), the choices allowed, the image, network and dependency install. **machine** (commands on the worker
  itself) needs an admin key unless `isolation.machine` is `"submit"`. A job with its own `environment` keeps it unless
  it also says `isolation`. Server tab → New job → **Isolation**; Python client: `submit(..., isolation="docker")`.

**Permissions**

- **Control files are protected**: agents may not change `.swarmlab/policy.json`, `mcp.json`, `graph.json`,
  `environment.json`, `project.json`, rules, prompts, workflows, hooks and plans, `.claude/settings*.json` or
  `swarmlab.server.json`, whatever their edit paths (an agent can no longer widen its own permissions, add a tool server,
  or rewrite its prompt). Claude Code turns that change them are reverted by Git safety. Setup → Isolation → *Agents may
  not change Swarm Lab's control files* (on).
- **Server approvals only an admin may loosen**: a job's `approvals` may always be stricter than the server's; looser
  (for example `"commands": "auto"` on a server with `allowlist`) needs an admin key, or `approvalsLoosen: "submit"`.
- **Allow-list**: inline code given to an interpreter (`python -c`, `node -e`, `bash -c`…) always asks, and entries that
  would allow any code (`python`, `bash`, `node`, `npx`, `env`, `sudo`…) never match; the server refuses them from
  non-admin jobs.
- **Cannot be undone** also covers `find … -delete`, `xargs rm`, `rsync --delete`, `truncate -s 0`, `shred`, inline
  Python or JavaScript that deletes files or runs commands, `curl … | sh`, `git push --mirror`, `gh repo delete` and
  `npm unpublish`: they always ask, in every mode.
- `/job` agent steps with *Files the job may read* are told they cannot run commands (the read-only slice has none).
- Fix: in an environment with a virtual environment, its `python` and `pip` come first on PATH (a Python alias made
  for the machine could shadow them).

## 0.43.5 — Long jobs that understand the code base, with the context you choose

- **Understand the code first** (Setup → Long jobs; *auto* for repository jobs of more than 3 files): before
  planning, the worker model writes one short card per file (what it does, what it gives, what it uses, what to know
  before changing it) and Swarm Lab maps who imports whom (Python, JavaScript, TypeScript). The plan is made from this
  map, and each step gets the cards of the files its file uses and of the files that use it. Cards are kept between
  jobs by the file's content (`.swarmlab/jobs/cards.json`): unchanged files cost nothing the next time.
- **Files the job may read** (patterns such as `src/**`, `tests/**`, `*.md`): the file list, the code base map and
  agent steps stay inside them, and the plan cannot change, create or delete a file outside them.
- **Context per step**: *Lean* (fewest tokens), *Balanced* (default) or *Full*: how much of the plan, the notes,
  the outline of earlier cells, the related cells and files and the output hints each step gets. Each step's
  estimated tokens, and the average, show in the Job view; the choice can be changed while the plan waits for Start.
- Plain steps never call tools or explore: each is one call with exactly this context.

## 0.43.4 — Long jobs: live kernel, settings per job, review before applying

- **The job's settings in the Job view**: cells per step, run the code (and kernel or script), review rounds, tries,
  agent steps, tests, check command, models, review before applying. They are saved with the job (a resumed job runs
  the same way) and can be changed while the plan waits for **Start**.
- **A live Jupyter kernel** for Run the code (Setup → Long jobs → Use a live Jupyter kernel, on): the notebook's state
  stays loaded, so after a step only the new or changed cells run; an earlier change restarts the kernel and replays.
  The failing cell comes straight from the kernel. Needs `jupyter_client` and `ipykernel`; without them, the notebook
  runs as a script, as before.
- **The code a cell builds on**: besides the names and the outline, each cell now gets, in full, the earlier cells
  that define the names it uses.
- **Order by dependency** (repositories): the plan says which files each file needs first, and a step waits for them,
  also with several steps at once.
- **Review before applying** (on): when the steps are done, the Job view lists them with their diffs: **Undo** leaves
  a step out, **Redo…** does it again with your words; then **Apply** or **Discard**. ⚡ Auto: everything applies at
  once.
- **Tests** (optional): the plan ends with test steps (an assert cell for a notebook; test files for a repository),
  and a **check command** for repositories (for example `pytest -q`) runs at the end; a failure goes to the review,
  which sends the steps to fix back (up to 2 rounds).
- Fixed: a server or CLI process that used the live kernel waited 2 minutes before it could exit (a start timer was
  not cleared).

## 0.43.3 — Long jobs you can check: context, plan, live preview, running the code

- **Every cell knows what comes before it.** Each notebook step now gets the names defined in all earlier cells
  (imports, variables, functions, classes, and which cell defines them, from their new versions), a one-line outline
  of every earlier cell, the last two cells in full, and what the cell showed last time (as a hint about the data).
- **Useful code.** Steps follow quality rules: reuse what earlier cells define (no re-imports or re-loading),
  focused cells, clear vectorized code, brief results (a head(), a chart, a summary), no placeholders. Outputs are
  never cells: they are never written or rewritten; raw cells are left alone.
- **The plan is checked** before you see it: duplicate or contradictory steps fixed, then the lead model looks for
  missing, needless or misplaced steps (Setup → Long jobs → Check the plan). Its findings show in the Job view.
- **The plan first** (Setup → Show the plan before starting, on): in the Run tab, untick the steps you do not want,
  then **Start**. Not with ⚡ Auto: everything, which also applies the result without asking.
- **Fewer steps**: neighbouring cell edits are done together (Notebook: cells per step, 3 by default).
- **Live preview**: the text of the step being written appears in the Job view as it arrives; click a finished step
  to see its diff.
- **Run the code** (Setup → Long jobs; off by default): after each step (the notebook so far) or at the end (the
  whole notebook), with Python in the notebook's folder and a time limit; an error is traced to its cell and the
  step that made it is redone with the traceback. Asked once per job; ⚡ Auto answers it.
- **🔐 Access** in the chat: what the assistant can read and change, commands, web research, the browser, data
  folders, MCP tools, Work on its own, and what is attached to your message.

## 0.43.2 — Jobs in the harness, and jobs that survive provider trouble

- **The Job view in the Run tab**: the goal, a progress bar, what happens now (including waits: *⏳ waiting 60 s:
  rate limit reached*), steps done, calls, cost and time, **Stop** and **Resume**, and every step with its status
  (✓ → · ✕), its tries, and its note or error. The Run tab's Stop also stops a job.
- **Provider trouble does not fail a job.** Rate limits (429), overload (529), server errors (5xx) and network drops
  are waited through, longer each time (30 s, 1, 2, 5 min) or as long as the server asks (Retry-After and the
  x-ratelimit reset headers are followed); these waits do not count as tries. After *Wait for a busy provider up to*
  (10 min by default) the job **pauses**, saved: `/job resume` (or Resume) continues from the next step.
- **“Context too long” makes the step smaller** (shorter journal and neighbours), up to 3 times, without counting as
  a try; a whole file that is still too long is split into parts.
- **Planning never leaves you with no plan**: when the plan cannot be read twice, a simple plan is used (every code
  cell of the notebook, or every file you gave).
- **Agent steps** (optional, Setup → Long jobs): each step is an agent turn that can read other files, search the
  code and run a check command (the tests, or the code) before it answers, never changing files itself; with its own
  limits (tool turns, tokens, time). When it gives nothing, the step is done with one plain call.
- The model clients report typed errors (status, Retry-After, temporary or not) and follow Retry-After in their own
  quick retries.

## 0.43.1 — Long jobs: notebooks and repositories, step by step

- **`/job <goal>`**, with a notebook or files attached, or none for the whole repository; the assistant also starts
  a job itself (the `start_job` tool) when you ask for a long rewrite. The work is not limited by the model's context
  or output: the **lead model plans** (cell by cell for a notebook; file by file for a repository, big files in
  parts), the **worker model does each step** with the goal, the plan with what is done, the **journal** (one note per
  finished step: what it did and the names it introduced) and only its own cell, file or part with its neighbours,
  and the **lead model reviews** and can send steps back with a fix.
- Each step is checked (Python syntax, JSON, not empty, not shortened with “…” or “rest unchanged”) and retried with
  the error; cut output continues in parts and is joined. Notebooks are written back as valid `.ipynb` (metadata kept;
  changed cells lose their old outputs).
- The state is saved after every step in `.swarmlab/jobs/`: **`/job resume`** continues an unfinished job (finished
  steps are not redone; failed ones are tried again); **`/job status`** lists the jobs. The result is shown as diffs
  to approve (⚡ Auto applies them), with a table of every step and its note.
- Setup → Long jobs: steps at once (different files only), review rounds, tries per step, steps at most, lines per
  part. With a known context window, steps and parts are sized for it.
- New test: `longJobSim`.

## 0.43.0 — Tasks, documents, browser, cited answers, and self-hosted models

Everything below up to the 0.41.0 entry is part of this release. Main points: the Tasks and Make tabs, `/task`;
long ASD-STE100 reports (`/stereport`), live presentations (`/livedeck`) and `/build`; a browser for screenshots and
pages (`/screenshot`); cited answers with verified citations; Work on its own (⚡ Auto); a working card with live
tokens; complete answers by default and an explanation instead of “No answer”; helpers for smaller models; context
windows per model for self-hosted models (LiteLLM, vLLM, Ollama), with cut answers continued in parts; file
metadata; the source-available Swarm Lab License. Settings wording is now precise throughout.

### Cut answers continue even when the server says “stop”

- **Setup → Context windows per model → Continue a cut answer when**: *the server says it was cut* (default, as
  before), *it used all its tokens* (also when the answer used about all its output tokens, or filled the model's
  window, though the server says “stop”: some servers and proxies do), or *it also looks unfinished* (an open code
  block, or a sentence that stops in the middle). Up to Max continuations times. Models with a known context window
  use the second choice on their own.
- Better joining of the parts: the continuation starts by repeating the last words written, and the parts are
  joined on that overlap, so a cut inside a word and a cut between words both read right (before: “thenconfigure”).
- An answer that still stops in the middle gets a **Continue** button.

### Big attached files are shortened to fit, not removed

- Fixed: when a message did not fit the input limit (Max input tokens, or a model's context window), every attached
  file was removed, including the one you had just attached; the model only saw “(attached files removed from
  context)”. Now files attached to earlier messages go first, and the files of the message being answered are
  **shortened to fit**: each keeps its beginning and says where it was cut, so the model reads the rest from the
  file (read_data or read_file). Only if even that cannot fit are they removed.
- With context windows on and a small window, big files are read in smaller parts (about a quarter of the window
  each) and the agent goes on with start_line: nothing is lost, it is read in more steps. With the feature off, or
  a model with a large window, files are read exactly as before.

### Context windows per model (for self-hosted models)

- **Setup → Context windows per model** (off by default: nothing changes for any provider). For self-hosted models
  with a small window shared by the prompt and the answer (LiteLLM, vLLM, Ollama…):
  - **Ask the server**: each model's limits are read once from LiteLLM's `/model/info` (`max_input_tokens`,
    `max_output_tokens`), or from vLLM, LM Studio, OpenRouter and Ollama (`num_ctx`), and kept across restarts.
  - **My list**: `model=window[/max answer]`, for example `llama-3-8b=8192/2048`, `qwen*=32k/4k`; it is used first.
  - Each call is fitted to its model: the prompt is summarized or trimmed to leave room for the answer, the answer
    asks for the room that is left (within the model's own limit), cut answers continue in parts (Max continuations),
    and file reads get smaller for small windows. Models with no known window are never limited.
  - **Check the limits** shows, for each model in use, its window, its longest answer and where it came from; the
    Output panel logs what the server reported.
- New test: `contextWindowsSim` (also proves that off sends exactly the same requests as before).

### A working card while the assistant works

- While the assistant works, a **working card** stands in the conversation where its answer will come: an animated
  status (*Thinking*, *Working*, *Changing files*, *Running*, *On the web*, *Writing*, *Waiting for you*), the elapsed
  time, what it is doing now (*📄 read src/auth/login.ts*, *✍️ 412 tokens · 56 tok/s*), a chip for each step done
  (✏️ changed files, ▶ commands with their exit code, ✅ checks), this message's calls, tokens and cost, and the
  activity log folded under it. It turns yellow when an approval waits for you, and goes away when the answer comes.
  It keeps itself in view unless you scroll up to read; animations stop with the system's reduced-motion setting.
- The live token line and the activity lines are inside the card now, so the information is in one place.

### Complete answers, no more empty “No answer”

- Fixed: “No answer” after a good answer. When a model wrote its answer together with its suggested next steps,
  Swarm Lab made one more call; the model had nothing to add, replied empty, and the answer it had written was
  lost (and “continue” then made it repeat itself). Now the answer is kept, and that extra call is not made at all:
  it sent the whole conversation again for nothing (in a long chat, most of the cost of the message).
- Fixed: answers too short. The assistant's instructions ended with a fixed “Be concise”, whatever Answer length
  said. Now **Normal** asks for complete answers (the explanation, steps, reasons and details that matter, without
  padding), **Detailed** for step by step with reasons, examples and edge cases, **Short** for about 150 words.
- New rule: never repeat an answer already given; “continue” goes on from where it stopped.
- **Answer length** is now also in Setup → Chat and tasks (with where the token limits are); the chat's Context
  button names what is inside it.

### Answers no longer lost after their next steps

- Fixed: “No answer” after a good answer. When the model wrote its answer and its next steps (`suggest_next`) in
  the same reply, Swarm Lab made one more call; the model, with nothing to add, replied empty, and that empty reply
  replaced the answer. Now the turn ends right after wrap-up tools (`suggest_next`, `remember`) when the answer is
  written: the answer is shown, and the extra call is not made (it sent the whole conversation again: with a long
  chat, most of the message's cost). And when a last reply is empty, the text the model wrote earlier in the turn is
  kept instead of “No answer”.

### Live line fix, /task and /tasks

- Fixed: the live line kept saying “writing” after the model had finished its call (while tools ran, while waiting
  for an approval, until the whole answer was done). Now “writing” shows only while tokens arrive; when a call ends,
  or no tokens come for 2 seconds, the line keeps only this message's totals, and it goes away with the answer. The
  same fix for task threads and the task list (“working…” between calls).
- `/task <title>[: instructions]` starts a task on its own thread; `/task later <title>` puts it in Up next;
  `/tasks` opens the Tasks tab. The chat help now lists `/review`, `/task` and `/tasks`.

### Browser, screenshots and /build

- **A browser for agents and for you**, with your own Chrome, Edge or Chromium (nothing is downloaded; Setup →
  Browser → Browser path when it is not found). Each page opens in a fresh, temporary profile, without your cookies,
  logins or passwords, and it is deleted afterwards.
  - `screenshot_page` (agents): a workspace file (`site/index.html`), a local server (`http://localhost:3000`) or a
    web page; full page or window, any width (390 for a phone). The picture is saved in `.swarmlab/screenshots`, shown
    to models that can see, and shown in the answer. Console errors, failed files and uncaught exceptions are listed.
  - `browse_page` (agents): a page read after its JavaScript ran: title, visible text, links, console errors.
  - `/screenshot <path or address> [phone] [window]` in the chat, without the model.
  - Internet pages ask once per site and session (⚡ Auto answers it) and are marked as written by others; Setup →
    Browser can limit it to workspace files and local servers. Files outside the workspace are refused.
- **`/build <file> <what>`**: a file planned in parts, then a skeleton with one marker per part, then each part
  written with the file so far in view. An HTML page is then opened in the browser: its screenshot and console go
  to the model, which names the parts to fix, and only those are written again (Setup → /build: rounds, parts).
  The whole file is shown as one change to approve; the last screenshot is in the answer.
- Make tab: **Build a file** and **Screenshot** cards.
- New test: `browserSim` (uses a real browser when CHROME_PATH is set or one is installed).

### Cited answers

- **Cited answers** (Chat settings and Setup → Chat and tasks; off by default): answers explain step by step, and each
  statement ends with its source: `[src/auth.ts:42-58]`, and with *Everything* also `[docs/manual.pdf, p. 4]`,
  `[deck.pptx, slide 3]` and `[https://example.com/page]`.
- Each citation is a link to the exact place: a file opens with those lines selected; a PDF opens at its page (with
  viewers that follow #page) and the page or slide is named; a web page opens in your browser.
- Each citation is **checked** against what was really read in that answer: **✓** read, **⚠** the file exists but
  those lines (or that page) were not read in this answer, so open it to check, **✕** no such file or past its end
  (struck through, not clickable). A **Citation check** under the answer lists them, with **Wrong source** (the model
  finds the right one and corrects the answer) and **Use this** (points your next message at that place).
- With citations on, files are read with line numbers, so citations point to the right lines. Citations inside code
  are left alone. Attached files count as read.
- New test: `citationsSim`.
- Fixed: some hidden parts of the panel were still shown, because their layout style won over `hidden`: the new task
  form, the live token line, the slide rewrite box, and the empty compaction chip in the chat header (also in 0.41).
- README: a **New in 0.42** section with a screenshot of the Tasks tab (`docs/images/tasks.png`).

### Helpers for smaller models, STE reports, live presentations, tasks, work on its own, live tokens

New **Setup → Helpers for smaller models**: optional help for Mistral, Gemma, Llama, Qwen, Phi and other open
models, so they make fewer mistakes and finish in fewer steps. Off by default; you choose which helpers to use, and
for which models (**Recommended**: only the model families in your list; **For every model**; **Off**).

- **Repair tool calls**: broken JSON (trailing commas, single quotes, unquoted keys, a fence or text around it) and
  near-miss tool names (`readFile` → `read_file`) are fixed instead of failing. Works in native and text tool modes.
- **Simple working rules**: six short, numbered rules added to the instructions.
- **Shorter tool descriptions** (off by default): less to read on each call.
- **Stop repeated calls**: the same tool call with the same input is not run a third time, until a file changes.
- **Forgiving edits**: an `edit_file` whose old text differs from the file only in spaces or indentation finds its
  single place, and the new text is re-indented to match. Ambiguous matches are never guessed; you still see the diff.
- **Bigger model after failed tool calls** (default 3 in one message): uses Automatic model choice when it is on,
  otherwise moves from the worker model to the lead model.
- **Quick check after edits**: a fast command (for example `npx tsc --noEmit`) after each round of edits; its errors
  go back to the model with the edit.
- Every helper action shows in the log and the step map. Bench setups take `"helpers": "off" | "recommended" | "all"`,
  so you can measure the difference on your own tasks. The server uses the same settings.
- New test: `helpersSim`.

**Metadata: what happened, and what your files say about themselves**
- **Under each answer**: what the helpers did (*helpers: 2 repaired, 1 edit matched*); **details** lists each action.
  The Bench grid counts helper actions per run, and run metrics carry them.
- **File details** of attached files and files read with `read_data`: title, author, dates, pages, slides, sheets,
  words, picture size, from PDF, Word, PowerPoint, Excel, OpenDocument, pictures and Markdown front matter.
  **ⓘ** on an attachment shows every detail, the citation line, and which details go to the model.
- **File details to the model** (Setup → Quality and learning): *what a citation needs* (default), *all details*
  (also who last changed it, the company, the program), or *none*. Private details never go by default.
- **Record answer outcomes** (on): one line per answer in `.swarmlab/learn/outcomes.jsonl` with the models, helper
  actions, verified or not, tokens, cost and time. No message text or file content.
- New test: `metaSim`.

**Long ASD-STE100 reports: `/stereport <topic>`**
- Attach your files and send `/stereport <topic>` (or `/stereport 8 <topic>` for 8 sections). The report is written
  in steps that also suit smaller models: notes from each file, part by part, with page numbers; an outline; each
  section with citations `[S1, p. 4]` and a Mermaid diagram where it helps; the ASD-STE100 check of each section and
  one repair pass; a summary; the references from the files' own details; and a check table (findings before and
  after, sources cited, diagrams, STE score).
- Every fact must come from a source: citations to no source are removed and reported; sources never cited are listed.
  Broken diagrams are removed instead of breaking the export.
- With web research on, web pages are sources too (`[W1]`), marked as written by others.
- Sections are written in parallel (Model calls at once), the cost shows under the answer, Stop ends it, and the
  report is saved in `.swarmlab/out/reports/`. Save as Word or PDF with the template "ASD-STE100 technical".
- Setup → Long ASD-STE100 reports: sections, repair passes, web pages, author.
- New test: `steReportSim`.

**Live presentations: `/livedeck [ste] [slides] <topic>`**
- The plan comes first (slide titles), then the slides one by one, in a panel above the chat input. You change
  anything while it writes: edit a slide's title, content or speaker notes; lock it; add, delete or move slides;
  **Rewrite…** one with an instruction (*one bullet only*, *add the costs*); pause and resume; stop.
- Before each slide the deck is read again, so your changes count at once. A slide you type in is marked yours as you
  type and is never written over, even if the model was writing it at that moment.
- Slides use your attached files (and web pages with web research on) with citations, tables and Mermaid diagrams;
  `ste` writes them in ASD-STE100. At the end the deck is an answer in the chat (Save as PowerPoint, with the speaker
  notes) and a file in `.swarmlab/out/decks/`. Change it more, then **Put this version in the chat**; add slides,
  then **Write the rest**.
- New test: `liveDeckSim`.

**Tasks: one chat, many tasks**
- New **Tasks** tab next to Chat. Talk to the assistant as usual: it puts separate pieces of work on the list with
  the new `create_task` tool, one task each, and each runs on its own thread (its own conversation, the same tools,
  permissions and approvals) while you keep talking.
- **Active**: *Working* (with what it is doing now), *Ready for review* (with its last question, for example
  *Which cover should I take forward?*), *Failed*, *Stopped*. **Up next**: tasks the assistant suggests, waiting for
  your **Go ahead**. **Done**: tasks you checked. A badge on the tab counts tasks ready for review.
- Open a task to read its thread, follow its steps live, send it a message (an answer, a change), stop it, run it
  again, or mark it done. Files changed, verified or not, calls and cost show at the end of the thread.
- **＋ Task** adds one yourself. Tasks are kept in `.swarmlab/tasks/tasks.json`; after VS Code closes, a working
  task comes back as Stopped. **Tasks working at once** (1 by default, up to 4).
- New **Make** tab: cards for a long ASD-STE100 report, a live presentation (also in STE), a quick report, an analysis,
  an STE procedure and a task; each puts the command in the chat input.
- New test: `tasksSim`.

**Work on its own, live tokens, and no more silent “(no answer)”**
- **⚡ Auto** next to Send, and **Work on its own** in the chat settings and Setup → Chat and tasks: *Off* (you review
  each edit and command), *Edits* (edits and file changes apply on their own, commands ask), or *Everything* (no
  review: edits, commands and runs go ahead, questions get the recommended option, and at the step limit it continues
  on its own, up to 3 times). Each automatic action is written in the chat (*✓ auto: Apply — …*). Anything marked as
  impossible to undo still asks you, in every mode. The same applies to tasks.
- **Live tokens**: replies are streamed (Anthropic, OpenAI-compatible servers such as OpenRouter, Ollama, vLLM, LM
  Studio, and VS Code's models). Under the chat: the model, the tokens written so far (and thinking), tokens per
  second and time, and this message's calls, tokens in and out and cost so far. Task threads show it too. A server
  that answers without streaming is read as before; one that refuses the usage option is asked without it. Server
  jobs and the Bench do not stream. Setup → Chat and tasks → *Show tokens live* turns it off.
- **No answer, explained**: instead of “(no answer)”, the chat says what happened and what to do: the model spent
  its output tokens on thinking, wrote only thinking (or never closed it), returned an empty reply, was stopped by a
  content filter, refused, or ended on tool calls. Below: the model, stop reason, tokens, the content it returned,
  its thinking and raw text. The thinking that OpenRouter, DeepSeek, Qwen and vLLM give apart (`reasoning`,
  `reasoning_content`) is now kept for this.
- New test: `liveSim`.

## 0.41.0 — Quality and learning

New **Setup → Quality and learning** section: every feature has its switch there.

**Decisions** (from "Structure Tax", arXiv 2610.12056: asking for the answer before the reasoning lowers accuracy,
above all for small models)
- **Reason before the answer** (on): chat-model decisions write a short `reason` first, then the choice.
- **A very short reason counts as unsure** (on): under 4 words, the normal path runs instead.
- **Confidence needed when a chat model decides** (0.6, stricter than the normal 0.5): chat models' stated
  confidence tracks correctness poorly. Scale: 1 = certain, 0 = an even split; 0.5 ≈ 90/10, 0.6 ≈ 93/7.
- Workflow steps keep `DECISION:` as the last line (reasoning first, verdict last); a test guards it.
- Decision events now carry the confidence, the reason and any warning flag.

**Measure on your own model**
- **Compare output formats**: free text vs JSON answer-first vs JSON reason-first, on 20 built-in questions (math,
  knowledge, logic) or yours in `.swarmlab/format-check.jsonl`. Format followed and correct are counted separately,
  with the warning signs: reason length, and a reason whose result disagrees with the answer.
- **Server quality report** (`GET /v1/quality`, `?format=md`): decision calibration (stated confidence vs good
  outcomes) and **approved, then failed** (jobs where a person approved steps and the work then failed). The server
  keeps the log in `<dataDir>/quality/` (switch: **Keep a decision and outcome log**, on). API level 4.

**Keep your own skills** (from "What Human-AI Interaction Leaves Behind", arXiv 2610.18765)
- **Chat learning mode** (off): *Hints* (guiding questions, the full solution only when you ask) or *Think first* (it
  asks your idea first, then compares). Chat only, never server jobs.
- **Track how I rely on the agents** (off, this computer only): time to answer approvals, diffs opened, a weekly
  trend: **My AI reliance report**, **Delete my reliance record**.
- **Reviewer check**: a copy of ~30 lines of your real code with one planted mistake (comparison, off-by-one, and/or,
  true/false; never inside strings); find the line. Your files are never changed. **Reminder every N days** (0 = off)
  measures it again later, as the research recommends.
- Studio: **Plan an AI skills pilot for a team** writes `pilot-plan.md` (tasks without AI, two ways of using AI,
  measures, Day 0 and Day N, the accepted gap decided in advance, the decision rule) and checks each part is there.

## 0.40.5

- **`mode: "auto"` for server jobs**: a decision picks single, tree, swarm or graph for the task, with the same
  criteria as the chat's automatic runs. The server's decision model decides when it is on (Setup → Decisions, run
  mode point); otherwise the worker model. Graph is offered only when a workflow exists. An unsure or failed decision
  gives **single** (the cheapest). The job says what was chosen and why: an event ("Automatic mode: tree …"),
  `result.chosenMode`, and "auto → tree" in job lists.
- Server tab: **Organization → Automatic (a decision picks)**; dashboard: **auto**. Python: `mode="auto"`,
  `Result.chosen_mode`; `swarmlab submit --mode auto`. The API lists `auto` in `/v1/capabilities` modes.

## 0.40.4

- **Fixed: "could not copy … for its snapshot: Cannot copy … to a subdirectory of self"** when the server's data folder
  (`swarmlab-data/`) is inside the project folder, which is how VS Code sets it up. The snapshot copy now skips the
  data folder before entering it.

## 0.40.3

- **Fixed: server agents said "no workspace tools are available"** and could not read, change or test files. Setup →
  Tool mode **none** (often chosen in the chat to get past the reasoning-effort error) was copied to the server by
  0.40.1. Server jobs now keep their tools (Tool mode "text" is still copied). An existing `swarmlab.server.json` is
  corrected at the next Start. A job that does run with tool mode "none" now says so in its events.
- **Fixed: every hand-off between agents waited for approval** on the server ("waiting for approval: planner → fixer").
  Setup → Review messages is a chat setting and is no longer copied (server default "off"; a job can still ask).
- **Fixed: snapshot failed with "'python/' does not have a commit checked out"** when the folder contains another Git
  repository (a subfolder with its own `git init`). The snapshot is now taken from a private copy without `.git`
  folders; nested repositories' files are included as ordinary files. Your folders are only read.

## 0.40.2

- **Fixed: "python -m unittest" exited 127 in server jobs** where only `python3` exists (most macOS and Linux
  machines). Job commands now find `python` and `pip` (aliases to `python3` / `pip3`; on Windows, `python3` → `python`).
  Names that exist are not touched; a project venv still comes first.
- **Fixed: Studio and jobs on a folder without Git history** ('Repository "clients" … cannot resolve base reference
  "HEAD"'): a folder from a downloaded source ZIP, or one where `git init` ran but nothing was committed. Such jobs
  now work on a private snapshot of the folder (in the server's data folder, refreshed at each job, without
  `node_modules`, virtual environments, build output or the server's own data). The folder is not changed; changes come
  back as `changes.patch`. A note in the job says so. `swarm-lab check`, `run --repo-path` and Python
  `SwarmLab.local()` accept such folders too (with a note) instead of refusing them.
- **"succeeded" no longer hides rejected work**: a workflow that ended because a loop reached its limit (review
  rejected → implement again → … → limit) is marked **⚠ not accepted** with the reason, in the Server tab and on the
  dashboard. Python: `Result.accepted` and `Result.warning`; `Result.ok` and `check=True` treat it as not OK.

## 0.40.1

**Fixed: server jobs failed with "Function tools with reasoning_effort are not supported … use /v1/responses or set
reasoning effort to none"** (OpenAI GPT-5 models on /chat/completions). The chat worked because Setup → Reasoning
effort "none" was sent with every request; the server never got it: Start local server copied only the provider and
the models into `swarmlab.server.json`.
- **The OpenAI-compatible client recovers by itself**: on that error it retries with `reasoning_effort: "none"` and
  keeps it for later calls; a model that does not know `reasoning_effort` gets the request without it. Chat and server.
- **All of Setup goes to the server** on every start: provider and models, reasoning effort, extra request fields,
  extra headers, key header, limits (steps, agents, tokens, parallel calls), tool mode, answer length and style,
  automatic code context, command approvals and allow-list, message review, code search, the decision model,
  automatic model choice (with prices), memory. Repositories, access keys, triggers, store and port stay as you set
  them. Setting `swarmLab.server.syncSetup`: `all` (default), `models` (as before), `off`.
- **The first Start creates the configuration from Setup and starts at once** (before: a second click).
- **📄 Create run files** (Server tab) writes `swarmlab-run/`: `start-server.sh` / `start-server.cmd` (keys from
  `.env`), `.env.example` (the variables this configuration needs), `swarmlab.client.json` (server address, key
  variable, your Setup as job defaults), `example.py` and the Python library (no pip install), and a README.
- Python: `SwarmLab.from_config()` reads `swarmlab.client.json`; its `defaults` go into every job (keywords win;
  `settings` and `approvals` are merged). The library now ships inside the VSIX.

## 0.40.0

**Save chat answers as documents.** Under every answer: **Save as PowerPoint · Word · PDF · Excel · More…**. A dialog
lets you choose the format and the template, change the title, the author and the text before saving, see the slides
PowerPoint will get, and check the text against ASD-STE100. Diagrams (Mermaid, SVG) are drawn and put in as pictures.
- **PowerPoint**: a real deck (theme with the template's colours and fonts, a slide master, four layouts). Slides fill
  the layouts' placeholders, so every title, bullet, table and note is edited in PowerPoint like a hand-made slide, and
  a new theme restyles the deck. One slide per `#`/`##` heading or `---`; tables, diagrams and code get their own slide;
  numbered steps use PowerPoint numbering; paragraphs that start with `Notes:` become speaker notes.
- **Word**: real styles (Title, Heading 1-4, lists, Code, Quote, Notice, table style), pictures with captions,
  hyperlinks, header, footer with "Page n of N". A template can name your own `.docx` or `.dotx`: its styles, theme,
  headers, footers and page setup are kept and only the body is written.
- **PDF** with selectable text (pages, tables with repeated headers, code, diagrams, page numbers; Western European
  characters), **Excel** (a sheet per table, numbers stay numbers, filter and frozen header; the text on a Document
  sheet), **HTML** (one file, diagrams inside), **Markdown**, **text**, **Jupyter notebook** (Python code as code
  cells, diagrams as attachments), **JSON** (blocks, tables, slides) and **CSV**.
- **Templates**: Swarm Lab, Corporate, Minimal, Dark, Forest and **ASD-STE100 technical** (numbered headings, Arial, a
  check report saved next to the document). Your own in `.swarmlab/templates/documents/*.json` (colours, fonts, size,
  page A4/Letter, slides 16:9/4:3, header, footer, numbered headings, Word file); **Edit template…**, **New…** and
  **Word file…** in the dialog. A template can `extend` another one.
- **Chat commands**: `/report`, `/slides` (`/presentation`, `/deck`), `/analysis <topic>` ask for a complete,
  structured document; `/ste [procedure|description|rewrite|report] <topic or text>` writes in ASD-STE100 Simplified
  Technical English; `/stecheck` checks the last answer.
- **ASD-STE100 check** (local, no model): sentence length (20 words in procedures, 25 in descriptions), paragraphs of
  more than 6 sentences, passive voice, -ing forms, two instructions in one sentence, common unapproved words and
  phrasal verbs (with the STE word to use), warnings that do not start with a command. A score and the findings, with
  "Ask the assistant to fix…". The STE dictionary remains the reference for word meanings.
- **Export this chat…** saves the whole conversation in any of these formats (was Markdown only).

**Servers: replace the old one, several ports.**
- **Start local server** stops an old Swarm Lab server that holds the port (an older version, or one started in a
  terminal or another window) and starts the new one at once; when this window's server runs, Start restarts it.
  Another program on the port is never stopped without asking. Setting `swarmLab.server.replaceOld` (on).
- **↻ Restart** and **✕ Kill old server** in the Server tab. Kill stops the server at the Server tab's address,
  politely first (`POST /v1/admin/shutdown`), then through its process (also for versions without that endpoint).
- **Local servers**: start more servers with the same configuration on other ports (**Start on port**), each with its
  own data folder (`<dataDir>-<port>`); **Use** sends jobs to one, **Stop** / **↻** per server.
- Server: `POST /v1/admin/shutdown {"restart": true|false}` (admin key); `--wait-port SECONDS` waits for a port an old
  server is still freeing; `/v1/health` reports `pid` and `startedAt`; `<dataDir>/server.pid`. The dashboard has
  **↻ Restart server** and **■ Stop server**. API level 3.
- Version 0.40.0 across the extension, the server and the Python client.

## 0.39.2

**Fixes**
- Studio: the Settings box (access key) was always open over the page, greyed it out, blocked clicks, and its
  **Close** button did nothing. Hidden elements now stay hidden.
- Studio builder: a 🎯 Numbers gate step showed "🤖 An agent does something" in its kind menu and could not be
  switched back to a gate once changed. The menu now lists all five kinds with the same emojis as the buttons
  (🤖 ✅ 📓 🎯 ⚙️).

**Easier to find and to run on several ports**
- `--port N`, `--host ADDRESS` and `--data-dir FOLDER` for `serve`, `api`, `worker` and `check`, so one
  configuration can run on several ports at once (each with its own data folder).
- The startup line shows the server version and the Studio address; `GET /v1/health` returns `version`.
- The dashboard links to **✦ Studio** and **Decisions**; the Decisions page links to the Studio.

## 0.39.1

- **Studio and dashboard no longer stay empty when the browser blocks storage** (VS Code's Simple Browser, private
  windows, blocked site data): the page crashed before loading the gallery. The access key is then kept for the
  page's lifetime only.
- **A clear message when the server's port is taken** (for example by an older Swarm Lab server, or the one started
  from VS Code), instead of a crash with a stack trace.
- Version 0.39.1 across the extension, the server (`SERVER_VERSION`) and the Python client (`swarmlab`).

## 0.39.1

- Version bump of 0.39.0 (extension, built-in server, Python client). No functional changes.

## 0.39.0

**Environments.** A job can prepare its own environment before its agents start, and every command of the job
(agents' commands and tests, workflow command steps, the final check) then runs inside it.
- Presets detected from the project (`auto`) or named: `node`, `python` (own virtual environment), `go`, `rust`,
  `java`, `dotnet`, `vscode-extension` (install, compile, virtual screen, cached VS Code downloads), `none`.
- Runtimes: `local` (the job's own folders, shared download caches, optional isolated HOME) and `docker`/`podman`
  (any image; workspace, job folder and cache mounted; optional `network: false`).
- From the job, its profile, its saved workflow, the repository's `.swarmlab/environment.json`, or the server's
  default; named server environments. Server rules: `allowSetup`, `runtimes`, `docker.allowImages`.
- What the setup created is kept out of the job's commit; tracked files it rewrote are restored.
  `result.environment`, the `environment.log` artifact and `environment` events.
- `swarm-lab env PATH`: an environment and commands, without agents (`--test`, `--isolated`, `--json`).

**Studio, ready workflows, native notebooks, checks for small models.**
- `/studio`: a gallery of 20 ready workflows with forms, an inbox for what needs a person, results shown as text,
  tables and notebooks with charts, and a builder with emoji steps (🤖 agent, ✅ check, 📓 notebook, 🎯 numbers gate,
  ⚙️ command) and a live diagram.
- Banking and the model lifecycle: train until targets are met, independent validation pack, go-live readiness
  (champion / challenger, change request with rollback, never deploys), monthly monitoring, credit memo, AML / fraud
  alert review pack, reconciliation; plus draft replies to customer messages. Decisions stay with a named person.
- `swarmlab-nb` runs notebooks cell by cell with parameters (outputs and charts kept, each failing cell reported);
  `swarmlab-check` checks results in plain words, now with `metrics` (thresholds) and `compare` (champion /
  challenger). Rules reach commands as words (`auc:ge:0.75`), so gates never stop for an approval.
- A `check` on any agent step: when it fails, the agent gets exactly what it said and retries (`retries`, up to 5),
  then `onFail`. A model per step (`lead` / `worker`).
- Schedules in the server (cron with time zones) and an outcomes report (runs, success, cost, time saved).
- Python: `run_template`, `templates`, `schedule`, `outcomes`; steps `notebook`, `gate`, `compare`, `ensure`;
  `check=` / `retries=` on agent steps; `Environment.notebooks_env()`.
- Fixes: package downloads retry (pip, npm); the server keeps idle connections 65 s (a connection-reset race);
  test suites delete their temporary folders (a full run left ~700 MB).

**A real editor in the environment** (`environment.vscode`, on by default with the `vscode-extension` preset).
- VS Code, Insiders or VSCodium downloaded for the OS and processor (Linux, macOS, Windows; x64, arm64; the Linux
  build in containers), cached and shared by jobs, the newest cached one used offline; or an installed editor
  (`executable`: code, codium, cursor, windsurf, an .app, Code.exe), also used when a download is impossible.
- The workspace's extension packaged with vsce; .vsix files and marketplace ids installed into the job's own folder.
- A smoke check inside the editor: extensions activate, contributed commands registered, chosen `commands` run (with
  their results), a `check` script run with the editor's API. A baseline before the job, a final check after it;
  `require: regression` (default) fails a job that breaks a working extension, and it is not pushed.
- `swarmlab-vscode` (check, smoke, package, install, run, info) on the job's PATH and as its test command, for agents
  and workflow steps; `SWARMLAB_VSCODE_EXECUTABLE` for the project's own tests; the editor linked into
  `.vscode-test/` for `@vscode/test-electron`; `.vscode-test/` kept out of results.
- Works when the server runs inside VS Code (the editor never inherits ELECTRON_RUN_AS_NODE; `node` provided).
- Docker: the editor's system libraries and xvfb installed with apt-get, dnf or apk.
- Verified with a real VSCodium 1.140: a sample extension (activation, commands, results, a check script, a broken
  activation and a missing command caught with their reasons), Swarm Lab's own VSIX (28 commands), and Swarm Lab's
  real-editor test suite (8 checks) run against the environment's editor.
- Fixed: the documentation claimed a VSCODE_TEST_CACHE variable that @vscode/test-electron does not read.

**Server.**
- Saved workflows: `GET/PUT/DELETE /v1/workflows/:name`, `GET /v1/workflows`, `POST /v1/workflows/validate`. A
  saved workflow carries its agents, prompts, environment, checks, settings and approvals; jobs use it by name.
- `GET /v1/capabilities` (what the server allows) and `POST /v1/validate` (check a job without queueing it).
- `swarm-lab run` needs no configuration file: `--spec` (the API's job JSON), `--repo-path`, `--env`, `--set`,
  `--provider/--model/--base-url/--api-key-env`, `--data-dir`, `--out`, `--jsonl`, and `--approve
  ask|auto|reject|stdin` (approvals were previously left waiting in CLI runs).
- `swarm-lab workflow validate FILE`, `swarm-lab version`. Profiles may hold `environment`, `web` and `data`.

**Python.** The new `swarmlab` package (`pip install ./clients/python`): `SwarmLab` for a server or
`SwarmLab.local(repo)` without one; every job option as a keyword with early errors; `Agent`, `Workflow` (auto-linked
steps, offline validation, Mermaid diagrams, save/load), `Environment`, `Settings`, `Approvals`…; `Job` and `Result`;
approvals answered by Python functions; `run_many`; `python -m swarmlab`. `swarmlab_client.py` gains `environment=`,
`capabilities()`, `validate()` and workflow methods.

**Tests.** `editorSim` (61 checks offline with a fake editor and a local download server; with
`SWARMLAB_REAL_EDITOR=1` it downloads VSCodium and checks a real extension), `environmentSim` (127 checks), `pythonLibrarySim` (25 live checks through the library, server and local),
`test_swarmlab_package` (29 offline tests).
