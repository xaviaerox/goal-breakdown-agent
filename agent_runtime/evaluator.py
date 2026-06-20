class RuntimeEvaluator:
    def __init__(self):
        pass

    def evaluate_plan(self, plan: dict) -> dict:
        """
        Validates the generated plan structure:
        - Checks for the presence and validity of goal, milestones, tasks, timeline, and sessions.
        Returns a dict with verification results and an evaluation score out of 100.
        """
        results = {
            "is_valid": True,
            "checks": {
                "goal_present": False,
                "milestones_present": False,
                "tasks_present": False,
                "timeline_present": False,
                "sessions_present": False
            },
            "error_messages": [],
            "evaluation_score": 0
        }

        # 1. Goal Check
        goal = plan.get("goal", "")
        if goal and isinstance(goal, str) and len(goal.strip()) > 0:
            results["checks"]["goal_present"] = True
        else:
            results["is_valid"] = False
            results["error_messages"].append("Missing or empty 'goal' field.")

        # 2. Milestones Check
        milestones = plan.get("milestones", [])
        if milestones and isinstance(milestones, list) and len(milestones) > 0:
            if all(isinstance(m, str) and len(m.strip()) > 0 for m in milestones):
                results["checks"]["milestones_present"] = True
            else:
                results["is_valid"] = False
                results["error_messages"].append("Milestones list contains empty or invalid strings.")
        else:
            results["is_valid"] = False
            results["error_messages"].append("Missing or empty 'milestones' field.")

        # 3. Tasks Check
        tasks = plan.get("tasks", [])
        if tasks and isinstance(tasks, list) and len(tasks) > 0:
            if all(isinstance(t, str) and len(t.strip()) > 0 for t in tasks):
                results["checks"]["tasks_present"] = True
            else:
                results["is_valid"] = False
                results["error_messages"].append("Tasks list contains empty or invalid strings.")
        else:
            results["is_valid"] = False
            results["error_messages"].append("Missing or empty 'tasks' field.")

        # 4. Timeline Check
        timeline = plan.get("timeline", "")
        if timeline and isinstance(timeline, str) and len(timeline.strip()) > 0:
            results["checks"]["timeline_present"] = True
        else:
            results["is_valid"] = False
            results["error_messages"].append("Missing or empty 'timeline' field.")

        # 5. Sessions Check
        sessions = plan.get("sessions", [])
        if sessions and isinstance(sessions, list) and len(sessions) > 0:
            valid_sessions = True
            for s in sessions:
                if not isinstance(s, dict) or not all(k in s for k in ["week", "day", "time", "task"]):
                    valid_sessions = False
                    break
            if valid_sessions:
                results["checks"]["sessions_present"] = True
            else:
                results["is_valid"] = False
                results["error_messages"].append("Sessions list contains malformed session dictionaries.")
        else:
            results["is_valid"] = False
            results["error_messages"].append("Missing or empty 'sessions' field.")

        # Calculate final evaluation score (percentage of checks passed)
        passed_checks = sum(1 for val in results["checks"].values() if val)
        total_checks = len(results["checks"])
        results["evaluation_score"] = int((passed_checks / total_checks) * 100)

        # The plan is still considered valid for output if we have at least milestones, tasks and timeline,
        # but is_valid determines overall schema strictness.
        return results
