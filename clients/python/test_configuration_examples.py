"""Offline tests for configuration_examples.py.

    python -m unittest clients/python.test_configuration_examples
    python -m unittest clients/python.test_configuration_examples -v
"""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import configuration_examples
import fix_job


class ConfigurationExamplesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = self.temp.name

    def config(self, value):
        p = Path(self.dir) / "extra.json"
        p.write_text(json.dumps(value), encoding="utf-8")
        return str(p)

    def test_all_modes_present_and_have_required_fields(self):
        examples = configuration_examples.build_examples()
        self.assertEqual(set(examples), {"single", "tree", "swarm", "graph"})
        for name, body in examples.items():
            self.assertIn("task", body)
            self.assertIn("mode", body)
            self.assertIsInstance(body["settings"], dict)
            self.assertEqual(body["mode"], name)
            # settings keys are API camelCase, not Python snake_case
            for k in body["settings"]:
                self.assertFalse("_" in k, f"setting {k} is snake_case, must be camelCase")

    def test_run_settings_reference_complete(self):
        expected = {
            "leadModel", "workerModel", "maxStepsPerAgent", "maxAgents",
            "tokenBudget", "maxTokensPerCall", "allowEdits", "allowCommands",
            "useMemory", "defaultEngine", "commandAllowList", "chatCompactChars",
            "chatKeepMessages", "sequentialTools", "maxContinuations",
            "maxInputTokens", "answerLength", "answerStyle", "ragAuto",
            "ragTopK", "ragAutoK", "costBudgetUsd", "finalAnswerOnLimit",
            "toolMode", "maxParallelCalls",
        }
        self.assertEqual(set(configuration_examples.RUN_SETTINGS), expected)

    def test_intersect_allowlist_drops_unlisted_keys(self):
        s = {"a": 1, "b": 2, "c": 3}
        self.assertEqual(configuration_examples.intersect_allowlist(s, {"a", "c"}), {"a": 1, "c": 3})
        self.assertEqual(configuration_examples.intersect_allowlist(s, set()), {})

    def test_default_allowlist_matches_server(self):
        import re
        source = (Path(__file__).resolve().parents[2] / "src/server/config.ts").read_text(encoding="utf-8")
        fields = re.search(r'allowedSettingOverrides: \[([^\]]+)\]', source).group(1)
        allowed = set(re.findall(r'"([^"]+)"', fields))
        self.assertEqual(configuration_examples.DEFAULT_SETTING_OVERRIDES, allowed)
        for body in configuration_examples.build_examples().values():
            self.assertEqual(set(body["settings"]), allowed)
            self.assertNotIn("costBudgetUsd", body["settings"])
            self.assertNotIn("workerModel", body["settings"])

    def test_tree_swarm_graph_share_tree_allowlist(self):
        ex = configuration_examples.build_examples()
        for name in ("tree", "swarm", "graph"):
            settings = ex[name]["settings"]
            self.assertTrue(set(settings) <= configuration_examples.DEFAULT_SETTING_OVERRIDES, name)
            self.assertIn("maxAgents", settings)

    def test_no_secret_fields_in_any_payload(self):
        for body in configuration_examples.build_examples().values():
            fix_job.reject_secrets(body)  # tokenBudget and maxTokensPerCall are legitimate
        for key in ("key", "api_key", "API-Key", "authorization", "password", "secret", "token", "credentials", "headers", "extraHeaders"):
            malicious = {"prompts": {"agents": [{key: "do-not-print"}]}}
            with self.subTest(key=key), self.assertRaises(ValueError):
                fix_job.reject_secrets(malicious)
            with self.subTest(merge=key), self.assertRaises(ValueError):
                configuration_examples.merge_config(configuration_examples.build_examples()["single"], self.config(malicious))

    def test_dry_run_is_default_and_submits_nothing(self):
        out = io.StringIO()
        with patch("configuration_examples.SwarmLabClient") as c, contextlib.redirect_stdout(out):
            code = configuration_examples.main(["--example", "single"])
        self.assertEqual(code, 0)
        c.assert_not_called()
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["mode"], "single")

    def test_dry_run_output_matches_submit_payload(self):
        out = io.StringIO()
        with patch("configuration_examples.SwarmLabClient") as c, contextlib.redirect_stdout(out):
            configuration_examples.main(["--example", "tree", "--dry-run"])
        c.assert_not_called()  # explicit --dry-run also submits nothing
        self.assertEqual(json.loads(out.getvalue())["mode"], "tree")

    def test_submit_actually_posts_with_settings(self):
        out = io.StringIO()
        fake = Mock()
        fake.submit.return_value = {"id": "job-1", "status": "queued"}
        with patch("configuration_examples.SwarmLabClient", return_value=fake), \
                patch.dict(os.environ, {"SWARMLAB_KEY": "k"}), \
                contextlib.redirect_stdout(out):
            code = configuration_examples.main(["--example", "swarm", "--submit"])
        self.assertEqual(code, 0)
        call = fake.submit.call_args
        self.assertEqual(call.kwargs["mode"], "swarm")
        self.assertIsNotNone(call.kwargs["settings"])
        self.assertIn("Submitted", out.getvalue())

    def test_no_autoapproval_anywhere(self):
        # The client's decide()/approvals paths are approval-answering; the
        # examples must never touch them. Verify submit kwargs carry no approvals.
        fake = Mock()
        fake.submit.return_value = {"id": "j", "status": "queued"}
        with patch("configuration_examples.SwarmLabClient", return_value=fake):
            configuration_examples.main(["--example", "single", "--submit"])
        self.assertNotIn("approvals", fake.submit.call_args.kwargs)
        self.assertNotIn("on_approval", fake.submit.call_args.kwargs)

    def test_config_merge_settings_by_key(self):
        cfg = self.config({"task": "override", "settings": {"tokenBudget": 1, "answerStyle": "plain"}})
        body = configuration_examples.merge_config(
            configuration_examples.build_examples()["single"], cfg)
        self.assertEqual(body["task"], "override")
        self.assertEqual(body["settings"]["tokenBudget"], 1)
        self.assertEqual(body["settings"]["answerStyle"], "plain")
        self.assertIn("maxStepsPerAgent", body["settings"])  # example setting retained

    def test_submit_forwards_merged_fields_and_aliases(self):
        extra = {"profile": "review", "policy": {"agents": {}}, "prompts": {},
                 "providers": {"rag": {"autoK": 4}}, "rag": "off", "decision": "off",
                 "mcp": {}, "skills": [], "labels": {"ticket": "123"},
                 "idempotencyKey": "example-1", "timeoutSec": 60, "maxAttempts": 1}
        fake = Mock()
        fake.submit.return_value = {"id": "j", "status": "queued"}
        with patch("configuration_examples.SwarmLabClient", return_value=fake), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(configuration_examples.main(["--example", "graph", "--config", self.config(extra), "--submit"]), 0)
        kwargs = fake.submit.call_args.kwargs
        for key, value in extra.items():
            self.assertEqual(kwargs[fix_job.ALIASES.get(key, key)], value)
        self.assertEqual(kwargs["workflow"], configuration_examples.build_examples()["graph"]["workflow"])

    def test_unknown_fields_rejected_before_client_creation(self):
        with patch("configuration_examples.SwarmLabClient") as client, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(configuration_examples.main(["--example", "single", "--submit", "--config", self.config({"unknown": True})]), 2)
        client.assert_not_called()

    def test_reference_enums_and_numeric_k(self):
        settings = configuration_examples.RUN_SETTINGS
        self.assertIn(settings["defaultEngine"], ("native", "claude-code"))
        self.assertIn(settings["answerLength"], ("short", "normal", "long"))
        self.assertIn(settings["answerStyle"], ("visual", "plain"))
        self.assertIn(settings["toolMode"], ("native", "text", "none"))
        self.assertIs(type(settings["ragAutoK"]), int)

    def test_config_rejects_non_object(self):
        cfg = self.config([1, 2, 3])
        with self.assertRaises(ValueError):
            configuration_examples.merge_config(
                configuration_examples.build_examples()["single"], cfg)

    def test_config_rejects_non_object_settings(self):
        cfg = self.config({"settings": []})
        with self.assertRaises(ValueError):
            configuration_examples.merge_config(
                configuration_examples.build_examples()["single"], cfg)

    def test_list_and_missing_example(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = configuration_examples.main(["--list"])
        self.assertEqual(code, 0)
        self.assertIn("single", out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()) as err, \
                patch("configuration_examples.SwarmLabClient") as c:
            code = configuration_examples.main([])
        self.assertEqual(code, 2)
        c.assert_not_called()
        self.assertIn("--example", err.getvalue())


if __name__ == "__main__":
    unittest.main()