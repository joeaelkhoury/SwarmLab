# Programmatic configuration

## Deployment is your choice — Docker is optional

Use the same Python/API job payloads with any of these deployments:

- **Native Node:** build and run the server directly, as described in SERVER-QUICKSTART.md. Docker and PostgreSQL are not required for the single-process file-store server.
- **VS Code:** use the extension's local-server controls, or connect it to an existing server.
- **Optional Docker:** use Dockerfile for a server image, or docker-compose.yml for PostgreSQL, API and workers. This is an opt-in deployment, not a prerequisite for the extension, Python client or native server.

The Python caller connects to the URL you choose; it does not launch Docker. It may run on the host or in a separate container. Inside a container, localhost refers to that container, not the host or another service. Configure container networking and mount paths accordingly.

Worker containers and Git worktrees are not per-job security sandboxes. Limit credentials, mounts, command permissions and network access. Install project-specific build tools in the worker environment. Do not expose an unauthenticated API publicly.

## Configuration layers

| Layer | Controls |
|---|---|
| Host configuration | Provider endpoints and credentials, repositories, worker concurrency, feature gates, setting allowlist, MCP configuration and host restrictions |
| Job fields | Task, mode, workflow, profile, agent policy, prompts, skills, MCP selection, memory, data, checks, hooks, labels and timeouts |
| Job settings | RunSettings values explicitly permitted by the host's allowedSettingOverrides |
| Job provider bindings | RAG model/topK/autoK and decision model/minConfidence, within configured host services |

Not every engine setting is an agent-specific setting. The API and host policy validate what a caller may change; arbitrary keys do not create new capabilities.

## Python examples

The client uses Python 3.8+ and the standard library. These commands do not require Docker:

```sh
python clients/python/configuration_examples.py --list
python clients/python/configuration_examples.py --example graph --dry-run
python clients/python/configuration_examples.py --example single --config my-job.json --submit
```

Examples use the server repository name demo-app, which you must configure or replace. Printing a payload is not an effective-policy preview or proof that your host accepts it. The server validates submissions. The example builder uses the source's default setting allowlist; it does not discover your host's customized policy. The graph example is a small inline workflow, not a parallel fan-out implementation.

For bounded polling and report files, use fix_job.py. Neither example tool automatically answers approval requests.

## Run settings

Authoritative types are in src/core/types.ts; host defaults are in src/server/config.ts.

| Settings | Meaning |
|---|---|
| leadModel, workerModel | Model IDs for lead and worker roles |
| maxStepsPerAgent, maxAgents | Agent loop step and team limits; steps are not a precise conversation-turn count |
| tokenBudget, maxTokensPerCall | Run token allowance and model-call output limit |
| maxContinuations | Continuations after output truncation |
| maxInputTokens | Provider input-context limit; zero means no configured limit |
| maxParallelCalls | Concurrent model calls/Claude Code turns, not tool-call parallelism; zero/unset means no run-level limit |
| sequentialTools | Execute tools from one model answer sequentially |
| allowEdits, allowCommands, commandAllowList | Tool availability and command controls, still constrained by server approval policy |
| useMemory | Engine memory use; job memory settings and host mode also apply |
| defaultEngine | native or claude-code; not a model ID |
| toolMode | native, text or none |
| answerLength | short, normal or long |
| answerStyle | visual or plain |
| chatCompactChars, chatKeepMessages | Chat history compaction controls |
| ragAuto, ragTopK, ragAutoK | Automatic context toggle and numeric retrieval counts |
| costBudgetUsd | Stop based on known model costs; zero/unset means no configured budget |
| finalAnswerOnLimit | Request a best-effort final answer at the step limit |

The default override allowlist is:

```json
[
  "maxStepsPerAgent", "maxAgents", "tokenBudget", "maxTokensPerCall",
  "answerLength", "answerStyle", "toolMode", "maxContinuations",
  "ragTopK", "maxParallelCalls"
]
```

Other settings, including leadModel, workerModel and costBudgetUsd, require explicit host authorization before a job can override them. Do not assume that every key in the Python reference dictionary can be submitted to a default host.

### Costs are not a strict invoice cap

A run-level costBudgetUsd exists. It depends on known model prices; unknown prices do not contribute to known-cost totals. In-flight calls and external tools/providers can incur costs outside that accounting. Inspect reports for unknown-price usage and do not treat this setting as a guaranteed billing ceiling. Experiments separately support maxCostUsd and maxTokens; those are not ordinary top-level job fields.

## Agents and architecture

Choose single, tree, swarm or graph in the job's mode field. A named top-level agent is single-mode only. Graph jobs supply a workflow with start and nodes; graph controls include maxSteps, routes, maxVisits and onLimit. See src/core/types.ts for the exact graph schema.

Agent policy supports description, model, tools, readPaths, editPaths, engine, claudeCode options, toolMode and data. Tool availability depends on role and host policy. Restricted read scopes have additional shared-workspace/mode constraints; not every combination is supported. Token budgets, step limits and concurrency are run settings, not arbitrary per-agent policy keys.

Role and agent prompt overrides use prompts.roles and prompts.agents. Inline skills use name, description and instructions. Job memory may be false or a session/topics object, subject to host memory mode. Data roots and writes, web access, hooks and verification checks remain host-gated.

## MCP

Jobs can select configured servers through mcp.use and add servers through mcp.add. A non-admin key may add remote URLs only for configured mcpAllowHosts. Starting local programs requires an admin key. MCP calls remain subject to approval and irreversible-action rules. Local program paths and dependencies refer to the worker environment, including its container if you chose Docker.

Configure credentials securely on the host rather than embedding them in example job JSON. The helper scripts reject credential/header fields.

## RAG and decision models

```json
{
  "rag": "on",
  "decision": "on",
  "providers": {
    "rag": { "model": "your-embedding-model", "topK": 6, "autoK": 4 },
    "decision": { "model": "your-decision-model", "minConfidence": 0.7 }
  }
}
```

Feature flags accept on, off or inherit. Model bindings require compatible host configuration. RAG retrieval in the server runner is attached to repository jobs; turning it on does not create an arbitrary external knowledge source for a repository-free job.

The host owns embedding/provider endpoints and environment-based credentials. Decision providers are configured on the host (openrouter, typesafe, custom or chat-model). Per-job provider objects accept only the documented model/tuning fields; URLs, endpoints, keys and related transport fields are rejected. These bindings cannot redirect a job to an arbitrary provider endpoint.

## Verification status

Version 0.38.0 adds dedicated runner-level concurrent RAG isolation coverage (70 assertions), server-side execution of all four Python examples (4/4 succeeded with the mock provider), and export/start orchestration coverage (19 checks). Python tests (28), real-provider-runner offline tests (8), compilation and the harness/server/report regression suites passed. RAG cancellation cleanup is tested after retrieval, not during an in-flight embedding request.

Export and start can start a stopped native local server when an existing workspace configuration matches its loopback host and port. It validates workspace trust and the target, shares concurrent startup, bounds readiness checks and exports only after readiness. Missing/mismatched local configuration fails closed; configure and start manually first. Reachable remote servers export without launching locally. Docker remains optional.

Live-provider verification remains blocked: no provider API key was available. The opt-in runner uses an isolated native server, checks an exact answer marker and positive report usage, and never substitutes a mock provider. Supply a minimal provider configuration containing type (anthropic/openai/openrouter), leadModel, workerModel and apiKeyEnv, plus baseUrl if needed. Keyless openai-compatible endpoints are accepted only on loopback. Then run:

```powershell
$env:SWARMLAB_REAL_PROVIDER = '1'
$env:SWARMLAB_REAL_CONFIG = 'C:\\path\\provider.json'
node scripts/real-provider-e2e.cjs
```

This calls the configured provider and may incur charges; token and time limits are not an invoice guarantee. Offline runner tests use a fake HTTP provider and are explicitly not live-provider evidence. Docker deployment, installed VSIX UI and accessibility checks remain unverified.
