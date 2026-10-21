"""Live check of the swarmlab package against a running server (SWARMLAB_URL) and in local mode (SL_REPO).

Run by src/test/pythonLibrarySim.ts with the offline mock model. Prints one line per check; exits 1 on failure.
"""
import os
import sys
import tempfile

from swarmlab import Agent, Environment, SwarmLab, Workflow

checks = 0


def ok(cond, msg):
    global checks
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    checks += 1
    print(f"ok {checks} - {msg}")


def make_and_check(name="make-and-check"):
    return (Workflow(name, "Make a file in a prepared environment, then check it",
                     environment=Environment.none(setup=["echo setup > setup-made.txt"], env={"CHECK": "yes"}))
            .command("make", "sh -c 'echo \"$CHECK\" > step-made.txt'")
            .command("check", 'test "$(cat step-made.txt)" = yes'))


def server(url):
    sl = SwarmLab(url, verbose=False)
    caps = sl.capabilities()
    ok(caps["apiLevel"] >= 2 and "vscode-extension" in caps["environments"]["presets"], "capabilities")
    ok(not sl.validate("x", repo="nope")["valid"], "validate refuses an unknown repository")
    ok(sl.validate("x", repo="app", environment="auto")["valid"], "validate accepts a good job")

    wf = make_and_check()
    ok(sl.validate_workflow(wf) == [], "the workflow is valid on the server")
    sl.save_workflow(wf)
    ok(any(w["name"] == "make-and-check" for w in sl.workflows()), "saved and listed")
    ok(sl.workflow("make-and-check").graph() == wf.graph(), "read back as a Workflow")

    events = []
    r = sl.run("make the file", repo="app", workflow="make-and-check", approve="auto", on_event=events.append)
    ok(r.ok, f"a saved workflow by name ({r.error})")
    ok("step-made.txt" in r.files and "setup-made.txt" not in r.files, "the step's file is in the result, the setup's is not")
    ok(r.environment and r.environment["ok"], "environment in the result")
    ok("echo setup" in r.environment_log(), "environment log")
    ok("step-made.txt" in r.patch(), "the patch")
    ok("make" in r.report(), "the report")
    ok(any(e.get("kind") == "environment" for e in events), "events reach on_event, flat")

    r = sl.run("make the file", repo="app", workflow=make_and_check("inline"), approve="auto")
    ok(r.ok and "step-made.txt" in r.files, "a Workflow object, inline")

    seen = []
    r = sl.run("add a note to the first file", repo="app", approvals={"edits": "ask"}, approve=lambda a: seen.append(a["title"]) or True)
    ok(seen and r.ok and "Reviewed by" in r.patch(), f"an approval answered by a Python function ({seen})")
    r = sl.run("add a note to the first file", repo="app", approvals={"edits": "ask"}, approve=lambda a: False)
    ok(r.ok and r.patch() == "", "a rejected edit is not applied")

    r = sl.run("list the files", repo="app", agent=Agent("lister", "List the files and stop."), max_steps=4)
    ok(r.ok and r.job["spec"]["agent"] == "lister", "a named agent with its own prompt")

    rs = sl.run_many(["list the files", {"task": "summarize the files", "mode": "tree"}], repo="app", approve="auto")
    ok(len(rs) == 2 and all(x.ok for x in rs), "run_many")

    job = sl.submit("list the files", repo="app")
    ok(job.wait(approve="auto").ok and any(e.get("kind") == "status" for e in job.events(follow=False)), "submit, wait, events")

    folder = tempfile.mkdtemp()
    with open(os.path.join(folder, "check.sh"), "w") as f:
        f.write('test "$WHO" = me && echo checked\n')
    out = sl.env(folder, Environment.none(env={"WHO": "me"}), run=["sh check.sh"])
    ok(out["ok"] and "checked" in out["runs"][0]["output"], "env(): a prepared environment, no agents")
    sl.delete_workflow("make-and-check")


def local(repo):
    data = tempfile.mkdtemp()
    lo = SwarmLab.local(repo, provider="mock", data_dir=data, verbose=False)
    r = lo.run("make the file", workflow=make_and_check(), approve="auto")
    ok(r.ok and "step-made.txt" in r.files and r.environment["ok"], f"local: a workflow with an environment ({r.error})")
    ok("step-made.txt" in r.patch() and "environment.log" in r.artifacts(), "local: patch and artifacts")
    seen = []
    r = lo.run("add a note to the first file", approvals={"edits": "ask"}, approve=lambda a: seen.append(a["id"]) or True)
    ok(seen and r.ok and "Reviewed by" in r.patch(), "local: approvals answered by a Python function")
    lo.save_workflow(make_and_check("saved-local"))
    ok(lo.run("make the file", workflow="saved-local", approve="auto").ok, "local: a saved workflow by name")
    r = lo.run("x", environment={"preset": "none", "setup": ["exit 3"]}, approve="auto")
    ok(r.status == "failed" and "environment setup failed" in (r.error or ""), "local: a failed setup fails the job")


if __name__ == "__main__":
    if os.environ.get("SWARMLAB_URL"):
        server(os.environ["SWARMLAB_URL"])
    if os.environ.get("SL_REPO"):
        local(os.environ["SL_REPO"])
    print(f"live_check: {checks} checks passed")
