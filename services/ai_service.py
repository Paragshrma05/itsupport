import os
import json
import re
import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"


def _call_claude(prompt: str, max_tokens: int = 600) -> str:
    """Make a call to Claude API and return text response."""
    if not ANTHROPIC_API_KEY:
        return None

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"].strip()
    except Exception:
        return None


def categorize_ticket(title: str, description: str) -> dict:
    """Use AI to detect category and priority, and suggest fixes."""
    prompt = f"""You are an IT support AI. Analyze this support ticket and respond ONLY with valid JSON.

Ticket Title: {title}
Description: {description}

Return EXACTLY this JSON structure (no extra text):
{{
  "category": "one of: Hardware, Software, Network, Security, Database, Authentication, Performance, Other",
  "priority": "one of: Low, Medium, High, Critical",
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}

Base priority on urgency/impact. Suggestions should be actionable troubleshooting steps."""

    raw = _call_claude(prompt, 400)
    if not raw:
        return _fallback_categorize(title, description)

    try:
        # Strip markdown code fences if present
        clean = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(clean)
        # Validate fields
        valid_categories = ["Hardware", "Software", "Network", "Security", "Database", "Authentication", "Performance", "Other"]
        valid_priorities = ["Low", "Medium", "High", "Critical"]
        result["category"] = result.get("category", "Other") if result.get("category") in valid_categories else "Other"
        result["priority"] = result.get("priority", "Medium") if result.get("priority") in valid_priorities else "Medium"
        if not isinstance(result.get("suggestions"), list):
            result["suggestions"] = ["Review system logs for errors.", "Restart the affected service.", "Contact your system administrator."]
        return result
    except Exception:
        return _fallback_categorize(title, description)


def _fallback_categorize(title: str, description: str) -> dict:
    """Rule-based fallback when AI is unavailable."""
    text = (title + " " + description).lower()
    category = "Other"
    priority = "Medium"

    if any(w in text for w in ["password", "login", "auth", "access denied", "locked"]):
        category = "Authentication"
    elif any(w in text for w in ["network", "internet", "wifi", "vpn", "connection", "ping"]):
        category = "Network"
    elif any(w in text for w in ["database", "db", "sql", "query", "connection pool"]):
        category = "Database"
    elif any(w in text for w in ["crash", "blue screen", "bsod", "hardware", "disk", "ram", "cpu"]):
        category = "Hardware"
    elif any(w in text for w in ["slow", "performance", "lag", "timeout", "memory"]):
        category = "Performance"
    elif any(w in text for w in ["virus", "malware", "hack", "breach", "security"]):
        category = "Security"
    elif any(w in text for w in ["install", "software", "app", "update", "error", "bug"]):
        category = "Software"

    if any(w in text for w in ["critical", "urgent", "down", "breach", "cannot work", "production"]):
        priority = "Critical"
    elif any(w in text for w in ["high", "important", "asap", "blocked"]):
        priority = "High"
    elif any(w in text for w in ["low", "minor", "when possible", "question"]):
        priority = "Low"

    suggestions_map = {
        "Authentication": ["Reset your password via the account portal.", "Clear browser cookies and cache.", "Contact admin to verify account status."],
        "Network": ["Run ping/traceroute to diagnose connectivity.", "Restart your router/switch.", "Check firewall rules and VPN configuration."],
        "Database": ["Check DB connection pool settings.", "Review slow query logs.", "Verify DB server health and disk space."],
        "Hardware": ["Run hardware diagnostics tool.", "Check device manager for driver errors.", "Verify physical connections and power supply."],
        "Performance": ["Check CPU and memory utilization.", "Review running processes for resource hogs.", "Consider increasing allocated resources."],
        "Security": ["Isolate the affected system immediately.", "Run a full antivirus/malware scan.", "Change all potentially compromised credentials."],
        "Software": ["Restart the application and check logs.", "Reinstall or update the software.", "Check for known bugs in the release notes."],
        "Other": ["Document the exact error message.", "Check system event logs.", "Escalate to your IT administrator."],
    }
    return {"category": category, "priority": priority, "suggestions": suggestions_map.get(category, suggestions_map["Other"])}


def analyze_log(log_text: str) -> dict:
    """Analyze a log file for common IT issues."""
    prompt = f"""You are an IT log analysis expert. Analyze this log and respond ONLY with valid JSON.

LOG CONTENT:
{log_text[:3000]}

Return EXACTLY this JSON (no extra text):
{{
  "summary": "2-3 sentence overview of what the log shows",
  "issues": [
    {{"type": "issue type", "severity": "High/Medium/Low", "count": 0, "detail": "specific finding"}}
  ],
  "recommendations": ["action 1", "action 2", "action 3"],
  "health_score": 75
}}

Check for: authentication failures, timeouts, API errors, DB connection issues, crashes, memory errors."""

    raw = _call_claude(prompt, 800)
    if not raw:
        return _fallback_log_analysis(log_text)

    try:
        clean = re.sub(r"```json|```", "", raw).strip()
        return json.loads(clean)
    except Exception:
        return _fallback_log_analysis(log_text)


def _fallback_log_analysis(log_text: str) -> dict:
    """Rule-based log analysis fallback."""
    text = log_text.lower()
    issues = []

    patterns = [
        (["authentication failed", "login failed", "invalid credentials", "auth error"], "Authentication Failures", "High"),
        (["timeout", "timed out", "connection timeout", "read timeout"], "Timeout Errors", "Medium"),
        (["api error", "api failure", "http 5", "503", "502", "500 error"], "API Failures", "High"),
        (["database connection", "db connection", "connection refused", "could not connect to"], "DB Connection Issues", "Critical"),
        (["out of memory", "memory error", "heap space"], "Memory Issues", "Critical"),
        (["exception", "error", "traceback", "fatal"], "Application Errors", "Medium"),
    ]

    for keywords, issue_type, severity in patterns:
        count = sum(text.count(kw) for kw in keywords)
        if count > 0:
            issues.append({"type": issue_type, "severity": severity, "count": count, "detail": f"Found {count} occurrence(s) in log."})

    health_score = max(10, 100 - (len(issues) * 15) - sum(1 for i in issues if i["severity"] == "Critical") * 10)

    return {
        "summary": f"Log analysis complete. Found {len(issues)} issue type(s) requiring attention." if issues else "No critical issues detected in the log.",
        "issues": issues if issues else [{"type": "No Issues", "severity": "Low", "count": 0, "detail": "Log appears clean."}],
        "recommendations": [
            "Review all ERROR and CRITICAL log entries.",
            "Set up automated alerting for critical patterns.",
            "Schedule regular log rotation and archiving.",
        ],
        "health_score": health_score,
    }
