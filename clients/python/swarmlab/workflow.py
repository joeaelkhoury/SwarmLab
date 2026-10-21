"""Build workflows (graphs of steps) in Python, check them offline, save them, run them anywhere.

A workflow is a list of steps. Steps follow each other in the order you add them, unless you say otherwise, so a
straight pipeline needs no wiring at all::

    wf = (Workflow("fix-and-test", "Fix a bug, test, review")
          .agent("fix", "Fix this: {task}", agent=Agent("fixer", "Make the smallest change that fixes it."))
          .command("test", "pytest -q", on_fail="fix", max_visits=3)      # pass → next step, fail → back to fix
          .agent("review", "Review the change. Answer DECISION: ok or DECISION: redo.\\n{last}",
                 routes={"ok": "done", "redo": "fix"}))

Placeholders in a step's task: {task} (the job's task), {last} (the previous step's output), {node:<id>} (that
step's latest output), {data} and {output} (the job's data).

Kinds of steps: agent (an agent works), command (a shell command; exit 0 = pass), decide (yes/no), choice (one of
several options) and score (a level on a scale), the last three answered by the decision model.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from .spec import Agent, Approvals, Checks, Environment, Settings, SpecError, environment_value, to_api

__all__ = ["Workflow", "validate_graph"]

END = ("done", "end")
_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class Workflow:
    """A graph of steps, plus (optionally) the agents, environment, checks and settings it needs."""

    def __init__(self, name: str, description: Optional[str] = None, *, max_steps: Optional[int] = None,
                 environment: Any = None, agents: Optional[Sequence[Union[Agent, Mapping[str, Any]]]] = None,
                 settings: Union[Settings, Mapping[str, Any], None] = None, checks: Union[Checks, Mapping[str, Any], None] = None,
                 approvals: Union[Approvals, Mapping[str, Any], None] = None, inputs: Optional[Mapping[str, str]] = None):
        if not re.match(r"^[a-zA-Z0-9][\w.-]{0,63}$", name):
            raise SpecError(f"workflow name {name!r}: letters, digits, . _ - (up to 64), starting with a letter or digit")
        self.name = name
        self.description = description
        self.max_steps = max_steps
        self.environment = environment
        self.settings = settings
        self.checks = checks
        self.approvals = approvals
        self.inputs = dict(inputs or {})
        self._steps: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []
        self._explicit: Dict[str, set] = {}
        self._agents: Dict[str, Agent] = {}
        self._start: Optional[str] = None
        for a in agents or []:
            self.add_agent(a)

    # ------------------------------------------------------------------ agents

    def add_agent(self, a: Union[Agent, Mapping[str, Any]]) -> "Workflow":
        """Make an agent part of this workflow (its permissions and prompt travel with it)."""
        agent = a if isinstance(a, Agent) else Agent(**dict(a))
        old = self._agents.get(agent.name)
        if old is not None and old != agent:
            raise SpecError(f"two different agents are named {agent.name!r}")
        self._agents[agent.name] = agent
        return self

    @property
    def agents(self) -> List[Agent]:
        return list(self._agents.values())

    # ------------------------------------------------------------------ steps

    def _add(self, id: str, node: Dict[str, Any], explicit: set) -> "Workflow":
        if not _ID.match(id):
            raise SpecError(f"step id {id!r}: letters, digits, - and _ (up to 64)")
        if id in END:
            raise SpecError(f"{id!r} is reserved for the end of the workflow; name the step differently")
        if id in self._steps:
            raise SpecError(f"there is already a step {id!r}")
        self._steps[id] = {k: v for k, v in node.items() if v is not None}
        self._order.append(id)
        self._explicit[id] = explicit
        if self._start is None:
            self._start = id
        return self

    def agent(self, id: str, task: str = "{task}", *, agent: Union[Agent, str, None] = None, model: Optional[str] = None,
              next: Optional[str] = None, routes: Optional[Mapping[str, str]] = None, max_visits: Optional[int] = None,
              on_limit: Optional[str] = None, data: Optional[Mapping[str, Any]] = None, description: Optional[str] = None,
              check: Optional[str] = None, retries: Optional[int] = None, on_fail: Optional[str] = None) -> "Workflow":
        """An agent step. agent: an Agent (added to the workflow) or the name of one (default: an agent named like the step).
        routes: the agent ends its reply with "DECISION: <key>" and the key picks the next step ("else" for the rest).
        check: a command that judges the result (exit 0 = good), e.g. "swarmlab-check files report.md"; when it fails the
        agent is told exactly what it said and retries (retries, default 2); still failing, the step goes to on_fail.
        This is what lets small, cheap models do reliable work."""
        if retries is not None and not (isinstance(retries, int) and 0 <= retries <= 5):
            raise SpecError(f"step {id!r}: retries is 0 to 5")
        if on_fail is not None and not check:
            raise SpecError(f"step {id!r}: on_fail on an agent step needs a check")
        if routes is not None and next is not None:
            raise SpecError(f"step {id!r}: give next or routes, not both")
        name = None
        if isinstance(agent, Agent):
            self.add_agent(agent)
            name = agent.name
        elif isinstance(agent, str):
            name = agent
        if model is not None and model not in ("lead", "worker"):
            raise SpecError(f"step {id!r}: model is \"lead\" or \"worker\" (an exact model id goes on the Agent)")
        return self._add(id, {"task": task, "agent": name, "model": model, "next": next, "routes": dict(routes) if routes else None,
                              "maxVisits": max_visits, "onLimit": on_limit, "data": dict(data) if data else None, "description": description,
                              "check": check, "retries": retries, "onFail": on_fail},
                         {"next"} if next or routes else set())

    step = agent  # an alias that reads well: wf.step("plan", "Plan: {task}")

    def command(self, id: str, command: str, *, on_pass: Optional[str] = None, on_fail: Optional[str] = None,
                max_visits: Optional[int] = None, on_limit: Optional[str] = None, description: Optional[str] = None) -> "Workflow":
        """A command step: exit code 0 goes to on_pass (default: the next step), anything else to on_fail (default: done)."""
        if not command.strip():
            raise SpecError(f"step {id!r}: the command is empty")
        return self._add(id, {"command": command, "onPass": on_pass, "onFail": on_fail, "maxVisits": max_visits, "onLimit": on_limit,
                              "description": description}, {"onPass"} if on_pass else set())

    def notebook(self, id: str, file: str, params: Optional[Mapping[str, Any]] = None, *, on_pass: Optional[str] = None,
                 on_fail: Optional[str] = None, max_visits: Optional[int] = None, on_limit: Optional[str] = None,
                 optional: bool = False, description: Optional[str] = None) -> "Workflow":
        """Run a Jupyter notebook cell by cell (needs an environment with notebooks). params fill its "parameters" cell;
        the executed notebook keeps outputs and charts; a failing cell fails the step, with its error for the next step."""
        cmd = ["swarmlab-nb", "run", _q(file)] + [f"-p {_q(f'{k}={json.dumps(v)}')}" for k, v in (params or {}).items()] + (["--optional"] if optional else [])
        return self.command(id, " ".join(cmd), on_pass=on_pass, on_fail=on_fail, max_visits=max_visits, on_limit=on_limit, description=description)

    def gate(self, id: str, metrics_file: str, *rules: str, on_pass: Optional[str] = None, on_fail: Optional[str] = None,
             description: Optional[str] = None) -> "Workflow":
        """Numbers decide, not a model: gate("targets", "metrics.json", "auc>=0.75", "psi<0.2", on_fail="improve")."""
        if not rules:
            raise SpecError(f"step {id!r}: a gate needs at least one rule, like \"auc>=0.75\"")
        words = [_rule_words(r) for r in rules]
        return self.command(id, " ".join(["swarmlab-check", "metrics", _q(metrics_file), *words]), on_pass=on_pass, on_fail=on_fail, description=description)

    def compare(self, id: str, new: str, current: str, metrics: Sequence[str], *, max_drop: float = 0.0, on_pass: Optional[str] = None,
                on_fail: Optional[str] = None, description: Optional[str] = None) -> "Workflow":
        """Champion / challenger: the new model is not worse on any metric by more than max_drop ("-latency_ms": lower is better)."""
        return self.command(id, " ".join(["swarmlab-check", "compare", _q(new), _q(current), *[_q(m) for m in metrics], "--max-drop", str(max_drop)]),
                            on_pass=on_pass, on_fail=on_fail, description=description)

    def ensure(self, id: str, what: str, *args: str, on_pass: Optional[str] = None, on_fail: Optional[str] = None) -> "Workflow":
        """A swarmlab-check step: ensure("has_card", "files", "MODEL_CARD.md"), ensure("no_prices", "prices", "offer.md"),
        ensure("sourced", "sources", "brief.md"), ensure("cols", "csv", "out.csv", "--columns", "a,b"), ensure("tests", "test")."""
        if what not in ("files", "sources", "contains", "absent", "prices", "csv", "json", "words", "test", "metrics", "compare"):
            raise SpecError(f"step {id!r}: unknown check {what!r}")
        return self.command(id, " ".join(["swarmlab-check", what, *[_q(a) for a in args]]), on_pass=on_pass, on_fail=on_fail)

    def decide(self, id: str, question: str, *, yes: str, no: str, state: Optional[str] = None, threshold: Optional[float] = None,
               description: Optional[str] = None) -> "Workflow":
        """A yes/no decision about {last} (or state): "yes" when its probability is at least threshold (default 0.5)."""
        d: Dict[str, Any] = {"type": "noul", "instructions": question}
        if threshold is not None:
            d["threshold"] = threshold
        return self._add(id, {"decide": d, "routes": {"yes": yes, "no": no}, "state": state, "description": description}, {"next"})

    def choice(self, id: str, question: str, options: Mapping[str, str], routes: Optional[Mapping[str, str]] = None, *,
               state: Optional[str] = None, description: Optional[str] = None) -> "Workflow":
        """One of several options (option: what it means). routes: option → step (default: the step named like the option)."""
        if not options:
            raise SpecError(f"step {id!r}: a choice needs options")
        r = dict(routes) if routes else {k: k for k in options}
        return self._add(id, {"decide": {"type": "choice", "instructions": question, "criteria": dict(options)}, "routes": r,
                              "state": state, "description": description}, {"next"})

    def score(self, id: str, question: str, levels: Sequence[str], routes: Mapping[Union[int, str], str], *,
              state: Optional[str] = None, description: Optional[str] = None) -> "Workflow":
        """A level on a scale (levels described in words, lowest first); routes by level number, "else" for the rest."""
        return self._add(id, {"decide": {"type": "score", "instructions": question, "criteria": list(levels)},
                              "routes": {str(k): v for k, v in routes.items()}, "state": state, "description": description}, {"next"})

    def start_at(self, id: str) -> "Workflow":
        self._start = id
        return self

    # ------------------------------------------------------------------ output

    def graph(self) -> Dict[str, Any]:
        """The graph as the server reads it, with the default links filled in."""
        nodes: Dict[str, Dict[str, Any]] = {}
        for i, id in enumerate(self._order):
            n = dict(self._steps[id])
            following = self._order[i + 1] if i + 1 < len(self._order) else "done"
            if "command" in n:
                n.setdefault("onPass", following)
                n.setdefault("onFail", "done")
            elif "decide" not in n and "routes" not in n:
                n.setdefault("next", following)
            nodes[id] = n
        g: Dict[str, Any] = {"start": self._start, "nodes": nodes}
        if self.max_steps is not None:
            g["maxSteps"] = self.max_steps
        return g

    def to_dict(self) -> Dict[str, Any]:
        """The saved-workflow document: the graph, with its agents, prompts, environment and defaults."""
        out: Dict[str, Any] = {"graph": self.graph()}
        if self.description:
            out["description"] = self.description
        if self.inputs:
            out["inputs"] = self.inputs
        if self._agents:
            out["policy"] = {"agents": {a.name: a.policy() for a in self._agents.values()}}
            prompts = {a.name: a.prompt for a in self._agents.values() if a.prompt}
            if prompts:
                out["prompts"] = {"agents": prompts}
        if self.environment is not None:
            out["environment"] = environment_value(self.environment)
        for k in ("settings", "checks", "approvals"):
            v = getattr(self, k)
            if v is not None:
                out[k] = to_api(v)
        return out

    def validate(self) -> List[str]:
        """Problems, in plain words (empty: valid). The same rules as the server, offline."""
        errs = validate_graph(self.graph())
        names = set(self._agents)
        if names:
            for id, n in self._steps.items():
                a = n.get("agent")
                if a and a not in names and not any("*" in x for x in names):
                    errs.append(f"step {id}: agent {a!r} is not one of the workflow's agents ({', '.join(sorted(names))})")
        for id, n in self._steps.items():
            for ref in re.findall(r"\{node:([^}]+)\}", n.get("task", "") + (n.get("state") or "")):
                if ref not in self._steps:
                    errs.append(f"step {id}: {{node:{ref}}} names no step")
        return errs

    def check(self) -> "Workflow":
        """Raise SpecError with every problem, or return the workflow."""
        errs = self.validate()
        if errs:
            raise SpecError(f"workflow {self.name}:\n- " + "\n- ".join(errs))
        return self

    def mermaid(self) -> str:
        """A Mermaid flowchart of the workflow (paste it in a Markdown file, GitHub renders it)."""
        g = self.graph()
        lines = ["flowchart TD", f"  start((start)) --> {g['start']}"]
        label = lambda s: s.replace('"', "'")[:60]
        for id, n in g["nodes"].items():
            if "command" in n:
                lines.append(f'  {id}[/"$ {label(n["command"])}"/]')
            elif "decide" in n:
                lines.append(f'  {id}{{"{label(n["decide"]["instructions"])}"}}')
            else:
                lines.append(f'  {id}["{id}: {label(n.get("agent") or id)}{" ✓" if n.get("check") else ""}"]')
            edges: List[tuple] = []
            for k, lab in (("next", ""), ("onPass", "pass"), ("onFail", "fail"), ("onLimit", "limit")):
                if n.get(k):
                    edges.append((n[k], lab))
            for key, target in (n.get("routes") or {}).items():
                edges.append((target, key))
            for target, lab in edges:
                t = "done((done))" if target in END else target
                lines.append(f"  {id} -->{'|' + lab + '|' if lab else ''} {t}")
        return "\n".join(lines)

    def save(self, file: str) -> str:
        """Write the workflow as JSON (usable with `swarm-lab run --workflow FILE` and `python -m swarmlab run --workflow FILE`)."""
        os.makedirs(os.path.dirname(os.path.abspath(file)), exist_ok=True)
        with open(file, "w", encoding="utf-8") as f:
            json.dump({"name": self.name, **self.to_dict()}, f, indent=2)
            f.write("\n")
        return file

    @classmethod
    def load(cls, file: str, name: Optional[str] = None) -> "Workflow":
        with open(file, encoding="utf-8") as f:
            doc = json.load(f)
        return cls.from_dict(doc, name or doc.get("name") or os.path.splitext(os.path.basename(file))[0])

    @classmethod
    def from_dict(cls, doc: Mapping[str, Any], name: str) -> "Workflow":
        """A saved-workflow document or a bare graph ({start, nodes})."""
        graph = doc.get("graph", doc) if "nodes" not in doc else doc
        wf = cls(re.sub(r"[^\w.-]", "-", name)[:64] or "workflow", doc.get("description"), max_steps=graph.get("maxSteps"),
                 environment=doc.get("environment"), settings=doc.get("settings"), checks=doc.get("checks"), approvals=doc.get("approvals"),
                 inputs=doc.get("inputs"))
        prompts = (doc.get("prompts") or {}).get("agents") or {}
        for aname, pol in ((doc.get("policy") or {}).get("agents") or {}).items():
            wf.add_agent(Agent(name=aname, prompt=prompts.get(aname), model=pol.get("model"), tools=pol.get("tools"), edit=pol.get("editPaths"),
                               read=pol.get("readPaths"), description=pol.get("description"), tool_mode=pol.get("toolMode"), data=pol.get("data")))
        for id, n in (graph.get("nodes") or {}).items():
            wf._steps[id] = dict(n)
            wf._order.append(id)
            wf._explicit[id] = set(n)
        wf._start = graph.get("start")
        return wf

    def __repr__(self) -> str:
        return f"Workflow({self.name!r}, steps={self._order}, agents={list(self._agents)})"


_OPS = {">=": "ge", "<=": "le", "!=": "ne", "=": "eq", ">": "gt", "<": "lt"}


def _rule_words(rule: str) -> str:
    """auc>=0.75 → auc:ge:0.75 (no character a shell or the server's allow-list treats as special)."""
    m = re.match(r"^\s*([A-Za-z_][\w.-]*)\s*(<=|>=|!=|=|<|>)\s*(-?\d+(?:\.\d+)?)\s*$", rule)
    if not m:
        raise SpecError(f"not a rule: {rule!r} (write it like \"auc>=0.75\")")
    return f"{m.group(1)}:{_OPS[m.group(2)]}:{m.group(3)}"


def _q(s: str) -> str:
    """Quote for the job's shell (POSIX and Windows): plain words stay as they are."""
    return s if re.match(r"^[\w./:=@+,-]+$", s) else '"' + s.replace('"', '\\"') + '"'


def validate_graph(g: Any) -> List[str]:
    """The server's graph rules (engine.validateGraph), in Python."""
    errs: List[str] = []
    if not isinstance(g, Mapping) or not isinstance(g.get("nodes"), Mapping):
        return ['it needs "start" and "nodes".']
    nodes = g["nodes"]
    if not nodes:
        errs.append('"nodes" is empty.')
    if not g.get("start") or g["start"] not in nodes:
        errs.append(f'start "{g.get("start")}" is not a node.')
    for id, n in nodes.items():
        if id in END:
            errs.append(f'"{id}" is reserved for the end; rename that node.')
        if n.get("command") and n.get("task"):
            errs.append(f'{id}: give either "command" or "task", not both.')
        d = n.get("decide")
        routes = n.get("routes") or {}
        if d is not None:
            if n.get("command") or n.get("task"):
                errs.append(f'{id}: a decision step ("decide") has no "command" or "task".')
            t = d.get("type") if isinstance(d, Mapping) else None
            if t not in ("choice", "score", "noul"):
                errs.append(f"{id}: decide.type must be choice, score or noul.")
            elif not str(d.get("instructions", "")).strip():
                errs.append(f'{id}: decide needs "instructions" (the question).')
            elif t == "choice" and not (isinstance(d.get("criteria"), Mapping) and d["criteria"]):
                errs.append(f'{id}: a choice needs "criteria": {{"option": "what it means", …}}.')
            elif t == "score" and not (isinstance(d.get("criteria"), list) and 2 <= len(d["criteria"]) <= 10):
                errs.append(f'{id}: a score needs "criteria": 2 to 10 levels described in words, lowest first.')
            th = d.get("threshold") if isinstance(d, Mapping) else None
            if th is not None and not (isinstance(th, (int, float)) and 0 < th < 1):
                errs.append(f"{id}: threshold must be between 0 and 1.")
            if not routes:
                errs.append(f'{id}: a decision step needs "routes".')
            elif t == "choice" and isinstance(d.get("criteria"), Mapping):
                for k in routes:
                    if k != "else" and k not in d["criteria"]:
                        errs.append(f'{id}: route "{k}" is not one of the options ({", ".join(d["criteria"])}).')
            elif t == "noul":
                for k in routes:
                    if k not in ("yes", "no", "else"):
                        errs.append(f'{id}: a yes/no step routes "yes", "no" (and "else"), not "{k}".')
            elif t == "score" and isinstance(d.get("criteria"), list):
                for k in routes:
                    if k != "else" and not (str(k).isdigit() and int(k) < len(d["criteria"])):
                        errs.append(f'{id}: a score step routes by level number 0 to {len(d["criteria"]) - 1}, not "{k}".')
        if not n.get("command") and n.get("routes") and n.get("next"):
            errs.append(f'{id}: give either "routes" or "next", not both.')
        targets = [n.get(k) for k in ("next", "onPass", "onFail", "onLimit")] + list(routes.values())
        for t in [x for x in targets if x]:
            if t not in END and t not in nodes:
                errs.append(f'{id} points to "{t}", which is not a node.')
        if n.get("check") is not None and (not isinstance(n.get("check"), str) or not n["check"].strip() or n.get("command") or n.get("decide")):
            errs.append(f'{id}: "check" is a command, on an agent step (a step with "task").')
        rt = n.get("retries")
        if rt is not None and not (isinstance(rt, int) and 0 <= rt <= 5):
            errs.append(f"{id}: retries is 0 to 5.")
        mv = n.get("maxVisits")
        if mv is not None and not (isinstance(mv, int) and mv >= 1):
            errs.append(f"{id}: maxVisits must be a whole number ≥ 1.")
    return errs
