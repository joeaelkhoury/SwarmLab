"""Offline regression tests: python -m unittest discover -s clients/python -p test_*.py."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error

import fix_job
from swarmlab_client import SwarmLabClient, SwarmLabError


class FixJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = str(Path(self.temp.name) / "reports")

    def args(self, *args):
        return fix_job.parser().parse_args(["--out", self.out] + list(args))

    def config(self, value):
        p = Path(self.temp.name) / "config.json"
        p.write_text(json.dumps(value), encoding="utf-8")
        return str(p)

    def client(self, status):
        c = Mock()
        c.submit.return_value = {"id": "job-1", "status": status, "result": {"branch": "fix/job-1"}}
        c.report.side_effect = ["# Report", {"steps": []}]
        return c

    def test_actual_http_payload_new_fields_and_legacy_defaults(self):
        response = Mock()
        response.read.return_value = b'{"id":"j"}'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            c = SwarmLabClient(api_key="private")
            extra = {"harness": {"version": 1, "name": "fix", "mode": "tree"}, "providers": {"rag": {"topK": 3}}, "rag": "off", "decision": "inherit", "web": False, "data": {"inputs": ["README.md"]}}
            c.submit("app", "fix", **extra)
            req = urlopen.call_args[0][0]
            self.assertEqual(req.method, "POST")
            self.assertEqual(req.full_url, "http://127.0.0.1:8787/v1/jobs")
            self.assertEqual(req.get_header("Authorization"), "Bearer private")
            self.assertEqual(json.loads(req.data), dict(extra, repo="app", task="fix", mode="single", priority=0))
            c.submit(None, "fix", mode=None)
            self.assertEqual(json.loads(urlopen.call_args[0][0].data), {"task": "fix", "priority": 0})

    def test_precedence_and_task_file(self):
        cfg = self.config({"task": "old", "repo": "app", "settings": {"tokenBudget": 100, "maxStepsPerAgent": 5}, "models": {"auto": "best"}, "checks": {"verify": True}})
        task = Path(self.temp.name) / "task.txt"
        task.write_text("Fix UTF-8: café", encoding="utf-8")
        b = fix_job.build_payload(self.args("--config", cfg, "--task-file", str(task), "--no-repo", "--token-budget", "200", "--lead-model", "exact/id"))
        self.assertNotIn("repo", b)
        self.assertEqual(b["task"], "Fix UTF-8: café")
        self.assertEqual(b["settings"], {"tokenBudget": 200, "maxStepsPerAgent": 5, "leadModel": "exact/id"})
        self.assertEqual(b["models"], {"auto": "off"})
        self.assertEqual(b["checks"], {"verify": True})

    def test_validation(self):
        for config in ([1], {"decisions": True}, {"settings": []}, {"policy": {"apiKey": "secret"}}, {"task": ""}, {"agent": "x", "mode": "tree", "task": "x"}, {"task": "x", "settings": {"tokenBudget": True}}, {"task": "x", "decision": True}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                fix_job.build_payload(self.args("--config", self.config(config)))
        for flags in (("--max-steps", "0"), ("--lead-model", "auto:best"), ("--ref", "HEAD", "--no-repo")):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                fix_job.build_payload(self.args("--task", "fix", *flags))

    def test_dry_run_no_client_network_or_files_and_redaction(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"SWARMLAB_KEY": "hidden"}), patch("fix_job.SwarmLabClient") as c, contextlib.redirect_stdout(output):
            code = fix_job.main(["--out", self.out, "--task", "Do not echo hidden", "--dry-run"])
        self.assertEqual(code, 0)
        c.assert_not_called()
        self.assertNotIn("hidden", output.getvalue())
        self.assertFalse(Path(self.out).exists())

    def test_terminal_reports(self):
        for status, code in (("succeeded", 0), ("failed", 1), ("cancelled", 3)):
            with self.subTest(status=status):
                a = self.args("--task", "fix", "--repo", "app", "--idempotency-key", "ticket-42")
                a.out = str(Path(self.temp.name) / status)
                c = self.client(status)
                self.assertEqual(fix_job.run(a, fix_job.build_payload(a), c, emit=lambda _: None), code)
                c.submit.assert_called_once_with(task="fix", repo="app", idempotency_key="ticket-42", mode=None)
                self.assertEqual(json.loads((Path(a.out) / "report.json").read_text()), {"steps": []})
                self.assertTrue((Path(a.out) / "report.md").exists())
                c.decide.assert_not_called()

    def test_waiting_never_approves(self):
        c = self.client("waiting")
        messages = []
        self.assertEqual(fix_job.run(self.args("--task", "fix"), {"task": "fix"}, c, emit=messages.append), 4)
        c.decide.assert_not_called()
        c.report.assert_not_called()
        self.assertIn("Waiting for you", " ".join(messages))
        self.assertTrue((Path(self.out) / "job.json").exists())

    def test_poll_and_resume(self):
        c = self.client("queued")
        c.get.return_value = {"id": "job-1", "status": "succeeded"}
        with patch("fix_job.time.sleep"):
            self.assertEqual(fix_job.run(self.args("--task", "fix"), {"task": "fix"}, c, emit=lambda _: None), 0)
        self.assertLessEqual(c.timeout, 30)
        a = self.args("--job-id", "job-1")
        a.out = str(Path(self.temp.name) / "resume")
        c = self.client("waiting")
        c.get.return_value = {"id": "job-1", "status": "waiting"}
        self.assertEqual(fix_job.run(a, fix_job.build_payload(a), c, emit=lambda _: None), 4)
        c.submit.assert_not_called()

    def test_deadline_no_cancel(self):
        c = self.client("running")
        with patch("fix_job.time.monotonic", side_effect=[0, 0, 601]):
            self.assertEqual(fix_job.run(self.args("--task", "fix"), {"task": "fix"}, c, emit=lambda _: None), 5)
        c.cancel.assert_not_called()
        c.get.assert_not_called()

    def test_path_traversal_and_no_overwrite(self):
        c = self.client("succeeded")
        c.submit.return_value["id"] = "../escape"
        with self.assertRaises(ValueError):
            fix_job.run(self.args("--task", "fix"), {"task": "fix"}, c)
        self.assertFalse(Path(self.out).exists())
        Path(self.out).mkdir()
        p = Path(self.out) / "job.json"
        p.write_text("keep")
        with self.assertRaises(FileExistsError):
            fix_job.run(self.args("--task", "fix"), {"task": "fix"}, self.client("succeeded"))
        self.assertEqual(p.read_text(), "keep")

    def test_actionable_errors_never_echo_server_secret(self):
        for error, hint in ((SwarmLabError(401, "hidden"), "SWARMLAB_KEY"), (SwarmLabError(403, "hidden"), "roles"), (SwarmLabError(400, "hidden"), "allowedSettingOverrides"), (urllib.error.URLError("hidden"), "Network")):
            with self.subTest(error=error), patch.dict(os.environ, {"SWARMLAB_KEY": "hidden"}), patch("fix_job.SwarmLabClient") as c, contextlib.redirect_stderr(io.StringIO()) as err:
                c.return_value.submit.side_effect = error
                self.assertEqual(fix_job.main(["--task", "fix", "--out", self.out]), 2)
                self.assertIn(hint, err.getvalue())
                self.assertNotIn("hidden", err.getvalue())

    def test_bad_url_limits_and_json(self):
        for flags in (("--url", "http://key@localhost"), ("--wait", "nan"), ("--poll", "0")):
            with contextlib.redirect_stderr(io.StringIO()), patch("fix_job.SwarmLabClient") as c:
                self.assertEqual(fix_job.main(["--task", "fix", "--out", self.out] + list(flags)), 2)
                c.assert_not_called()


if __name__ == "__main__":
    unittest.main()
