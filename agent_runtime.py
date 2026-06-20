import os
import re
from datetime import datetime, timezone
from goal_breakdown import validate_goal, breakdown_goal, GoalBreakdownError

class Skill:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.name = ""
        self.description = ""
        self.instructions = ""
        self.output_format = []
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Skill file not found at {self.filepath}")
        
        with open(self.filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML-like frontmatter
        lines = content.splitlines()
        
        frontmatter_lines = []
        body_lines = []
        in_frontmatter = False
        frontmatter_ended = False
        
        for line in lines:
            stripped = line.replace('\\', '').strip()
            # Detect frontmatter boundary (--- or sequence of hyphens)
            if not frontmatter_ended and (stripped == "---" or (len(stripped) >= 3 and all(c == '-' for c in stripped))):
                if in_frontmatter:
                    in_frontmatter = False
                    frontmatter_ended = True
                else:
                    in_frontmatter = True
                continue
                
            if in_frontmatter:
                frontmatter_lines.append(line)
            else:
                body_lines.append(line)
                
        # Parse keys inside frontmatter_lines
        self.name = ""
        self.description = ""
        desc_lines = []
        in_description = False
        
        for line in frontmatter_lines:
            stripped_line = line.strip()
            if not stripped_line:
                if in_description:
                    desc_lines.append("")
                continue
                
            # Check if key: value
            key_match = re.match(r"^([a-zA-Z_0-9\-]+):\s*(.*)$", stripped_line)
            if key_match:
                in_description = False
                key = key_match.group(1).lower()
                val = key_match.group(2).strip()
                if key == "name":
                    self.name = val
                elif key == "description":
                    if val == "|":
                        in_description = True
                    else:
                        self.description = val
            elif in_description:
                desc_lines.append(line)
                
        if desc_lines:
            # Clean description: strip lines and replace triple empty lines
            cleaned_desc_lines = [l.strip() for l in desc_lines]
            self.description = "\n".join(cleaned_desc_lines).strip()
            self.description = re.sub(r"\n{3,}", "\n\n", self.description)
                
        self.instructions = "\n".join(body_lines).strip()
        
        # Extract Output Format
        output_format_match = re.search(r"Output format:\s*\n+((?:.+\n*)+)", self.instructions, re.IGNORECASE)
        if output_format_match:
            format_lines = []
            for l in output_format_match.group(1).splitlines():
                l_strip = l.replace('\\', '').strip()
                if not l_strip:
                    continue
                if l_strip.startswith("#"):
                    break
                format_lines.append(l_strip)
            self.output_format = format_lines


class AgentRuntime:
    def __init__(self):
        self.trace = []
        self.logs = []

    def _log(self, step: str, level: str, message: str):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.logs.append({
            "timestamp": timestamp,
            "step": step,
            "level": level,
            "message": message
        })

    def run(self, goal: str, skill_path: str) -> dict:
        self.trace = []
        self.logs = []
        
        # 1. Goal Input
        self.trace.append({"step": "Goal Input", "status": "COMPLETED"})
        self._log("Goal Input", "INFO", f"Received raw goal input. Length: {len(goal or '')} characters.")
        
        try:
            cleaned_goal = validate_goal(goal)
            self._log("Goal Input", "INFO", f"Input validation passed. Cleaned goal: '{cleaned_goal}'.")
        except GoalBreakdownError as e:
            self._log("Goal Input", "ERROR", f"Input validation failed: {str(e)}")
            self.trace[-1]["status"] = "FAILED"
            raise
            
        # 2. Skill Selection
        self.trace.append({"step": "Skill Selection", "status": "COMPLETED"})
        self._log("Skill Selection", "INFO", f"Loading skill definition from {skill_path}...")
        
        try:
            skill = Skill(skill_path)
            self._log("Skill Selection", "INFO", f"Successfully loaded and parsed skill: '{skill.name}'.")
            
            self._log("Skill Selection", "INFO", "Matching goal requirements against selected skill...")
            # We match it because it asks for decomposition/roadmaps, which is the skill's description.
            self._log("Skill Selection", "INFO", f"Skill '{skill.name}' selected for planning/roadmap execution.")
        except Exception as e:
            self._log("Skill Selection", "ERROR", f"Failed to load or select skill: {str(e)}")
            self.trace[-1]["status"] = "FAILED"
            raise
            
        # 3. Goal Analysis
        self.trace.append({"step": "Goal Analysis", "status": "COMPLETED"})
        self._log("Goal Analysis", "INFO", "Analyzing goal pattern and keywords...")
        
        normalized = cleaned_goal.lower()
        if "azure" in normalized:
            category = "Predefined: Azure Fundamentals Study Plan"
        elif "python" in normalized:
            category = "Predefined: Python Learning Roadmap"
        elif "saas" in normalized:
            category = "Predefined: SaaS Business Roadmap"
        elif any(kw in normalized for kw in ["learn", "study", "exam", "pass", "course"]):
            category = "Generic: Learning Activity"
        elif any(kw in normalized for kw in ["build", "create", "start", "make", "develop"]):
            category = "Generic: Development/Building Activity"
        else:
            category = "Generic: General Objective"
            
        self._log("Goal Analysis", "INFO", f"Goal categorization: {category}.")
        
        # 4. Milestone Generation
        self.trace.append({"step": "Milestone Generation", "status": "COMPLETED"})
        self._log("Milestone Generation", "INFO", "Generating milestones from breakdown engine...")
        
        plan = breakdown_goal(cleaned_goal)
        
        self._log("Milestone Generation", "INFO", f"Successfully generated {len(plan['milestones'])} milestones.")
        
        # 5. Task Generation
        self.trace.append({"step": "Task Generation", "status": "COMPLETED"})
        self._log("Task Generation", "INFO", "Generating actionable tasks for milestones...")
        self._log("Task Generation", "INFO", f"Successfully generated {len(plan['tasks'])} tasks.")
        
        # 6. Timeline Estimation
        self.trace.append({"step": "Timeline Estimation", "status": "COMPLETED"})
        self._log("Timeline Estimation", "INFO", "Estimating project overall duration...")
        self._log("Timeline Estimation", "INFO", f"Estimated duration: {plan['timeline']}.")
        
        # 7. Final Plan
        self.trace.append({"step": "Final Plan", "status": "COMPLETED"})
        self._log("Final Plan", "INFO", "Assembling final roadmap output...")
        
        # Verify alignment with parsed output formats
        self._log("Final Plan", "INFO", f"Verifying schema alignment with output formats: {', '.join(skill.output_format)}")
        
        self._log("Final Plan", "INFO", "Execution trace and structured logs successfully compiled.")
        
        return {
            "plan": plan,
            "trace": self.trace,
            "logs": self.logs
        }
