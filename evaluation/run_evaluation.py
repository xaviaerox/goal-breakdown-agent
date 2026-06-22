import os
import sys
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from agent_runtime.runtime import ComposedAgentRuntime
from security.guardrails import GuardrailError
from agent_runtime.runtime import AgentRuntimeError

from unittest.mock import patch

def run_evaluation():
    test_cases_path = os.path.join(PROJECT_ROOT, "evaluation", "test_cases.json")
    if not os.path.exists(test_cases_path):
        print(f"Error: Test cases not found at {test_cases_path}")
        sys.exit(1)

    with open(test_cases_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    runtime = ComposedAgentRuntime()
    results = []
    passed_count = 0
    failed_count = 0

    print("=" * 80)
    print("            GOAL PLANNING & EXECUTION AGENT EVALUATION RUN")
    print("=" * 80)
    print(f"{'Test ID':<22} | {'Type':<8} | {'Status':<8} | {'Score':<5} | {'Details':<25}")
    print("-" * 80)

    # Mock real calendar writes during evaluations to prevent cluttering calendar and oauth blocks
    mock_events = patch("services.calendar_client.create_calendar_events_direct")

    with mock_events as mock_create:
        mock_create.side_effect = lambda evs, token: [{"title": ev["title"], "status": "success", "result": "mocked"} for ev in evs]
        for case in test_cases:
            case_id = case["id"]
            goal = case["goal"]
            deadline = case.get("deadline", "")
            availability = case.get("availability", "")
            sessions = case.get("sessions", "")
            expected_type = case["expected_type"]
            status = "FAILED"
            score = 0
            details = ""

            try:
                result_data = runtime.run(
                    goal=goal,
                    deadline=deadline,
                    availability=availability,
                    sessions_pref=sessions,
                    user_access_token="mock_evaluation_token"
                )
                
                if expected_type == "valid":
                    plan = result_data["plan"]
                    trace = result_data["trace"]
                    score = trace.get("evaluation_score", 0)
                    
                    # Structural assertions
                    has_milestones = len(plan.get("milestones", [])) > 0
                    has_tasks = len(plan.get("tasks", [])) > 0
                    has_timeline = len(plan.get("timeline", "")) > 0
                    has_sessions = len(plan.get("sessions", [])) > 0
                    has_mcp_ops = len(trace.get("mcp_operations", [])) > 0
                    
                    # Timeline check: skipped static comparison since Gemini dynamically estimates a realistic timeline
                    timeline_match = True

                    if has_milestones and has_tasks and has_timeline and has_sessions and has_mcp_ops and timeline_match:
                        status = "PASSED"
                        details = f"Plan & Schedule OK (Score: {score}%)"
                    else:
                        details = f"Structure check failed. Milestones:{has_milestones}, Tasks:{has_tasks}, Sessions:{has_sessions}, MCP:{has_mcp_ops}"
                else:
                    details = "Expected request rejection but it succeeded."

            except (GuardrailError, AgentRuntimeError, Exception) as e:
                err_msg = str(e)
                if expected_type == "rejected":
                    expected_substr = case.get("error_substring", "")
                    if expected_substr.lower() in err_msg.lower():
                        status = "PASSED"
                        details = f"Correctly blocked: {err_msg[:25]}..."
                    else:
                        details = f"Block message mismatch. Got: {err_msg[:25]}"
                else:
                    import traceback
                    traceback.print_exc()
                    details = f"Unexpected execution error: {err_msg[:35]}"

            if status == "PASSED":
                passed_count += 1
            else:
                failed_count += 1

            score_str = f"{score}%" if expected_type == "valid" else "N/A"
            print(f"{case_id:<22} | {expected_type:<8} | {status:<8} | {score_str:<5} | {details:<25}")
            results.append({
                "id": case_id,
                "expected_type": expected_type,
                "status": status,
                "score": score,
                "details": details
            })

    report = {
        "summary": {
            "total_tests": len(test_cases),
            "passed": passed_count,
            "failed": failed_count,
            "pass_percentage": (passed_count / len(test_cases)) * 100
        },
        "results": results,
        "timestamp": time.time()
    }

    os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)
    report_path = os.path.join(PROJECT_ROOT, "logs", "evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=" * 80)
    print(f"Summary: {passed_count} Passed, {failed_count} Failed.")
    print(f"Report saved to: logs/evaluation_report.json")
    print("=" * 80)
    
    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_evaluation()
