---
name: goal-analysis
trigger: "Analyze raw goal input, target deadline, availability, and session preferences to extract constraints and complexity"
description: |
  Analyzes user goal inputs alongside timeline parameters (deadline, availability, sessions)
  to identify task category, estimated difficulty, and time constraints.
---

# Goal Analysis Skill

When a goal is received:
1. Normalize and clean the input text.
2. Determine category (Azure study, Python learning, SaaS project, etc.).
3. Extract date constraints (deadline) and weekly availability details.
4. Assess complexity (low, medium, high) based on goal scope and available hours.
5. Return structured analysis.
