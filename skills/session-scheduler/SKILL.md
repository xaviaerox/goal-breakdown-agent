---
name: session-scheduler
trigger: "Schedule specific time blocks and sessions based on user availability windows and target completion deadline"
description: |
  Allocates the list of planned tasks into the user's weekly availability windows
  and preferred sessions, outputting a structured timetable of study or work blocks.
---

# Session Scheduler Skill

Given the tasks, availability windows, and preferred session times:
1. Map tasks to specific weekdays and hours matching availability.
2. Group sessions chronologically (e.g., Week 1, Week 2).
3. Ensure the schedule fits the availability constraints.
4. Output a list of session allocations (each containing day, time range, and focus task).
