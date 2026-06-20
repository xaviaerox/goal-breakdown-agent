\# Goal Breakdown Agent



\## Objective



Transform user goals into actionable plans.



\## User



Students, professionals and personal development enthusiasts.



\## Input



A goal written in natural language.



\## Output



A structured action plan divided into milestones and tasks.



\## Guardrails



\* Never execute code.

\* Never browse external systems.

\* Reject empty goals.

\* Reject goals longer than 1000 characters.



\## Scenarios



\### Scenario 1



Given a user wants to pass Azure Fundamentals



When the goal is submitted



Then the system generates a study plan



\### Scenario 2



Given a user wants to learn Python



When the goal is submitted



Then the system generates a learning roadmap



\### Scenario 3



Given the goal is empty



When submitted



Then an error message is returned



