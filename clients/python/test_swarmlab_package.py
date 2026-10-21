"""Offline tests of the swarmlab package: job building, workflows, environments, agents. No server, no network."""
import json
import os
import tempfile
import unittest

from swarmlab import (Agent, Approvals, Checks, Environment, Settings, SpecError, SwarmLab, Workflow, build_spec, validate_graph)
from swarmlab.client import _answer


class BuildSpec(unittest.TestCase):
    def test_minimal(self):
        self.assertEqual(build_spec("Do it"), {"task": "Do it"})

    def test_empty_task(self):
        with self.assertRaises(SpecError):
            build_spec("  ")

    def test_settings_as_keywords_and_aliases(self):
        s = build_spec("t", max_steps=20, token_budget=1000, rag_top_k=4, cost_budget_usd=0.5)
        self.assertEqual(s["settings"], {"maxStepsPerAgent": 20, "tokenBudget": 1000, "ragTopK": 4, "costBudgetUsd": 0.5})

    def test_settings_object_and_keywords_merge(self):
        s = build_spec("t", settings=Settings(max_agents=3), max_steps=9)
        self.assertEqual(s["settings"], {"maxAgents": 3, "maxStepsPerAgent": 9})

    def test_bad_setting_value(self):
        with self.assertRaises(SpecError):
            build_spec("t", max_steps=-1)
        with self.assertRaises(SpecError):
            Settings(answer_length="huge")

    def test_unknown_keyword_lists_the_valid_ones(self):
        with self.assertRaises(SpecError) as c:
            build_spec("t", colour="red")
        self.assertIn("max_steps_per_agent", str(c.exception))
        self.assertIn("extra=", str(c.exception))

    def test_job_fields(self):
        s = build_spec("t", repo="app", mode="tree", max_attempts=2, timeout_sec=60, idempotency_key="k", labels={"a": "b"}, priority=3, files=True)
        self.assertEqual(s["maxAttempts"], 2)
        self.assertEqual(s["timeoutSec"], 60)
        self.assertEqual(s["idempotencyKey"], "k")
        self.assertEqual(s["mode"], "tree")

    def test_bad_mode(self):
        with self.assertRaises(SpecError):
            build_spec("t", mode="crowd")

    def test_friendly_forms(self):
        s = build_spec("t", checks=True, memory="sprint-1", data=["inputs/"], mcp=["github"], models="cheapest", rag=False, decision=True,
                       approvals="unattended", environment="python")
        self.assertEqual(s["checks"], {"tests": True, "verify": True})
        self.assertEqual(s["memory"], {"session": "sprint-1"})
        self.assertEqual(s["data"], {"inputs": ["inputs/"]})
        self.assertEqual(s["mcp"], {"use": ["github"]})
        self.assertEqual(s["models"], {"auto": "cheapest"})
        self.assertEqual((s["rag"], s["decision"]), ("off", "on"))
        self.assertEqual(s["approvals"]["commands"], "auto")
        self.assertEqual(s["environment"], "python")
        self.assertEqual(build_spec("t", checks="pytest -q")["checks"], {"tests": "pytest -q", "verify": True})
        self.assertIs(build_spec("t", memory=False)["memory"], False)
        self.assertIs(build_spec("t", environment=False)["environment"], False)

    def test_agent_makes_single_mode(self):
        a = Agent("fixer", "Fix with the smallest change.", model="lead", edit=["src/**"], tools=["read_file", "edit_file"])
        s = build_spec("t", agent=a)
        self.assertEqual(s["mode"], "single")
        self.assertEqual(s["agent"], "fixer")
        self.assertEqual(s["policy"]["agents"]["fixer"], {"model": "lead", "tools": ["read_file", "edit_file"], "editPaths": ["src/**"]})
        self.assertEqual(s["prompts"]["agents"]["fixer"], "Fix with the smallest change.")
        with self.assertRaises(SpecError):
            build_spec("t", agent=a, mode="swarm")

    def test_team(self):
        s = build_spec("t", mode="swarm", agents=[Agent("scout", description="maps the code"), {"name": "tester", "tools": ["run_tests"]}])
        self.assertEqual(set(s["policy"]["agents"]), {"scout", "tester"})

    def test_lead_prompt(self):
        self.assertEqual(build_spec("t", mode="tree", prompt="Split it.")["prompts"]["roles"], {"tree-lead": "Split it."})
        with self.assertRaises(SpecError):
            build_spec("t", workflow="x", prompt="no")

    def test_extra_passthrough(self):
        self.assertEqual(build_spec("t", extra={"newField": 1})["newField"], 1)

    def test_agent_validation(self):
        with self.assertRaises(SpecError):
            Agent("bad name")
        with self.assertRaises(SpecError):
            Agent("x", tools=["teleport"])
        self.assertEqual(Agent("x", tools=["mcp__jira__search"]).tools, ["mcp__jira__search"])


class Environments(unittest.TestCase):
    def test_presets(self):
        self.assertEqual(Environment.auto().to_dict(), {"preset": "auto"})
        self.assertEqual(Environment.vscode_extension().to_dict(), {"preset": "vscode-extension", "display": "virtual"})
        d = Environment.docker("node:22", setup=["apt-get update"], network=False).to_dict()
        self.assertEqual(d, {"preset": "none", "runtime": "docker", "image": "node:22", "setup": ["apt-get update"], "network": False})
        self.assertEqual(Environment.named("gpu-box").to_dict(), "gpu-box")
        self.assertEqual(Environment(preset="python", setup="pip install -e .", pre_setup=["echo hi"], timeout_sec=60).to_dict(),
                         {"preset": "python", "setup": ["pip install -e ."], "preSetup": ["echo hi"], "timeoutSec": 60})

    def test_editor(self):
        from swarmlab import VSCode
        e = Environment.vscode_extension(VSCode(flavor="vscodium", install=["deps.vsix"], commands=["my.hello", {"command": "my.add", "args": [1]}],
                                                check="test/smoke-check.js", require="pass", project_tests=False))
        self.assertEqual(e.to_dict()["vscode"], {"flavor": "vscodium", "install": ["deps.vsix"], "commands": ["my.hello", {"command": "my.add", "args": [1]}],
                                                 "check": "test/smoke-check.js", "projectTests": False, "require": "pass"})
        self.assertEqual(Environment.editor(VSCode(install="x.vsix")).to_dict(), {"preset": "none", "display": "virtual", "vscode": {"install": ["x.vsix"]}})
        self.assertEqual(Environment.editor().to_dict()["vscode"], True)
        self.assertEqual(Environment(preset="vscode-extension", vscode=False).to_dict(), {"preset": "vscode-extension", "vscode": False})
        self.assertEqual(Environment.from_dict({"preset": "none", "vscode": {"executable": "cursor", "systemDeps": False}}).vscode.system_deps, False)
        with self.assertRaises(SpecError):
            VSCode(flavor="atom")
        with self.assertRaises(SpecError):
            VSCode(require="sometimes")

    def test_rules(self):
        with self.assertRaises(SpecError):
            Environment(runtime="docker")
        with self.assertRaises(SpecError):
            Environment(preset="cobol")
        with self.assertRaises(SpecError):
            Environment(env={"PATH": "/x"})
        with self.assertRaises(SpecError):
            Environment.from_dict({"preset": "auto", "sudo": True})

    def test_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, ".swarmlab", "environment.json")
            Environment.python(setup=["pip install -e ."], env={"A": "1"}, continue_on_error=True).save(f)
            with open(f) as fh:
                self.assertEqual(json.load(fh), {"preset": "python", "setup": ["pip install -e ."], "env": {"A": "1"}, "continueOnError": True})
            self.assertEqual(Environment.load(f).continue_on_error, True)


class Workflows(unittest.TestCase):
    def pipeline(self):
        return (Workflow("fix-and-test", "Fix, test, review", environment=Environment.python())
                .agent("fix", "Fix: {task}", agent=Agent("fixer", "Smallest change."))
                .command("test", "pytest -q", on_fail="fix", max_visits=3)
                .agent("review", "Review: {last}", agent=Agent("reviewer", tools=["read_file"]), routes={"ok": "done", "redo": "fix"}))

    def test_auto_links(self):
        g = self.pipeline().graph()
        self.assertEqual(g["start"], "fix")
        self.assertEqual(g["nodes"]["fix"]["next"], "test")
        self.assertEqual(g["nodes"]["test"]["onPass"], "review")
        self.assertEqual(g["nodes"]["test"]["onFail"], "fix")
        self.assertNotIn("next", g["nodes"]["review"])
        self.assertEqual(validate_graph(g), [])

    def test_last_step_ends(self):
        g = Workflow("w").agent("a", "x").agent("b", "y").graph()
        self.assertEqual(g["nodes"]["b"]["next"], "done")
        self.assertEqual(Workflow("w").command("c", "make").graph()["nodes"]["c"], {"command": "make", "onPass": "done", "onFail": "done"})

    def test_document(self):
        d = self.pipeline().to_dict()
        self.assertEqual(set(d["policy"]["agents"]), {"fixer", "reviewer"})
        self.assertEqual(d["prompts"]["agents"], {"fixer": "Smallest change."})
        self.assertEqual(d["environment"], {"preset": "python"})
        self.assertEqual(d["description"], "Fix, test, review")

    def test_decisions(self):
        wf = (Workflow("triage").decide("is_bug", "Is this a bug report?", yes="fix", no="done")
              .choice("area", "Which area?", {"ui": "the interface", "api": "the server"}, routes={"ui": "fix", "api": "fix"})
              .score("severity", "How bad?", ["minor", "major", "critical"], {0: "done", 1: "fix", 2: "fix"})
              .agent("fix", "Fix it"))
        self.assertEqual(wf.validate(), [])
        n = wf.graph()["nodes"]
        self.assertEqual(n["is_bug"]["decide"]["type"], "noul")
        self.assertEqual(n["severity"]["routes"], {"0": "done", "1": "fix", "2": "fix"})
        self.assertEqual(Workflow("c").choice("pick", "Which?", {"a": "A", "b": "B"}).agent("a", "x").agent("b", "y").validate(), [])

    def test_validation(self):
        wf = Workflow("w").agent("a", "x", next="nowhere")
        self.assertTrue(any("not a node" in e for e in wf.validate()))
        with self.assertRaises(SpecError):
            wf.check()
        self.assertTrue(any("not one of the workflow's agents" in e for e in Workflow("w", agents=[Agent("x")]).agent("s", "t", agent="y").validate()))
        self.assertTrue(any("names no step" in e for e in Workflow("w").agent("s", "use {node:ghost}").validate()))
        with self.assertRaises(SpecError):
            Workflow("w").agent("done", "x")
        with self.assertRaises(SpecError):
            Workflow("w").agent("a", "x").agent("a", "y")
        with self.assertRaises(SpecError):
            Workflow("w").agent("a", "x", next="b", routes={"k": "b"})
        with self.assertRaises(SpecError):
            Workflow("bad name!")
        self.assertTrue(validate_graph({"start": "a", "nodes": {"a": {"decide": {"type": "noul", "instructions": "?"}, "routes": {"maybe": "done"}}}}))

    def test_save_load(self):
        with tempfile.TemporaryDirectory() as d:
            f = self.pipeline().save(os.path.join(d, "wf.json"))
            back = Workflow.load(f)
            self.assertEqual(back.name, "fix-and-test")
            self.assertEqual(back.graph(), self.pipeline().graph())
            self.assertEqual(back.to_dict()["policy"], self.pipeline().to_dict()["policy"])
            bare = os.path.join(d, "bare.json")
            with open(bare, "w") as fh:
                json.dump({"start": "x", "nodes": {"x": {"task": "go", "next": "done"}}}, fh)
            self.assertEqual(Workflow.load(bare).graph()["nodes"]["x"]["next"], "done")

    def test_in_a_job(self):
        s = build_spec("Fix the date bug", workflow=self.pipeline(), settings={"maxAgents": 2})
        self.assertEqual(s["mode"], "graph")
        self.assertEqual(s["workflow"]["start"], "fix")
        self.assertEqual(s["environment"], {"preset": "python"})
        self.assertIn("reviewer", s["policy"]["agents"])
        s2 = build_spec("x", workflow=self.pipeline(), environment=False)
        self.assertIs(s2["environment"], False, "the job's own environment wins")
        self.assertEqual(build_spec("x", workflow="fix-and-test"), {"task": "x", "workflow": "fix-and-test", "mode": "graph"})

    def test_model_lifecycle_steps(self):
        wf = (Workflow("train", environment=Environment.notebooks_env(["pandas"]))
              .notebook("train", "models/pd model.ipynb", {"max_depth": 4, "region": "south"}, on_fail="repair")
              .gate("targets", "metrics.json", "auc>=0.75", "ks >= 0.3", on_fail="improve")
              .agent("card", "Write MODEL_CARD.md", check="swarmlab-check contains MODEL_CARD.md \"## Metrics\"", retries=3, on_fail="repair")
              .compare("cc", "new.json", "cur.json", ["auc", "-latency_ms"], max_drop=0.005)
              .agent("improve", "Improve", next="train")
              .agent("repair", "Fix", next="train"))
        self.assertEqual(wf.validate(), [])
        n = wf.graph()["nodes"]
        self.assertEqual(n["train"]["command"], 'swarmlab-nb run "models/pd model.ipynb" -p max_depth=4 -p "region=\\"south\\""')
        self.assertEqual(n["targets"]["command"], "swarmlab-check metrics metrics.json auc:ge:0.75 ks:ge:0.3", "rules as words: nothing the allow-list refuses")
        self.assertNotRegex(n["targets"]["command"], r"[<>|&;$]")
        self.assertEqual((n["card"]["check"], n["card"]["retries"], n["card"]["onFail"]), ('swarmlab-check contains MODEL_CARD.md "## Metrics"', 3, "repair"))
        self.assertEqual(n["cc"]["command"], "swarmlab-check compare new.json cur.json auc -latency_ms --max-drop 0.005")
        self.assertEqual(wf.to_dict()["environment"], {"preset": "python", "notebooks": {"packages": ["pandas"]}})
        self.assertIn("card: card ✓", wf.mermaid())
        self.assertEqual(Workflow("o").notebook("s", "x.ipynb", optional=True).graph()["nodes"]["s"]["command"], "swarmlab-nb run x.ipynb --optional")
        self.assertEqual(Workflow("e").ensure("c", "csv", "out.csv", "--columns", "a,b").graph()["nodes"]["c"]["command"], "swarmlab-check csv out.csv --columns a,b")

    def test_step_rules(self):
        with self.assertRaises(SpecError):
            Workflow("w").gate("g", "m.json")                      # no rule
        with self.assertRaises(SpecError):
            Workflow("w").gate("g", "m.json", "auc is good")       # not a rule
        with self.assertRaises(SpecError):
            Workflow("w").agent("a", "x", retries=9, check="swarmlab-check test")
        with self.assertRaises(SpecError):
            Workflow("w").agent("a", "x", on_fail="b")             # on_fail needs a check
        with self.assertRaises(SpecError):
            Workflow("w").ensure("c", "teleport")
        self.assertTrue(any("retries" in e for e in validate_graph({"start": "a", "nodes": {"a": {"task": "x", "check": "y", "retries": 7, "next": "done"}}})))
        self.assertTrue(any('"check"' in e for e in validate_graph({"start": "a", "nodes": {"a": {"command": "x", "check": "y"}}})))

    def test_mermaid(self):
        m = self.pipeline().mermaid()
        self.assertIn("flowchart TD", m)
        self.assertIn("test -->|fail| fix", m)
        self.assertIn("review -->|ok| done((done))", m)


class Approving(unittest.TestCase):
    def test_answers(self):
        a = {"id": "1", "title": "x", "choices": ["Run", "Reject"]}
        self.assertEqual(_answer("auto", a), {"decision": "approve"})
        self.assertEqual(_answer("reject", a), {"decision": "reject"})
        self.assertIsNone(_answer(None, a))
        self.assertEqual(_answer(lambda x: True, a), {"decision": "approve"})
        self.assertEqual(_answer(lambda x: False, a), {"decision": "reject"})
        self.assertEqual(_answer(lambda x: "Run", a), {"decision": "approve", "choice": "Run"})
        self.assertEqual(_answer(lambda x: {"decision": "approve", "text": "edited"}, a)["text"], "edited")
        with self.assertRaises(SpecError):
            _answer("maybe", a)


class Offline(unittest.TestCase):
    def test_preview_needs_no_server(self):
        sl = SwarmLab("http://127.0.0.1:9")  # nothing listens there
        self.assertEqual(sl.preview("t", repo="app")["repo"], "app")
        self.assertFalse(sl.validate("t", colour=1)["valid"])

    def test_unreachable_server_message(self):
        from swarmlab import SwarmLabError
        with self.assertRaises(SwarmLabError) as c:
            SwarmLab("http://127.0.0.1:9", timeout=2).capabilities()
        self.assertIn("SwarmLab.local", str(c.exception))

    def test_cli_preview(self):
        from swarmlab.cli import main
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(["preview", "Fix it", "--repo", "app", "--env", "vscode-extension", "--set", "max_steps=5", "--checks", "pytest"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue()), {"task": "Fix it", "repo": "app", "settings": {"maxStepsPerAgent": 5},
                                                      "environment": "vscode-extension", "checks": {"tests": "pytest", "verify": True}})


if __name__ == "__main__":
    unittest.main()
