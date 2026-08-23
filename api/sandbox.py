"""
Sandboxed Execution & Replay Harness
=====================================
Runs a scenario against a target agent and captures a structured trace.

Two target modes:
  - "builtin"  -> runs one of the three demo agents in sample_agents.py
                  (zero setup, deterministic, great for a live demo)
  - "webhook"  -> POSTs {scenario} to a real agent's HTTP endpoint that the
                  hackathon team points at their own project, and expects
                  back {"trace": [ {type, content, tool_name?, tool_args?}, ... ]}

Every trace is stored verbatim (deterministic replay) so a judge can re-open
a run later and see exactly what happened, without re-calling any agent.
"""
from __future__ import annotations
from typing import Dict, Any, List
import time
import json
import urllib.request

from .models import AgentConfig, Scenario
from .sample_agents import run_builtin_agent


class SandboxTimeout(Exception):
    pass


def execute_scenario(agent: AgentConfig, scenario: Scenario, timeout_s: float = 8.0) -> Dict[str, Any]:
    """Returns {"trace": [...], "duration_ms": int, "error": str|None}"""
    t0 = time.time()
    error = None
    trace: List[Dict[str, Any]] = []

    try:
        if agent.target_type == "builtin":
            trace = run_builtin_agent(agent.builtin_id, scenario)
        elif agent.target_type == "webhook":
            trace = _call_webhook(agent.webhook_url, scenario, timeout_s)
        else:
            raise ValueError(f"unknown target_type {agent.target_type}")
    except Exception as e:  # noqa: BLE001 — sandbox must never crash the run
        error = str(e)
        trace = [{"step": 1, "type": "final_answer",
                  "content": f"[sandbox] agent raised an error: {error}"}]

    duration_ms = int((time.time() - t0) * 1000)
    return {"trace": trace, "duration_ms": duration_ms, "error": error}


def _call_webhook(url: str, scenario: Scenario, timeout_s: float) -> List[Dict[str, Any]]:
    # Reverted to to_dict()
    payload = json.dumps({"scenario": scenario.to_dict()}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    trace = body.get("trace")
    if not isinstance(trace, list):
        raise ValueError("webhook response missing a 'trace' list")
    return trace