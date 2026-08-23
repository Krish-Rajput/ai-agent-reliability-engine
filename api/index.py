from __future__ import annotations
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Relative imports specifically for Vercel's api directory
from .models import AgentConfig, Scenario, RunResult, EvalRun, new_id
from .scenario_generator import generate_scenarios
from .sandbox import execute_scenario
from .classifier import classify, risk_score_for
from .scorecard import aggregate, diff_against, worst_findings
from .sample_agents import BUILTIN_AGENTS
from . import storage

app = FastAPI(title="AgentGuard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentIn(BaseModel):
    name: str
    description: str = ""
    tools: List[str] = []
    system_prompt: str = ""
    target_type: str = "builtin"
    builtin_id: Optional[str] = None
    webhook_url: Optional[str] = None

class GenerateIn(BaseModel):
    n_per_category: int = 1

class RunIn(BaseModel):
    label: str = "manual run"

@app.get("/api/builtin-agents")
def list_builtin_agents():
    return BUILTIN_AGENTS

@app.post("/api/agents")
def create_agent(body: AgentIn):
    db = storage.load()
    # Reverted to dict() and to_dict()
    agent = AgentConfig(id=new_id("agt"), **body.dict())
    db["agents"][agent.id] = agent.to_dict()
    storage.save(db)
    return agent.to_dict()

@app.get("/api/agents")
def list_agents():
    db = storage.load()
    return list(db["agents"].values())

@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str):
    db = storage.load()
    agent = db["agents"].get(agent_id)
    if not agent:
        raise HTTPException(404, "agent not found")
    return agent

@app.post("/api/agents/{agent_id}/scenarios/generate")
def generate(agent_id: str, body: GenerateIn):
    db = storage.load()
    agent_dict = db["agents"].get(agent_id)
    if not agent_dict:
        raise HTTPException(404, "agent not found")
    agent = AgentConfig(**agent_dict)

    scenarios = generate_scenarios(agent, n_per_category=body.n_per_category)
    for s in scenarios:
        # Reverted to to_dict()
        db["scenarios"][s.id] = s.to_dict()
    storage.save(db)
    return [s.to_dict() for s in scenarios]

@app.get("/api/agents/{agent_id}/scenarios")
def list_scenarios(agent_id: str):
    db = storage.load()
    return [s for s in db["scenarios"].values() if s["agent_id"] == agent_id]

@app.post("/api/agents/{agent_id}/run")
def run_eval(agent_id: str, body: RunIn):
    db = storage.load()
    agent_dict = db["agents"].get(agent_id)
    if not agent_dict:
        raise HTTPException(404, "agent not found")
    agent = AgentConfig(**agent_dict)

    scenario_dicts = [s for s in db["scenarios"].values() if s["agent_id"] == agent_id]
    if not scenario_dicts:
        raise HTTPException(400, "generate scenarios before running an eval")

    result_ids, result_objs = [], []

    for sd in scenario_dicts:
        scenario = Scenario(**sd)
        exec_out = execute_scenario(agent, scenario)
        trace = exec_out["trace"]
        findings = classify(scenario, trace)
        risk = risk_score_for(findings)

        rr = RunResult(
            id=new_id("res"), agent_id=agent_id, scenario_id=scenario.id,
            scenario_category=scenario.category, scenario_severity=scenario.severity,
            trace=trace, findings=findings, passed=(len(findings) == 0),
            risk_score=risk, duration_ms=exec_out["duration_ms"],
        )
        # Reverted to to_dict()
        db["results"][rr.id] = rr.to_dict()
        result_ids.append(rr.id)
        result_objs.append(rr)

    agg = aggregate(result_objs)

    prev_runs = sorted(
        [r for r in db["runs"].values() if r["agent_id"] == agent_id],
        key=lambda r: r["created_at"],
    )
    prev_category_scores = prev_runs[-1]["category_scores"] if prev_runs else None

    eval_run = EvalRun(
        id=new_id("run"), agent_id=agent_id, label=body.label,
        results=result_ids, reliability_score=agg["reliability_score"],
        category_scores=agg["category_scores"],
    )
    # Reverted to to_dict()
    db["runs"][eval_run.id] = eval_run.to_dict()
    storage.save(db)

    return {
        "run": eval_run.to_dict(),
        "results": [r.to_dict() for r in result_objs],
        "regression": diff_against(prev_category_scores, agg["category_scores"]),
        "worst_findings": worst_findings(result_objs),
    }

@app.get("/api/agents/{agent_id}/scorecard")
def scorecard(agent_id: str):
    db = storage.load()
    runs = [r for r in db["runs"].values() if r["agent_id"] == agent_id]
    if not runs:
        raise HTTPException(404, "no runs yet for this agent")
    runs.sort(key=lambda r: r["created_at"])
    latest = runs[-1]
    result_objs = [RunResult(**db["results"][rid]) for rid in latest["results"]]
    return {
        "latest_run": latest,
        "history": [{"label": r["label"], "reliability_score": r["reliability_score"],
                      "created_at": r["created_at"]} for r in runs],
        "worst_findings": worst_findings(result_objs),
    }

@app.get("/api/health")
def health():
    return {"status": "ok"}