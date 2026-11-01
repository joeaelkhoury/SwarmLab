# Beginner Workflow roadmap — bounded phase 1

Baseline: 0.37.1. This slice changes presentation and focused assertions only; no package, release build, permission expansion, new wizard state or new execution API.

## Phase 1: guided quick-start (implemented)

The Workflow view now has four numbered steps: choose a template; assign agents/tasks; review routes, files and test commands; validate/save/run. A visible checklist distinguishes saving the active workflow from saving a reusable template and explains the native read-scope boundary. Template help includes a no-template fallback. Existing template, validation, save, dry-run and JSON handlers remain in place.

This is a **guided quick-start, not a full wizard**. It does not create agents, skills or reusable templates for the user, and saving does not execute a workflow.

Implementation: `src/panelWorkbench.ts` (Workflow markup, `changedGraph`, template/save/dry-run listeners). Coverage: `src/test/presentationSim.ts` checks original control IDs, four numbered steps, accessible guide/checklist headings, onboarding boundaries and generated JavaScript parsing, alongside existing draft/route checks. These are simulations, not browser or screenshot verification.

## Audited capability matrix

The runtime facts below retain the previously verified audit baseline; this phase does not claim a fresh full host-parity or security audit. Paths identify the implementation to revisit.

| Capability | Current boundary | Evidence / follow-up |
| --- | --- | --- |
| Native tool availability | Role base tools are combined with supplied host controls and settings, then filtered by policy tool allowlists and other restrictions. There is no promise that every host exposes every tool. | `src/core/engine.ts`: `toolsFor`, `agentSetup`; `src/core/types.ts`: Controls. Never add an all-tools bypass. |
| Native read scopes | Explicit readPaths support bounded read-only native single/chat execution; Graph/cross-agent use is rejected. Input data paths are not permission grants. | `src/core/engine.ts`: policy resolution, scoped tool filtering, role checks and dispatch; `src/test/readScopeSim.ts`. Do not describe this as general Graph isolation. |
| Editor code intelligence | Extension supplies code symbols and call hierarchy through editor support; server runner does not wire that editor control. | `src/extension.ts`: codeIntel wiring; `src/vscodeCodeMap.ts`; `src/core/engine.ts`; `src/server/runner.ts`; `src/test/decisionSim.ts`. |
| Named-agent consultation | Extension wires consultation for chat; server runner does not wire the consultation callback. This is not universal host parity. | `src/extension.ts`: chat controls/consultAgent; `src/core/engine.ts`: consultation availability and dispatch; `src/server/runner.ts`. |
| Active workflow / reusable templates | Save workflow persists `.swarmlab/graph.json`. Reusable templates in `.swarmlab/templates` are separate from the active draft. Loading a template replaces the draft. | `src/panelWorkbench.ts`; `src/core/templates.ts`; `src/extension.ts`: workbench handlers. No new reusable-template creation flow in this slice. |
| Server job configuration | Runner supports per-job MCP selection/additions and skill loading. Saved profiles supply reusable job configuration, not editor-only controls. | `src/server/runner.ts`: MCP and skills setup; `src/server/profiles.ts`; `clients/python/swarmlab_client.py`: profile methods and submit. |
| Python submission | Client submit accepts agent, workflow, profile, mcp and skills keyword arguments. Exact HTTP payloads must be checked against client/server validation before publishing examples. | `clients/python/swarmlab_client.py`: submit; `src/server/api.ts`; `src/server/profiles.ts`. |
| Skills | Skills are instructions loaded inside agent jobs, not independently executable jobs. Creation still follows applicable edit approval. | `src/server/runner.ts`: controls.skills; `src/core/skills.ts`; `src/core/engine.ts`: use_skill/create_skill. |
| MCP schema compatibility | Tool schema mapping retains top-level properties and required while constructing an object schema. This is not proof of full JSON Schema fidelity. | `src/core/mcp.ts`: McpHub.tools; `src/core/types.ts`: ToolSpec. Follow-up compatibility audit required before parity claims. |

## Next phases (not implemented here)

### Phase 2 — actual wizard and reusable creation

- Design an explicit multi-step wizard with back/cancel, unsaved-draft confirmation and final review; do not relabel the current guide as a wizard.
- Add distinct actions for active-workflow save and reusable-template creation, with name/path validation, overwrite approval and round-trip validation tests.
- Guide agent creation (prompt, model, role, tools and file permissions) and skill creation (when-to-use description and instructions), reusing existing approved persistence paths.
- Acceptance: create/reload a template, agent and skill; preserve existing drafts on cancel/error; retain all current permission and Graph validation boundaries.

### Phase 3 — effective-tool diagnostics and host parity audit

- Show effective tools for the selected agent/role/engine/host and explain exclusions: missing host control, setting disabled, policy allowlist or scope restriction.
- Compare extension/native, server/native and other engine adapters explicitly; never infer parity from a shared tool name or settings checkbox.
- Audit MCP schema composition, references, top-level constraints, provider conversions and error handling with compatibility fixtures. Do not silently advertise unsupported schemas as equivalent.
- Acceptance: diagnostics match tools actually sent and dispatch restrictions; tests cover denied tools as well as available tools. No permission loosening or all-tools toggle.

### Phase 4 — scripting examples, approvals and secret protection

- Publish tested Python examples for selecting an agent, loading a workflow, using a profile, selecting MCP and loading skills inside a job. Verify signatures and server validation at implementation time; do not guess endpoint fields.
- Explain that skill instructions are not an independent executable API. Keep local editor-only capabilities clearly distinguished from server capabilities.
- Demonstrate approval waits, rejection, cancellation, bounded commands and safe output locations. Review command text and external MCP destinations before execution.
- Use environment/secret-store references and redacted logs; never embed credentials in templates, skills, profiles, examples or diagnostics. Preserve server host/network restrictions and existing approval gates.
- Acceptance: mock/local examples with no real credentials, negative approval tests, redaction checks and documented limitations before broader onboarding claims.

## Verification gate

Run TypeScript compilation, then presentationSim, navigationSim, permissionPickerSim, readScopeSim, chatInputSim and projectSim. Record actual results in the implementation handoff; do not equate these simulations with a packaged release or a manual UI accessibility review. Preserve package version 0.37.1 and do not run a release build for this slice.
