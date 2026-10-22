# Changelog

## 0.42.4 — Live line fix, /task and /tasks

- Fixed: the live line kept saying “writing” after the model had finished its call (while tools ran, while waiting
  for an approval, until the whole answer was done). Now “writing” shows only while tokens arrive; when a call ends,
  or no tokens come for 2 seconds, the line keeps only this message's totals, and it goes away with the answer. The
  same fix for task threads and the task list (“working…” between calls).
- `/task <title>[: instructions]` starts a task on its own thread; `/task later <title>` puts it in Up next;
  `/tasks` opens the Tasks tab. The chat help now lists `/review`, `/task` and `/tasks`.

## 0.42.3 — Browser, screenshots and /build

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

## 0.42.2 — Cited answers

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

## 0.42.1 — Helpers for smaller models, STE reports, live presentations, tasks, work on its own, live tokens

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
