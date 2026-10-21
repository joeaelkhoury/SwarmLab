#!/usr/bin/env python3
"""
Full test of a Swarm Lab server from a script (Python 3.8+, standard library only).

    python full_test.py --url http://127.0.0.1:8787 --key sl_... --repo app --out reports
    python full_test.py ... --experiment          # also a small experiment: single vs swarm, with a cost limit

What it does:
  1. Starts two small local servers inside this script: an MCP server (one tool, project_facts) and a hook receiver
     (it checks each call's signature, logs every event, and denies list_files with a note).
  2. Saves a profile on the server: agents, prompts, an inline skill, the independent check of "done", the hooks and the
     MCP server. (Writing a profile needs a key with the approve or admin role; the server must allow 127.0.0.1 in
     "hooks.allowHosts" and "mcpAllowHosts", as run_full_test.sh does.)
  3. Runs a single job, then a swarm and a graph job, all from that profile and sharing one memory session.
  4. Prints and saves each job's full report (every step with tokens, cost and time; totals by agent and model;
     memory; what the hooks allowed or blocked), what the hooks and the MCP server saw, and the usage reports.

Exit code 0 when every job ended, every report could be read, and the hooks and the MCP server were reached; 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from swarmlab_client import FINISHED, SwarmLabClient, SwarmLabError

HOOK_SECRET = "full-test-secret"

POLICY = {"agents": {
    "reviewer": {"tools": ["list_files", "read_file", "search_text", "use_skill"]},
    "planner": {"tools": ["list_files", "read_file", "search_text", "use_skill"]},
    "writer": {"editPaths": [".swarmlab/out/**"]},
}}
PROMPTS = {"agents": {
    "reviewer": "Be concrete: name files and lines. Rank by impact. Approve only work that is complete.",
    "planner": "Plan in short numbered steps, each with the files it touches.",
    "writer": "Write plain Markdown for a busy reader: headings, short paragraphs, no filler.",
}}
SKILLS = [{"name": "project-overview", "description": "When asked to explain or map a project",
           "instructions": "1. Read README.md first.\n2. List the main folders and what each holds.\n3. Name the entry points.\n4. Say how to run the tests."}]
WORKFLOW = {
    "start": "plan", "maxSteps": 8,
    "nodes": {
        "plan": {"agent": "planner", "task": "Task: {task}\nRead the project and plan a one-page overview. Do not edit.", "next": "write"},
        "write": {"agent": "writer", "maxVisits": 3, "onLimit": "done", "next": "review",
                  "task": "Plan:\n{node:plan}\n\nReview feedback (if any):\n{node:review}\n\nWrite .swarmlab/out/overview.md with write_file."},
        "review": {"agent": "reviewer", "maxVisits": 2, "onLimit": "done", "routes": {"approve": "done", "reject": "write"},
                   "task": "Read .swarmlab/out/overview.md. Approve if it is accurate and complete, otherwise reject with exact fixes."},
    },
}
SESSION = {"session": "full-test", "topics": ["overview"]}


# ---------- 1. Two local servers: an MCP server and a hook receiver ----------

class Log:
    def __init__(self):
        self.lock = threading.Lock()
        self.items = []

    def add(self, x):
        with self.lock:
            self.items.append(x)


MCP_LOG, HOOK_LOG = Log(), Log()


class McpHandler(BaseHTTPRequestHandler):
    """A minimal MCP server over HTTP (JSON-RPC): initialize, tools/list, tools/call."""
    def log_message(self, *a):  # quiet
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("content-length") or 0)) or b"{}")
        method, rid = req.get("method"), req.get("id")
        MCP_LOG.add(method)
        if rid is None:  # a notification
            self.send_response(202); self.end_headers(); return
        if method == "initialize":
            result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "full-test-facts", "version": "1"}}
        elif method == "tools/list":
            result = {"tools": [{"name": "project_facts", "description": "Facts about this project the code does not say (owners, release dates).",
                                 "inputSchema": {"type": "object", "properties": {"topic": {"type": "string"}}}}]}
        elif method == "tools/call":
            result = {"content": [{"type": "text", "text": "Owner: the platform team. Next release: Friday. Tests run with pytest."}]}
        else:
            result = {}
        body = json.dumps({"jsonrpc": "2.0", "id": rid, "result": result}).encode()
        self.send_response(200); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(body))); self.end_headers()
        self.wfile.write(body)


class HookHandler(BaseHTTPRequestHandler):
    """Checks the signature, logs the event, denies list_files (with a note), allows the rest."""
    def log_message(self, *a):
        pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        good = SwarmLabClient.verify_signature(HOOK_SECRET, raw, self.headers.get("x-swarmlab-signature", ""))
        ev = json.loads(raw or b"{}")
        HOOK_LOG.add({"event": ev.get("event"), "tool": ev.get("tool"), "signed": good, "job": (ev.get("job") or {}).get("id", "")[:8]})
        answer = {}
        if ev.get("event", "").startswith("before:"):
            if not good:
                answer = {"decision": "deny", "note": "bad signature"}
            elif ev.get("tool") == "list_files":
                answer = {"decision": "deny", "note": "Listing every file is not allowed in this test: read README.md instead."}
            else:
                answer = {"decision": "allow"}
        body = json.dumps(answer).encode()
        self.send_response(200); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(body))); self.end_headers()
        self.wfile.write(body)


def serve(handler) -> str:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


def money(x: float) -> str:
    return f"${x:.4f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=os.environ.get("SWARMLAB_URL", "http://127.0.0.1:8787"))
    ap.add_argument("--key", default=os.environ.get("SWARMLAB_KEY", ""))
    ap.add_argument("--repo", default=os.environ.get("SWARMLAB_REPO", "app"), help="a repository from the server's configuration")
    ap.add_argument("--out", default="swarmlab-reports", help="folder for the reports")
    ap.add_argument("--profile", default="full-test", help="name of the profile to save and use")
    ap.add_argument("--timeout", type=float, default=900, help="seconds to wait for each job")
    ap.add_argument("--experiment", action="store_true", help="also run a small experiment (single vs swarm)")
    ap.add_argument("--max-cost", type=float, default=1.0, help="cost limit of the experiment, USD")
    a = ap.parse_args()

    sl = SwarmLabClient(a.url, api_key=a.key, timeout=60)
    os.makedirs(a.out, exist_ok=True)
    mcp_url, hook_url = serve(McpHandler), serve(HookHandler)
    print(f"local MCP server {mcp_url}/mcp · hook receiver {hook_url}/hook")

    # ---------- 2. The profile: everything a job is configured with ----------
    profile = {
        "description": "Swarm Lab full test: agents, prompts, a skill, checks, hooks, an MCP server",
        "policy": POLICY, "prompts": PROMPTS, "skills": SKILLS,
        "checks": {"verify": True},
        "mcp": {"add": {"facts": {"url": f"{mcp_url}/mcp"}}},
        "hooks": [{"url": f"{hook_url}/hook", "events": ["before:command", "before:edit", "before:tool", "after:call", "after:edit", "after:command", "after:verify", "job:end"],
                   "secret": HOOK_SECRET, "timeoutMs": 3000}],
        "approvals": {"mcp": "auto"},
    }
    saved = sl.put_profile(a.profile, profile)
    print(f"profile {a.profile!r} saved ({saved.get('updatedAt', '')}); profiles on the server: {', '.join(p['name'] for p in sl.profiles())}")

    labels = {"suite": "full-test", "run": time.strftime("%Y%m%d-%H%M%S")}
    ok = True

    # ---------- 3. Three jobs from the profile, sharing one memory session ----------
    first = sl.submit(a.repo, "Review this repository and list its three most important improvements, with the files concerned.", "single",
                      agent="reviewer", profile=a.profile, memory=SESSION, labels={**labels, "kind": "single"})
    print(f"submitted single {first['id']}")
    sl.wait(first["id"], poll=1, timeout=a.timeout)
    jobs = {
        "single": first,
        "swarm": sl.submit(a.repo, "Map the structure of this project: what each part does and how the parts connect.", "swarm",
                           settings={"maxAgents": 3}, profile=a.profile, memory=SESSION, labels={**labels, "kind": "swarm"}),
        "graph": sl.submit(a.repo, "Write a one-page overview of this project for a new team member.", "graph",
                           workflow=WORKFLOW, profile=a.profile, memory=SESSION, labels={**labels, "kind": "graph"}),
    }
    for kind in ("swarm", "graph"):
        print(f"submitted {kind:6} {jobs[kind]['id']}")

    t0, done = time.time(), {}
    while len(done) < len(jobs):
        for kind, j in jobs.items():
            if kind in done:
                continue
            cur = sl.get(j["id"])
            if cur["status"] in FINISHED:
                done[kind] = cur
                print(f"{kind:6} {cur['status']:9} {cur.get('tokens') or 0:>9,} tokens  {money(cur.get('costUsd') or 0)}")
        if time.time() - t0 > a.timeout:
            print("timeout: some jobs did not end", file=sys.stderr)
            return 1
        if len(done) < len(jobs):
            time.sleep(1)
    time.sleep(1)  # let the last after-hooks arrive

    # ---------- 4. Reports, hooks, MCP, usage ----------
    print("\nReports")
    for kind, j in done.items():
        try:
            md, rep = sl.report(j["id"], "md"), sl.report(j["id"], "json")
        except SwarmLabError as e:
            print(f"  {kind}: no report ({e})", file=sys.stderr); ok = False; continue
        path = os.path.join(a.out, f"{kind}-{j['id'][:8]}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        t = rep["totals"]
        print(f"  {kind:6} {t['calls']} calls · {t['tokensIn']:,} in · {t['tokensOut']:,} out · {money(t['costUsd'])} · {t['tools']} tools"
              f" · {t.get('blocked', 0)} blocked by hooks · memory used {len(rep['memory']['used'])}"
              f"{' · check: ' + rep['verify']['status'] if rep.get('verify') else ''} → {path}")
        for model, u in sorted(rep["byModel"].items(), key=lambda kv: -kv[1]["costUsd"]):
            print(f"         {model:28} {u['calls']:>3} calls  {u['tokensIn'] + u['tokensOut']:>9,} tokens  {money(u['costUsd'])}")
        for s in rep["steps"]:
            if s["kind"] == "hook" and "denied" in s["what"]:
                print(f"         blocked: {s['what']}")
                break
        if j["status"] != "succeeded":
            print(f"         ended {j['status']}: {j.get('error') or ''}"[:200])

    hooks = HOOK_LOG.items
    by_event = {}
    for h in hooks:
        by_event[h["event"]] = by_event.get(h["event"], 0) + 1
    denied = sum(1 for h in hooks if h["event"] == "before:tool" and h["tool"] == "list_files")
    print(f"\nHooks: {len(hooks)} calls, all signed: {all(h['signed'] for h in hooks)} · " + ", ".join(f"{k} {v}" for k, v in sorted(by_event.items())) + f" · list_files denied {denied}×")
    print(f"MCP server: {', '.join(sorted(set(MCP_LOG.items))) or 'not called'} ({len(MCP_LOG.items)} requests)")
    if not hooks or not all(h["signed"] for h in hooks) or by_event.get("job:end", 0) < len(jobs):
        print("  the hooks were not all reached or not all signed", file=sys.stderr); ok = False
    if "tools/list" not in MCP_LOG.items:
        print("  the MCP server was not reached", file=sys.stderr); ok = False

    print("\nUsage by mode (these jobs)")
    print(sl.costs(group_by="mode", fmt="md", label=f"run={labels['run']}"))
    by_model = sl.costs(group_by="model", label=f"run={labels['run']}")
    print("Usage by model:", ", ".join(f"{r['group']} {money(r['costUsd'])}" for r in by_model["rows"]) or "none")
    with open(os.path.join(a.out, "usage-by-day.csv"), "w", encoding="utf-8") as f:
        f.write(sl.costs(group_by="day", fmt="csv"))
    with open(os.path.join(a.out, "usage-by-kind.md"), "w", encoding="utf-8") as f:
        f.write(sl.costs(group_by="label:kind", fmt="md", label=f"suite={labels['suite']}"))
    print(f"Saved {a.out}/usage-by-day.csv and {a.out}/usage-by-kind.md")

    if a.experiment:
        suite = {"name": "full-test experiment", "repeats": 2,
                 "setups": [{"name": "single", "mode": "single"}, {"name": "swarm", "mode": "swarm", "maxStepsPerAgent": 6}],
                 "tasks": [{"id": "explain", "task": "Explain what this project does in five lines.", "checks": [{"type": "files", "unchanged": ["**"]}]}]}
        x = sl.submit_experiment(suite, a.repo, concurrency=2, max_cost_usd=a.max_cost, label="full-test")
        print(f"\nExperiment {x['id']}: {x['total']} runs")
        x = sl.wait_experiment(x["id"], poll=2, on_progress=lambda e: print(f"  {e['done']}/{e['total']} done, {e['passed']} passed, {money(e['costUsd'])}"))
        for s in x.get("summary") or []:
            print(f"  {s['setup']:8} {s['passed']}/{s['runs']} passed · {s['avgTokens']:,} tokens/run · {money(s['costUsd'])}")
        print(f"  ended {x['status']}{' (' + x['reason'] + ')' if x.get('reason') else ''}")
        ok = ok and x["status"] in ("done", "stopped")

    return 0 if ok and all(j["status"] in FINISHED for j in done.values()) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SwarmLabError as e:
        print(f"server error {e.status}: {e}", file=sys.stderr)
        sys.exit(1)
