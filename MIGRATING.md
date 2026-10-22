# Moving to Swarm Lab from Cline, Roo Code or Continue

Most of your setup moves over with one command. This page shows where each old setting goes, and what is different.

## The one command

In VS Code, open your project, then Command Palette → **Swarm Lab: Import settings from Cline, Roo Code or Continue**.

1. Choose the tool, or **All three**.
2. For Roo Code, you can pick its settings export (optional; see below).
3. Swarm Lab shows what it found and asks before writing anything.

From a terminal, in your project folder:

```bash
node migrate-to-swarmlab.mjs                      # preview: writes nothing
node migrate-to-swarmlab.mjs --write              # copy everything found
node migrate-to-swarmlab.mjs --write --from roo   # only one tool (cline, roo, continue)
node migrate-to-swarmlab.mjs --write --roo-settings ~/Downloads/roo-code-settings.json
```

| Option | What it does |
|---|---|
| `--workspace DIR` | Use another project folder |
| `--no-global` | Read only the project's files, not `~/.continue` or the extensions' global settings |
| `--force` | Replace files and MCP servers already in Swarm Lab (by default, they are kept) |

**What the import never does:**

- It never copies API keys. Add yours with **Swarm Lab: Set API key**, so they stay in VS Code's secret storage.
- It never changes your old tool's files.
- It never replaces an existing Swarm Lab file unless you pass `--force`.

The report, `.swarmlab/MIGRATION-REPORT.md`, lists everything copied, a checklist of what is left to do by hand, and what has no equivalent. Afterwards, open Swarm Lab's **Check** tab to validate it all.

---

## Cline

| In Cline | In Swarm Lab | Copied automatically |
|---|---|---|
| `.clinerules` (a file or a folder) | `.swarmlab/rules/cline-*.md`, followed by every agent | ✅ |
| Global rules (`~/Documents/Cline/Rules`) | `.swarmlab/rules/cline-global-*.md` | ✅ |
| Workflows (`.clinerules/workflows/*.md`) | Skills: `.swarmlab/skills/<name>/SKILL.md` | ✅ |
| MCP servers (`cline_mcp_settings.json`) | `.swarmlab/mcp.json` (disabled servers are skipped) | ✅ |
| Auto-approved MCP tools | Each server starts at "ask"; set `"approval": "allow"` in the **Tools** tab | Listed in the report |
| `.clineignore` | `swarmLab.rag.exclude` (kept out of code search). To block edits, set `editPaths` per agent | ✅ (search) |
| Provider, model, API key | **Setup** tab, and **Set API key** | ✋ (stored inside VS Code) |
| Auto-approve: edits / commands | `swarmLab.edits`, `swarmLab.commands` (with an optional allow-list) | ✋ |
| Plan / Act | Chat with read-only agents, or a **graph** workflow such as plan → fix → test → review | ✋ |
| Checkpoints | Git safety: each run on its own branch, **Keep / Revert all**; **Undo these changes** in the chat | Built in |
| Browser tool | **🌐 Web** (`web_search`, `fetch_url`) | Turn it on |

## Roo Code

| In Roo Code | In Swarm Lab | Copied automatically |
|---|---|---|
| `.roorules`, `.roo/rules/*` | `.swarmlab/rules/roo-*.md` | ✅ |
| Custom modes (`.roomodes`, global `custom_modes.yaml`) | **Agents**: `.swarmlab/policy.json` (description, tools) and `.swarmlab/prompts/agent-<slug>.md` (instructions) | ✅ |
| Mode rules (`.roorules-<mode>`, `.roo/rules-<mode>/`) | That agent's instructions (built-in modes' rules apply to every agent) | ✅ |
| Mode tool groups: read, edit, command, mcp, browser | The agent's `tools`: read and search tools, file edits, `run_command`, `mcp__*`, `web_search` / `fetch_url` | ✅ |
| `fileRegex` limits on edits | `editPaths` (globs such as `docs/**/*.md`) | ✋ (listed in the report) |
| MCP (`.roo/mcp.json`, global `mcp_settings.json`) | `.swarmlab/mcp.json` | ✅ |
| `.rooignore` | `swarmLab.rag.exclude` | ✅ |
| API profiles | Provider, base URL and models from **Settings → Export** (`--roo-settings`); keys by hand | ✅ with the export |
| Orchestrator (Boomerang) mode | **Tree** or **swarm** runs: a lead hands sub-tasks to agents | Built in |
| Codebase indexing | `search_code` (keywords, meaning, or both) | Built in |

Use a migrated mode in the chat with **Talk to → \<mode slug\>**. In tree and swarm runs, leads see each agent's description and pick the right one.

## Continue

| In Continue | In Swarm Lab | Copied automatically |
|---|---|---|
| `models` (`config.yaml` / `config.json`) | `swarmLab.provider`, `baseUrl`, `leadModel`; a smaller model of the same provider (edit/apply role) becomes `workerModel` | ✅ |
| `apiKey` in the config | **Set API key** (never copied) | ✋ |
| Ollama / LM Studio models | Provider **OpenAI-compatible**, base URL `…:11434/v1` / `…:1234/v1` | ✅ |
| `rules`, `systemMessage`, `.continue/rules/*.md` | `.swarmlab/rules/continue-*.md` | ✅ |
| `prompts`, `customCommands`, `.continue/prompts/*.prompt` | Skills (agents use them when the task matches) | ✅ |
| `mcpServers`, `.continue/mcpServers/*.yaml` | `.swarmlab/mcp.json` | ✅ |
| Embeddings model | `swarmLab.rag.embeddingModel` | ✋ (listed in the report) |
| `@docs`, `@codebase` and other context providers | `search_code`, **Data** (files and folders), **🌐 Web** | Built in |
| Tab autocomplete | Not in Swarm Lab: keep Continue or VS Code's own for autocomplete | — |

---

## What you gain

| You had | Now you also have |
|---|---|
| One agent at a time | **Tree**, **swarm** and **graph** runs, with several agents working at the same time and a cap on parallel model calls |
| Approve or reject a diff | **Edit before applying**, editable commands, and **Edit** on any answer, code block or diagram (the model reads your version) |
| Chat about code | **Data** inputs (Excel, Word, PDF, PowerPoint, notebooks, ZIP files, pictures) and an output folder for results |
| A model per profile | Automatic model choice by task difficulty, cost per answer, daily limits, and optional cheap decision models |
| Trust the output | A **Bench** for your own tasks, verified "done", and an LLM-judge calibration workflow |
| Only in the editor | The same agents as **background jobs** on a server, with API, dashboard and approvals from the browser |

## Questions

**Can I keep using my old tool?** Yes. The import only reads its files, and Swarm Lab keeps its own in `.swarmlab/`. Both can work on the same project.

**Should I commit `.swarmlab/`?** Commit `rules/`, `skills/`, `policy.json`, `prompts/` and `graph.json` to share them with your team. Keep `mcp.json` out of Git if it holds tokens (the report warns you when it might).

**Something did not come over?** Run the import again after fixing the source (`--force` replaces what was copied before). If an old setting is missing here, please open an issue.
