# 🛡️ AgentGuard
### Reliability Inspection Line for Autonomous AI Agents

[![Live Demo](https://img.shields.io/badge/🚀_Live_App-Vercel-success?style=for-the-badge)](https://vercel.com/krish-8142/ai-agent-reliability-engine/5LDrqbiBiTq6HT3GGYyX9Qm4KbUD)
[![YouTube Demo](https://img.shields.io/badge/📺_Watch_Demo-YouTube-red?style=for-the-badge)](https://youtu.be/WUqWTALxTQ4)

> **AgentGuard** is a lightweight, deterministic evaluation harness and inspection line designed to test autonomous AI agents for critical failure modes *before* they hit production.

---

## 🚀 The Problem
Autonomous AI agents are powerful, but they fail in silent, dangerous ways:
* **Tool Loops:** Getting stuck calling a failing tool infinitely.
* **Hallucinated Confidence:** Asserting completely false answers with 100% certainty when a tool errors out.
* **Unsafe Destructive Actions:** Deleting or modifying data under ambiguous user instructions without checking scope.
* **Prompt Injection:** Blindly executing malicious commands smuggled inside untrusted tool outputs.
* **Goal Drift:** Abandoning the original user objective mid-conversation.

AgentGuard acts as an automated CI/CD safety pipeline that runs an agent through a standardized battery of adversarial and edge-case scenarios to quantify its reliability.

---

## 🛠️ Core Architecture & Components

AgentGuard is built with a clean, modular Python backend (FastAPI) and a modern dark-mode web dashboard:

1. **`scenario_generator.py`** — Dynamically generates a testing battery across 7 key failure categories based on the agent's declared tools and purpose.
2. **`sandbox.py`** — Executes scenarios against target agents in a secure, timed harness and captures a structured, deterministic execution trace (`trace.json`). Supports both built-in toy agents and real HTTP webhooks.
3. **`classifier.py`** — A pure heuristic failure-mode classifier that scans execution traces for rule violations, tagging them with severity (*low, medium, high, critical*).
4. **`scorecard.py`** — Aggregates test results into a single **Reliability Score (0–100)**, provides per-category breakdowns, and tracks regressions across evaluation runs.
5. **`sample_agents.py`** — Ships with three pre-configured reference agents with distinct reliability profiles so judges can test the engine instantly with zero setup.

---

## 📊 Failure Taxonomy Tested

| Category | Description | Severity |
| :--- | :--- | :--- |
| **Happy Path** | Baseline sanity check for routine, well-specified requests. | Low / Info |
| **Tool Loop** | Detects infinite retries on identical failing tool outputs. | High |
| **Hallucinated Confidence** | Flags when an agent lies or acts overly confident despite tool errors. | Critical |
| **Destructive Action** | Catches irreversible actions (delete/cancel) taken on ambiguous scopes. | Critical |
| **Goal Drift** | Tracks whether an agent abandons its primary task after a distraction. | Medium |
| **Prompt Injection** | Identifies if untrusted text inside tool outputs was treated as commands. | Critical |
| **Ambiguous Instruction** | Checks if the agent asks clarifying questions instead of guessing. | Medium |

---

## 🏃 Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone [https://github.com/Krish-Rajput/ai-agent-reliability-engine.git](https://github.com/Krish-Rajput/ai-agent-reliability-engine.git)
cd ai-agent-reliability-engine
2. Install Dependencies
Bash
pip install -r requirements.txt
3. Run Locally
Bash
uvicorn api.index:app --reload
Open index.html or visit http://localhost:8000 to access the inspection dashboard.

🔌 Connecting a Custom Agent (Webhook Mode)
AgentGuard can evaluate any custom AI agent (including OpenAI, Gemini, or LangChain agents) via webhook.

Configure your agent to accept a POST request with a scenario object, and return a JSON response containing an execution trace:

JSON
{
  "trace": [
    {"step": 1, "type": "thought", "content": "Analyzing user request..."},
    {"step": 2, "type": "tool_call", "tool_name": "lookup", "tool_args": {}},
    {"step": 3, "type": "final_answer", "content": "Done!"}
  ]
}
💡 Built-in Demo Agents
To demonstrate discrimination across agent quality without needing external API keys, AgentGuard includes:

Reliable Reference Agent: Retries with a budget, asks for confirmation, and admits uncertainty.

Loopy / Overconfident Agent: Retries forever and executes destructive actions blindly.

Confident Hallucinator Agent: Drifts off-goal easily and falls for prompt injections.

🛡️ License
Distributed under the MIT License. See LICENSE for more information.
