# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""Public source-free tests. Run: python -m unittest -v test_workflow_demos"""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import workflow_demos as demos
from fix_job import build_payload, parser


class WorkflowDemoTests(unittest.TestCase):
    def test_four_default_previews_are_valid_json_without_network(self):
        for mode in demos.MODES:
            out = io.StringIO()
            with patch.object(demos, "SwarmLabClient") as client, contextlib.redirect_stdout(out):
                self.assertEqual(demos.main(["--mode", mode, "--repo", "registered-demo"]), 0)
            client.assert_not_called()
            body = json.loads(out.getvalue())
            self.assertEqual(body, demos.build_job(mode, "registered-demo"))
            self.assertEqual(body["ref"], "demo-baseline")
            self.assertNotIn("approvals", body)
            self.assertLessEqual(set(body["settings"]), demos.DEFAULT_SETTING_OVERRIDES)
            self.assertNotIn("leadModel", body["settings"])
            with tempfile.TemporaryDirectory() as tmp:
                cfg = Path(tmp) / "job.json"
                cfg.write_text(out.getvalue(), encoding="utf-8")
                args = parser().parse_args(["--config", str(cfg), "--out", str(Path(tmp) / "reports"), "--dry-run"])
                self.assertEqual(build_payload(args), body)

    def test_explicit_submit_only_and_no_approvals(self):
        client = Mock()
        client.submit.return_value = {"id": "demo-1", "status": "queued"}
        with patch.object(demos, "SwarmLabClient", return_value=client), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(demos.main(["--mode", "swarm", "--repo", "demo", "--submit"]), 0)
        client.submit.assert_called_once()
        self.assertEqual(client.submit.call_args.kwargs["max_attempts"], 1)
        self.assertEqual(client.method_calls[0][0], "submit")
        self.assertEqual(len(client.method_calls), 1)
        self.assertNotIn("approvals", client.submit.call_args.kwargs)

    def test_fixture_is_intentionally_red_and_copied_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "fresh-demo"
            with patch.object(subprocess, "run") as run:
                self.assertEqual(demos.create_demo(str(dest)), dest.resolve())
                run.assert_not_called()
            self.assertFalse((dest / ".git").exists())
            result = subprocess.run([sys.executable, "-m", "unittest", "-v"], cwd=dest, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Ran 6 tests", result.stderr)
            self.assertIn("FAILED (failures=2)", result.stderr)
            self.assertIn("FAIL: test_quantities", result.stderr)
            self.assertIn("FAIL: test_mixed_whitespace", result.stderr)
            with self.assertRaises(FileExistsError):
                demos.create_demo(str(dest))

    def test_setup_refuses_relative_existing_and_git_ancestor(self):
        with self.assertRaises(ValueError):
            demos.create_demo("relative-demo")
        with self.assertRaises(ValueError):
            demos.create_demo(str(demos.HERE / "must-not-create"))
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            (parent / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
            with self.assertRaises(ValueError):
                demos.create_demo(str(parent / "fresh"))
            self.assertFalse((parent / "fresh").exists())

    def test_flat_kit_allows_sibling_demo_but_not_kit_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            kit = Path(tmp) / "kit"
            kit.mkdir()
            # Fixture sources stay real while HERE represents a downloaded flat kit.
            import shutil
            shutil.copytree(demos.HERE / "demo_project", kit / "demo_project")
            with patch.object(demos, "HERE", kit):
                dest = Path(tmp) / "demo-app"
                self.assertEqual(demos.create_demo(str(dest)), dest.resolve())
                with self.assertRaises(ValueError):
                    demos.create_demo(str(kit / "must-not-create"))

    def test_graph_has_real_bounded_command_and_handoffs(self):
        graph = demos.build_job("graph", "demo", "python3")["workflow"]
        self.assertEqual(graph["nodes"]["test"]["command"], "python3 -m unittest -v")
        self.assertEqual(graph["nodes"]["test"]["onFail"], "implement")
        self.assertEqual(graph["nodes"]["implement"]["maxVisits"], 3)
        self.assertEqual(graph["nodes"]["review"]["routes"]["reject"], "implement")
        self.assertEqual(graph["maxSteps"], 12)
        for mode, marker in (("tree", "delegate"), ("swarm", "post_note")):
            self.assertIn(marker, demos.build_job(mode, "demo")["task"])

    def test_bad_config_never_submits_or_echoes_credentials(self):
        for extra in ({"settings": {"allowCommands": True}}, {"providers": {"key": "private-marker"}}, {"unknown": True}):
            with tempfile.TemporaryDirectory() as tmp:
                cfg = Path(tmp) / "config.json"
                cfg.write_text(json.dumps(extra), encoding="utf-8")
                err = io.StringIO()
                with patch.object(demos, "SwarmLabClient") as client, contextlib.redirect_stderr(err):
                    self.assertEqual(demos.main(["--mode", "single", "--repo", "demo", "--config", str(cfg), "--submit"]), 2)
                client.assert_not_called()
                self.assertNotIn("private-marker", err.getvalue())

    def test_valid_config_merges_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            cfg.write_text(json.dumps({"settings": {"tokenBudget": 50000}, "labels": {"exercise": "demo"}}), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(demos.main(["--mode", "tree", "--repo", "demo", "--config", str(cfg)]), 0)
            body = json.loads(out.getvalue())
            self.assertEqual(body["settings"]["tokenBudget"], 50000)
            self.assertEqual(body["settings"]["maxAgents"], 4)

    def test_modes_and_missing_required_fields(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(demos.main(["--list"]), 0)
        self.assertEqual(set(out.getvalue().split()), set(demos.MODES))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(demos.main([]), 2)
        with self.assertRaises(ValueError):
            demos.build_job("graph", "demo", "python; unsafe")


if __name__ == "__main__":
    unittest.main()
