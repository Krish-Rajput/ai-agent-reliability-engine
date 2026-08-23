"""
AgentGuard — data models.

These are deliberately plain dataclasses / dicts (no ORM) so the project
stays readable in a hackathon review and is trivial to serialize to JSON
for storage and for the frontend.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import time
import uuid


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@dataclass
class AgentConfig:
    id: str
    name: str
    description: str
    tools: List[str]                 # names of tools the agent can call
    system_prompt: str
    target_type: str                 # "builtin" | "webhook"
    builtin_id: Optional[str] = None     # e.g. "reliable_v1", "loopy_v1", "confident_liar_v1"
    webhook_url: Optional[str] = None    # POST {scenario} -> {trace}
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Scenario:
    id: str
    agent_id: str
    category: str            # tool_loop | hallucinated_confidence | destructive_action |
                              # goal_drift | prompt_injection | ambiguous_instruction | happy_path
    title: str
    prompt: str
    setup: Dict[str, Any]     # simulated tool outputs / environment state fed to the agent
    severity: str              # "low" | "medium" | "high" | "critical"
    rationale: str             # why this scenario matters / what it probes

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TraceStep:
    step: int
    type: str                 # "thought" | "tool_call" | "tool_result" | "final_answer"
    content: str = ""
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunResult:
    id: str
    agent_id: str
    scenario_id: str
    scenario_category: str
    scenario_severity: str
    trace: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]    # failure-mode classifier output
    passed: bool
    risk_score: int                   # 0-100, higher = worse
    duration_ms: int
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvalRun:
    """One full evaluation pass (a batch of RunResults) — this is the unit
    that gets compared version-over-version for regression tracking."""
    id: str
    agent_id: str
    label: str                 # e.g. "v1.0", "pre-deploy check", a git sha...
    results: List[str]          # RunResult ids
    reliability_score: int      # 0-100 aggregate
    category_scores: Dict[str, int]
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
