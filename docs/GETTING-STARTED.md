# Getting started with Swarm Lab

[README](../README.md) · [Run modes](RUN-MODES.md) · [Detailed manual](../MANUAL.md)

## 1. Install the public package

Download the 0.42.4 VSIX from [GitHub Releases](https://github.com/joeaelkhoury/SwarmLab/releases).
Use VS Code **Extensions → ⋯ → Install from VSIX…**. Open a small practice folder,
then run **Swarm Lab: Open** from the Command Palette. You do not need npm or
extension source. Source publication is planned for a later update.

## 2. Choose how to learn

- **Offline mock:** explore the interface without a key or model charges. Its answers
  are scripted; it cannot demonstrate real debugging ability.
- **Real provider:** in Setup select your API service or running local model service,
  enter exact lead/worker model IDs, and use **Set API key** if required.
- **VS Code language models:** useful for editor work when your account has access;
  not available to the standalone server.

Save settings, then run **Test connection** and **Test tool calling**. Local model
servers must be started separately. API usage may incur charges.

## 3. Read before changing

Send this in Chat:

```text
Explain the entry points and test setup. Read the files first and name them.
Do not edit files or run commands.
```

Check the activity and compare the answer with the files. If you are using the
mock, treat this as a UI exercise, not factual project analysis.

## 4. Make one bounded change

Save and preferably commit your existing work first. Open Run, choose Single agent,
and give a narrow task with an expected outcome:

```text
Add one regression test for the date parser's empty input. Keep the public API
unchanged. Propose the edit and ask before running the focused test.
```

Use a task that fits your actual project; this example does not create a parser.
Review every proposed diff and command in **Waiting for you**. Reject anything
unrelated. Stop interrupts work but does not reverse changes already made.

Review the final diff, test output, and stop reason. A successful run or test exit
is not a guarantee that the change is correct. Git safety requires a repository
with a commit; inspect run-branch Keep/Revert choices before acting.

## 5. Expand deliberately

- Tree: split independent questions between temporary workers.
- Swarm: let persistent workers exchange findings.
- Graph: configure and save a workflow before running it.
- Server/Python: follow [Python workflows](PYTHON-WORKFLOWS.md); Docker is optional.

Keep edits/commands restricted until you understand their effects. Command
allowlists are not a sandbox, and tests execute project code. Optional MCP tools,
external engines, and Bench have separate permission behavior. Scoped reads are
bounded native single/chat read-only support, not full isolation. Project plan
approval does not authorize commands; requirement status is not verification.

## If you get stuck

Use **Check → Check everything**, then **View → Output → Swarm Lab**. Check the
provider, model ID, loaded local model, and pending approvals. Share only sanitized
errors in [Issues](https://github.com/joeaelkhoury/SwarmLab/issues).
For limits, RAG, routing, Project, permissions, and recovery, keep the
[Manual](../MANUAL.md) nearby.
