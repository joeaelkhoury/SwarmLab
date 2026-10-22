# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""Typed building blocks for Swarm Lab jobs: every field the server accepts, in Python names.

Each class turns into the JSON the server expects with ``.to_dict()``. Plain dicts are accepted everywhere a class
is, so you can start simple and switch to classes when you want autocompletion and early errors::

    Settings(max_steps_per_agent=20, token_budget=200_000)
    Approvals(commands="allowlist", command_allow_list=["pytest -q"])
    Environment.python(setup=["pip install -e ."])
    Agent("fixer", "You fix bugs with the smallest change.", model="lead", edit=["src/**"])
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

__all__ = [
    "Settings", "Approvals", "Environment", "VSCode", "Agent", "Checks", "Memory", "Data", "Skill", "Hook", "Mcp", "Models",
    "Providers", "SpecError", "to_api", "camel", "SETTINGS_FIELDS",
]


class SpecError(ValueError):
    """A job, workflow or environment that cannot work, found before anything is sent."""


def camel(name: str) -> str:
    """snake_case → camelCase (the server's names)."""
    head, *rest = name.split("_")
    return head + "".join(p[:1].upper() + p[1:] for p in rest)


def to_api(value: Any) -> Any:
    """Classes of this module (and lists/dicts of them) → plain JSON values."""
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {k: to_api(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_api(v) for v in value]
    return value


def _compact(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class _Spec:
    """A dataclass whose non-None fields become camelCase JSON."""

    _rename: Dict[str, str] = {}

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for f in fields(self):  # type: ignore[arg-type]
            v = getattr(self, f.name)
            if v is None or f.name.startswith("_"):
                continue
            out[self._rename.get(f.name, camel(f.name))] = to_api(v)
        return out


# --------------------------------------------------------------------------- settings


@dataclass
class Settings(_Spec):
    """Run settings. The server only accepts the ones in its ``allowedSettingOverrides`` (see ``capabilities()``)."""

    max_steps_per_agent: Optional[int] = None
    max_agents: Optional[int] = None
    token_budget: Optional[int] = None
    max_tokens_per_call: Optional[int] = None
    cost_budget_usd: Optional[float] = None
    lead_model: Optional[str] = None
    worker_model: Optional[str] = None
    answer_length: Optional[str] = None          # "short" | "normal" | "long"
    answer_style: Optional[str] = None           # "visual" | "plain"
    tool_mode: Optional[str] = None              # "native" | "text" | "none"
    max_continuations: Optional[int] = None
    max_input_tokens: Optional[int] = None
    max_parallel_calls: Optional[int] = None
    sequential_tools: Optional[bool] = None
    final_answer_on_limit: Optional[bool] = None
    rag_top_k: Optional[int] = None
    rag_auto_k: Optional[int] = None
    _rename = {"rag_top_k": "ragTopK", "rag_auto_k": "ragAutoK", "cost_budget_usd": "costBudgetUsd"}

    def __post_init__(self) -> None:
        _choice("answer_length", self.answer_length, ("short", "normal", "long"))
        _choice("answer_style", self.answer_style, ("visual", "plain"))
        _choice("tool_mode", self.tool_mode, ("native", "text", "none"))
        for n in ("max_steps_per_agent", "max_agents", "token_budget", "max_tokens_per_call", "max_continuations", "max_parallel_calls"):
            v = getattr(self, n)
            if v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < 0):
                raise SpecError(f"Settings.{n} must be a whole number ≥ 0, not {v!r}")


SETTINGS_FIELDS = tuple(f.name for f in fields(Settings) if not f.name.startswith("_"))
# Short names people reach for.
SETTINGS_ALIASES = {"max_steps": "max_steps_per_agent", "budget": "token_budget", "max_tokens": "max_tokens_per_call", "cost_limit": "cost_budget_usd"}


def _choice(name: str, value: Any, allowed: Sequence[str]) -> None:
    if value is not None and value not in allowed:
        raise SpecError(f"{name} must be one of {', '.join(allowed)}, not {value!r}")


# --------------------------------------------------------------------------- approvals


@dataclass
class Approvals(_Spec):
    """What waits for a human. edits/file_ops/mcp: "auto" | "ask" | "off"; commands: "auto" | "allowlist" | "ask" | "off"."""

    edits: Optional[str] = None
    file_ops: Optional[str] = None
    commands: Optional[str] = None
    command_allow_list: Optional[List[str]] = None
    mcp: Optional[str] = None
    messages: Optional[str] = None               # "off" | "lead" | "all"
    timeout_sec: Optional[int] = None

    def __post_init__(self) -> None:
        for n in ("edits", "file_ops", "mcp"):
            _choice(f"Approvals.{n}", getattr(self, n), ("auto", "ask", "off"))
        _choice("Approvals.commands", self.commands, ("auto", "allowlist", "ask", "off"))
        _choice("Approvals.messages", self.messages, ("off", "lead", "all"))

    @classmethod
    def unattended(cls, allow: Optional[List[str]] = None) -> "Approvals":
        """Nothing waits: edits and file operations apply (the result is still a branch to review); commands on the list run."""
        return cls(edits="auto", file_ops="auto", commands="allowlist" if allow else "auto", command_allow_list=allow, mcp="auto", messages="off")

    @classmethod
    def careful(cls) -> "Approvals":
        """Every edit, file operation, command and MCP call waits for a human."""
        return cls(edits="ask", file_ops="ask", commands="ask", mcp="ask")


# --------------------------------------------------------------------------- editor

@dataclass
class VSCode(_Spec):
    """A real editor in the environment: downloaded once (VS Code, Insiders, VSCodium) or one you have installed.

    Extensions are installed from .vsix files or ids, the workspace's extension is packaged and installed, and a smoke
    check runs inside the editor: the extensions activate, their commands exist, `commands` run (their results are
    reported), and `check` (a script run in the editor) can test anything. `swarmlab-vscode check` does it again on
    demand (agents, workflow steps); the job ends with a final check (see `require`).
    """

    flavor: Optional[str] = None                 # "vscode" | "insiders" | "vscodium"
    version: Optional[str] = None                # "stable" (default) or "1.95.3" / a VSCodium tag
    executable: Optional[str] = None             # an installed editor: code, codium, cursor, …/Code.exe, ….app
    package: Optional[bool] = None
    install: Optional[List[str]] = None          # .vsix files and extension ids
    smoke: Optional[bool] = None
    commands: Optional[List[Union[str, Dict[str, Any]]]] = None
    check: Optional[str] = None                  # module.exports = async (vscode, report) => true | false
    verify: Optional[List[str]] = None
    open: Optional[str] = None
    project_tests: Optional[bool] = None
    timeout_sec: Optional[int] = None
    system_deps: Optional[bool] = None
    require: Optional[str] = None                # "regression" (default) | "pass" | "none"

    def __post_init__(self) -> None:
        _choice("VSCode.flavor", self.flavor, ("vscode", "insiders", "vscodium"))
        _choice("VSCode.require", self.require, ("regression", "pass", "none"))
        for n in ("install", "verify"):
            if isinstance(getattr(self, n), str):
                setattr(self, n, [getattr(self, n)])


# --------------------------------------------------------------------------- environment

ENV_PRESETS = ("auto", "none", "node", "python", "go", "rust", "java", "dotnet", "vscode-extension")


@dataclass
class Environment(_Spec):
    """Where the job's commands run, installed before the agents start.

    ``Environment.auto()`` detects the project (package.json, pyproject.toml, requirements.txt, go.mod, Cargo.toml…);
    ``Environment.docker("node:22", setup=[...])`` runs everything in a container you choose, so anything can be
    installed; ``Environment.vscode_extension()`` installs, compiles and gives tests a virtual screen.
    """

    preset: Optional[str] = None
    runtime: Optional[str] = None                # "local" | "docker"
    image: Optional[str] = None
    setup: Optional[List[str]] = None
    pre_setup: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    path: Optional[List[str]] = None
    display: Optional[str] = None                # "auto" | "virtual" | "none"
    test: Optional[str] = None
    home: Optional[str] = None                   # "inherit" | "isolated"
    network: Optional[bool] = None
    timeout_sec: Optional[int] = None
    continue_on_error: Optional[bool] = None
    vscode: Optional[Union[VSCode, bool, Dict[str, Any]]] = None
    notebooks: Optional[Union[bool, Dict[str, Any]]] = None   # True, or {"packages": [...], "kernel", "cellTimeoutSec"}
    _name: Optional[str] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        _choice("Environment.preset", self.preset, ENV_PRESETS)
        _choice("Environment.runtime", self.runtime, ("local", "docker"))
        _choice("Environment.display", self.display, ("auto", "virtual", "none"))
        _choice("Environment.home", self.home, ("inherit", "isolated"))
        if self.runtime == "docker" and not self.image:
            raise SpecError("Environment: runtime \"docker\" needs an image, e.g. Environment.docker(\"node:22\")")
        for n in ("setup", "pre_setup", "path"):
            v = getattr(self, n)
            if isinstance(v, str):
                setattr(self, n, [v])
        if self.env:
            for k in self.env:
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k):
                    raise SpecError(f"Environment.env: {k!r} is not a variable name")
                if k.upper() == "PATH":
                    raise SpecError("Environment.env: put folders in path=[...] instead of PATH")
            self.env = {k: str(v) for k, v in self.env.items()}

    def to_dict(self) -> Any:  # type: ignore[override]
        if self._name is not None:
            return self._name
        return super().to_dict()

    # Ready-made environments -------------------------------------------------
    @classmethod
    def named(cls, name: str) -> "Environment":
        """A preset or one of the server's named environments (see capabilities()['environments']['server'])."""
        e = cls()
        e._name = name
        return e

    @classmethod
    def auto(cls, **kw: Any) -> "Environment":
        return cls(preset="auto", **kw)

    @classmethod
    def none(cls, **kw: Any) -> "Environment":
        return cls(preset="none", **kw)

    @classmethod
    def notebooks_env(cls, packages: Optional[List[str]] = None, **kw: Any) -> "Environment":
        """Python with Jupyter: `swarmlab-nb` runs notebooks cell by cell (packages: extra pip packages, e.g. ["pandas"])."""
        return cls(preset="python", notebooks={"packages": list(packages)} if packages else True, **kw)

    @classmethod
    def node(cls, **kw: Any) -> "Environment":
        return cls(preset="node", **kw)

    @classmethod
    def python(cls, **kw: Any) -> "Environment":
        return cls(preset="python", **kw)

    @classmethod
    def vscode_extension(cls, editor: Union[VSCode, Dict[str, Any], None] = None, **kw: Any) -> "Environment":
        """Install and compile the extension, then a real editor: package it, install it, smoke-check it (VSCode(...) for options)."""
        kw.setdefault("display", "virtual")
        return cls(preset="vscode-extension", vscode=editor if editor is not None else None, **kw)

    @classmethod
    def editor(cls, editor: Union[VSCode, Dict[str, Any], None] = None, preset: str = "none", **kw: Any) -> "Environment":
        """Just an editor with extensions, e.g. Environment.editor(VSCode(install=["my.vsix"], commands=["my.hello"]))."""
        return cls(preset=preset, vscode=editor if editor is not None else True, display=kw.pop("display", "virtual"), **kw)

    @classmethod
    def docker(cls, image: str, setup: Optional[List[str]] = None, preset: str = "none", **kw: Any) -> "Environment":
        return cls(runtime="docker", image=image, setup=setup, preset=preset, **kw)

    @classmethod
    def load(cls, file: str) -> "Environment":
        """Read a .swarmlab/environment.json style file."""
        with open(file, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def from_dict(cls, d: Union[str, Mapping[str, Any]]) -> "Environment":
        if isinstance(d, str):
            return cls.named(d)
        snake = {re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower(): v for k, v in d.items()}
        if isinstance(snake.get("vscode"), Mapping):
            snake["vscode"] = VSCode(**{re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower(): v for k, v in snake["vscode"].items()})
        known = {f.name for f in fields(cls) if not f.name.startswith("_")}
        unknown = set(snake) - known
        if unknown:
            raise SpecError(f"Environment: unknown field(s) {', '.join(sorted(unknown))}")
        return cls(**snake)

    def save(self, file: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(file)), exist_ok=True)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")


def environment_value(e: Any) -> Any:
    """What a job's "environment" field holds: a name, an object, or False."""
    if e is None or e is False:
        return e
    if isinstance(e, str):
        return e
    if isinstance(e, Environment):
        return e.to_dict()
    if isinstance(e, Mapping):
        return Environment.from_dict(e).to_dict()
    raise SpecError(f"environment must be an Environment, a dict, a name or False, not {type(e).__name__}")


# --------------------------------------------------------------------------- agents


TOOLS = ("list_files", "read_file", "search_text", "search_code", "code_symbols", "call_graph", "edit_file", "write_file", "save_block",
         "delete_file", "rename_file", "run_command", "run_tests", "remember", "use_skill", "create_skill", "list_data", "read_data", "write_output",
         "web_search", "fetch_url", "post_note", "read_board", "ask_peer", "delegate", "create_agent", "ask_agent", "finish", "check_workflow")


@dataclass
class Agent(_Spec):
    """One agent: its instructions, model and permissions.

    name: how steps and leads refer to it. prompt: its instructions (its system prompt for this job).
    model: "lead", "worker" or an exact model id. tools: the only tools it gets (default: its role's).
    edit: file globs it may change ([] = none). read: file globs it may read (single mode only).
    """

    name: str = ""
    prompt: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    edit: Optional[List[str]] = None
    read: Optional[List[str]] = None
    description: Optional[str] = None
    tool_mode: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.name or not re.match(r"^[A-Za-z0-9_*-]{1,64}$", self.name):
            raise SpecError(f"Agent name {self.name!r}: use letters, digits, - and _ (up to 64)")
        _choice(f"Agent({self.name}).tool_mode", self.tool_mode, ("native", "text", "none"))
        if self.tools is not None:
            unknown = [t for t in self.tools if t not in TOOLS and not t.startswith("mcp__")]
            if unknown:
                raise SpecError(f"Agent({self.name}): unknown tool(s) {', '.join(unknown)} (tools: {', '.join(TOOLS)}, or mcp__server__tool)")
        for n in ("edit", "read", "tools"):
            v = getattr(self, n)
            if isinstance(v, str):
                setattr(self, n, [v])

    def policy(self) -> Dict[str, Any]:
        """Its entry in policy.agents."""
        return _compact({"description": self.description, "model": self.model, "tools": self.tools, "editPaths": self.edit,
                         "readPaths": self.read, "toolMode": self.tool_mode, "data": self.data})

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, **self.policy(), **({"prompt": self.prompt} if self.prompt else {})}


def agents_into(spec: Dict[str, Any], agents: Sequence[Union[Agent, Mapping[str, Any]]]) -> None:
    """Put agents into spec.policy.agents and their prompts into spec.prompts.agents (existing entries win)."""
    for a in agents:
        if isinstance(a, Mapping):
            a = Agent(**{k: v for k, v in a.items()})
        pol = spec.setdefault("policy", {}).setdefault("agents", {})
        pol.setdefault(a.name, a.policy())
        if a.prompt:
            spec.setdefault("prompts", {}).setdefault("agents", {}).setdefault(a.name, a.prompt)


# --------------------------------------------------------------------------- the rest


@dataclass
class Checks(_Spec):
    """tests: True (the environment's or a detected test command) or a command. verify: check "done" independently."""

    tests: Optional[Union[bool, str]] = None
    verify: Optional[bool] = None
    retry: Optional[bool] = None


@dataclass
class Memory(_Spec):
    """Share memory with other jobs of the same session, and with topics. Memory(False) is not possible: pass memory=False."""

    session: Optional[str] = None
    topics: Optional[List[str]] = None


@dataclass
class Data(_Spec):
    """Files or folders every agent may read, and the folder where results go."""

    inputs: Optional[List[str]] = None
    output: Optional[str] = None


@dataclass
class Skill(_Spec):
    name: str = ""
    description: str = ""
    instructions: str = ""
    status: Optional[str] = None                 # "trial" | "trusted"


@dataclass
class Hook(_Spec):
    """An HTTP hook: called before commands, edits or tools (allow / deny / note), or after events."""

    url: str = ""
    events: Optional[List[str]] = None           # "before:command", "before:edit", "before:tool", "after:call", "job:end"…
    tools: Optional[List[str]] = None            # before:tool only: these tools (names or globs)
    secret: Optional[str] = None                 # write "${ENV_NAME}", not the secret itself
    timeout_ms: Optional[int] = None
    on_timeout: Optional[str] = None             # "allow" | "deny"


@dataclass
class Mcp(_Spec):
    """MCP servers for the job: use= names from the server's configuration, add= {"name": {"url": "..."}}."""

    use: Optional[List[str]] = None
    add: Optional[Dict[str, Dict[str, Any]]] = None


@dataclass
class Models(_Spec):
    auto: Optional[str] = None                   # "off" | "cheapest" | "balanced" | "best"

    def __post_init__(self) -> None:
        _choice("Models.auto", self.auto, ("off", "cheapest", "balanced", "best"))


@dataclass
class Providers(_Spec):
    """Models of the host's RAG and decision services for this job (no URLs or keys)."""

    rag_model: Optional[str] = None
    rag_top_k: Optional[int] = None
    rag_auto_k: Optional[int] = None
    decision_model: Optional[str] = None
    decision_min_confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        rag = _compact({"model": self.rag_model, "topK": self.rag_top_k, "autoK": self.rag_auto_k})
        dec = _compact({"model": self.decision_model, "minConfidence": self.decision_min_confidence})
        return _compact({"rag": rag or None, "decision": dec or None})
