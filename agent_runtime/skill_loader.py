import os
import re

class Skill:
    def __init__(self, directory: str):
        self.directory = directory
        self.filepath = os.path.join(directory, "SKILL.md")
        self.name = ""
        self.description = ""
        self.trigger = ""
        self.instructions = ""
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"SKILL.md not found in {self.directory}")
            
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
        self.trigger = ""
        desc_lines = []
        in_description = False
        
        for line in frontmatter_lines:
            stripped_line = line.strip()
            if not stripped_line:
                if in_description:
                    desc_lines.append("")
                continue
                
            key_match = re.match(r"^([a-zA-Z_0-9\-]+):\s*(.*)$", stripped_line)
            if key_match:
                in_description = False
                key = key_match.group(1).lower()
                val = key_match.group(2).strip()
                if key == "name":
                    self.name = val
                elif key == "trigger":
                    self.trigger = val
                elif key == "description":
                    if val == "|":
                        in_description = True
                    else:
                        self.description = val
            elif in_description:
                desc_lines.append(line)
                
        if desc_lines:
            cleaned_desc_lines = [l.strip() for l in desc_lines]
            self.description = "\n".join(cleaned_desc_lines).strip()
            self.description = re.sub(r"\n{3,}", "\n\n", self.description)
                
        self.instructions = "\n".join(body_lines).strip()


def discover_skills(skills_dir: str) -> dict:
    """
    Scans the skills directory for subdirectories containing SKILL.md.
    Returns a dictionary of {skill_name: Skill} mappings.
    """
    skills = {}
    if not os.path.exists(skills_dir):
        return skills
        
    for entry in os.listdir(skills_dir):
        entry_path = os.path.join(skills_dir, entry)
        if os.path.isdir(entry_path):
            skill_file = os.path.join(entry_path, "SKILL.md")
            if os.path.exists(skill_file):
                try:
                    skill = Skill(entry_path)
                    if skill.name:
                        skills[skill.name] = skill
                except Exception:
                    pass
    return skills
