# The public benchmark: when do more agents help, and at what cost?

Swarm Lab can run one agent (Single), a lead with workers (Tree) or a group of peers (Swarm). More agents do not
automatically give better answers, and they always cost more: every step resends the conversation so far. The public
benchmark measures that trade-off on a task set anyone can see and rerun.

## What it is

- **A small project:** `minilib`, a Python 3.9+ library with known bugs and one missing function, no packages needed
  (`media/bench/public/project` in the source).
- **Five tasks, the same for every setup:** fix `money.py`, fix `dates.py`, fix `textstats.py`, make every test pass,
  and add a new function `longest_word`.
- **Graded by tests, some of them hidden.** The visible tests are in the project. Each task also has checks the agents
  never see, so passing means the code is right, not only that it fits the visible tests.
- **Isolated runs.** Each run works in a fresh Git worktree of the benchmark's commit. Commands are limited to the
  suite's allow-list and the test command; nothing waits for you.

## Run it

1. **Bench → Public benchmark…** (or **Swarm Lab: Set up the public benchmark (Single vs Tree vs Swarm)**). Choose an
   empty folder: Swarm Lab writes the project there, commits it, and adds `.swarmlab/bench/public.json`.
2. Open that folder, pick your models (Setup), then **Bench → Run**. Use at least 3 repeats: with fewer, a difference of
   one or two runs is noise.
3. **Copy report** gives Markdown to publish: the setups, models, extension version, operating system, every run's result,
   tokens, cost and time, and the exact steps to rerun it.

The cost forecast appears before the run, and every run stops at `swarmLab.runs.maxCostUsd`.

## Results

No results are published here yet. When you publish yours, include the whole report (not only the pass rates): the
models, the repeats and the cost are what make it comparable. A result is worth publishing when someone else can rerun
it and get close to the same numbers.

## Limits

Five small Python tasks say little about large codebases, other languages or long tasks. Treat the benchmark as a
check of the trade-off on your own models and prices, not as a ranking of tools.
