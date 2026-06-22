import os
import uuid
import time
import json
from datetime import datetime, timezone

class ExecutionTrace:
    def __init__(self):
        self.execution_id = str(uuid.uuid4())
        self.skill_sequence = []
        self.start_time = 0.0
        self.duration_ms = 0
        self.status = "in_progress"
        self.evaluation_score = 0
        self.mcp_operations = []
        self.logs = []

    def start(self):
        self.start_time = time.time()
        self.log("Agent Runtime", "INFO", f"Execution trace initialized with ID {self.execution_id}.")

    def add_skill(self, skill_name: str):
        self.skill_sequence.append(skill_name)
        self.log("Skill Selection", "INFO", f"Loaded and selected composable skill: {skill_name}")

    def log(self, step: str, level: str, message: str):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)
        
        # Write to structured log file
        os.makedirs("logs", exist_ok=True)
        log_line = f"[{timestamp}] [{step}] [{level}] {message}\n"
        with open(os.path.join("logs", "runtime.log"), "a", encoding="utf-8") as f:
            f.write(log_line)

    def add_mcp_operation(self, op_type: str, title: str, status: str = "success"):
        self.mcp_operations.append({
            "type": op_type,
            "title": title,
            "status": status
        })
        self.log("MCP Execution", "INFO", f"Executed real MCP operation: {op_type} for '{title}'. Status: {status}")

    def set_evaluation_score(self, score: int):
        self.evaluation_score = score
        self.log("Evaluation", "INFO", f"Assigned runtime evaluation score: {score}/100")

    def stop(self, status: str = "success"):
        self.status = status
        self.duration_ms = int((time.time() - self.start_time) * 1000)
        self.log("Agent Runtime", "INFO", f"Execution pipeline completed. Status: {status}. Total duration: {self.duration_ms}ms.")
        self.save()

    def save(self):
        os.makedirs("logs", exist_ok=True)
        trace_data = {
            "execution_id": self.execution_id,
            "skill_sequence": self.skill_sequence,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "evaluation_score": self.evaluation_score,
            "mcp_operations": self.mcp_operations,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "logs": self.logs
        }
        filepath = os.path.join("logs", f"trace_{self.execution_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace_data, f, indent=2)
            
    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "skill_sequence": self.skill_sequence,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "evaluation_score": self.evaluation_score,
            "mcp_operations": self.mcp_operations,
            "logs": self.logs
        }
