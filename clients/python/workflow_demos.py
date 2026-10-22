# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""Complete offline-first workflows. Python 3.8+, standard library only."""
import argparse
import json
import os
from pathlib import Path
import sys
import urllib.parse

from configuration_examples import DEFAULT_SETTING_OVERRIDES, merge_config
from fix_job import ALIASES, reject_secrets
from swarmlab_client import SwarmLabClient, SwarmLabError

HERE = Path(__file__).resolve().parent
MODES = ("single", "tree", "swarm", "graph")
FIXTURE_FILES = ("README.md", ".gitignore", "pricing.py", "labels.py", "test_demo.py")
GOAL = (
    "Repair the two regressions in this tiny stdlib project. Read README.md and test_demo.py. "
    "pricing.total(lines) must sum unit_price * quantity (empty input = 0). "
    "labels.slug(text) must trim, lowercase, and join whitespace-separated words with one hyphen "
    "(blank input = empty string). Keep public function names and do not weaken existing tests. "
    "Change only pricing.py and labels.py; report any additional test suggestions without editing tests. "
    "Run python -m unittest -v before and after edits; report actual exit codes, never assume success. "
    "Use the server's Python command if it differs from python. No dependencies, network, or git commands. "
    "Use native workspace tools; edits and commands require host permission and may need human approval. "
)


def build_job(mode, repo, python_command="python"):
    """Return the complete API body; python_command is a host shell command, not a path."""
    if mode not in MODES or not isinstance(repo, str) or not repo.strip():
        raise ValueError("choose a mode and nonempty registered repository name")
    if python_command not in ("python", "python3", "py -3"):
        raise ValueError("--python-command must be python, python3, or py -3")
    body = {
        "repo": repo, "ref": "demo-baseline", "mode": mode,
        "task": GOAL.replace("python -m unittest", python_command + " -m unittest"),
        "settings": {"maxStepsPerAgent": 24, "maxAgents": 4,
                     "tokenBudget": 80000, "maxTokensPerCall": 2048},
        "timeoutSec": 900, "maxAttempts": 1,
    }
    if mode == "tree":
        body["task"] += (
            " Lead: delegate two independent repair tasks in one message: pricing worker owns only "
            "pricing.py and runs test_demo.PricingTests; labels worker owns only labels.py and runs "
            "test_demo.LabelTests. Give both the contract above. A third read-only verifier runs the "
            "full suite after both reports return, not while edits are pending. Combine their exact "
            "file/test evidence and disclose failures or approval blocks. Workers do not edit each "
            "other's files; the lead cannot inspect files directly."
        )
    elif mode == "swarm":
        body["task"] += (
            " Lead: create persistent workers named pricing, labels, and verifier with distinct "
            "ownership. Pricing alone edits pricing.py; labels alone edits labels.py; verifier is "
            "read-only. Each worker reads read_board first. Repair workers reproduce their component "
            "failure, post_note the cause and proposed change, then implement and post_note the exact "
            "component test output plus READY or BLOCKED. Verifier uses ask_peer to clarify findings, "
            "waits for BOTH READY handoffs on the board, then runs the full suite and posts its exit "
            "code and findings. Lead uses read_board and ask_agent to resolve blockers; ask the owning "
            "worker to repair any failure, never assign a second editor to the same file. Finish only "
            "with an honest summary of tests actually run and unresolved approvals."
        )
    elif mode == "graph":
        body["workflow"] = {
            "start": "plan", "maxSteps": 12,
            "nodes": {
                "plan": {"agent": "planner", "model": "lead", "next": "implement",
                         "task": "{task}\nRead the files and reproduce the baseline failures. Do not edit. Give a short file-by-file repair plan and baseline test evidence."},
                "implement": {"agent": "fixer", "next": "test", "maxVisits": 3, "onLimit": "review",
                              "task": "{task}\nPlan: {node:plan}\nLatest test evidence: {node:test}\nReview: {node:review}\nImplement the smallest repair to pricing.py and labels.py only. Do not change tests. Report edits and approval blocks."},
                "test": {"command": python_command + " -m unittest -v", "onPass": "review",
                         "onFail": "implement", "maxVisits": 3, "onLimit": "review"},
                "review": {"agent": "checker", "maxVisits": 2, "onLimit": "done",
                           "routes": {"approve": "done", "reject": "implement", "else": "done"},
                           "task": "{task}\nPlan: {node:plan}\nImplementation: {node:implement}\nLatest command evidence: {node:test}\nRead the changed source and unchanged tests; do not edit. Approve only if the latest test command ran with exit code 0 and both contracts hold. Otherwise reject with exact remaining problems. Report exhausted retries or missing evidence as NOT VERIFIED, not success. End with DECISION: approve or DECISION: reject."},
            },
        }
    return body


def create_demo(destination):
    """Copy only known fixture files to an explicit new folder. Never invoke Git."""
    dest = Path(destination).expanduser()
    if not dest.is_absolute():
        raise ValueError("--init-demo requires an absolute path")
    dest = dest.resolve()
    # Refuse this distribution/developer checkout and any existing Git ancestor.
    excluded = [HERE]
    developer_root = HERE.parents[1] if len(HERE.parents) > 1 else HERE
    if (developer_root / "package.json").is_file():
        excluded.append(developer_root)
    if any(dest == root or root in dest.parents for root in excluded):
        raise ValueError("choose a dedicated folder outside this checkout/download")
    if any((p / ".git").exists() for p in dest.parents):
        raise ValueError("refusing a folder inside an existing Git workspace")
    dest.mkdir(exist_ok=False)  # Parent must exist; existing files/folders are refused.
    for name in FIXTURE_FILES:
        with (dest / name).open("xb") as target:
            target.write((HERE / "demo_project" / name).read_bytes())
    return dest


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--list", action="store_true")
    p.add_argument("--init-demo", metavar="ABSOLUTE_NEW_FOLDER", help="copy fixture only; does not run Git")
    p.add_argument("--mode", choices=MODES)
    p.add_argument("--repo", help="server registered name, not a local path")
    p.add_argument("--config", help="optional job JSON overrides; settings merge by key")
    p.add_argument("--python-command", choices=("python", "python3", "py -3"), default="python")
    p.add_argument("--url", default=os.environ.get("SWARMLAB_URL", "http://127.0.0.1:8787"))
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="print JSON only (default)")
    g.add_argument("--submit", action="store_true", help="explicitly POST once; never approve or wait")
    a = p.parse_args(argv)
    try:
        if a.list or a.init_demo:
            if a.submit or a.mode or a.repo or a.config or (a.list and a.init_demo):
                raise ValueError("use --list or --init-demo alone")
            if a.list:
                print("\n".join(MODES))
            else:
                print("Created " + str(create_demo(a.init_demo)) + ". Git was NOT run. Follow demo_project/README.md to commit and tag the baseline.")
            return 0
        body = merge_config(build_job(a.mode, a.repo, a.python_command), a.config)
        # This CLI promises mode/repo from explicit flags, and only host-default setting keys.
        body["mode"], body["repo"] = a.mode, a.repo
        if set(body["settings"]) - DEFAULT_SETTING_OVERRIDES:
            raise ValueError("settings outside the server default override allowlist")
        reject_secrets(body)
        url = urllib.parse.urlsplit(a.url)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("use an HTTP(S) URL without credentials, query, or fragment")
        if a.submit:
            client = SwarmLabClient(a.url, api_key=os.environ.get("SWARMLAB_KEY", ""))
            job = client.submit(**{ALIASES.get(k, k): v for k, v in body.items()})
            print("Submitted {}. Status: {}. Not completion or test verification; review Server approvals and follow with fix_job.py --job-id ID --out NEW_FOLDER.".format(job.get("id", "?"), job.get("status", "?")))
        else:
            text = json.dumps(body, indent=2)
            key = os.environ.get("SWARMLAB_KEY", "")
            print(text.replace(key, "[REDACTED]") if key else text)
        return 0
    except (ValueError, TypeError, OSError, SwarmLabError):
        # Never echo credential-bearing configuration, URLs, or server response bodies.
        print("Demo input, I/O, or submission error. Check flags/config, a fresh folder, and host setup. Nothing was approved; inspect Server before retrying a submission.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
