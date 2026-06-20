# Capstone Presentation Script (5-Minute Video)

This document provides a slide-by-slide script for presenting the **Goal Planning & Execution Agent** Capstone project.

---

## 0:00 - Slide 1: Introduction & Problem
**[Visual: Title Slide - Goal Planning & Execution Agent: Composed & Safe Scheduling Concierge]**

* **Speaker Script:**
  "Hello everyone. Today, I am thrilled to present the Goal Planning & Execution Agent—an intelligent, safe concierge assistant that doesn't just generate static milestones, but converts your goals into a personalized calendar-ready schedule and automatically executes sync actions to external tasks and calendar tools. 
  
  Most people fail to reach their goals because they don't break them down into realistic study or work sessions that fit their actual weekly availability. This agent resolves that gap entirely."

---

## 0:45 - Slide 2: The Composed Agent Architecture
**[Visual: High-Level Architecture Flowchart showing Goal + Deadline + Availability → Security Guardrails → Composed Runtime Pipeline (6 Composable Skills) → Simulated MCP Google Tasks/Calendar Execution Layer → Final Web Output + Logs + Traces]**

* **Speaker Script:**
  "Our architecture is built on a modular **Agent Runtime Layer** executing a 9-step pipeline:
  1. The user inputs their Goal, Target Deadline, and Availability Windows.
  2. The input passes through strict Security Guardrails.
  3. The runtime dynamically loads six specialized skills to analyze the goal, generate milestones, plan weekly tasks, schedule concrete study blocks, estimate deadlines, and run self-evaluation checks.
  4. Finally, an MCP Execution Layer automatically registers tasks and calendar events."

---

## 1:45 - Slide 3: Composable Skills & Scheduling Engine
**[Visual: Side-by-side view of skills/ folder and a code snippet of services/scheduler.py]**

* **Speaker Script:**
  "By decoupling the planning steps into modular skills under the `skills/` directory (such as `goal-analysis`, `milestone-generator`, `task-planner`, `session-scheduler`, `timeline-estimator`, and `evaluation`), we can adjust instructions dynamically.
  
  Our scheduling engine in `scheduler.py` maps the generated tasks directly into the user's availability windows (e.g., Monday-Friday evenings and Saturday mornings) to output a clean, weekly calendar timetable."

---

## 2:30 - Slide 4: Simulated MCP Execution Layer
**[Visual: Code snippet of services/mcp_simulator.py and logs/mcp_simulated_db.json]**

* **Speaker Script:**
  "To demonstrate real-world deployability and tool utilization, the agent includes an **MCP Execution Layer**. 
  
  If live Google API endpoints are not linked, the runtime routes events to our local MCP simulation service. It exposes `create_task` and `create_event` functions, writing simulated sync records directly to a local JSON database. This ensures the agent codebase remains 100% MCP-compatible and ready to be connected to real Model Context Protocol servers."

---

## 3:15 - Slide 5: Live Demonstration
**[Visual: Web UI showing Goal 'Pass AI-900', Sept 15 Deadline, and availability. Shows Plan & Sync tab rendering Milestones, Tasks checklist, a Recommended Study Schedule table, and green MCP Sync status messages]**

* **Speaker Script:**
  "Let's look at the web interface. Here we enter the goal 'Pass AI-900', set the deadline, and input availability. We click 'Generate & Sync Plan'.
  
  Within milliseconds, the agent completes the pipeline. In the **Plan & Sync tab**, we see the milestone roadmap, tasks, a personalized weekly study table, and green alerts showing the simulated MCP sync of tasks and calendar events.
  
  The **Execution Trace tab** displays the UUID, runtime duration, the 100/100 Evaluation Score, and the skill sequence checklist. The **Agent Logs tab** outputs structured JSON console logs."

---

## 4:15 - Slide 6: Security, Evaluation, & Deployability
**[Visual: Terminal screens showing pytest passing and run_evaluation.py table; Dockerfile listing]**

* **Speaker Script:**
  "Security is built-in; guardrails screen and log injections (like 'ignore rules') or harmful prompts.
  
  Our automated **Evaluation Framework** runs 9 test scenarios (valid goals, injections, empty cases), validates structures, and outputs report logs. Finally, with the provided `Dockerfile` and `docker-compose.yml`, deploying this entire concierge agent locally requires only a single command: `docker-compose up`."

---

## 4:45 - Slide 7: Conclusion
**[Visual: Summary Slide - Key highlights: Composed Skills, Custom Scheduling, local MCP, Observability, and Docker Staging]**

* **Speaker Script:**
  "The Goal Planning & Execution Agent represents a complete, secure, and production-ready Capstone project. It showcases robust composition, security, tool integration, and developer observability. 
  
  Thank you for listening!"
