#!/usr/bin/env python3
# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""
Example application: send a task to a Swarm Lab server, follow it live, answer its approvals,
and save the result (answer, diff, report).

    export SWARMLAB_URL=http://127.0.0.1:8787 SWARMLAB_KEY=sl_...
    python example_app.py --repo app --mode graph --task "Fix the failing date test"
    python example_app.py --repo app --mode swarm --task-file task.md --approve ask --out results/
    python example_app.py --list
"""
import argparse
import json
import os
import pathlib
import sys
import threading

from swarmlab_client import FINISHED, SwarmLabClient, SwarmLabError

KIND_LINES = {
    "status": lambda e: f"status → {e.get('status')}" + (f" ({e.get('error')})" if e.get("error") else ""),
    "sandbox": lambda e: f"working on branch {e.get('branch')}",
    "call": lambda e: f"{e.get('agent')}: model call ({e.get('inputTokens')} tokens in)",
    "tool": lambda e: f"{e.get('agent')} → {e.get('tool')} {e.get('detail', '')[:100]}",
    "message": lambda e: f"{e.get('from')} → {e.get('to')}: {str(e.get('text', ''))[:120]}",
    "node": lambda e: f"step {e.get('node')} {e.get('status')} {e.get('detail', '')}",
    "edit": lambda e: f"{'edited' if e.get('applied') else 'edit refused'} {e.get('path')}",
    "command": lambda e: f"{'ran' if e.get('ran') else 'not run'} {e.get('command')}" + (f" → exit {e.get('exitCode')}" if e.get("ran") else ""),
    "approval": lambda e: f"WAITING FOR APPROVAL: {e.get('title')}",
    "approval-decided": lambda e: f"approval {e.get('status')}" + (f" by {e.get('by')}" if e.get("by") else ""),
    "final": lambda e: "answer ready",
}


def approver(mode: str, sl: SwarmLabClient):
    """Answer approvals: 'auto' approves everything, 'reject' rejects everything, 'ask' asks on the terminal."""
    def answer(a):
        print(f"\n--- Approval: {a['title']}")
        if a.get("detail"):
            print(a["detail"])
        if a.get("diff"):
            print(a["diff"])
        if mode == "auto":
            print("→ approved automatically")
            return {"decision": "approve"}
        if mode == "reject":
            print("→ rejected automatically")
            return {"decision": "reject"}
        choice = input(f"Approve? [{'/'.join(a['choices'])}, or 'n' to reject] ").strip()
        if choice.lower() in ("n", "no", "reject"):
            return {"decision": "reject"}
        return {"decision": "approve", "choice": choice if choice in a["choices"] else a["choices"][0]}
    return answer


def main() -> int:
    p = argparse.ArgumentParser(description="Send a task to a Swarm Lab server and get the result.")
    p.add_argument("--url", default=os.environ.get("SWARMLAB_URL", "http://127.0.0.1:8787"))
    p.add_argument("--key", default=os.environ.get("SWARMLAB_KEY", ""))
    p.add_argument("--repo", help="a repository name (see --list-repos)")
    p.add_argument("--no-repo", action="store_true", help="work without a repository: ideas, tickets, diagrams, documents")
    p.add_argument("--files", dest="files", action="store_true", default=None, help="return every created or changed file")
    p.add_argument("--no-files", dest="files", action="store_false", help="only the patch and the report")
    p.add_argument("--mode", default="single", choices=["single", "tree", "swarm", "graph"])
    p.add_argument("--task")
    p.add_argument("--task-file")
    p.add_argument("--workflow", help="graph mode: 'default' or a workflow name")
    p.add_argument("--agent", help="single mode: run as this agent")
    p.add_argument("--priority", type=int, default=0)
    p.add_argument("--edits", choices=["auto", "ask", "off"], help="override the server's edit rule for this job")
    p.add_argument("--approve", default="ask", choices=["ask", "auto", "reject"], help="how this app answers approvals")
    p.add_argument("--label", action="append", default=[], help="key=value, may repeat")
    p.add_argument("--out", help="folder for answer.md, changes.patch, report.json")
    p.add_argument("--list", action="store_true", help="list recent jobs and exit")
    a = p.parse_args()

    sl = SwarmLabClient(a.url, a.key)
    try:
        if a.list:
            for j in sl.list(limit=20)["jobs"]:
                print(f"{j['id'][:8]}  {j['status']:<10} {j['mode']:<7} {j['task'][:70]}")
            return 0
        repo = None if a.no_repo else (a.repo or (sl.repos() or [None])[0])
        task = a.task or (pathlib.Path(a.task_file).read_text() if a.task_file else None)
        if not task:
            p.error("give --task or --task-file")
        labels = dict(x.split("=", 1) for x in a.label)
        job = sl.submit(repo, task, a.mode, files=a.files, workflow=a.workflow or ("default" if a.mode == "graph" else None), agent=a.agent,
                        priority=a.priority, approvals={"edits": a.edits} if a.edits else None, labels=labels or None)
        print(f"Job {job['id']} queued ({a.mode}, {('repository ' + repo) if repo else 'no repository'}).")

        # Answer approvals in the background while the events are printed.
        done = threading.Event()
        def approvals_loop():
            seen = set()
            ans = approver(a.approve, sl)
            while not done.is_set():
                for ap in sl.job_approvals(job["id"]):
                    if ap["status"] == "pending" and ap["id"] not in seen:
                        seen.add(ap["id"])
                        res = ans(ap)
                        if res:
                            try:
                                sl.decide(ap["id"], **res)
                            except SwarmLabError as e:
                                print(f"(approval: {e})")
                done.wait(1.5)
        t = threading.Thread(target=approvals_loop, daemon=True)
        t.start()

        for ev in sl.stream(job["id"]):
            e = ev["event"]
            line = KIND_LINES.get(e.get("kind"))
            if line:
                print(f"  {ev['at'][11:19]}  {line(e)}")
        done.set()

        job = sl.get(job["id"])
        r = job.get("result") or {}
        print(f"\n{job['status'].upper()}" + (f" · branch {r['branch']}" if r.get("branch") else "") + (f" · {r['prUrl']}" if r.get("prUrl") else ""))
        if job.get("tokens"):
            print(f"{job['tokens']:,} tokens" + (f", ${job['costUsd']:.3f}" if job.get("costUsd") else ""))
        print("\n" + (r.get("answer") or job.get("error") or ""))
        if r.get("diffStat"):
            print("\n" + r["diffStat"])
        if r.get("files"):
            print("Files: " + ", ".join(r["files"]))
        if a.out:
            out = pathlib.Path(a.out) / job["id"][:8]
            out.mkdir(parents=True, exist_ok=True)
            (out / "answer.md").write_text(r.get("answer") or job.get("error") or "")
            (out / "job.json").write_text(json.dumps(job, indent=2))
            for art in sl.artifacts(job["id"]):
                if not art["name"].startswith("files/"):
                    (out / art["name"]).write_text(sl.artifact(job["id"], art["name"]))
            created = sl.download_files(job["id"], str(out / "files"))
            print(f"\nSaved in {out}/" + (f" (+ {len(created)} files in files/: {', '.join(created)})" if created else ""))
        return 0 if job["status"] == "succeeded" else 1
    except SwarmLabError as e:
        print(f"Server: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped watching (the job continues on the server).", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
