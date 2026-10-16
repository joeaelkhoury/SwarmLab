"""
Swarm Lab server client (Python 3.8+, standard library only).

    from swarmlab_client import SwarmLabClient
    sl = SwarmLabClient("http://127.0.0.1:8787", api_key="sl_...")
    job = sl.submit(repo="app", task="Fix the failing date test", mode="graph", workflow="default")
    for ev in sl.stream(job["id"]):           # live events until the job ends
        print(ev["event"]["kind"])
    job = sl.get(job["id"])                   # final state: status, result.answer, result.branch, ...
    patch = sl.artifact(job["id"], "changes.patch")
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Iterator, List, Optional

FINISHED = ("succeeded", "failed", "cancelled")


class SwarmLabError(Exception):
    """An error answered by the server (status code and message)."""

    def __init__(self, status: int, message: str):
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


class SwarmLabClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8787", api_key: str = "", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    # ---------- low level ----------

    def _request(self, method: str, path: str, body: Any = None, raw: bool = False) -> Any:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("content-type", "application/json")
        if self.api_key:
            req.add_header("authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                text = r.read().decode()
        except urllib.error.HTTPError as e:
            text = e.read().decode()
            try:
                msg = json.loads(text).get("error", text)
            except ValueError:
                msg = text or e.reason
            raise SwarmLabError(e.code, msg) from None
        if raw:
            return text
        return json.loads(text) if text else {}

    # ---------- jobs ----------

    def submit(self, repo: Optional[str], task: str, mode: str = "single", *, files: Optional[bool] = None, workflow: Any = None, agent: Optional[str] = None,
               ref: Optional[str] = None, priority: int = 0, approvals: Optional[Dict[str, Any]] = None,
               settings: Optional[Dict[str, Any]] = None, labels: Optional[Dict[str, str]] = None,
               webhook: Optional[str] = None, idempotency_key: Optional[str] = None,
               max_attempts: Optional[int] = None, timeout_sec: Optional[int] = None) -> Dict[str, Any]:
        """Queue a job. Returns the job (status "queued"). The same idempotency_key returns the existing job.

        repo=None: a job without a repository (ideas, tickets, diagrams, documents) in a fresh empty workspace.
        files=True: every created or changed file comes back as its own artifact (default: True without a repository)."""
        body: Dict[str, Any] = {"task": task, "mode": mode, "priority": priority}
        if repo:
            body["repo"] = repo
        for k, v in (("files", files), ("workflow", workflow), ("agent", agent), ("ref", ref), ("approvals", approvals), ("settings", settings),
                     ("labels", labels), ("webhook", webhook), ("idempotencyKey", idempotency_key),
                     ("maxAttempts", max_attempts), ("timeoutSec", timeout_sec)):
            if v is not None:
                body[k] = v
        return self._request("POST", "/v1/jobs", body)

    def get(self, job_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/jobs/{job_id}")

    def list(self, status: Optional[List[str]] = None, repo: Optional[str] = None, label: Optional[str] = None,
             limit: int = 50, before: Optional[str] = None) -> Dict[str, Any]:
        q = {"limit": limit}
        if status:
            q["status"] = ",".join(status)
        if repo:
            q["repo"] = repo
        if label:
            q["label"] = label            # "key=value"
        if before:
            q["before"] = before
        return self._request("GET", "/v1/jobs?" + urllib.parse.urlencode(q))

    def cancel(self, job_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/v1/jobs/{job_id}/cancel")

    def retry(self, job_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/v1/jobs/{job_id}/retry")

    def events(self, job_id: str, after: int = 0, limit: int = 500) -> List[Dict[str, Any]]:
        return self._request("GET", f"/v1/jobs/{job_id}/events?after={after}&limit={limit}")["events"]

    def stream(self, job_id: str, after: int = 0) -> Iterator[Dict[str, Any]]:
        """Live events (server-sent events) until the job ends. Reconnects after a network cut, without repeats."""
        last = after
        while True:
            req = urllib.request.Request(f"{self.base_url}/v1/jobs/{job_id}/stream?after={last}")
            if self.api_key:
                req.add_header("authorization", f"Bearer {self.api_key}")
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    event_name, data = "message", []
                    for raw in r:
                        line = raw.decode().rstrip("\n").rstrip("\r")
                        if line.startswith("event:"):
                            event_name = line[6:].strip()
                        elif line.startswith("data:"):
                            data.append(line[5:].strip())
                        elif line == "" and data:
                            payload = json.loads("\n".join(data))
                            if event_name == "end":
                                return
                            last = payload["seq"]
                            yield payload
                            event_name, data = "message", []
                return
            except urllib.error.HTTPError as e:
                raise SwarmLabError(e.code, e.read().decode()) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(2)  # reconnect and continue after the last event received
                if self.get(job_id)["status"] in FINISHED and not self.events(job_id, after=last, limit=1):
                    return

    def wait(self, job_id: str, poll: float = 2.0, timeout: Optional[float] = None,
             on_approval: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None) -> Dict[str, Any]:
        """Wait until the job ends. on_approval(approval) can answer approvals: return {"decision": "approve"|"reject", ...} or None to leave it."""
        t0, seen = time.time(), set()
        while True:
            job = self.get(job_id)
            if job["status"] in FINISHED:
                return job
            if job["status"] == "waiting" and on_approval:
                for a in self.job_approvals(job_id):
                    if a["status"] == "pending" and a["id"] not in seen:
                        seen.add(a["id"])
                        answer = on_approval(a)
                        if answer:
                            self.decide(a["id"], **answer)
            if timeout and time.time() - t0 > timeout:
                raise TimeoutError(f"job {job_id} is still {job['status']}")
            time.sleep(poll)

    def run(self, repo: Optional[str], task: str, mode: str = "single", **kw: Any) -> Dict[str, Any]:
        """Submit and wait; returns the finished job."""
        on_approval = kw.pop("on_approval", None)
        job = self.submit(repo, task, mode, **kw)
        return self.wait(job["id"], on_approval=on_approval)

    # ---------- artifacts ----------

    def artifacts(self, job_id: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/v1/jobs/{job_id}/artifacts")["artifacts"]

    def artifact(self, job_id: str, name: str) -> str:
        """"changes.patch" (the diff), "report.json" (answer, metrics, every agent), or "files/<path>" (a created file)."""
        return self._request("GET", f"/v1/jobs/{job_id}/artifacts?name={urllib.parse.quote(name, safe='')}", raw=True)

    def download_files(self, job_id: str, folder: str) -> List[str]:
        """Save every created or changed file of a job (needs files=True) under folder, with its path. Returns the paths."""
        import os
        saved = []
        for a in self.artifacts(job_id):
            if not a["name"].startswith("files/"):
                continue
            rel = a["name"][len("files/"):]
            target = os.path.normpath(os.path.join(folder, rel))
            if not target.startswith(os.path.normpath(folder)):
                continue  # never write outside the folder
            os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(self.artifact(job_id, a["name"]))
            saved.append(rel)
        return saved

    # ---------- approvals ----------

    def approvals(self, status: str = "pending") -> List[Dict[str, Any]]:
        return self._request("GET", f"/v1/approvals?status={status}")["approvals"]

    def job_approvals(self, job_id: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/v1/jobs/{job_id}/approvals")["approvals"]

    def decide(self, approval_id: str, decision: str, choice: Optional[str] = None, text: Optional[str] = None) -> Dict[str, Any]:
        """decision: "approve" or "reject". choice: one of the approval's choices. text: an edited message or task."""
        body: Dict[str, Any] = {"decision": decision}
        if choice is not None:
            body["choice"] = choice
        if text is not None:
            body["text"] = text
        return self._request("POST", f"/v1/approvals/{approval_id}", body)

    # ---------- server ----------

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/health")

    def repos(self) -> List[str]:
        return self._request("GET", "/v1/repos")["repos"]
