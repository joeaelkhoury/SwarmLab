# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""python -m swarmlab: run jobs and workflows, manage saved workflows, prepare environments.

    python -m swarmlab run "Fix the failing test" --repo app --env auto --checks
    python -m swarmlab run "Fix it" --local . --workflow fix-and-test.json --approve auto
    python -m swarmlab workflow validate fix-and-test.json
    python -m swarmlab workflow push fix-and-test.json
    python -m swarmlab env . --test
    python -m swarmlab caps
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .client import SwarmLab, SwarmLabError, build_spec
from .spec import Environment, SpecError
from .workflow import Workflow


def _kv(items: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for x in items:
        if "=" not in x:
            raise SpecError(f"use KEY=VALUE, not {x!r}")
        k, v = x.split("=", 1)
        try:
            out[k.replace("-", "_")] = json.loads(v)
        except ValueError:
            out[k.replace("-", "_")] = v
    return out


def _client(a: argparse.Namespace) -> SwarmLab:
    if getattr(a, "local", None) is not None:
        return SwarmLab.local(a.local or None, provider=a.provider, model=a.model, data_dir=a.data_dir, config=a.config, verbose=not a.quiet)
    return SwarmLab(a.url, a.key, verbose=not getattr(a, "quiet", False))


def _env_arg(v: Optional[str]) -> Any:
    if v is None:
        return None
    if v in ("off", "false", "no"):
        return False
    if v.endswith(".json"):
        return Environment.load(v)
    if v.strip().startswith("{"):
        return Environment.from_dict(json.loads(v))
    return v


def _job_kwargs(a: argparse.Namespace) -> Dict[str, Any]:
    kw: Dict[str, Any] = _kv(a.set or [])
    for k in ("repo", "mode", "agent", "profile", "ref"):
        v = getattr(a, k, None)
        if v is not None:
            kw[k] = v
    if a.workflow:
        kw["workflow"] = a.workflow
    if a.env is not None:
        kw["environment"] = _env_arg(a.env)
    if a.checks:
        kw["checks"] = True if a.checks == "yes" else a.checks
    if a.approvals:
        kw["approvals"] = a.approvals
    if a.files:
        kw["files"] = True
    if a.spec:
        with open(a.spec, encoding="utf-8") if a.spec != "-" else sys.stdin as f:
            kw["extra"] = json.load(f)
    return kw


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="python -m swarmlab", description="Swarm Lab agents and workflows from the command line.")
    p.add_argument("--url", help="server URL (default $SWARMLAB_URL or http://127.0.0.1:8787)")
    p.add_argument("--key", help="API key (default $SWARMLAB_KEY)")
    p.add_argument("--local", nargs="?", const="", metavar="REPO", help="no server: run here, on this git repository")
    p.add_argument("--provider", help="local: anthropic | openai | openrouter | mock")
    p.add_argument("--model", help="local: the model for every agent")
    p.add_argument("--data-dir", help="local: where jobs, caches and saved workflows are kept")
    p.add_argument("--config", help="local: a swarmlab.server.json to use")
    p.add_argument("-q", "--quiet", action="store_true", help="no progress lines")
    sub = p.add_subparsers(dest="cmd", required=True)

    def job_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("task")
        sp.add_argument("--repo"), sp.add_argument("--mode", choices=["single", "tree", "swarm", "graph", "auto"]), sp.add_argument("--agent")
        sp.add_argument("--workflow", help="a saved workflow's name, or a .json file"), sp.add_argument("--profile"), sp.add_argument("--ref")
        sp.add_argument("--env", help="auto | node | python | vscode-extension | … | a server environment | FILE.json | JSON | off")
        sp.add_argument("--checks", nargs="?", const="yes", help="run the tests and check the result (optionally: the test command)")
        sp.add_argument("--approvals", choices=["unattended", "careful"])
        sp.add_argument("--files", action="store_true", help="return every changed file")
        sp.add_argument("--set", action="append", metavar="KEY=VALUE", help="any job field or setting, e.g. max_steps=20, labels={\"team\":\"web\"}")
        sp.add_argument("--spec", help="more job fields as JSON (FILE or -)")

    r = sub.add_parser("run", help="run a job and wait for it")
    job_args(r)
    r.add_argument("--approve", default="default", help="auto | reject | ask | none (default: ask in a terminal)")
    r.add_argument("--timeout", type=float)
    r.add_argument("--json", action="store_true", help="print the finished job as JSON")
    r.add_argument("--patch", help="save the changes to this file")
    r.add_argument("--download", help="save the changed files under this folder")
    job_args(sub.add_parser("preview", help="print a job's JSON without sending it"))
    v = sub.add_parser("validate", help="check a job with the server's rules, without running it")
    job_args(v)

    w = sub.add_parser("workflow", help="saved workflows")
    wsub = w.add_subparsers(dest="wcmd", required=True)
    for name, helptext in (("validate", "check a workflow file"), ("push", "save a workflow file on the server (or locally with --local)"),
                           ("diagram", "print a Mermaid diagram of a workflow file")):
        x = wsub.add_parser(name, help=helptext)
        x.add_argument("file")
        x.add_argument("--name")
    wsub.add_parser("list", help="saved workflows")
    sh = wsub.add_parser("show", help="print a saved workflow")
    sh.add_argument("name")
    rm = wsub.add_parser("delete", help="delete a saved workflow")
    rm.add_argument("name")

    e = sub.add_parser("env", help="prepare an environment for a folder and run commands in it (no agents)")
    e.add_argument("path", nargs="?", default=".")
    e.add_argument("--env", default="auto", help="preset, FILE.json or JSON (default auto)")
    e.add_argument("--run", action="append", help="a command to run in it (repeat for more)")
    e.add_argument("--test", action="store_true", help="run its test command")
    e.add_argument("--isolated", action="store_true", help="work on a temporary copy")
    e.add_argument("--keep", action="store_true")

    sub.add_parser("caps", help="what the server allows (modes, repositories, settings, environments…)")
    sub.add_parser("jobs", help="recent jobs")
    sub.add_parser("approvals", help="pending approvals")
    d = sub.add_parser("decide", help="approve or reject an approval")
    d.add_argument("id"), d.add_argument("--reject", action="store_true"), d.add_argument("--choice"), d.add_argument("--text")

    a = p.parse_args(argv)
    try:
        if a.cmd == "preview":
            print(json.dumps(build_spec(a.task, **_job_kwargs(a)), indent=2))
            return 0
        if a.cmd == "workflow" and a.wcmd in ("validate", "diagram") and a.local is None and not a.url:
            wf = Workflow.load(a.file, a.name)
            if a.wcmd == "diagram":
                print(wf.mermaid())
                return 0
            errs = wf.validate()
            print(f"✕ {a.file}:\n- " + "\n- ".join(errs) if errs else f"✓ {a.file} is a valid workflow ({len(wf.graph()['nodes'])} steps).")
            return 1 if errs else 0
        sl = _client(a)
        if a.cmd == "run":
            approve = None if a.approve == "none" else a.approve
            res = sl.run(a.task, approve=approve, timeout=a.timeout, **_job_kwargs(a))
            if a.patch:
                res.save_patch(a.patch)
            if a.download:
                res.download_files(a.download)
            if a.json:
                print(json.dumps(res.job, indent=2))
            else:
                print(f"\n{res.status.upper()}{' · branch ' + res.branch if res.branch else ''} · {res.tokens:,} tokens · ${res.cost_usd:.4f}\n")
                print(res.answer or res.error or "")
                if res.diff_stat:
                    print("\n" + res.diff_stat)
            return 0 if res.ok else 1
        if a.cmd == "validate":
            r = sl.validate(a.task, **_job_kwargs(a))
            print(json.dumps(r, indent=2))
            return 0 if r["valid"] else 1
        if a.cmd == "workflow":
            if a.wcmd == "validate":
                errs = sl.validate_workflow(Workflow.load(a.file, a.name))
                print(f"✕ {a.file}:\n- " + "\n- ".join(errs) if errs else f"✓ {a.file} is valid on this server.")
                return 1 if errs else 0
            if a.wcmd == "diagram":
                print(Workflow.load(a.file, a.name).mermaid())
                return 0
            if a.wcmd == "push":
                wf = Workflow.load(a.file, a.name)
                sl.save_workflow(wf)
                print(f"✓ saved workflow {wf.name}: run it with --workflow {wf.name}")
                return 0
            if a.wcmd == "list":
                for x in sl.workflows():
                    print(f"{x['name']:<28} {x.get('source', '')} {x.get('steps', '')} steps  {x.get('description', '')}")
                return 0
            if a.wcmd == "show":
                print(json.dumps(sl.workflow(a.name).to_dict(), indent=2))
                return 0
            if a.wcmd == "delete":
                sl.delete_workflow(a.name)
                return 0
        if a.cmd == "env":
            r = sl.env(a.path, _env_arg(a.env), run=a.run, test=a.test, isolated=a.isolated, keep=a.keep)
            for run in r.get("runs", []):
                print(f"$ {run['command']}  → exit {run['exitCode']}\n{run.get('output', '')}")
            info = r.get("environment") or {}
            print(f"{'✓' if r.get('ok') else '✕'} {info.get('runtime')} environment ({', '.join(info.get('detected') or []) or info.get('preset')})", file=sys.stderr)
            return 0 if r.get("ok") else 1
        if a.cmd == "caps":
            print(json.dumps(sl.capabilities(), indent=2))
            return 0
        if a.cmd == "jobs":
            for j in sl.jobs():
                print(f"{j['id'][:8]}  {j['status']:<10} {j['mode']:<7} {(j.get('repo') or '-'):<12} {j['task'].splitlines()[0][:60]}")
            return 0
        if a.cmd == "approvals":
            for x in sl.approvals():
                print(f"{x['id']}  job {x['jobId'][:8]}  {x['title']}  [{' / '.join(x['choices'])}]")
            return 0
        if a.cmd == "decide":
            sl.decide(a.id, "reject" if a.reject else "approve", a.choice, a.text)
            return 0
    except (SwarmLabError, SpecError) as err:
        print(f"✕ {err}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0
