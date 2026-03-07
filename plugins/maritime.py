"""
maritime.py - Maritime Assistant Plugin
Reports + Troubleshooting for LPG vessel ETO
"""

import os
from datetime import datetime

DESCRIPTION = "Maritime reports and ship equipment troubleshooting"
COMMANDS    = ["report", "fix", "troubleshoot", "diagnose", "show reports"]

LOG_DIR = os.path.expanduser("~/Jarvis/jarvis_logs")
os.makedirs(LOG_DIR, exist_ok=True)

REPORT_TYPES = {
    "daily"    : "Daily Maintenance Report",
    "defect"   : "Defect and Repair Report",
    "handover" : "Watch Handover Report",
    "incident" : "Incident / Near-Miss Report",
    "stores"   : "Stores and Spares Consumption Report",
    "rounds"   : "Engine Room Rounds Report",
}

def generate_report(report_type: str, notes: str) -> str:
    from brain import ask_ai
    report_name = REPORT_TYPES.get(report_type.lower(), "Technical Report")
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = f"""Write a professional {report_name} for an LPG vessel.
Date/Time: {timestamp}
Department: Electrical / ETO

Rough notes from ETO:
{notes}

Format with sections:
1. REPORT TYPE & DATE
2. EQUIPMENT / SYSTEM
3. OBSERVATION / DEFECT
4. ACTION TAKEN
5. CURRENT STATUS
6. RECOMMENDATIONS

Use proper maritime technical language.
ISM code compliant format."""
    print(f"\n📝 Generating {report_name}...")
    result = ask_ai(prompt)
    _save_report(report_name, result)
    return result

def _save_report(report_name: str, content: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"{report_name.replace(' ','_')}_{timestamp}.txt"
    filepath  = os.path.join(LOG_DIR, filename)
    try:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"💾 Saved: {filepath}")
    except Exception as e:
        print(f"⚠️ Save error: {e}")

def troubleshoot(problem: str) -> str:
    from brain import ask_ai
    prompt = f"""I am an ETO on an LPG vessel. Equipment problem:

PROBLEM: {problem}

Provide:
1. MOST LIKELY CAUSES (ranked by probability)
2. STEP BY STEP DIAGNOSTIC PROCEDURE
3. TOOLS / EQUIPMENT NEEDED
4. SAFETY PRECAUTIONS
5. WHEN TO ESCALATE TO SUPERINTENDENT

Specific to LPG vessel electrical and automation systems.
Always prioritize safety.
Never suggest bypassing safety systems."""
    print(f"\n🔧 Analyzing problem...")
    return ask_ai(prompt)

def add_log(entry: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    today     = datetime.now().strftime("%Y-%m-%d")
    log_file  = os.path.join(LOG_DIR, f"daily_log_{today}.txt")
    try:
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {entry}\n")
        return f"✅ Logged: {entry}"
    except Exception as e:
        return f"❌ Log error: {e}"

def show_log() -> str:
    today    = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"daily_log_{today}.txt")
    if not os.path.exists(log_file):
        return "📋 No log entries today yet."
    result = f"\n📋 Today's Log — {today}\n\n"
    with open(log_file, "r") as f:
        result += f.read()
    return result

def list_reports() -> str:
    try:
        files = [
            f for f in os.listdir(LOG_DIR)
            if f.endswith(".txt") and "daily_log" not in f
        ]
        if not files:
            return "📁 No saved reports yet."
        result = "\n📁 Saved Reports:\n\n"
        for i, f in enumerate(sorted(files, reverse=True)[:10], 1):
            result += f"  {i}. {f}\n"
        return result
    except:
        return "📁 No reports folder yet."

def handle_command(query: str) -> str:
    q = query.strip()

    if q.startswith("report "):
        parts = q[7:].strip().split(" ", 1)
        if len(parts) < 2:
            return ("⚠️ Usage: report <type> <notes>\n"
                    "Types: daily, defect, handover, incident, stores, rounds\n"
                    "Example: report daily gen1 4521h all normal")
        return generate_report(parts[0], parts[1])

    if q.startswith(("fix ", "troubleshoot ", "diagnose ")):
        problem = q.split(" ", 1)[1].strip()
        return troubleshoot(problem)

    if q.startswith("log "):
        return add_log(q[4:].strip())

    if q in ("show log", "today log"):
        return show_log()

    if q in ("show reports", "list reports"):
        return list_reports()

    return "⚠️ Unknown maritime command. Try: report, fix, log, show log"
