# Choosing a run mode

[README](../README.md) · [Getting started](GETTING-STARTED.md) · [Manual](../MANUAL.md)

## Organization, not intelligence level

| Mode | What happens | Useful when |
|---|---|---|
| Single | One agent uses workspace tools | A focused question or small change |
| Tree | Lead delegates independent tasks; temporary workers report back and retire | Parts can be investigated separately and combined |
| Swarm | Lead coordinates persistent workers; workers share a board and ask peers | Findings need to circulate while work continues |
| Graph | Configured nodes and transitions control execution | You need a repeatable workflow |

Tree/swarm leads coordinate rather than reading project files themselves. Tree
workers start without memory and are deleted after answering. Swarm workers remain
available for coordination. More agents add calls, context, and coordination costs;
they do not guarantee a better result. Start with Single.

Graph requires a valid configured workflow, supplied as a saved workflow or an
accepted inline graph on the server. Choosing Graph does not invent that workflow.
Named single-agent selection and graph workflow selection are different controls.

## Manual choice

Choose a mode in Run, or use a Chat slash command:

```text
/single Explain the test setup without changing files
/tree Investigate API and UI validation independently; report findings
/swarm Review error handling and share findings before proposing edits
/graph Review the parser using my saved workflow
```

These explicit choices do not require a decision model. Python job modes are
single, tree, swarm, or graph; the starter CLI does not accept auto as a job mode.

## Ordinary assistant suggestions

The normal assistant prompt says to handle small changes itself and offer/start
a run for bigger work. It can select single/tree/swarm/graph through its run tool.
This is the assistant model's contextual, heuristic judgment—not a deterministic
size classifier, benchmark result, or guarantee of the optimal mode. You can
request an explicit mode instead.

## Optional decision-model selection

The decision model is disabled by default. Once enabled with a usable client,
**Pick the run mode** is on by default; it adds an auto choice to the assistant's
start-run tool. It does not force every task through automatic selection.
The default minimum confidence is **0.5**.

For auto selection, the engine asks which organization fits best, using these criteria:

- Single: a focused question or small change one agent can do alone.
- Tree: independent parts that can run in parallel and then be merged.
- Swarm: larger work where workers must share findings and ask questions.
- Graph: the user's fixed plan/change/test/review workflow—offered only when a
  workflow is available in the run controls.

Below-threshold, missing, or failed decisions do not silently start a Single run.
The tool returns a fallback asking the assistant to choose single/tree/swarm/graph
itself. Tests cover a confident Swarm selection and a low-confidence response
that starts no run. Confidence is not a probability that the chosen organization
will produce correct code. Inspect decision activity and resulting costs.

## Different feature: model routing

Run-mode selection chooses **how agents are organized**. Automatic model routing
chooses **which model handles a task**, using a configured model pool, strategy,
and optional difficulty decisions. A Single run may use routing; choosing Swarm
does not by itself enable routing or select the best model. Lead/worker defaults,
named-agent models, and workflow node models also have their own precedence.

For configuration and permissions, see the [Manual](../MANUAL.md). For API jobs,
exact model overrides, host gates, and approvals, see [Python workflows](PYTHON-WORKFLOWS.md).
