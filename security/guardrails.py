import re
import os
from datetime import datetime, timezone

class GuardrailError(Exception):
    pass

def log_rejected_request(reason: str, goal: str):
    """
    Logs rejected requests to logs/rejected_requests.log for audit and visibility.
    """
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_line = f"[{timestamp}] [REJECTED] Reason: {reason} | Input: {repr(goal)}\n"
    with open(os.path.join("logs", "rejected_requests.log"), "a", encoding="utf-8") as f:
        f.write(log_line)

def check_guardrails(goal: str) -> str:
    """
    Validates goal input against security guardrails:
    - Empty check
    - Maximum length check (1000 chars)
    - Prompt injection detection
    - Harmful keyword validation
    """
    if not goal:
        reason = "Goal cannot be empty."
        log_rejected_request(reason, "")
        raise GuardrailError(reason)

    cleaned = goal.strip()
    if not cleaned:
        reason = "Goal cannot be empty (whitespace only)."
        log_rejected_request(reason, goal)
        raise GuardrailError(reason)

    if len(cleaned) > 1000:
        reason = f"Goal cannot exceed 1000 characters (Length: {len(cleaned)})."
        log_rejected_request(reason, cleaned)
        raise GuardrailError(reason)

    # Prompt injection patterns
    injection_patterns = [
        r"ignore\s+.*instructions?",
        r"system\s+prompts?",
        r"you\s+are\s+now\s+a\s+\w+",
        r"override\s+instructions?",
        r"developer\s+mode",
        r"bypass\s+restrictions?",
        r"delete\s+all\s+files",
        r"acting\s+as\s+a\s+\w+"
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            reason = "Potential prompt injection attack detected."
            log_rejected_request(reason, cleaned)
            raise GuardrailError(reason)

    # Harmful instructions
    harmful_keywords = [
        "malware", "hack ", "hacker", "cyberattack", "exploit", "ddos",
        "bomb", "weapon", "kill ", "suicide", "illegal", "pirate", 
        "crack software", "ransomware", "trojan", "virus"
    ]
    
    cleaned_lower = cleaned.lower()
    for kw in harmful_keywords:
        if kw in cleaned_lower:
            reason = f"Harmful or unauthorized content detected (Keyword: '{kw}')."
            log_rejected_request(reason, cleaned)
            raise GuardrailError(reason)

    return cleaned
