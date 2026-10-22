# Environments: let a job install what it needs, then work inside it

A Swarm Lab job can prepare its own environment before its agents start: install the project's dependencies,
create a Python virtual environment, start a container of any image, give windowed programs (VS Code, Electron,
browsers) a virtual screen. Every command of the job then runs **inside** that environment: the agents'
`run_command` and `run_tests`, a workflow's command steps, and the final check.

It works the same everywhere: on a Swarm Lab server, with `swarm-lab run` (no server), with `swarm-lab env`
(no agents at all), and from Python (`environment=` on any job, or `SwarmLab.env(...)`).

## 1. The quickest way

```json
{ "task": "Fix the failing test", "repo": "app", "environment": "auto", "checks": { "tests": true } }
```

`auto` looks at the project's files and installs what they ask for. `checks.tests: true` then uses the
environment's own test command.

| Found | Installed | Test command |
|---|---|---|
| `package.json` (+ `package-lock.json`, `yarn.lock` or `pnpm-lock.yaml`) | `npm ci` / `yarn install --frozen-lockfile` / `pnpm install --frozen-lockfile` (or `npm install`); `node_modules/.bin` on PATH | `npm test` (or yarn/pnpm), when there is a test script |
| `package.json` with `engines.vscode` (a VS Code extension) | as above, then `npm run compile`; a virtual screen; **a real editor** with the extension packaged, installed and smoke-checked (section 6) | `swarmlab-vscode check` (smoke check, then `npm test`) |
| `requirements*.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | a virtual environment in the job's own folder, first on PATH; `pip install -r` each requirements file, or `pip install -e .` (`.[dev]` when it exists); pytest if missing | `python -m pytest -q` |
| `go.mod` | `go mod download` | `go test ./...` |
| `Cargo.toml` | `cargo fetch` | `cargo test` |
| `pom.xml`, `build.gradle(.kts)` | dependencies resolved | `mvn -q -B test`, `./gradlew test` |
| `*.sln`, `*.csproj` | `dotnet restore` | `dotnet test` |

Several languages in one project are all prepared. Name one preset instead of `auto` to install only that one:
`"node"`, `"python"`, `"go"`, `"rust"`, `"java"`, `"dotnet"`, `"vscode-extension"`, or `"none"` (nothing).

## 2. Every field

```json
"environment": {
  "preset": "auto",
  "runtime": "local",
  "image": "node:22",
  "preSetup": ["apt-get update", "apt-get install -y xvfb libnss3 libasound2"],
  "setup": ["npm run build"],
  "env": { "NODE_OPTIONS": "--max-old-space-size=4096", "DATA": "${WORKSPACE}/fixtures" },
  "path": ["tools/bin"],
  "display": "auto",
  "test": "npm run test:unit",
  "home": "inherit",
  "network": true,
  "timeoutSec": 1800,
  "continueOnError": false
}
```

| Field | Meaning |
|---|---|
| `preset` | What to install (section 1). Default `auto`. |
| `runtime` | `local` (default): on the machine that runs the job, with the job's own folders. `docker`: in a container of `image` (Docker or Podman). |
| `image` | The container image, for `docker`. Any image works: `node:22`, `python:3.12`, `mcr.microsoft.com/devcontainers/universal`, your own. |
| `preSetup` | Commands **before** the preset's steps (system packages the preset needs). |
| `setup` | Commands **after** the preset's steps (build, seed a database, download a model…). |
| `env` | Variables for every command. `${WORKSPACE}`, `${ENV_DIR}` and `${CACHE_DIR}` are filled in. Do not put secrets here: set them in the server's environment instead. |
| `path` | Folders put first on PATH (relative to the workspace). |
| `display` | `auto` (a virtual screen when the preset needs one), `virtual` (always), `none`. On Linux it uses `xvfb-run` (install `xvfb`); in a container, `xvfb-run` when the image has it. macOS and Windows have a screen already. |
| `test` | The environment's test command (default: the preset's). It runs without asking: the submitter chose it. |
| `home` | Local runtime: `inherit` (default) keeps your HOME and its tool configuration; `isolated` gives the job an empty HOME of its own. |
| `network` | Docker: `false` runs the container without network (the image is still pulled first). |
| `timeoutSec` | Seconds each setup command may take (default 1800). |
| `continueOnError` | `true`: a failed setup step is reported as a warning and the job goes on. Default: the job fails at once, with the step's output. |
| `vscode` | A real editor in the environment (section 6). On by default with the `vscode-extension` preset; `false` turns it off; `true` or an object adds it to any environment. |

**Where things go.** Each job gets a folder of its own (`dataDir/envs/<job>`) with `tmp/`, `bin/` (on PATH), the
Python virtual environment, and its own HOME when `home: isolated`; it is removed at the end. Download caches (npm,
pip, Go, Gradle, NuGet, and downloaded editors) are shared by all jobs in `dataDir/envs/_cache`, so the second job installs much
faster. In a container the workspace is `/workspace`, the job's folder `/swarmlab-env` and the cache `/swarmlab-cache`;
files the container made are given back to your user before it is removed.

**What ends up in the result.** Files and folders the setup created (`node_modules/`, `.vscode-test/`, build
output) are left out of the job's commit and patch; tracked files the setup rewrote (a lock file updated by an
install) are restored when no agent changed them afterwards. The job's result has `result.environment` (runtime,
detected languages, every step with its exit code and time, warnings), and the full output is the
`environment.log` artifact. Events of kind `environment` (`start`, `step`, `step-done`, `ready`) show progress live.

## 3. Where an environment comes from

1. The job's `environment` (or its profile's, or its saved workflow's). `false` means none at all.
2. Otherwise the repository's **`.swarmlab/environment.json`**: same fields, committed with the code, so every job on
   that repository gets the right environment without saying anything.
3. Otherwise the server's `environments.default`.
4. Otherwise none: commands run on the machine as they are.

A job can also name one of the server's environments: `"environment": "web-e2e"` (see SERVER.md, section 4.21).

## 4. Examples

**A Python project, tested**

```json
{ "task": "Fix the rounding bug in invoices", "repo": "billing", "environment": "python", "checks": { "tests": true } }
```

**A VS Code extension: install, compile, package, install it in a real editor, check it**

```json
{ "task": "Make the 'Explain' command work on unsaved files, with a test",
  "repo": "my-extension", "environment": "vscode-extension", "checks": { "tests": true } }
```

That is all it takes: section 6 explains what happens. On a Linux server without a screen, install `xvfb` once
(`apt-get install -y xvfb`), or use a container (the editor's system libraries are installed in it for you):

```json
"environment": { "runtime": "docker", "image": "node:22", "preset": "vscode-extension", "vscode": { "flavor": "vscodium" } }
```

**Anything else: a container you choose**

```json
"environment": { "runtime": "docker", "image": "rust:1.82", "preset": "rust",
  "setup": ["rustup component add clippy"], "test": "cargo clippy -- -D warnings && cargo test" }
```

**Your own tools for the job**

```json
"environment": { "preset": "node",
  "setup": ["curl -fsSL https://example.com/tool.tar.gz | tar -xz -C \"$SWARMLAB_ENV_DIR/bin\""],
  "env": { "TOOL_CONFIG": "${WORKSPACE}/tool.yaml" } }
```

`$SWARMLAB_ENV_DIR/bin` is on PATH for every command of the job, and removed with the job.

## 5. Without agents: `swarm-lab env`

Prepare an environment for a folder and run commands in it, exactly as a job would. Handy to try an environment
before giving it to agents, or as a universal "install and test" step in CI:

```bash
swarm-lab env .                       # detect, install, report
swarm-lab env . --test                # … and run the test command
swarm-lab env . --runtime docker --image python:3.12 --preset python --run "pytest -q -x"
swarm-lab env ../ext --preset vscode-extension --test --isolated   # on a temporary copy (git worktree) of HEAD
swarm-lab env . --file envs/ci.json --json                         # machine-readable result
```

`--isolated` works on a temporary copy, so your folder is not touched; without it the folder is used as it is (an
install changes it as it would by hand). `--keep` keeps the job folder (and the copy) for a look afterwards. The exit
code is 0 when the setup and every command succeeded.

From Python: `SwarmLab().env(".", "auto", test=True)` or `python -m swarmlab env . --test`.

## 6. A real editor: VS Code, VSCodium, or the one you have

An environment can bring a real editor, so a job can **install VS Code by itself, install .vsix files, start the
editor, and test what the extensions do in it**, on Linux, macOS and Windows, on this machine or in a container.

```json
"environment": {
  "preset": "vscode-extension",
  "vscode": {
    "flavor": "vscode",
    "version": "stable",
    "install": ["vendor/dependency.vsix", "ms-python.python"],
    "commands": ["myExt.hello", { "command": "myExt.add", "args": [41] }],
    "check": "test/smoke-check.js",
    "require": "regression"
  }
}
```

**What happens, in order:**

1. **The editor.** `flavor` `vscode` (default), `insiders` or `vscodium` is downloaded for this OS and processor
   (or, in a container, its Linux build), unpacked into the shared cache (`dataDir/envs/_cache/editors/`) and
   reused by every later job: the first job downloads ~150–220 MB, the next ones nothing. `version` is
   `stable` (the latest, looked up each time; offline, the newest cached one is used) or exact (`"1.95.3"`;
   VSCodium: its release tag). `executable` uses an editor already installed instead: `"code"`, `"codium"`,
   `"cursor"`, `"windsurf"`, `"/Applications/Visual Studio Code.app"`, `"C:\\Tools\\VSCode\\Code.exe"`. When the
   download is impossible and an editor is on PATH, that one is used, with a warning.
2. **The extensions.** The workspace's own extension is packaged with `vsce` (`package`, default: when the workspace
   is an extension), then it and everything in `install` (.vsix files and marketplace ids; VSCodium uses Open VSX)
   are installed into the job's own extensions folder. Your own editor and its extensions are never touched.
3. **The smoke check (a baseline).** The editor starts (with a virtual screen where there is none) with an empty
   profile and those extensions, and checks, inside the editor: each extension activates, every command it
   contributes is registered, every command in `commands` runs without an error (its return value is reported),
   and `check`, a script run inside the editor, passes. It tells you whether the extension worked **before** the job;
   it never fails the setup, because making it work may be the job.
4. **The job.** `swarmlab-vscode` is on the job's PATH; agents and workflow command steps run it after a change, and
   it is the environment's test command (so `run_tests` and `checks.tests` use it):

   | Command | Does |
   |---|---|
   | `swarmlab-vscode check` | package, install, smoke check, then the project's own `npm test` (`projectTests`, default: when there is a test script); exit 1 when something fails |
   | `swarmlab-vscode smoke` | the smoke check only (`--no-package`, `--no-install` to skip those) |
   | `swarmlab-vscode package` / `install` | one step |
   | `swarmlab-vscode run [args…]` | the editor with the job's extensions (for example `run --list-extensions --show-versions`) |
   | `swarmlab-vscode info` | where everything is |

   A failure prints what failed and why: the activation error with its stack trace, the missing commands, the
   command that threw, the end of the editor's logs.
5. **The final check.** After the job's result is committed, `swarmlab-vscode check` runs once more on it.
   `require` decides what it means: `regression` (default): the job fails when the check passed before the job and
   fails after it (the job broke the extension); `pass`: the job fails whenever the final check fails; `none`: only
   reported. A failing job is never pushed. Results: `result.environment.vscode` (`baseline`, `final`), and the
   artifacts `vscode-smoke.json` (every extension, command result, error and log) and `vscode-check.log`.

**A check script** runs inside the editor after the extensions activated, with the editor's API. Return `false` or
throw to fail:

```js
// test/smoke-check.js
module.exports = async (vscode, report) => {
  const doc = await vscode.workspace.openTextDocument({ language: "markdown", content: "# Title" });
  await vscode.window.showTextDocument(doc);
  await vscode.commands.executeCommand("myExt.formatTitle");
  const text = vscode.window.activeTextEditor.document.getText();
  if (text !== "# TITLE") throw new Error("formatTitle gave: " + text);
  return true;
};
```

**The project's own tests in the same editor.** Every command of the job sees `SWARMLAB_VSCODE_EXECUTABLE` (the
editor program), `SWARMLAB_VSCODE_CLI` and `SWARMLAB_VSCODE_EXTENSIONS_DIR`. With `@vscode/test-electron`, pass
`vscodeExecutablePath: process.env.SWARMLAB_VSCODE_EXECUTABLE` to `runTests`; with `@vscode/test-cli`,
`useInstallation: { fromPath: process.env.SWARMLAB_VSCODE_EXECUTABLE }`. For `flavor: "vscode"` the editor is also
linked into `.vscode-test/` under the name `@vscode/test-electron` looks for, so tests that download VS Code by
themselves find it there and download nothing. `.vscode-test/` is never part of a job's result.

**A workflow that fixes until the extension works in the editor:**

```json
{ "start": "fix", "nodes": {
  "fix":   { "agent": "fixer", "task": "{task}\n\nThe last editor check said:\n{last}", "next": "check" },
  "check": { "command": "swarmlab-vscode check", "onPass": "done", "onFail": "fix", "maxVisits": 4, "onLimit": "done" } } }
```

**Only an editor, any project:** `"environment": { "preset": "none", "vscode": { "install": ["build/my.vsix"],
"commands": ["my.hello"] } }` checks a .vsix built elsewhere; `swarm-lab env . --file that.json --run "swarmlab-vscode
smoke"` does it without agents (in CI too).

**Where it runs.** Linux: needs a screen or `xvfb` (used automatically), and the editor's libraries (`libnss3`,
`libgbm1`, `libgtk-3-0`, `libasound2`, `libxkbfile1`, `libsecret-1-0`; a missing one is named in a warning before
anything starts). macOS and Windows: nothing to install. Docker: an image with Node (`node:22`, devcontainer
images); the libraries and `xvfb` are installed with the image's apt-get, dnf or apk (`systemDeps: false` to skip).
The server may run inside VS Code: the editor is started as an editor anyway, and `node` is provided to the job's
commands even where none is installed.

## 7. Safety

An environment is not an operating-system sandbox. The local runtime runs commands as the server's user, with the
job's own folders but the machine's programs, files and network. The docker runtime isolates the file system (only
the workspace, the job's folder and the cache are mounted) and, with `network: false`, the network. On a server
shared by several people, use `allowSetup: "admin"` or `"off"`, `runtimes: ["docker"]` and `docker.allowImages`,
and give the container limits with `docker.extraArgs` (`--cpus`, `--memory`, `--pids-limit`).
