# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""Offline-first job examples. Python 3.8+, standard library only.

Use --list or --example single|tree|swarm|graph. Only --submit uses networking.
Values below are examples, not server defaults or discovered host capabilities.
"""
import argparse
import json
import os
import sys

from swarmlab_client import SwarmLabClient
from fix_job import ALIASES, FIELDS, reject_secrets

# Reference values; only default-allowed settings are included in example jobs.
RUN_SETTINGS = {
    "leadModel": "your-exact-model-id", "workerModel": "your-exact-model-id",
    "maxStepsPerAgent": 12, "maxAgents": 5, "tokenBudget": 100000,
    "maxTokensPerCall": 2048, "allowEdits": True, "allowCommands": True,
    "useMemory": True, "defaultEngine": "native", "commandAllowList": ["git"],
    "chatCompactChars": 120000, "chatKeepMessages": 20,
    "sequentialTools": False, "maxContinuations": 3, "maxInputTokens": 0,
    "answerLength": "normal", "answerStyle": "visual", "ragAuto": True,
    "ragTopK": 6, "ragAutoK": 4, "costBudgetUsd": 5.0,
    "finalAnswerOnLimit": True, "toolMode": "native", "maxParallelCalls": 4,
}

# Exact defaultConfig().allowedSettingOverrides in src/server/config.ts.
# An administrator may change this; this client does not discover host policy.
DEFAULT_SETTING_OVERRIDES = {
    "maxStepsPerAgent", "maxAgents", "tokenBudget", "maxTokensPerCall",
    "answerLength", "answerStyle", "toolMode", "maxContinuations",
    "ragTopK", "maxParallelCalls",
}


def intersect_allowlist(settings, allowlist):
    """Select reference values for the explicitly supplied allowlist."""
    return {k: v for k, v in settings.items() if k in allowlist}


def build_examples():
    """Build bodies without network access; demo-app must exist on the host."""
    tasks = {
        "single": "Fix the failing date-parsing test in src/dates.py.",
        "tree": "Split the parser into focused modules and update the callers.",
        "swarm": "Independently evaluate three JSON libraries and compare results.",
        "graph": "Review the date parser and summarize recommended fixes.",
    }
    examples = {mode: {
        "repo": "demo-app", "task": task, "mode": mode,
        "settings": intersect_allowlist(RUN_SETTINGS, DEFAULT_SETTING_OVERRIDES),
    } for mode, task in tasks.items()}
    examples["graph"]["workflow"] = {
        "start": "review", "nodes": {"review": {"next": "done"}},
    }
    return examples


EXAMPLES = {
    "single": "One agent fixes a test.",
    "tree": "Lead and workers split a module.",
    "swarm": "Independent agents evaluate alternatives.",
    "graph": "An inline one-step review workflow.",
}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default=os.environ.get("SWARMLAB_URL", "http://127.0.0.1:8787"))
    p.add_argument("--example", choices=list(EXAMPLES))
    p.add_argument("--list", action="store_true")
    p.add_argument("--config", help="JSON job fields merged over the example; settings merge by key")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="print only (default)")
    g.add_argument("--submit", action="store_true", help="POST to the chosen server")
    return p


def merge_config(example, config_path):
    extra = {}
    if config_path:
        with open(config_path, encoding="utf-8-sig") as f:
            extra = json.load(f)
    if not isinstance(extra, dict):
        raise ValueError("--config must be a JSON object")
    reject_secrets(extra)
    if set(extra) - FIELDS:
        raise ValueError("unknown config fields: " + ", ".join(sorted(set(extra) - FIELDS)))
    merged = dict(example)
    merged.update({k: v for k, v in extra.items() if k != "settings"})
    if "settings" in extra:
        if not isinstance(extra["settings"], dict):
            raise ValueError("settings must be an object")
        merged["settings"] = dict(example.get("settings", {}), **extra["settings"])
    reject_secrets(merged)
    return merged


def main(argv=None):
    a = parser().parse_args(argv)
    if a.list:
        for name in sorted(EXAMPLES):
            print(f"{name:8} {EXAMPLES[name]}")
        return 0
    if not a.example:
        print("choose --example (or --list). Nothing was submitted.", file=sys.stderr)
        return 2
    try:
        body = merge_config(build_examples()[a.example], a.config)
    except (ValueError, OSError) as e:
        # Do not echo config contents or credential-bearing parser errors.
        print("Invalid configuration ({}).".format(type(e).__name__), file=sys.stderr)
        return 2
    if a.submit:
        client = SwarmLabClient(a.url, api_key=os.environ.get("SWARMLAB_KEY", ""))
        job = client.submit(**{ALIASES.get(k, k): v for k, v in body.items()})
        print("Submitted", job.get("id", "?") + ". Status:", job.get("status", "?"))
        return 0
    text = json.dumps(body, indent=2, ensure_ascii=False)
    key = os.environ.get("SWARMLAB_KEY", "")
    print(text.replace(key, "[REDACTED]") if key else text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
