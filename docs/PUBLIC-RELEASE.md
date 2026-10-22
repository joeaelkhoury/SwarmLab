# Public release checklist: 0.42.4

Canonical repository: <https://github.com/joeaelkhoury/SwarmLab>.
Publisher remains **joe-el-khoury**. This checklist is a publication plan; it does
not assert any upload has occurred. Do not push or upload as part of docs editing.

## Distribution scope

The current public release provides an installable VSIX, documentation, and Python
client/examples. Extension source code will follow in a later update. Do not
promise a buildable public source checkout or ask beginners to run npm there.
The native server is available through the installed extension's Server tab;
Docker is optional, not a requirement for Python use.

From 0.41.0, Swarm Lab is under the source-available [Swarm Lab License](../LICENSE)
by Joe El Khoury: use is free, but copying, redistribution, and publishing
modified versions need written permission. Versions released earlier under MIT
keep MIT for those who received them. A VSIX is still inspectable bundled
JavaScript; protection comes from the license and copyright, not secrecy. Keep
LICENSE, NOTICE.md, CITATION.cff, and bundled third-party notices in every release.

## Exact minimal Git upload allowlist

Copy only these paths into a clean staging folder, preserving directories. This
list includes the focused guides' advanced reference link and optional starter
application so their direct links/imports remain useful:

```text
README.md
LICENSE
NOTICE.md
CITATION.cff
CHANGELOG.md
MANUAL.md
SERVER.md
SERVER-QUICKSTART.md
MIGRATING.md
media/screenshot-chat.png
media/tasks.png
docs/DOCUMENTS.md
docs/GETTING-STARTED.md
docs/PYTHON-WORKFLOWS.md
docs/RUN-MODES.md
docs/PUBLIC-RELEASE.md
docs/PROGRAMMATIC-CONFIGURATION.md
docs/PYTHON-LIBRARY.md
docs/ENVIRONMENTS.md
docs/WORKFLOWS.md
clients/python/README.md
clients/python/swarmlab_client.py
clients/python/fix_job.py
clients/python/configuration_examples.py
clients/python/example_app.py
clients/python/workflow_demos.py
clients/python/test_workflow_demos.py
clients/python/demo_project/README.md
clients/python/demo_project/.gitignore
clients/python/demo_project/pricing.py
clients/python/demo_project/labels.py
clients/python/demo_project/test_demo.py
clients/python/pyproject.toml
clients/python/test_swarmlab_package.py
clients/python/swarmlab/__init__.py
clients/python/swarmlab/__main__.py
clients/python/swarmlab/cli.py
clients/python/swarmlab/client.py
clients/python/swarmlab/spec.py
clients/python/swarmlab/workflow.py
```

The actual license filename is LICENSE (not LICENSE.md). The first three Python
files form the offline configuration/bounded-job set; example_app imports the
client and is optional for use, but included in this upload list. Keep sibling
imports together when downloading. Detailed retained references may discuss
source-only development paths not included in this minimal repository; those
sections do not imply source availability. The Server quickstart labels that
boundary explicitly. Check retained reference links before publication.

## Release assets, not Git files

- Attach the locally prepared 0.42.4 VSIX to a GitHub Release, rather than committing
  it to Git. A checksum may accompany the asset.
- Verify the actual filename, version, publisher, installability, bundled native
  server, license, and third-party notices before uploading.
- Test in a clean VS Code profile; test the README install path and screenshot.
- Marketplace metadata is maintained locally in the developer checkout when
  publishing an extension listing. It is not required in the minimal public repo.
- Build/package and any public download ZIP are separate maintainer steps; this
  workflow builds them locally but performs no external uploads.

## ZIP layout and GitLab publication

The public ZIP preserves the exact allowlisted repository paths above. The Python
starter ZIP contains only the allowlisted clients/python files, relative to that
folder, including demo_project subdirectories (never flatten to basenames). Its
README uses external canonical documentation URLs, so it works without root docs.
The packaging check copies this identical layout, runs all four workflow previews,
and runs the public test_workflow_demos suite without a server.

For GitLab, create/select your own project and copy only the allowlist into a clean
staging repository, preserving paths. Review the staged diff and secret scan before
manually committing/pushing; attach VSIX and ZIPs as release assets, not Git files.
No GitLab URL was supplied: do not invent a remote or replace canonical GitHub links.
No push or upload is performed by the packaging script.

## Never copy wholesale from the working checkout

Explicitly exclude the following from the minimal public Git repository:

```text
src/
out/
dist/
node_modules/
.git/
.swarmlab/
.env
.env.*
swarmlab.server.json
package.json
package-lock.json
package.json.patch.json
*.vsix
clients/python/full_test.py
clients/python/run_full_test.sh
clients/python/test_*.py (except the explicitly allowlisted test_workflow_demos.py)
```

Also exclude real server configurations under any name, API keys, credentials,
logs, run reports, project data, private prompts, caches, worktrees, source ZIPs,
and developer-only automation. A denylist alone is insufficient: upload only the
allowlist above. Inspect files and VSIX separately for secrets; do not delete
required license notices while reducing package contents.

## Pre-upload review

- [ ] GitHub URLs use the canonical case above; publisher ID is unchanged.
- [ ] Version is 0.42.4; LICENSE is the Swarm Lab License; NOTICE.md and CITATION.cff are included.
- [ ] README clearly states the source publication intention without claiming an upload.
- [ ] Every allowlisted file exists; screenshot and starter-guide links resolve.
- [ ] Downloaded Python neighbors import together without any source-tree imports.
- [ ] Run offline list/dry-run checks from the starter folder, without a server.
- [ ] Explain that real submissions need a reachable configured native server,
  registered repo/commit, credentials, host permissions, and approval review.
- [ ] No fake-model result is presented as evidence of real-model correctness.
- [ ] No real keys, logs, configurations, or workspace data are staged.
- [ ] Review VSIX contents/notices and install it separately; do not commit it.
- [ ] Upload/push only after explicit maintainer review, outside this task.

Return to [README](../README.md) or [Python workflows](PYTHON-WORKFLOWS.md).
