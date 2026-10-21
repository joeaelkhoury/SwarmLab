"""Swarm Lab for Python: agents, teams and workflows, on a Swarm Lab server or on this machine.

    from swarmlab import SwarmLab, Agent, Workflow, Environment

    sl = SwarmLab()                     # or SwarmLab.local("path/to/repo") without a server
    r = sl.run("Fix the failing test", repo="app", environment="auto", checks=True)
    print(r.answer)

See docs/PYTHON-LIBRARY.md.
"""
from .client import Job, JobFailed, Result, SwarmLab, SwarmLabError, build_spec, find_server
from .spec import Agent, Approvals, Checks, Data, Environment, Hook, Mcp, Memory, Models, Providers, Settings, Skill, SpecError, VSCode
from .workflow import Workflow, validate_graph

__version__ = "0.40.0"
__all__ = ["SwarmLab", "Job", "Result", "SwarmLabError", "JobFailed", "SpecError", "build_spec", "find_server",
           "Agent", "Workflow", "Environment", "VSCode", "Settings", "Approvals", "Checks", "Memory", "Data", "Skill", "Hook", "Mcp",
           "Models", "Providers", "validate_graph", "__version__"]
