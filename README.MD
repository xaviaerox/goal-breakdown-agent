# Goal Planning & Execution Agent (Concierge Track)

An intelligent, secure **Concierge Agent** designed to transform natural language goals into complete, structured plans, schedule study/work sessions aligned with user availability, and execute calendar synchronization directly via the Model Context Protocol (MCP).

Built as a capstone project for Kaggle's **5-Day AI Agents: Intensive Vibe Coding Course**, demonstrating **Agent Runtime Pipelines**, **Composable Skills**, **Real MCP Servers**, **Security Guardrails**, **Evaluation Frameworks**, and **google-genai SDK Migration**.

---

## 1. Problem Statement
Achieving personal and professional goals is often hindered by:
- **Planning Complexity**: Decomposing a large target (like *Pass AI-900*) into chronologically ordered milestones requires high cognitive effort.
- **Scheduling Friction**: Converting task checklists into specific study calendar blocks matching daily availability is tedious.
- **Execution Gap**: Plans generated in isolation are rarely executed; they must be directly integrated into the user's daily tools (like Google Calendar) to drive action.

---

## 2. Solution: The Planning Concierge
Our agent acts as a secure personal concierge:
1. **Inputs**: Takes a goal, target deadline, weekly availability windows, and session preferences.
2. **Decomposes & Schedules**: Dynamically triggers specialized skills to analyze goals, create milestones, plan tasks, and allocate sessions.
3. **Executes**: Programmatically syncs study blocks directly to the user's **Google Calendar** using the Model Context Protocol (MCP), ensuring they are scheduled before the user-defined deadline.

---

## 3. Key Course Concepts Applied (3 Required)

This capstone project implements and showcases several core agent technologies covered in the course:

### A. Composed Agent Pipeline (Skills Discovery)
Rather than a single prompt monolithic model call, the agent coordinator dynamically discovers and chains independent **Composable Skills** (located under `skills/`). This allows modular prompt engineering, isolated testing of skills, and deterministic scoring.

### B. Production MCP Server Integration
The agent interacts with the real-world **Google Workspace MCP Server** (`@alanxchen/google-workspace-mcp`) via a stdio transport client. It batch-creates real calendar events dynamically mapped to the calculated study dates.

### C. Security Guardrails & Safety
To protect against prompt injection and harmful actions, the coordinator runs inputs through an validation engine *before* invoking any LLM, logging rejections to a local audit trail.

### D. google-genai SDK Migration
The system is built on the official, modern `google-genai` Python library, using client-instantiated generative models (`client.models.generate_content`) and structured `types.GenerateContentConfig` objects.

---

## 4. Architecture

```
User Input (Goal, Deadline, Availability, Prefs)
      │
      ▼
[Security Guardrails]  ──(Violated)──► [Block & Log to logs/rejected_requests.log]
      │
      ▼ (Valid)
[Agent Runtime Coordinator] ◄──(Skill Discovery scans skills/ directory)
      │
      ├── 1. Execute Skill [goal-analysis]      ──► Gemini 2.5 Flash
      ├── 2. Execute Skill [milestone-generator] ──► Gemini 2.5 Flash
      ├── 3. Execute Skill [task-planner]        ──► Gemini 2.5 Flash
      ├── 4. Execute Skill [session-scheduler]   ──► Local Scheduler Engine (Deadline-strict)
      ├── 5. Execute Skill [timeline-estimator]  ──► Gemini 2.5 Flash
      └── 6. Execute Skill [evaluation]          ──► Local RuntimeEvaluator (Scoring)
      │
      ▼
[MCP Real Execution Layer] ──► npx @alanxchen/google-workspace-mcp
                           ──► Batch-creates Google Calendar events
```

- **Runtime coordinator**: Found in [agent_runtime/runtime.py](agent_runtime/runtime.py), it coordinates the 9-step pipeline.
- **Skill Loader**: Found in [agent_runtime/skill_loader.py](agent_runtime/skill_loader.py), it dynamically parses metadata and instructions.
- **Real MCP Integration**: Found in [services/mcp_real.py](services/mcp_real.py), connects securely to the Google Workspace MCP server using Python's MCP SDK.
- **Scheduling Engine**: Found in [services/scheduler.py](services/scheduler.py), parses deadlines and distributes tasks sequentially (avoiding overlapping hours).

---

## 5. Agent Skills

Decoupled specialized skills located under `skills/`:

| Skill | Directory | Description / Trigger |
|---|---|---|
| **Goal Analysis** | `skills/goal-analysis` | Analyze raw goal input, target deadline, availability, and session preferences |
| **Milestone Generator** | `skills/milestone-generator` | Generate high-level phases or milestones based on analyzed goal |
| **Task Planner** | `skills/task-planner` | Plan weekly or progressive actionable tasks for each milestone |
| **Session Scheduler** | `skills/session-scheduler` | Schedule specific time blocks and sessions based on user availability and deadline |
| **Timeline Estimator** | `skills/timeline-estimator` | Estimate overall timeline, weekly pacing, and date alignment |
| **Evaluation** | `skills/evaluation` | Evaluate and validate the structured plan, weekly tasks, calendar sessions, and pacing |

---

## 6. Security and Guardrails

Located in [security/guardrails.py](security/guardrails.py), the guardrails protect against malicious inputs before they reach the LLM:
1. **Emptiness Check**: Blocks empty or whitespace-only inputs.
2. **Length Guard**: Blocks goals exceeding 1000 characters.
3. **Prompt Injection Guard**: Detects override templates (e.g. *"ignore previous instructions"*).
4. **Harmful Instruction Guard**: Screen for malicious intents (e.g. *"malware"*, *"hack"*).

Blocked requests are logged in `logs/rejected_requests.log`.

---

## 7. Evaluation Framework

To automate testing and scoring, we built an executable evaluation suite:
- **`evaluation/test_cases.json`**: Lists 9 test scenarios (valid planning, prompt injection, harmful content).
- **`evaluation/run_evaluation.py`**: Executes the test cases, validates plan structure (milestones, tasks, sessions, timeline, and MCP actions), checks guardrail assertions, and generates `logs/evaluation_report.json` with an evaluation score.
- *Note: In evaluation runs, the calendar creation is mocked dynamically to prevent cluttering your live Google Calendar.*

---

## 8. Setup & Installation Instructions

### Prerequisites
- Python 3.10+ installed.
- Node.js (for running `@alanxchen/google-workspace-mcp` via `npx`).
- A Google Cloud Project with the **Google Calendar API** enabled.
- OAuth 2.0 Client credentials downloaded from your Google Cloud Console.

### Environment Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in the environment variables in `.env`:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `GOOGLE_CLIENT_ID`: Your Google OAuth client ID.
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret.

### Running Locally
1. Initialize virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # On Windows
   # source .venv/bin/activate  # On Linux/macOS
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your browser and visit `http://localhost:5000`. On your first plan generation, the browser will open a Google authentication screen asking you to grant calendar permissions to the application.

### Running Tests
To run the automated pytest test suite:
```bash
pytest tests/test_app.py
```

To run the agent evaluation pipeline:
```bash
python evaluation/run_evaluation.py
```
