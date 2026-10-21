"""SwarmLab: run Swarm Lab agents and workflows from Python, on a server or on this machine.

    from swarmlab import SwarmLab, Agent, Workflow, Environment

    sl = SwarmLab()                                   # a server (SWARMLAB_URL, SWARMLAB_KEY, default 127.0.0.1:8787)
    sl = SwarmLab.local("path/to/repo")               # no server: runs the swarm-lab program here

    r = sl.run("Fix the failing test", repo="app", environment=Environment.auto(), checks=True)
    print(r.answer)
    r.save_patch("fix.patch")

The same calls work in both modes. Every field of a job can be given as a keyword (see build_spec).
"""
from __future__ import annotations

import glob
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Union

from .spec import (SETTINGS_ALIASES, SETTINGS_FIELDS, Agent, Approvals, Environment, Settings, SpecError, agents_into, camel,
                   environment_value, to_api)
from .workflow import Workflow

__all__ = ["SwarmLab", "Job", "Result", "SwarmLabError", "JobFailed", "build_spec", "find_server"]

FINISHED = ("succeeded", "failed", "cancelled")
Approver = Union[str, Callable[[Dict[str, Any]], Any], None]


class SwarmLabError(Exception):
    """An error answered by the server (status code and message), or by the local program."""

    def __init__(self, status: int, message: str):
        super().__init__(f"{status}: {message}" if status else message)
        self.status = status
        self.message = message


class JobFailed(SwarmLabError):
    """Raised by Result.raise_for_status() (and run(..., check=True)) when a job did not succeed."""

    def __init__(self, result: "Result"):
        super().__init__(0, f"job {result.id} {result.status}: {result.error or result.answer[:300]}")
        self.result = result


# --------------------------------------------------------------------------- building a job

# Job fields: Python name → API name. Values are passed through to_api().
_FIELDS = {
    "repo": "repo", "mode": "mode", "files": "files", "ref": "ref", "priority": "priority", "webhook": "webhook", "labels": "labels",
    "max_attempts": "maxAttempts", "timeout_sec": "timeoutSec", "idempotency_key": "idempotencyKey", "policy": "policy", "prompts": "prompts",
    "profile": "profile", "skills": "skills", "hooks": "hooks", "harness": "harness", "providers": "providers", "web": "web",
}
_MODES = ("single", "tree", "swarm", "graph")
_LEAD_ROLE = {"single": "single", "tree": "tree-lead", "swarm": "swarm-lead"}


def build_spec(task: str, *, agent: Union[Agent, str, None] = None, agents: Optional[Sequence[Union[Agent, Mapping[str, Any]]]] = None,
               workflow: Union[Workflow, str, Mapping[str, Any], None] = None, environment: Any = None,
               settings: Union[Settings, Mapping[str, Any], None] = None, approvals: Union[Approvals, Mapping[str, Any], str, None] = None,
               checks: Any = None, memory: Any = None, data: Any = None, mcp: Any = None, models: Any = None, rag: Any = None,
               decision: Any = None, prompt: Optional[str] = None, extra: Optional[Mapping[str, Any]] = None, **kw: Any) -> Dict[str, Any]:
    """The JSON of a job (what POST /v1/jobs takes), from Python values.

    Shortcuts: agent=Agent(...) (single mode with that agent); agents=[...] (workers a lead may use); workflow=Workflow |
    "name" | "file.json"; environment="auto" | Environment | dict | False; checks=True (tests + verify) | "pytest -q";
    memory="session" | False; data=["inputs/"] ; mcp=["server"]; models="cheapest"; rag/decision=True | False;
    approvals="unattended" | "careful" | Approvals; prompt="..." (the lead's instructions);
    any Settings field as a keyword (max_steps_per_agent=20, token_budget=..., or max_steps=20);
    extra={...} for fields this library does not know yet (sent as they are).
    """
    if not isinstance(task, str) or not task.strip():
        raise SpecError("the task is empty")
    spec: Dict[str, Any] = {"task": task}
    sett: Dict[str, Any] = dict(to_api(settings) or {}) if not isinstance(settings, Settings) else settings.to_dict()
    unknown = []
    for k, v in kw.items():
        if v is None:
            continue
        if k in _FIELDS:
            spec[_FIELDS[k]] = to_api(v)
        elif k in SETTINGS_FIELDS or k in SETTINGS_ALIASES:
            name = SETTINGS_ALIASES.get(k, k)
            sett[Settings._rename.get(name, camel(name))] = v
        else:
            unknown.append(k)
    if unknown:
        raise SpecError(f"unknown parameter(s) {', '.join(sorted(unknown))}. Job fields: {', '.join(sorted(list(_FIELDS) + ['agent', 'agents', 'workflow', 'environment', 'settings', 'approvals', 'checks', 'memory', 'data', 'mcp', 'models', 'rag', 'decision', 'prompt', 'extra']))}; "
                        f"settings: {', '.join(SETTINGS_FIELDS)} (or max_steps, budget, max_tokens). Fields not listed: extra={{...}}.")
    if "mode" in spec and spec["mode"] not in _MODES:
        raise SpecError(f"mode must be one of {', '.join(_MODES)}, not {spec['mode']!r}")
    if sett:
        Settings(**{_snake(k): v for k, v in sett.items() if _snake(k) in SETTINGS_FIELDS})  # checks the values it knows
        spec["settings"] = sett
    # Agents
    if agent is not None:
        if spec.get("mode", "single") != "single":
            raise SpecError("agent= runs one agent (single mode); for teams use agents=[...] with mode tree or swarm")
        spec["mode"] = "single"
        if isinstance(agent, Agent):
            agents_into(spec, [agent])
            spec["agent"] = agent.name
        else:
            spec["agent"] = agent
    if agents:
        agents_into(spec, agents)
    # Workflow
    if workflow is not None:
        if isinstance(workflow, str) and workflow.endswith(".json") and os.path.exists(workflow):
            workflow = Workflow.load(workflow)
        if isinstance(workflow, Workflow):
            workflow.check()
            _merge_workflow(spec, workflow.to_dict())
        elif isinstance(workflow, Mapping):
            _merge_workflow(spec, dict(workflow) if "graph" in workflow else {"graph": dict(workflow)})
        elif isinstance(workflow, str):
            spec["workflow"] = workflow
        else:
            raise SpecError("workflow is a Workflow, a saved workflow's name, a .json file, or a dict")
        spec.setdefault("mode", "graph")
        if spec["mode"] != "graph":
            raise SpecError(f"a workflow runs in graph mode, not {spec['mode']}")
    if prompt:
        role = _LEAD_ROLE.get(spec.get("mode", "single"))
        if not role:
            raise SpecError("prompt= sets the lead's instructions; a workflow's steps have their own (Agent(prompt=...))")
        spec.setdefault("prompts", {}).setdefault("roles", {})[role] = prompt
    # The rest, with friendly forms
    if environment is not None:
        spec["environment"] = environment_value(environment)
    if approvals is not None:
        if isinstance(approvals, str):
            presets = {"unattended": Approvals.unattended(), "auto": Approvals.unattended(), "careful": Approvals.careful()}
            if approvals not in presets:
                raise SpecError("approvals is an Approvals, a dict, or \"unattended\" / \"careful\"")
            approvals = presets[approvals]
        spec["approvals"] = to_api(approvals)
    if checks is not None and checks is not False:
        spec["checks"] = {"tests": True, "verify": True} if checks is True else {"tests": checks, "verify": True} if isinstance(checks, str) else to_api(checks)
    if memory is not None:
        spec["memory"] = False if memory is False else {"session": memory} if isinstance(memory, str) else to_api(memory)
    if data is not None:
        spec["data"] = {"inputs": list(data)} if isinstance(data, (list, tuple)) else {"inputs": [data]} if isinstance(data, str) else to_api(data)
    if mcp is not None:
        spec["mcp"] = {"use": list(mcp)} if isinstance(mcp, (list, tuple)) else to_api(mcp)
    if models is not None:
        spec["models"] = {"auto": models} if isinstance(models, str) else to_api(models)
    for name, v in (("rag", rag), ("decision", decision)):
        if v is not None:
            spec[name] = "on" if v is True else "off" if v is False else v
    if extra:
        spec.update(to_api(dict(extra)))
    return spec


def _snake(k: str) -> str:
    return {"ragTopK": "rag_top_k", "ragAutoK": "rag_auto_k", "costBudgetUsd": "cost_budget_usd"}.get(k) or re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower()


def _merge_workflow(spec: Dict[str, Any], doc: Mapping[str, Any]) -> None:
    """A workflow's graph goes in as the job's workflow; its agents, prompts and defaults go under the job's own."""
    spec["workflow"] = doc["graph"]
    for a, p in ((doc.get("policy") or {}).get("agents") or {}).items():
        spec.setdefault("policy", {}).setdefault("agents", {}).setdefault(a, p)
    for a, p in ((doc.get("prompts") or {}).get("agents") or {}).items():
        spec.setdefault("prompts", {}).setdefault("agents", {}).setdefault(a, p)
    for k in ("settings", "approvals", "checks"):
        if doc.get(k):
            spec[k] = {**doc[k], **spec.get(k, {})}
    if "environment" in doc and "environment" not in spec:
        spec["environment"] = doc["environment"]


# --------------------------------------------------------------------------- approvals


def _answer(approve: Approver, a: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """What to answer an approval with ({"decision", "choice", "text"}), or None to leave it to someone else."""
    if approve is None:
        return None
    if approve == "auto":
        return {"decision": "approve"}
    if approve == "reject":
        return {"decision": "reject"}
    if approve == "ask":
        return _ask_terminal(a)
    if callable(approve):
        r = approve(a)
        if r is None:
            return None
        if r is True:
            return {"decision": "approve"}
        if r is False:
            return {"decision": "reject"}
        if isinstance(r, str):
            return {"decision": "reject"} if r.lower() == "reject" else {"decision": "approve", "choice": r}
        if isinstance(r, Mapping):
            return dict(r)
        raise SpecError(f"the approval handler returned {r!r}: return True, False, None, a choice, or a dict")
    raise SpecError("approve is \"auto\", \"reject\", \"ask\", None, or a function(approval) → True / False / None / choice / dict")


def _ask_terminal(a: Dict[str, Any]) -> Dict[str, Any]:
    print(f"\n── Approval: {a.get('title')}", file=sys.stderr)
    for part in (a.get("detail"), (a.get("diff") or "")[:6000]):
        if part:
            print(part, file=sys.stderr)
    choices = a.get("choices") or ["Approve", "Reject"]
    ans = input("  ".join(f"[{i + 1}] {c}" for i, c in enumerate(choices)) + f"  (Enter = {choices[0]}, r = reject): ").strip()
    if ans.lower() in ("r", "reject", "n", "no"):
        return {"decision": "reject"}
    choice = choices[int(ans) - 1] if ans.isdigit() and 0 < int(ans) <= len(choices) else choices[0]
    return {"decision": "reject"} if choice.lower() == "reject" else {"decision": "approve", "choice": choice}


def _default_approver() -> Approver:
    return "ask" if sys.stdin.isatty() and sys.stderr.isatty() else None


# --------------------------------------------------------------------------- results


class Result:
    """A finished job: its answer, status, files, patch, report, usage and environment."""

    def __init__(self, job: Dict[str, Any], backend: "_Backend"):
        self.job = job
        self._b = backend

    id = property(lambda self: self.job["id"])
    status = property(lambda self: self.job.get("status"))
    ok = property(lambda self: self.job.get("status") == "succeeded")
    error = property(lambda self: self.job.get("error"))
    result = property(lambda self: self.job.get("result") or {})
    answer = property(lambda self: (self.job.get("result") or {}).get("answer") or "")
    branch = property(lambda self: self.result.get("branch"))
    commit = property(lambda self: self.result.get("commit"))
    files = property(lambda self: self.result.get("files") or [])
    diff_stat = property(lambda self: self.result.get("diffStat") or "")
    environment = property(lambda self: self.result.get("environment"))
    metrics = property(lambda self: self.result.get("metrics") or {})
    tokens = property(lambda self: self.job.get("tokens") or 0)
    cost_usd = property(lambda self: self.job.get("costUsd") or 0.0)
    pr_url = property(lambda self: self.result.get("prUrl"))
    vscode = property(lambda self: (self.result.get("environment") or {}).get("vscode"))
    """The editor check: {"flavor", "version", "baseline": {...}, "final": {"ok", "extensions", "commands", "check"}}."""

    def editor_report(self) -> Optional[Dict[str, Any]]:
        """The last editor smoke check in full (vscode-smoke.json): every extension, command result, error, log."""
        return json.loads(self.artifact("vscode-smoke.json")) if "vscode-smoke.json" in self.artifacts() else None

    def artifacts(self) -> List[str]:
        return self._b.artifacts(self.id)

    def artifact(self, name: str) -> str:
        """"changes.patch", "report.md", "report.json", "environment.log", or "files/<path>"."""
        return self._b.artifact(self.id, name)

    def patch(self) -> str:
        """The diff of the job's changes ("" when it changed nothing)."""
        return self.artifact("changes.patch") if "changes.patch" in self.artifacts() else ""

    def save_patch(self, file: str) -> str:
        with open(file, "w", encoding="utf-8", newline="") as f:
            f.write(self.patch())
        return file

    def report(self, fmt: str = "md") -> Any:
        """Every step with its tokens, cost and time. fmt="json" returns a dict."""
        text = self.artifact("report.json" if fmt == "json" else "report.md")
        return (json.loads(text).get("report", json.loads(text))) if fmt == "json" else text

    def environment_log(self) -> str:
        return self.artifact("environment.log") if "environment.log" in self.artifacts() else ""

    def download_files(self, folder: str) -> List[str]:
        """Save the job's created or changed files (jobs with files=True, or without a repository) under folder."""
        saved = []
        root = os.path.abspath(folder)
        for name in self.artifacts():
            if not name.startswith("files/"):
                continue
            target = os.path.abspath(os.path.join(root, name[6:]))
            if not target.startswith(root + os.sep):
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(self.artifact(name))
            saved.append(name[6:])
        return saved

    def raise_for_status(self) -> "Result":
        if not self.ok:
            raise JobFailed(self)
        return self

    def __str__(self) -> str:
        return self.answer or (self.error or "")

    def __repr__(self) -> str:
        return f"Result(id={self.id!r}, status={self.status!r}, files={self.files}, tokens={self.tokens}, cost_usd={self.cost_usd})"


class Job:
    """A submitted job. wait() for its Result; events() to follow it; cancel() to stop it."""

    def __init__(self, info: Dict[str, Any], backend: "_Backend"):
        self.info = info
        self._b = backend

    @property
    def id(self) -> str:
        return self.info["id"]

    @property
    def status(self) -> str:
        return self.refresh().info["status"]

    def refresh(self) -> "Job":
        self.info = self._b.get(self.id)
        return self

    def events(self, follow: bool = True) -> Iterator[Dict[str, Any]]:
        """Events as flat dicts ({"seq", "kind", ...}); with follow, until the job ends."""
        return self._b.events(self, follow)

    def wait(self, approve: Approver = "default", timeout: Optional[float] = None,
             on_event: Optional[Callable[[Dict[str, Any]], None]] = None, verbose: Optional[bool] = None) -> Result:
        """Wait until the job ends and return its Result.

        approve: "auto" (approve everything), "reject", "ask" (in this terminal), a function(approval) → True / False /
        None / choice / {"decision", "choice", "text"}, or None (leave approvals to the dashboard or others).
        Default: "ask" in a terminal, otherwise None (server) or "reject" (local).
        """
        if approve == "default":
            approve = _default_approver()
        return self._b.wait(self, approve, timeout, on_event, self._b.verbose if verbose is None else verbose)

    def cancel(self) -> "Job":
        self._b.cancel(self.id)
        return self

    def approvals(self) -> List[Dict[str, Any]]:
        return self._b.job_approvals(self.id)

    def __repr__(self) -> str:
        return f"Job({self.id!r}, status={self.info.get('status')!r})"


def _progress(e: Dict[str, Any]) -> Optional[str]:
    """One line for the interesting events (for verbose runs)."""
    k = e.get("kind")
    if k == "environment":
        if e.get("phase") == "start":
            return f"⚙ environment: {e.get('runtime')}{' ' + e['image'] if e.get('image') else ''}, {', '.join(e.get('detected') or []) or e.get('preset')}"
        if e.get("phase") == "step":
            return f"  $ {e.get('command')}"
        if e.get("phase") == "step-done" and e.get("exitCode") != 0:
            return f"  ✕ exit {e.get('exitCode')}\n{e.get('tail') or ''}"
        if e.get("phase") == "ready":
            return f"⚙ environment {'ready' if e.get('ok') else 'FAILED'} in {e.get('durationMs', 0) / 1000:.1f} s"
    if k == "node" and e.get("status") == "start":
        return f"▶ {e.get('node')}: {e.get('detail', '')}"[:200]
    if k == "spawn":
        return f"＋ agent {e.get('agent')}"
    if k == "say":
        return f"  {e.get('agent')}: {str(e.get('text', ''))[:160]}"
    if k == "approval":
        return f"⏸ waiting for approval: {e.get('title')}"
    if k == "warning":
        return f"! {e.get('text')}"
    if k == "status" and e.get("status") in FINISHED:
        return f"■ {e.get('status')}"
    return None


# --------------------------------------------------------------------------- backends


class _Backend:
    verbose = True

    def get(self, job_id: str) -> Dict[str, Any]: raise NotImplementedError
    def artifacts(self, job_id: str) -> List[str]: raise NotImplementedError
    def artifact(self, job_id: str, name: str) -> str: raise NotImplementedError
    def cancel(self, job_id: str) -> None: raise NotImplementedError
    def job_approvals(self, job_id: str) -> List[Dict[str, Any]]: raise NotImplementedError
    def events(self, job: Job, follow: bool) -> Iterator[Dict[str, Any]]: raise NotImplementedError
    def wait(self, job: Job, approve: Approver, timeout: Optional[float], on_event: Any, verbose: bool) -> Result: raise NotImplementedError


def _flat(e: Dict[str, Any]) -> Dict[str, Any]:
    ev = e.get("event") if isinstance(e.get("event"), dict) else {}
    return {"seq": e.get("seq"), **ev}


class _Http(_Backend):
    def __init__(self, url: str, api_key: str, timeout: float):
        self.url = url.rstrip("/")
        self.key = api_key
        self.timeout = timeout

    def req(self, method: str, path: str, body: Any = None, raw: bool = False) -> Any:
        data = None if body is None else json.dumps(body).encode()
        r = urllib.request.Request(self.url + path, data=data, method=method)
        r.add_header("content-type", "application/json")
        if self.key:
            r.add_header("authorization", f"Bearer {self.key}")
        try:
            with urllib.request.urlopen(r, timeout=self.timeout) as resp:
                text = resp.read().decode()
        except urllib.error.HTTPError as e:
            text = e.read().decode()
            try:
                msg = json.loads(text).get("error", text)
            except ValueError:
                msg = text or str(e.reason)
            raise SwarmLabError(e.code, msg) from None
        except urllib.error.URLError as e:
            raise SwarmLabError(0, f"cannot reach the Swarm Lab server at {self.url} ({e.reason}). Start it (Server tab in VS Code, "
                                   f"or `swarm-lab serve`), or use SwarmLab.local(...) to run without a server.") from None
        if raw:
            return text
        return json.loads(text) if text else {}

    def submit(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self.req("POST", "/v1/jobs", spec)

    def get(self, job_id: str) -> Dict[str, Any]:
        return self.req("GET", f"/v1/jobs/{job_id}")

    def artifacts(self, job_id: str) -> List[str]:
        return [a["name"] for a in self.req("GET", f"/v1/jobs/{job_id}/artifacts")["artifacts"]]

    def artifact(self, job_id: str, name: str) -> str:
        return self.req("GET", f"/v1/jobs/{job_id}/artifacts?name={urllib.parse.quote(name, safe='')}", raw=True)

    def cancel(self, job_id: str) -> None:
        self.req("POST", f"/v1/jobs/{job_id}/cancel")

    def job_approvals(self, job_id: str) -> List[Dict[str, Any]]:
        return self.req("GET", f"/v1/jobs/{job_id}/approvals")["approvals"]

    def decide(self, approval_id: str, answer: Mapping[str, Any]) -> Dict[str, Any]:
        return self.req("POST", f"/v1/approvals/{approval_id}", {k: v for k, v in answer.items() if v is not None})

    def events(self, job: Job, follow: bool) -> Iterator[Dict[str, Any]]:
        after = 0
        while True:
            evs = self.req("GET", f"/v1/jobs/{job.id}/events?after={after}&limit=500")["events"]
            for e in evs:
                after = e["seq"]
                yield _flat(e)
            if not follow:
                return
            if not evs:
                if job.refresh().info["status"] in FINISHED:
                    for e in self.req("GET", f"/v1/jobs/{job.id}/events?after={after}&limit=1000")["events"]:
                        yield _flat(e)
                    return
                time.sleep(0.5)

    def wait(self, job: Job, approve: Approver, timeout: Optional[float], on_event: Any, verbose: bool) -> Result:
        t0, after, seen, hinted = time.time(), 0, set(), False
        while True:
            for e in self.req("GET", f"/v1/jobs/{job.id}/events?after={after}&limit=500")["events"]:
                after = e["seq"]
                ev = _flat(e)
                if on_event:
                    on_event(ev)
                if verbose:
                    line = _progress(ev)
                    if line:
                        print(line, file=sys.stderr)
            info = job.refresh().info
            if info["status"] in FINISHED:
                return Result(info, self)
            if info["status"] == "waiting":
                for a in self.job_approvals(job.id):
                    if a["status"] != "pending" or a["id"] in seen:
                        continue
                    ans = _answer(approve, a)
                    if ans is None:
                        if not hinted and verbose:
                            print(f"  (approve it in the dashboard: {self.url}/ , or wait(approve=...))", file=sys.stderr)
                            hinted = True
                        continue
                    seen.add(a["id"])
                    try:
                        self.decide(a["id"], ans)
                    except SwarmLabError as err:
                        if err.status != 409:  # already decided by someone else
                            raise
            if timeout and time.time() - t0 > timeout:
                raise TimeoutError(f"job {job.id} is still {info['status']} after {timeout} s")
            time.sleep(0.7)


def find_server(explicit: Optional[str] = None) -> List[str]:
    """The command that runs the swarm-lab program: [node, main.js] or [swarm-lab].

    Looks at: explicit, SWARMLAB_SERVER_JS, this source checkout (dist/ or out/), swarm-lab on PATH, then the installed
    VS Code extension (VS Code, Insiders, Remote/Server, Cursor, Windsurf, VSCodium).
    """
    node = os.environ.get("SWARMLAB_NODE") or shutil.which("node") or "node"
    tried: List[str] = []
    for cand in (explicit, os.environ.get("SWARMLAB_SERVER_JS")):
        if cand:
            tried.append(cand)
            if os.path.isfile(cand):
                return [node, cand] if cand.endswith(".js") else [cand]
    here = os.path.dirname(os.path.abspath(__file__))
    for rel in ("../../../dist/server/main.js", "../../../out/server/main.js"):
        f = os.path.normpath(os.path.join(here, rel))
        tried.append(f)
        if os.path.isfile(f):
            return [node, f]
    exe = shutil.which("swarm-lab")
    if exe:
        return [exe]
    tried.append("swarm-lab on PATH")
    home = os.path.expanduser("~")
    found = []
    for d in (".vscode", ".vscode-insiders", ".vscode-server", ".vscode-server-insiders", ".cursor", ".windsurf", ".vscode-oss"):
        for f in glob.glob(os.path.join(home, d, "extensions", "joe-el-khoury.swarm-lab-*", "dist", "server", "main.js")):
            m = re.search(r"swarm-lab-(\d+(?:\.\d+)*)", f)
            found.append((tuple(int(x) for x in m.group(1).split(".")) if m else (0,), f))
    tried.append(os.path.join(home, ".vscode*/extensions/joe-el-khoury.swarm-lab-*"))
    if found:
        return [node, max(found)[1]]
    raise SwarmLabError(0, "the swarm-lab program was not found. Install the Swarm Lab VS Code extension (the library uses its bundled server), "
                           "or set SWARMLAB_SERVER_JS to …/dist/server/main.js. Looked at: " + "; ".join(tried))


class _Local(_Backend):
    """Runs each job with `swarm-lab run --jsonl` in this process's machine: no server needed."""

    def __init__(self, repo: Optional[str], cmd: List[str], data_dir: str, flags: List[str], config: Optional[str]):
        self.repo = os.path.abspath(repo) if repo else None
        self.cmd = cmd
        self.data_dir = data_dir
        self.flags = flags
        self.config = config
        self.jobs: Dict[str, Dict[str, Any]] = {}
        os.makedirs(data_dir, exist_ok=True)

    def base(self) -> List[str]:
        return [*self.cmd, *(["--config", self.config] if self.config else [])]

    def submit(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        out = tempfile.mkdtemp(prefix="swarmlab-job-")
        spec_file = os.path.join(out, "spec.json")
        with open(spec_file, "w", encoding="utf-8") as f:
            json.dump(spec, f)
        args = [*self.cmd[:1], *self.cmd[1:], "run", "--spec", spec_file, "--jsonl", "--approve", "stdin", "--data-dir", self.data_dir,
                "--out", os.path.join(out, "artifacts"), *self.flags, *(["--config", self.config] if self.config else [])]
        repo = spec.get("repo")
        if self.repo and not repo:
            args += ["--repo-path", self.repo]
        elif repo and os.path.isdir(str(repo)):
            args += ["--repo-path", os.path.abspath(repo)]
        elif not repo:
            args += ["--no-repo"]
        popen_kw: Dict[str, Any] = {}
        if os.name == "nt":
            popen_kw["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", **popen_kw)
        lines: "queue.Queue[Optional[Dict[str, Any]]]" = queue.Queue()
        err: List[str] = []

        def read() -> None:
            assert p.stdout
            for line in p.stdout:
                line = line.strip()
                if line.startswith("{"):
                    try:
                        lines.put(json.loads(line))
                    except ValueError:
                        pass
            lines.put(None)

        def read_err() -> None:
            assert p.stderr
            for line in p.stderr:
                err.append(line)
                del err[:-200]

        threading.Thread(target=read, daemon=True).start()
        threading.Thread(target=read_err, daemon=True).start()
        first = lines.get(timeout=120)
        if not first or first.get("kind") != "job-start":
            p.wait(timeout=30)
            raise SwarmLabError(0, "".join(err).strip() or "the swarm-lab program ended before the job started")
        jid = first["job"]["id"]
        self.jobs[jid] = {"proc": p, "lines": lines, "err": err, "out": os.path.join(out, "artifacts"), "events": [], "final": None, "approvals": {}}
        return {"id": jid, "status": "running", "task": spec["task"], "spec": spec}

    def _pump(self, jid: str, block: bool, on_line: Optional[Callable[[Dict[str, Any]], None]] = None, wait_s: float = 0.5) -> bool:
        """Read what the program printed. Returns False when it has ended."""
        j = self.jobs[jid]
        while True:
            try:
                item = j["lines"].get(timeout=wait_s) if block else j["lines"].get_nowait()
            except queue.Empty:
                return True
            if item is None:
                j["proc"].wait()
                if j["final"] is None:
                    j["final"] = {"id": jid, "status": "failed", "error": "".join(j["err"]).strip()[-2000:] or "the swarm-lab program stopped"}
                return False
            if item.get("kind") == "job-end":
                j["final"] = item["job"]
            elif item.get("kind") == "approval-request":
                j["approvals"][item["approval"]["id"]] = item["approval"]
            else:
                ev = _flat(item)
                j["events"].append(ev)
            if on_line:
                on_line(item)
            block = False

    def get(self, job_id: str) -> Dict[str, Any]:
        j = self.jobs.get(job_id)
        if not j:
            raise SwarmLabError(404, "no such job in this session (local jobs live as long as their SwarmLab object)")
        self._pump(job_id, False)
        if j["final"]:
            return j["final"]
        return {"id": job_id, "status": "waiting" if j["approvals"] else "running"}

    def artifacts(self, job_id: str) -> List[str]:
        out = self.jobs[job_id]["out"]
        names = []
        for root, _, files in os.walk(out):
            for f in files:
                names.append(os.path.relpath(os.path.join(root, f), out).replace(os.sep, "/"))
        return sorted(n for n in names if n != "job.json")

    def artifact(self, job_id: str, name: str) -> str:
        f = os.path.join(self.jobs[job_id]["out"], *name.split("/"))
        if not os.path.isfile(f):
            raise SwarmLabError(404, f"no artifact {name!r}")
        with open(f, encoding="utf-8") as fh:
            return fh.read()

    def cancel(self, job_id: str) -> None:
        p = self.jobs[job_id]["proc"]
        if p.poll() is None:
            p.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)  # type: ignore[attr-defined]

    def job_approvals(self, job_id: str) -> List[Dict[str, Any]]:
        self._pump(job_id, False)
        return list(self.jobs[job_id]["approvals"].values())

    def events(self, job: Job, follow: bool) -> Iterator[Dict[str, Any]]:
        j = self.jobs[job.id]
        i = 0
        while True:
            alive = self._pump(job.id, follow)
            while i < len(j["events"]):
                yield j["events"][i]
                i += 1
            if not follow or not alive:
                return

    def wait(self, job: Job, approve: Approver, timeout: Optional[float], on_event: Any, verbose: bool) -> Result:
        if approve is None:
            approve = "reject"  # nobody else can answer a local job
        j = self.jobs[job.id]
        t0 = time.time()

        def line(item: Dict[str, Any]) -> None:
            if item.get("kind") == "approval-request":
                a = item["approval"]
                ans = _answer(approve, a) or {"decision": "reject"}
                j["approvals"].pop(a["id"], None)
                assert j["proc"].stdin
                try:
                    j["proc"].stdin.write(json.dumps({"id": a["id"], **ans}) + "\n")
                    j["proc"].stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
                if verbose:
                    print(f"{'✓' if ans.get('decision') == 'approve' else '✕'} {a.get('title')}", file=sys.stderr)
            elif item.get("kind") not in ("job-start", "job-end"):
                ev = _flat(item)
                if on_event:
                    on_event(ev)
                if verbose:
                    text = _progress(ev)
                    if text:
                        print(text, file=sys.stderr)

        while self._pump(job.id, True, line):
            if timeout and time.time() - t0 > timeout:
                self.cancel(job.id)
                raise TimeoutError(f"job {job.id} still running after {timeout} s (cancelled)")
        job.info = j["final"]
        return Result(j["final"], self)


# --------------------------------------------------------------------------- the entry point


class SwarmLab:
    """Run Swarm Lab agents and workflows. SwarmLab(url, api_key) for a server, SwarmLab.local(repo) without one."""

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, *, timeout: float = 30.0, verbose: bool = True):
        self._b: _Backend = _Http(url or os.environ.get("SWARMLAB_URL") or "http://127.0.0.1:8787",
                                  api_key if api_key is not None else os.environ.get("SWARMLAB_KEY", ""), timeout)
        self._b.verbose = verbose

    @classmethod
    def local(cls, repo: Optional[str] = None, *, provider: Optional[str] = None, model: Optional[str] = None, lead_model: Optional[str] = None,
              worker_model: Optional[str] = None, base_url: Optional[str] = None, api_key_env: Optional[str] = None,
              data_dir: Optional[str] = None, config: Optional[str] = None, server: Optional[str] = None, verbose: bool = True) -> "SwarmLab":
        """No server: each job runs here with the swarm-lab program (from the VS Code extension, or SWARMLAB_SERVER_JS).

        repo: the git repository jobs work on (default: none, or repo= per job). provider: "anthropic", "openai",
        "openrouter" or "mock" (default: the config file's, else mock); the key is read from api_key_env (default
        ANTHROPIC_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY). config: a swarmlab.server.json to use.
        """
        flags: List[str] = []
        for flag, v in (("provider", provider), ("model", model), ("lead-model", lead_model), ("worker-model", worker_model),
                        ("base-url", base_url), ("api-key-env", api_key_env)):
            if v:
                flags += [f"--{flag}", v]
        if repo and not os.path.isdir(os.path.join(repo, ".git")):
            raise SwarmLabError(0, f"{repo} is not a git repository (git init && git add -A && git commit -m start): jobs work on a branch of it")
        dd = data_dir or os.path.join(os.environ.get("XDG_CACHE_HOME") or (os.environ.get("LOCALAPPDATA") if os.name == "nt" else None)
                                      or os.path.join(os.path.expanduser("~"), ".cache"), "swarmlab", "local")
        self = cls.__new__(cls)
        self._b = _Local(repo, find_server(server), os.path.abspath(dd), flags, config)
        self._b.verbose = verbose
        return self

    @property
    def is_local(self) -> bool:
        return isinstance(self._b, _Local)

    # ------------------------------------------------------------------ jobs

    def spec(self, task: str, **kw: Any) -> Dict[str, Any]:
        """The job's JSON, built here and not sent (offline preview)."""
        return build_spec(task, **kw)

    preview = spec

    def validate(self, task: str, **kw: Any) -> Dict[str, Any]:
        """Check a job without running it: {"valid", "errors", "spec"} (the server's rules; offline rules when local)."""
        try:
            spec = build_spec(task, **kw)
        except SpecError as e:
            return {"valid": False, "errors": [str(e)], "spec": None}
        if isinstance(self._b, _Http):
            return self._b.req("POST", "/v1/validate", spec)
        return {"valid": True, "errors": [], "spec": spec}

    def submit(self, task: str, **kw: Any) -> Job:
        """Queue a job and return it at once (see build_spec for the keywords)."""
        spec = build_spec(task, **kw)
        return Job(self._b.submit(spec), self._b)  # type: ignore[attr-defined]

    def run(self, task: str, *, approve: Approver = "default", timeout: Optional[float] = None, check: bool = False,
            on_event: Optional[Callable[[Dict[str, Any]], None]] = None, verbose: Optional[bool] = None, **kw: Any) -> Result:
        """Submit, wait, return the Result. check=True raises JobFailed unless it succeeded. Keywords: see build_spec."""
        r = self.submit(task, **kw).wait(approve=approve, timeout=timeout, on_event=on_event, verbose=verbose)
        return r.raise_for_status() if check else r

    def run_many(self, tasks: Sequence[Union[str, Mapping[str, Any]]], *, approve: Approver = "default", **common: Any) -> List[Result]:
        """Several jobs at once (each a task, or a dict of keywords with "task"), with the same common keywords. Results in order."""
        jobs = [self.submit(t, **common) if isinstance(t, str) else self.submit(**{**common, **dict(t)}) for t in tasks]
        if isinstance(self._b, _Local):
            results: List[Optional[Result]] = [None] * len(jobs)
            threads = [threading.Thread(target=lambda i=i, j=j: results.__setitem__(i, j.wait(approve=approve, verbose=False))) for i, j in enumerate(jobs)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            return [r for r in results if r is not None]
        return [j.wait(approve=approve) for j in jobs]

    def job(self, job_id: str) -> Job:
        return Job(self._b.get(job_id), self._b)

    def jobs(self, status: Optional[Sequence[str]] = None, repo: Optional[str] = None, label: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        q: Dict[str, Any] = {"limit": limit}
        if status:
            q["status"] = ",".join(status)
        if repo:
            q["repo"] = repo
        if label:
            q["label"] = label
        return self._http().req("GET", "/v1/jobs?" + urllib.parse.urlencode(q))["jobs"]

    # ------------------------------------------------------------------ workflows

    def save_workflow(self, workflow: Union[Workflow, Mapping[str, Any]], name: Optional[str] = None) -> Dict[str, Any]:
        """Save a workflow (with its agents, prompts and environment) so any job can use it by name."""
        doc = workflow.check().to_dict() if isinstance(workflow, Workflow) else dict(workflow)
        name = name or (workflow.name if isinstance(workflow, Workflow) else doc.get("name"))
        if not name:
            raise SpecError("give the workflow a name")
        doc.pop("name", None)
        if isinstance(self._b, _Http):
            return self._b.req("PUT", f"/v1/workflows/{urllib.parse.quote(name)}", doc)
        folder = os.path.join(self._b.data_dir, "workflows")  # type: ignore[attr-defined]
        os.makedirs(folder, exist_ok=True)
        saved = {**doc, "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "updatedBy": "python"}
        with open(os.path.join(folder, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=2)
        return saved

    def workflow(self, name: str) -> Workflow:
        """A saved workflow, as a Workflow you can change and save again."""
        if isinstance(self._b, _Http):
            return Workflow.from_dict(self._b.req("GET", f"/v1/workflows/{urllib.parse.quote(name)}"), name)
        return Workflow.load(os.path.join(self._b.data_dir, "workflows", f"{name}.json"), name)  # type: ignore[attr-defined]

    def workflows(self) -> List[Dict[str, Any]]:
        if isinstance(self._b, _Http):
            return self._b.req("GET", "/v1/workflows")["workflows"]
        folder = os.path.join(self._b.data_dir, "workflows")  # type: ignore[attr-defined]
        return [{"name": f[:-5], "source": "local"} for f in sorted(os.listdir(folder))] if os.path.isdir(folder) else []

    def delete_workflow(self, name: str) -> None:
        if isinstance(self._b, _Http):
            self._b.req("DELETE", f"/v1/workflows/{urllib.parse.quote(name)}")
        else:
            os.remove(os.path.join(self._b.data_dir, "workflows", f"{name}.json"))  # type: ignore[attr-defined]

    def validate_workflow(self, workflow: Union[Workflow, Mapping[str, Any]]) -> List[str]:
        """Problems in a workflow: the server's rules (with its agents, settings and environment rules), offline when local."""
        if isinstance(workflow, Workflow):
            errs = workflow.validate()
            if errs or not isinstance(self._b, _Http):
                return errs
            workflow = workflow.to_dict()
        if isinstance(self._b, _Http):
            return self._b.req("POST", "/v1/workflows/validate", dict(workflow))["errors"]
        return Workflow.from_dict(workflow, "check").validate()

    # ------------------------------------------------------------------ ready workflows (the gallery)

    def templates(self, q: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Ready workflows: name, title, icon, category, description, inputs (their labels and examples)."""
        params = {k: v for k, v in (("q", q), ("category", category)) if v}
        return self._http().req("GET", "/v1/templates" + ("?" + urllib.parse.urlencode(params) if params else ""))["templates"]

    def template(self, name: str) -> Dict[str, Any]:
        return self._http().req("GET", f"/v1/templates/{urllib.parse.quote(name)}")

    def run_template(self, name: str, inputs: Optional[Mapping[str, Any]] = None, *, repo: Optional[str] = None, approve: Approver = "default",
                     wait: bool = True, timeout: Optional[float] = None, preview: bool = False, **form: Any) -> Any:
        """Run a ready workflow with its form: run_template("model-validation", notebook="models/pd.ipynb", recent="data/q2.csv").
        preview=True returns the job without running it; wait=False returns the Job at once."""
        values = {**dict(inputs or {}), **form}
        body: Dict[str, Any] = {"inputs": {k: ("\n".join(v) if isinstance(v, (list, tuple)) else v) for k, v in values.items()}, **({"repo": repo} if repo else {})}
        if preview:
            return self._http().req("POST", f"/v1/templates/{urllib.parse.quote(name)}/run", {**body, "preview": True})["spec"]
        job = Job(self._http().req("POST", f"/v1/templates/{urllib.parse.quote(name)}/run", body), self._b)
        return job.wait(approve=approve, timeout=timeout) if wait else job

    # ------------------------------------------------------------------ schedules and outcomes

    def schedule(self, name: str, cron: str, task: Optional[str] = None, *, timezone: Optional[str] = None, template: Optional[str] = None,
                 inputs: Optional[Mapping[str, Any]] = None, repo: Optional[str] = None, description: Optional[str] = None,
                 enabled: bool = True, **job: Any) -> Dict[str, Any]:
        """Run a job again and again: schedule("monthly-monitoring", "0 7 1 * *", template="model-monitoring", inputs={...},
        repo="models", timezone="Europe/Paris"). Or with a task and any job keywords (workflow=, environment=…)."""
        if template:
            spec = self.run_template(template, inputs, repo=repo, preview=True)
        elif task:
            spec = build_spec(task, repo=repo, **job)
        else:
            raise SpecError("a schedule needs a task or a template")
        doc = {"cron": cron, "job": spec, "enabled": enabled, **({"timezone": timezone} if timezone else {}), **({"description": description} if description else {})}
        return self._http().req("PUT", f"/v1/schedules/{urllib.parse.quote(name)}", doc)

    def schedules(self) -> List[Dict[str, Any]]:
        return self._http().req("GET", "/v1/schedules")["schedules"]

    def delete_schedule(self, name: str) -> None:
        self._http().req("DELETE", f"/v1/schedules/{urllib.parse.quote(name)}")

    def run_schedule_now(self, name: str) -> Job:
        return Job(self._http().req("POST", f"/v1/schedules/{urllib.parse.quote(name)}/run"), self._b)

    def outcomes(self, group_by: str = "workflow", fmt: str = "json", **q: Any) -> Any:
        """What the workflows did: runs, success rate, cost, human decisions, and the time saved against doing it by hand."""
        params = {"groupBy": group_by, **({"format": "md"} if fmt == "md" else {}), **{("from" if k == "date_from" else "to" if k == "date_to" else k): v for k, v in q.items() if v}}
        return self._http().req("GET", "/v1/outcomes?" + urllib.parse.urlencode(params), raw=fmt == "md")

    # ------------------------------------------------------------------ profiles, approvals, server

    def _http(self) -> _Http:
        if not isinstance(self._b, _Http):
            raise SwarmLabError(0, "this needs a server (SwarmLab(url, api_key)); local jobs are answered with run(..., approve=...)")
        return self._b

    def save_profile(self, name: str, **kw: Any) -> Dict[str, Any]:
        """A reusable configuration (same keywords as run, without the task); jobs use it with profile=name."""
        spec = build_spec("(profile)", **kw)
        spec.pop("task")
        return self._http().req("PUT", f"/v1/profiles/{urllib.parse.quote(name)}", spec)

    def profile(self, name: str) -> Dict[str, Any]:
        return self._http().req("GET", f"/v1/profiles/{urllib.parse.quote(name)}")

    def profiles(self) -> List[Dict[str, Any]]:
        return self._http().req("GET", "/v1/profiles")["profiles"]

    def delete_profile(self, name: str) -> None:
        self._http().req("DELETE", f"/v1/profiles/{urllib.parse.quote(name)}")

    def approvals(self, status: str = "pending") -> List[Dict[str, Any]]:
        return self._http().req("GET", f"/v1/approvals?status={status}")["approvals"]

    def decide(self, approval_id: str, decision: str = "approve", choice: Optional[str] = None, text: Optional[str] = None) -> Dict[str, Any]:
        return self._http().decide(approval_id, {"decision": decision, "choice": choice, "text": text})

    def capabilities(self) -> Dict[str, Any]:
        """What the server allows: modes, repositories, workflows, settings, environments, features, your roles."""
        if isinstance(self._b, _Http):
            return self._b.req("GET", "/v1/capabilities")
        v = subprocess.run([*self._b.cmd, "version"], capture_output=True, text=True, timeout=60)  # type: ignore[attr-defined]
        return {"version": v.stdout.strip(), "local": True, "modes": list(_MODES), "repos": [self._b.repo] if self._b.repo else []}  # type: ignore[attr-defined]

    def health(self) -> Dict[str, Any]:
        return self._http().req("GET", "/v1/health")

    def repos(self) -> List[str]:
        return self._http().req("GET", "/v1/repos")["repos"]

    def costs(self, group_by: str = "day", fmt: str = "json", **q: Any) -> Any:
        params = {"groupBy": group_by, "format": fmt, **{("from" if k == "date_from" else "to" if k == "date_to" else k): v for k, v in q.items() if v}}
        text = self._http().req("GET", "/v1/reports?" + urllib.parse.urlencode(params), raw=True)
        return json.loads(text) if fmt == "json" else text

    # ------------------------------------------------------------------ environments without agents

    def env(self, path: str = ".", environment: Any = "auto", *, run: Optional[Sequence[str]] = None, test: bool = False,
            isolated: bool = False, keep: bool = False) -> Dict[str, Any]:
        """Prepare an environment for a folder on this machine and run commands in it (no agents, no server).
        Returns {"ok", "environment", "runs": [{"command", "exitCode", "output"}]}."""
        cmd = self._b.cmd if isinstance(self._b, _Local) else find_server()
        args = [*cmd, "env", os.path.abspath(path), "--json"]
        env = environment_value(environment)
        tmp = None
        if isinstance(env, str):
            args += ["--preset", env] if env in ("auto", "none", "node", "python", "go", "rust", "java", "dotnet", "vscode-extension") else ["--file", env]
        elif isinstance(env, dict):
            fd, tmp = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w") as f:
                json.dump(env, f)
            args += ["--file", tmp]
        for c in run or []:
            args += ["--run", c]
        args += ["--test"] if test else []
        args += ["--isolated"] if isolated else []
        args += ["--keep"] if keep else []
        if isinstance(self._b, _Local):
            args += ["--data-dir", self._b.data_dir]
        try:
            p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
        finally:
            if tmp:
                os.remove(tmp)
        try:
            return json.loads(p.stdout)
        except ValueError:
            raise SwarmLabError(0, p.stderr.strip() or p.stdout.strip() or f"swarm-lab env exited {p.returncode}") from None
