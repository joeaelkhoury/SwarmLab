# Workflow Harness — Implementation Status

Status: bounded implementation, version 0.38.0. Harness and host-constrained model bindings have simulation coverage, plus dedicated concurrent server RAG isolation tests (70 assertions), all four Python examples executing successfully through the server with a mock provider, and tested cold-start export orchestration (19 checks). This is not full server/editor host parity or live-provider verification.

## Implemented

- `src/panelWorkbench.ts`: named harness editor with single/tree/swarm/graph mode selection, task, lead/worker models, budgets, step/agent limits, tool mode, RAG/decision inherit/on/off switches, host-bound provider fields (RAG model/topK/autoK, decision model/minConfidence), advanced policy JSON and graph JSON. Save/load/run messages are wired. "Run as (single)" writes the top-level `agent` field. "Export and start" posts `srv:exportStart`. Save replies preserve the current draft and errors remain visible.
- `src/vscodeHarness.ts`, `src/extension.ts`: trusted-workspace persistence, explicit overwrite confirmation, host message handling and per-run settings/policy/feature resolution without changing global settings.
- `src/core/harness.ts`: versioned schema, setting-value validation, mode/graph validation, feature flags, explicit multi-agent read-scope rejection, and strict host-constrained provider configuration (`providers.rag{model,topK,autoK}`, `providers.decision{model,minConfidence}`).
- `src/core/harnessStore.ts`: persistence and timestamp roundtrip; rejects symlinked roots/path components before directory creation.
- Server API/profiles/runner: harness profile persistence, restrictive policy subset, final merged-setting validation, per-job RAG/decision gates, and agent/provider (`agent`, `providers.rag/decision`) persistence, merging and run-local binding with the same fail-closed host gates as the extension.
- `src/core/diagnostics.ts`, `src/workbench.ts`: engine-backed effective-tool preview with engine source, exclusions, warnings and scope conflicts; panel renders diagnostics as escaped/literal text.

## Permission and host boundaries

Harness settings cannot turn on edits, commands or memory when the host disables them, widen the host command allowlist or switch the host engine. Harness role/agent engine and Claude Code overrides are rejected. Policies are merged conservatively; unsupported combinations fail closed.

Explicit native read scopes remain restricted to supported single/chat use. Multi-agent scoped configurations are rejected; this work does not introduce cross-agent context isolation.

RAG/decision switches use host-configured services only. Provider configuration is **model-only and host-constrained**: only `providers.rag{model,topK,autoK}` and `providers.decision{model,minConfidence}` are accepted, and `baseUrl`/`key`/`endpoint`/`env`/`header`/`url` are rejected at any depth (case-insensitive). They do not provide arbitrary provider, endpoint or credential configuration. Server authority and final allowed-setting validation remain enforced. There is no unrestricted all-tools mode, and editor-only capabilities are not promised on the server.

## Remaining

- Full per-workflow provider/model binding configuration for RAG and decisions: **PARTIAL** — only a model-only, host-constrained `providers` block is supported (`rag{model,topK,autoK}`, `decision{model,minConfidence}`). The resolved model is wired run-locally into the host RAG/decision client; arbitrary providers, base URLs or keys are never allowed.
- Full permissions/policies/provider configuration editor: current editor is bounded (model string inputs plus advanced JSON), not complete visual coverage.
- Server policy support remains a restrictive subset.
- Live-provider E2E and manual VS Code browser/accessibility verification remain outstanding. Dedicated concurrent RAG runner isolation and cleanup now have regression coverage.

## Python fix-job companion

`clients/python/fix_job.py` provides bounded submission/follow-up, JSON configuration, offline payload preview, human-approval handoff and fixed-name reports. `swarmlab_client.py` adds verified harness/providers, rag, singular decision, web and data fields without changing existing defaults. `test_fix_job.py` exercises offline mocked HTTP/client behavior; README section 17 gives source/VSIX examples. Python files are excluded from VSIX by `.vscodeignore`; obtain them separately. Package manifests are updated to 0.38.0; Python clients remain excluded from the VSIX.

**Cold-start export:** `srv:exportStart` now validates trust and ownership, starts an existing matching native loopback configuration if stopped, waits for readiness, then exports. Concurrent profiles share startup without losing exports. Remote/unmanaged targets never trigger local startup; missing or mismatched local configuration requires manual setup. Docker remains optional.

**Installed VSIX in a real editor (0.39.0):** an environment with `vscode` downloaded VSCodium 1.140, installed the 0.39.0 VSIX into an isolated profile, and its smoke check passed (the extension activated, its 28 commands registered, `swarmLab.open` ran); the real-editor suite (`test-vscode/run.js`, 8 checks) passed against the same editor. This covers activation and commands of the installed VSIX, not visual or accessibility review.

Remaining: live-provider verification (no configured credentials available), manual UI/accessibility checks and fuller host parity. The opt-in live runner is scripts/real-provider-e2e.cjs; its eight offline safety tests do not count as a real-provider result. This companion does not close those backlog items.

## Previous verification

The following sequence completed with exit code 0 after the named-agent, provider and export-and-start landing:

```sh
npm run compile && node out/test/harnessSim.js && node out/test/vscodeHarnessSim.js && node out/test/serverHarnessSim.js && node out/test/harnessPanelSim.js && node out/test/harnessStoreSim.js && node out/test/diagnosticsSim.js && node out/test/mapsSim.js && node out/test/readScopeSim.js && node out/test/decisionSim.js
```

- Harness (harnessSim): 81 checks passed.
- Server harness (serverHarnessSim): 34 focused checks passed.
- Panel harness (harnessPanelSim): 35 checks passed.
- VS Code harness, harness store, diagnostics, maps, read scope and decision suites passed.
- Failed-closed gates verified: decision.model is rejected when the host has no decision client; rag.model is rejected when the host has no embedding model configured;
  banned provider keys (`baseUrl`/`key`/`endpoint`/`url`/`header`/`env`, case-insensitive, any depth) and literal secrets are rejected; named `agent` is validated for existence (non-wildcard) before single-mode run start.

These are automated simulations, not visual verification or proof of full host parity.
