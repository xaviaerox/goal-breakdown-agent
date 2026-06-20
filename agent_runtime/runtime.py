import os
import json
import re
from datetime import datetime, timedelta, timezone
from security.guardrails import check_guardrails
from services.gemini_client import is_gemini_configured, call_gemini
from services.scheduler import generate_schedule
from agent_runtime.skill_loader import discover_skills
from agent_runtime.execution_trace import ExecutionTrace
from agent_runtime.evaluator import RuntimeEvaluator

class AgentRuntimeError(Exception):
    pass

def extract_json(text: str) -> dict:
    """
    Extracts and parses JSON object from text, handling markdown blocks if present.
    """
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    
    text_clean = text.strip()
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        brace_match = re.search(r"(\{.*\})", text_clean, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Failed to parse JSON from text: {repr(text)}")

class ComposedAgentRuntime:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.trace = None
        self.evaluator = RuntimeEvaluator()

    def run(self, goal: str, deadline: str = "", availability: str = "", sessions_pref: str = "") -> dict:
        self.trace = ExecutionTrace()
        self.trace.start()
        
        # Ensure default values if empty
        deadline = deadline or "Not specified"
        availability = availability or "Monday-Friday 19:00-20:30"
        sessions_pref = sessions_pref or "Evening study blocks"

        # 1. Goal Input & Guardrails
        self.trace.log("Goal Input", "INFO", "Validating goal input against security guardrails...")
        try:
            cleaned_goal = check_guardrails(goal)
            self.trace.log("Goal Input", "INFO", "Input validation successful.")
        except Exception as e:
            self.trace.log("Goal Input", "ERROR", f"Guardrail validation failed: {str(e)}")
            self.trace.stop(status="failed")
            raise

        # 2. Skill Discovery
        self.trace.log("Skill Discovery", "INFO", f"Scanning {self.skills_dir}/ directory for composable skills...")
        discovered = discover_skills(self.skills_dir)
        self.trace.log("Skill Discovery", "INFO", f"Discovered {len(discovered)} skills: {list(discovered.keys())}")
        
        required_skills = [
            "goal-analysis", "milestone-generator", "task-planner", 
            "session-scheduler", "timeline-estimator", "evaluation"
        ]
        missing_skills = [s for s in required_skills if s not in discovered]
        if missing_skills:
            err_msg = f"Missing required skills in directory: {missing_skills}"
            self.trace.log("Skill Discovery", "ERROR", err_msg)
            self.trace.stop(status="failed")
            raise AgentRuntimeError(err_msg)

        plan = {}
        use_gemini = is_gemini_configured()
        
        if not use_gemini:
            err_msg = "Gemini API key is not configured in the environment. Real-only execution requires Gemini API access."
            self.trace.log("Agent Runtime", "ERROR", err_msg)
            self.trace.stop(status="failed")
            raise AgentRuntimeError(err_msg)

        self.trace.log("Agent Runtime", "INFO", "Gemini client configured. Beginning multi-step skill composition...")
        try:
            # 3. Goal Analysis Step
            self.trace.add_skill("goal-analysis")
            analysis_skill = discovered["goal-analysis"]
            self.trace.log("Goal Analysis", "INFO", "Invoking Gemini for Goal Analysis...")
            
            analysis_prompt = f"""
            Goal: {cleaned_goal}
            Deadline: {deadline}
            Availability: {availability}
            Preferred Sessions: {sessions_pref}

            Follow the instructions:
            {analysis_skill.instructions}

            Output your response strictly as a JSON object with this format:
            {{
              "category": "study" | "learning" | "building" | "general",
              "complexity": "low" | "medium" | "high"
            }}
            """
            
            analysis_res_text = call_gemini(analysis_prompt, system_instruction=analysis_skill.description)
            analysis_data = extract_json(analysis_res_text)
            category = analysis_data.get("category", "general")
            complexity = analysis_data.get("complexity", "medium")
            self.trace.log("Goal Analysis", "INFO", f"Analysis completed. Category: {category}, Complexity: {complexity}")

            # 4. Milestone Generation Step
            self.trace.add_skill("milestone-generator")
            milestone_skill = discovered["milestone-generator"]
            self.trace.log("Milestone Generation", "INFO", "Invoking Gemini for Milestone Generation...")
            
            milestone_prompt = f"""
            Goal: {cleaned_goal}
            Category: {category}
            Complexity: {complexity}

            Follow the instructions:
            {milestone_skill.instructions}

            Generate 3 to 5 high-level milestones representing chronological progress.
            Output your response strictly as a JSON object with this format:
            {{
              "milestones": ["Milestone 1 description", "Milestone 2 description", ...]
            }}
            """
            
            milestone_res_text = call_gemini(milestone_prompt, system_instruction=milestone_skill.description)
            milestone_data = extract_json(milestone_res_text)
            milestones = milestone_data.get("milestones", [])
            self.trace.log("Milestone Generation", "INFO", f"Milestones generated. Count: {len(milestones)}")

            # 5. Task Planning Step
            self.trace.add_skill("task-planner")
            task_skill = discovered["task-planner"]
            self.trace.log("Task Planning", "INFO", "Invoking Gemini for Task Planning...")
            
            task_prompt = f"""
            Goal: {cleaned_goal}
            Milestones: {json.dumps(milestones)}

            Follow the instructions:
            {task_skill.instructions}

            Create actionable prioritized weekly tasks mapping directly to these milestones.
            Output your response strictly as a JSON object with this format:
            {{
              "tasks": ["Task 1 description", "Task 2 description", ...]
            }}
            """
            
            task_res_text = call_gemini(task_prompt, system_instruction=task_skill.description)
            task_data = extract_json(task_res_text)
            tasks = task_data.get("tasks", [])
            self.trace.log("Task Planning", "INFO", f"Tasks planned. Count: {len(tasks)}")

            # 6. Session Scheduling Step
            self.trace.add_skill("session-scheduler")
            self.trace.log("Session Scheduling", "INFO", "Invoking scheduler engine for Session Scheduling...")
            sessions = generate_schedule(tasks, availability, sessions_pref, deadline)
            self.trace.log("Session Scheduling", "INFO", f"Sessions scheduled. Count: {len(sessions)}")

            # 7. Timeline Estimation Step
            self.trace.add_skill("timeline-estimator")
            timeline_skill = discovered["timeline-estimator"]
            self.trace.log("Timeline Estimation", "INFO", "Invoking Gemini for Timeline Estimation...")
            
            timeline_prompt = f"""
            Goal: {cleaned_goal}
            Milestones: {json.dumps(milestones)}
            Availability: {availability}
            Deadline: {deadline}

            Follow the instructions:
            {timeline_skill.instructions}

            Estimate the overall timeframe and pacing.
            Output your response strictly as a JSON object with this format:
            {{
              "timeline": "estimated duration (e.g. 4 weeks)"
            }}
            """
            
            timeline_res_text = call_gemini(timeline_prompt, system_instruction=timeline_skill.description)
            timeline_data = extract_json(timeline_res_text)
            timeline = timeline_data.get("timeline", "4 weeks")
            self.trace.log("Timeline Estimation", "INFO", f"Timeline estimated: {timeline}")

            plan = {
                "goal": cleaned_goal,
                "milestones": milestones,
                "tasks": tasks,
                "sessions": sessions,
                "timeline": timeline
            }

        except Exception as e:
            err_msg = f"Gemini execution failed: {str(e)}"
            self.trace.log("Agent Runtime", "ERROR", err_msg)
            self.trace.stop(status="failed")
            raise AgentRuntimeError(err_msg)

        # 8. Plan Evaluation Step
        self.trace.add_skill("evaluation")
        eval_skill = discovered["evaluation"]
        self.trace.log("Evaluation", "INFO", "Evaluating final plan structure and content safety...")
        
        eval_results = self.evaluator.evaluate_plan(plan)
        self.trace.set_evaluation_score(eval_results["evaluation_score"])
        
        if not eval_results["is_valid"]:
            err_msg = f"Generated plan failed evaluation: {', '.join(eval_results['error_messages'])}"
            self.trace.log("Evaluation", "ERROR", err_msg)
            self.trace.stop(status="failed")
            raise AgentRuntimeError(err_msg)
            
        self.trace.log("Evaluation", "INFO", "Final plan validation checks passed successfully.")

        # 9. MCP Execution Layer
        self.trace.log("MCP Execution", "INFO", "Triggering local simulated MCP execution layer...")
        self._execute_mcp_ops(plan)
        
        self.trace.stop(status="success")
        
        return {
            "plan": plan,
            "trace": self.trace.to_dict()
        }

    def _execute_mcp_ops(self, plan: dict):
        """
        Executes real Google Calendar MCP operations.
        """
        # Monday, Jun 22, 2026 is our reference date for scheduling offsets
        base_date = datetime(2026, 6, 22, tzinfo=timezone.utc)
        day_offsets = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        real_events_to_create = []
        for s in plan.get("sessions", []):
            title = f"Study Block: {s['task']}"
            day = s["day"].lower()
            week = s["week"]
            time_range = s["time"]
            
            # Map day name to a specific ISO timestamp
            offset = day_offsets.get(day, 0)
            target_day = base_date + timedelta(days=(week - 1) * 7 + offset)
            
            # Parse times like 20:00-21:30
            start_iso = target_day.strftime("%Y-%m-%dT19:00:00Z")
            end_iso = target_day.strftime("%Y-%m-%dT20:30:00Z")
            
            time_match = re.match(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", time_range)
            if time_match:
                sh, sm, eh, em = map(int, time_match.groups())
                start_dt = target_day.replace(hour=sh, minute=sm, second=0)
                end_dt = target_day.replace(hour=eh, minute=em, second=0)
                if end_dt <= start_dt:
                    end_dt = end_dt + timedelta(days=1)
                start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                
            real_events_to_create.append({
                "title": title,
                "start_time": start_iso,
                "end_time": end_iso,
                "description": f"Automated study session for {plan['goal']}"
            })

        if real_events_to_create:
            from services.mcp_real import create_real_events
            self.trace.log("MCP Execution", "INFO", f"[Real MCP] Syncing {len(real_events_to_create)} calendar events in batch...")
            try:
                results = create_real_events(real_events_to_create)
                for res in results:
                    self.trace.add_mcp_operation(
                        op_type="create_event (Real)",
                        title=res["title"],
                        status=res["status"]
                    )
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self.trace.log("MCP Execution", "ERROR", f"[Real MCP] Batch sync failed: {str(e)}\n{tb}")
                for ev in real_events_to_create:
                    self.trace.add_mcp_operation(
                        op_type="create_event (Real)",
                        title=ev["title"],
                        status=f"failed: {str(e)}"
                    )
