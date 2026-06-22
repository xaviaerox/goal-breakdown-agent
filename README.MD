# Goal Planning & Execution Agent (Concierge Track)

![The Planning Concierge Banner](docs/project_banner.png)

An intelligent, secure **Concierge Agent** designed to transform natural language goals into complete, structured plans, schedule study/work sessions aligned with user availability, and execute calendar synchronization directly via the Model Context Protocol (MCP).

Built as a capstone project for Kaggle's **5-Day AI Agents: Intensive Vibe Coding Course**, demonstrating **Agent Runtime Pipelines**, **Composable Skills**, **Real MCP Servers**, **Security Guardrails**, **Evaluation Frameworks**, **google-genai SDK Migration**, and production deployment on **Google Cloud Run** using a **Headless OAuth Token Seeding** mechanism.

🚀 **Production Web App URL**: [https://goal-breakdown-agent-61703236417.us-central1.run.app/](https://goal-breakdown-agent-61703236417.us-central1.run.app/)

---

## 1. Problem Statement
Achieving personal and professional goals is often hindered by:
- **Planning Complexity**: Decomposing a large target (like *Pass Cisco CyberOps Associate*) into chronologically ordered milestones requires high cognitive effort.
- **Scheduling Friction**: Converting task checklists into specific study calendar blocks matching daily availability is tedious.
- **Execution Gap**: Plans generated in isolation are rarely executed; they must be directly integrated into the user's daily tools (like Google Calendar) to drive action.
- **Deployment & Latency**: Running agents locally limits access, but deploying them to the cloud often crashes due to headless environment restrictions (like browser-based OAuth flows).

---

## 2. Solution: The Planning Concierge
Our agent acts as a secure personal concierge:
1. **Inputs**: Takes a goal, target deadline, weekly availability windows, and session preferences.
2. **Decomposes & Schedules**: Dynamically triggers specialized skills to analyze goals, create milestones, plan tasks, and allocate sessions.
3. **Executes**: Programmatically syncs study blocks directly to the user's **Google Calendar** using secure, multi-tenant Google OAuth 2.0 authentication, ensuring they are scheduled before the user-defined deadline.
4. **Cloud Ready**: Operates on Google Cloud Run with OAuth redirects and automatic token refresh, allowing any public user to authenticate and sync.

---

## 3. Key Course Concepts Applied (5 Implemented)

This capstone project implements and showcases several core agent technologies covered in the course:

### A. Composed Agent Pipeline (Skills Discovery)
Rather than a single prompt monolithic model call, the agent coordinator dynamically discovers and chains independent **Composable Skills** (located under `skills/`). This allows modular prompt engineering, isolated testing of skills, and deterministic scoring.

### B. Production Google API Integration
The agent connects directly to the **Google Calendar API** to batch-create real calendar events dynamically mapped to the calculated study dates, adjusting for timezones and localOffsets.

### C. Security Guardrails & Safety
To protect against prompt injection and harmful actions, the coordinator runs inputs through a validation engine *before* invoking any LLM, logging rejections to a local audit trail.

### D. google-genai SDK Migration
The system is built on the official, modern `google-genai` Python library, using client-instantiated generative models (`client.models.generate_content`) and structured `types.GenerateContentConfig` objects.

### E. Cloud Deployability & Multi-Tenant OAuth 2.0
The backend is dockerized and deployed to **Google Cloud Run**. To support secure, multi-tenant user authentication in production, we implemented standard Google OAuth 2.0. Users log in securely with their own Google Account, authorizing the app to manage only their calendar events, with session-stored access tokens refreshed automatically in the background.

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
      ├── 4. Execute Skill [session-scheduler]   ──► Local Scheduler Engine (Midnight Rollover Fix)
      ├── 5. Execute Skill [timeline-estimator]  ──► Gemini 2.5 Flash
      └── 6. Execute Skill [evaluation]          ──► Local RuntimeEvaluator (Scoring)
      │
      ▼
[Google OAuth 2.0 Layer] ──► User log in / consent (redirects to /oauth2callback)
                         ──► Saves encrypted token in Flask Session
                         ──► Batch-creates events directly on user's Primary Calendar
```

- **Runtime coordinator**: Found in [agent_runtime/runtime.py](agent_runtime/runtime.py), it coordinates the 9-step pipeline.
- **Skill Loader**: Found in [agent_runtime/skill_loader.py](agent_runtime/skill_loader.py), it dynamically parses metadata and instructions.
- **Direct Calendar Client**: Found in [services/calendar_client.py](services/calendar_client.py), connects securely to the Google Calendar REST API using the user's OAuth access token.
- **Scheduling Engine**: Found in [services/scheduler.py](services/scheduler.py), parses deadlines and distributes tasks sequentially (avoiding overlapping hours and handling midnight rollover).

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
- **Score**: **100% Success (9/9 Passed)**.
- *Note: In evaluation runs, the calendar creation is mocked dynamically to prevent cluttering your live Google Calendar.*

---

## 8. Setup & Installation Instructions

### Prerequisites
- Python 3.10+ installed.
- A Google Cloud Project with the **Google Calendar API** and **Google People API** enabled.
- OAuth 2.0 Client credentials created in your Google Cloud Console.

### Environment Configuration
1. Create a `.env` file in the project root:
   ```bash
   # Gemini API Key
   GEMINI_API_KEY=your_gemini_api_key
   
   # Google OAuth Credentials
   GOOGLE_CLIENT_ID=your_oauth_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_oauth_client_secret
   ```

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
3. Open your browser and visit `http://localhost:5000`. Click the **"Iniciar sesión con Google"** button to log in.

### Running Tests & Evaluation
To run the automated pytest test suite:
```bash
pytest tests/test_app.py
```

To run the agent evaluation pipeline:
```bash
python evaluation/run_evaluation.py
```

---

## 9. Google Cloud Run Deployment

To deploy the entire application to Google Cloud Run, execute the following commands in PowerShell from the project root:

1. **Authenticate and configure project**:
   ```powershell
   gcloud.cmd auth login
   gcloud.cmd config set project gen-lang-client-0316055858
   ```
2. **Enable required services**:
   ```powershell
   gcloud.cmd services enable run.googleapis.com build.googleapis.com artifactregistry.googleapis.com
   ```
3. **Deploy**:
   ```powershell
   gcloud.cmd run deploy goal-breakdown-agent --source . --region us-central1 --allow-unauthenticated
   ```
4. **Configure Environment Variables**:
   In the Google Cloud Run Console for `goal-breakdown-agent`, add the following environment variables (or let them load from the deployed `.env` file):
   - `GEMINI_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_TOKEN_JSON`: Paste the JSON content of your locally authenticated `~/.google-workspace-mcp/token.json` file to support headless OAuth bypass.

---

## 10. Presentation & Deliverables

All presentation materials are located in the [docs/](file:///c:/Users/Xaviaerox/Documents/GitHub/goal-breakdown-agent/docs) folder:

- **Presentation Slides (PowerPoint)**: [The_Planning_Concierge.pptx](file:///c:/Users/Xaviaerox/Documents/GitHub/goal-breakdown-agent/docs/The_Planning_Concierge.pptx)
- **Presentation Slides (PDF format)**: [The_Planning_Concierge.pdf](file:///c:/Users/Xaviaerox/Documents/GitHub/goal-breakdown-agent/docs/The_Planning_Concierge.pdf)
- **Video Presentation Script (in Spanish)**: [presentation_script.MD](file:///c:/Users/Xaviaerox/Documents/GitHub/goal-breakdown-agent/docs/presentation_script.MD)
