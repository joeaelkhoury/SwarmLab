# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""Bounded server fix jobs; Python 3.8+, standard library only.

Import build_payload() or main(argv) from scripts. No approvals are answered.
Exit: 0 succeeded/dry-run, 1 failed, 2 input/transport/report error,
3 cancelled, 4 waiting for approval, 5 local deadline (job continues).
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse

from swarmlab_client import SwarmLabClient, SwarmLabError

# JSON uses API (camelCase) names, not Python client's keyword spellings.
FIELDS = set("task repo mode profile agent ref policy prompts workflow harness providers checks settings models rag decision web data files idempotencyKey timeoutSec maxAttempts labels memory mcp skills hooks priority".split())
ALIASES = {"idempotencyKey": "idempotency_key", "timeoutSec": "timeout_sec", "maxAttempts": "max_attempts"}
SECRET = re.compile(r"^(key|api[-_]?key|authorization|password|secret|token|credentials|headers|extraHeaders)$", re.I)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default=os.environ.get("SWARMLAB_URL", "http://127.0.0.1:8787"))
    p.add_argument("--config", help="UTF-8 JSON job fields; explicit CLI values win")
    r = p.add_mutually_exclusive_group()
    r.add_argument("--repo", help="server repository name, not a local path")
    r.add_argument("--no-repo", action="store_true")
    t = p.add_mutually_exclusive_group()
    t.add_argument("--task")
    t.add_argument("--task-file")
    for name in ("mode", "profile", "agent", "ref", "lead-model", "worker-model", "idempotency-key"):
        p.add_argument("--" + name)
    for name in ("token-budget", "max-steps", "max-tokens-per-call", "job-timeout"):
        p.add_argument("--" + name, type=int)
    p.add_argument("--job-id", help="follow an existing job; do not submit")
    p.add_argument("--out", required=True, help="explicit local report directory; files never overwritten")
    p.add_argument("--wait", type=float, default=600, help="local deadline seconds, including requests")
    p.add_argument("--poll", type=float, default=2)
    p.add_argument("--request-timeout", type=float, default=30)
    p.add_argument("--dry-run", action="store_true")
    return p


def reject_secrets(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if SECRET.fullmatch(k):
                raise ValueError("credentials/headers are not allowed in job configuration; configure the host")
            reject_secrets(v)
    elif isinstance(value, list):
        for v in value:
            reject_secrets(v)


def positive(value, name, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0 or (integer and not isinstance(value, int)):
        raise ValueError(name + " must be a positive " + ("integer" if integer else "finite number"))


def build_payload(a):
    """Defaults < JSON < explicit CLI; settings merge by key, not whole-object replacement.

    Profiles/harnesses resolve on the server; this is not an effective-policy preview.
    """
    body = {}
    if a.config:
        with open(a.config, encoding="utf-8-sig") as f:
            body = json.load(f)
        if not isinstance(body, dict):
            raise ValueError("config must be a JSON object")
        if set(body) - FIELDS:
            raise ValueError("unknown config fields: " + ", ".join(sorted(set(body) - FIELDS)))
    reject_secrets(body)
    for field in ("policy", "prompts", "harness", "providers", "checks", "settings", "models", "data", "labels", "mcp"):
        if field in body and not isinstance(body[field], dict):
            raise ValueError(field + " must be an object")
    for field in ("mode", "profile", "agent", "ref", "repo", "task"):
        value = getattr(a, field)
        if value is not None:
            body[field] = value
    if a.task_file:
        body["task"] = Path(a.task_file).read_text(encoding="utf-8-sig")
    if a.no_repo:
        body.pop("repo", None)
    for field, value in (("idempotencyKey", a.idempotency_key), ("timeoutSec", a.job_timeout)):
        if value is not None:
            body[field] = value
    settings = dict(body.get("settings", {}))
    for field, value in (("leadModel", a.lead_model), ("workerModel", a.worker_model), ("tokenBudget", a.token_budget), ("maxStepsPerAgent", a.max_steps), ("maxTokensPerCall", a.max_tokens_per_call)):
        if value is not None:
            settings[field] = value
    if a.lead_model is not None or a.worker_model is not None:
        body["models"] = dict(body.get("models", {}), auto="off")
    if settings:
        body["settings"] = settings
    for k in ("tokenBudget", "maxStepsPerAgent", "maxTokensPerCall", "maxAgents"):
        if k in settings:
            positive(settings[k], "settings." + k, integer=True)
    for k in ("leadModel", "workerModel"):
        if k in settings and (not isinstance(settings[k], str) or not settings[k].strip() or settings[k].startswith("auto:")):
            raise ValueError(k + " must be an exact nonempty model ID, not auto:...")
    for k in ("timeoutSec", "maxAttempts"):
        if k in body:
            positive(body[k], k, integer=True)
    if not a.job_id and (not isinstance(body.get("task"), str) or not body["task"].strip()):
        raise ValueError("provide --task, --task-file or config task")
    for k in ("repo", "profile", "agent", "ref", "idempotencyKey"):
        if k in body and (not isinstance(body[k], str) or not body[k].strip()):
            raise ValueError(k + " must be a nonempty string")
    mode = body.get("mode", body.get("harness", {}).get("mode", "single"))
    if mode not in ("single", "tree", "swarm", "graph", "auto"):
        raise ValueError("mode must be single, tree, swarm, graph or auto")
    if "agent" in body and (mode != "single" or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", body["agent"])):
        raise ValueError("agent requires single mode and 1–64 letters, digits, _ or -")
    if "ref" in body and (not body.get("repo") or not re.fullmatch(r"[\w./-]+", body["ref"])):
        raise ValueError("ref requires a repository and a valid Git reference")
    for flag in ("rag", "decision"):
        if flag in body and body[flag] not in ("on", "off", "inherit"):
            raise ValueError(flag + " must be on, off or inherit (API field is singular decision)")
    if a.job_id and body:
        raise ValueError("--job-id cannot be combined with submission fields/config")
    return body


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError("server returned an unsafe job ID")
    return value


def run(a, body, client, emit=print):
    """Reusable orchestration with an injected client; no approval or artifact downloads."""
    deadline = time.monotonic() + a.wait

    def request(fn, *args, **kwargs):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        client.timeout = min(a.request_timeout, remaining)
        return fn(*args, **kwargs)

    def save(name, text):
        # Fixed local filenames only; exclusive creation rejects existing files/symlinks.
        folder = Path(a.out)
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / name).open("x", encoding="utf-8") as f:
            f.write(clean(text))

    key = os.environ.get("SWARMLAB_KEY", "")

    def clean(text):
        return text.replace(key, "[REDACTED]") if key else text

    job = None
    try:
        if a.job_id:
            job = request(client.get, safe_id(a.job_id))
        else:
            kwargs = {ALIASES.get(k, k): v for k, v in body.items()}
            kwargs.setdefault("repo", None)
            # Do not let the client default single mode shadow a profile/harness mode.
            kwargs.setdefault("mode", None)
            job = request(client.submit, **kwargs)
        job_id = safe_id(job.get("id"))
        emit("Job " + job_id)
        while True:
            status = job.get("status")
            if status in ("succeeded", "failed", "cancelled", "waiting"):
                save("job.json", json.dumps(job, indent=2, ensure_ascii=False))
                emit("Status: " + status)
                if status == "waiting":
                    emit("Review Server tab → Waiting for you on the server, or dashboard approvals. No approval was sent. Follow later with --job-id " + job_id + " and a new --out directory.")
                    return 4
                for fmt in ("md", "json"):
                    report = request(client.report, job_id, fmt)
                    save("report." + fmt, report if isinstance(report, str) else json.dumps(report, indent=2, ensure_ascii=False))
                return {"succeeded": 0, "failed": 1, "cancelled": 3}[status]
            if status not in ("queued", "running"):
                raise ValueError("unexpected job status")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            time.sleep(min(a.poll, remaining))
            job = request(client.get, job_id)
    except TimeoutError:
        emit("Local deadline reached; no cancellation sent. Inspect the job in Server/dashboard; follow with --job-id and a new --out directory.")
        return 5


def main(argv=None):
    a = parser().parse_args(argv)
    key = os.environ.get("SWARMLAB_KEY", "")
    try:
        for name in ("wait", "poll", "request_timeout"):
            positive(getattr(a, name), name)
        url = urllib.parse.urlsplit(a.url)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("URL must be HTTP(S), without credentials, query or fragment")
        body = build_payload(a)
        if a.job_id:
            safe_id(a.job_id)
        if a.dry_run:
            text = json.dumps({"jobId": a.job_id} if a.job_id else body, indent=2, ensure_ascii=False)
            print(text.replace(key, "[REDACTED]") if key else text)
            return 0
        return run(a, body, SwarmLabClient(a.url, api_key=key), emit=lambda text: print(text.replace(key, "[REDACTED]") if key else text))
    except SwarmLabError as e:
        hints = {400: "Check config fields, profile, host feature gates and allowedSettingOverrides.", 401: "Set SWARMLAB_KEY to the server access key.", 403: "Check key roles (submit/read) and host allowlists.", 404: "Check URL, job/profile name and report availability.", 409: "Check the job state.", 429: "Queue/active-job limit; retry later with the same idempotency key."}
        # Server response bodies can echo credentials; never print them.
        print("HTTP {}. {}".format(e.status, hints.get(e.status, "Inspect server logs; retry submission only with the same idempotency key.")), file=sys.stderr)
        return 2
    except (urllib.error.URLError, OSError) as e:
        # Do not echo exception text: it may include URLs, headers or payloads.
        print("Network or report I/O error ({}). Check server/TLS, permissions and an unused --out directory. A submitted job may still run; inspect Server before retrying.".format(type(e).__name__), file=sys.stderr)
        return 2
    except (ValueError, TypeError) as e:
        # JSON parser diagnostics can include source text; keep them private.
        message = "Invalid JSON configuration." if isinstance(e, json.JSONDecodeError) else str(e)
        print(message.replace(key, "[REDACTED]") if key else message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
