"""
daily_ops.py - Daily Operations Plugin
Voice-driven reports, running hours,
equipment status, monthly summaries
"""

import os
import json
from datetime import datetime, timedelta

DESCRIPTION = "Daily operations, running hours, equipment tracker"
COMMANDS    = [
    "morning rounds", "end of watch",
    "log hours", "log defect", "log repair",
    "equipment status", "show hours",
    "monthly report", "weekly report",
    "show log today", "show log week",
]

BASE_DIR  = os.path.expanduser("~/Jarvis")
LOGS_DIR  = os.path.join(BASE_DIR, "jarvis_logs")
OPS_DIR   = os.path.join(LOGS_DIR, "operations")
HOURS_FILE= os.path.join(OPS_DIR,  "running_hours.json")
EQUIP_FILE= os.path.join(OPS_DIR,  "equipment_status.json")
DAILY_DIR = os.path.join(OPS_DIR,  "daily_logs")
REPORT_DIR= os.path.join(OPS_DIR,  "reports")

for d in [OPS_DIR, DAILY_DIR, REPORT_DIR]:
    os.makedirs(d, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW   = datetime.now().strftime("%H:%M")

# ── HELPERS ───────────────────────────────────
def load_json(f, default):
    try:
        if os.path.exists(f):
            return json.load(open(f))
    except:
        pass
    return default

def save_json(f, data):
    with open(f, "w") as fp:
        json.dump(data, fp, indent=2)

def today_log_file():
    return os.path.join(DAILY_DIR, f"{TODAY}.json")

def load_today() -> dict:
    return load_json(today_log_file(), {
        "date"    : TODAY,
        "entries" : [],
        "defects" : [],
        "repairs" : [],
        "hours"   : {},
        "rounds"  : [],
        "handover": []
    })

def save_today(data: dict):
    save_json(today_log_file(), data)

def add_entry(category: str, text: str):
    data = load_today()
    entry = {
        "time" : NOW,
        "text" : text,
        "type" : category
    }
    if category == "defect":
        data["defects"].append(entry)
    elif category == "repair":
        data["repairs"].append(entry)
    elif category == "rounds":
        data["rounds"].append(entry)
    elif category == "handover":
        data["handover"].append(entry)
    else:
        data["entries"].append(entry)
    save_today(data)
    return entry

# ── RUNNING HOURS ─────────────────────────────
def log_hours(args: str) -> str:
    """
    Usage: log hours <equipment> <hours>
    Example: log hours gen1 4521
             log hours gen2 3200
             log hours cargo pump 1850
    """
    parts = args.strip().rsplit(" ", 1)
    if len(parts) < 2:
        return ("⚠️ Usage: log hours <equipment> <hours>\n"
                "Example: log hours gen1 4521\n"
                "         log hours cargo compressor 2100")
    try:
        hours = float(parts[1])
        equip = parts[0].strip()
    except:
        return "❌ Hours must be a number"

    data  = load_json(HOURS_FILE, {})
    today = load_today()
    prev  = data.get(equip, {}).get("hours", 0)
    diff  = hours - prev if prev > 0 else 0

    data[equip] = {
        "hours"      : hours,
        "updated"    : f"{TODAY} {NOW}",
        "prev_hours" : prev,
        "diff"       : round(diff, 1)
    }
    save_json(HOURS_FILE, data)

    # Also log in today's entries
    today["hours"][equip] = hours
    save_today(today)

    result = f"✅ Running hours logged:\n"
    result += f"   {equip.upper()}: {hours}h"
    if diff > 0:
        result += f" (+{diff}h since last entry)"
    return result

def show_hours(args: str = "") -> str:
    data = load_json(HOURS_FILE, {})
    if not data:
        return "📊 No running hours logged yet."
    result = f"\n📊 Running Hours Log:\n\n"
    for equip, info in sorted(data.items()):
        result += f"  ⚙️  {equip.upper()}\n"
        result += f"     Hours:   {info['hours']}h\n"
        if info.get('diff', 0) > 0:
            result += f"     +{info['diff']}h since last entry\n"
        result += f"     Updated: {info['updated']}\n\n"
    return result

# ── MORNING ROUNDS ────────────────────────────
def morning_rounds(args: str) -> str:
    """
    Voice → professional morning rounds report
    Usage: morning rounds <your voice notes>
    """
    if not args.strip():
        return ("⚠️ Say your rounds notes after the command.\n"
                "Example:\n"
                "morning rounds gen1 normal gen2 normal "
                "purifier running cargo pumps standby "
                "all alarms clear")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    data      = load_today()

    # Parse common patterns from voice
    notes = args.strip()

    # Build professional report
    report = f"""
MORNING ENGINE ROOM ROUNDS REPORT
═══════════════════════════════════════════════
Vessel    : {get_vessel_name()}
Date      : {TODAY}
Time      : {NOW}
Reported by: ETO
═══════════════════════════════════════════════

ROUNDS NOTES:
{format_notes(notes)}

GENERAL STATUS:
  All equipment checked and recorded.
  Running hours updated in log.

═══════════════════════════════════════════════
Signature: _______________  Time: {NOW}
═══════════════════════════════════════════════
"""

    # Save entry
    entry = add_entry("rounds", notes)

    # Save report file
    filename = f"morning_rounds_{TODAY}_{NOW.replace(':','')}.txt"
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(report)

    return (f"✅ Morning rounds report saved!\n\n"
            f"{report}\n"
            f"📄 File: {filename}")

# ── END OF WATCH ──────────────────────────────
def end_of_watch(args: str) -> str:
    """
    Voice → professional handover report
    Usage: end of watch <your handover notes>
    """
    if not args.strip():
        return ("⚠️ Say your handover notes.\n"
                "Example:\n"
                "end of watch gen1 running gen2 standby "
                "purifier completed defect list updated "
                "no outstanding alarms")

    notes = args.strip()
    data  = load_today()

    # Get today's defects for report
    defects = data.get("defects", [])
    defect_text = ""
    if defects:
        defect_text = "\nDEFECTS/OBSERVATIONS:\n"
        for d in defects:
            defect_text += f"  [{d['time']}] {d['text']}\n"
    else:
        defect_text = "\nDEFECTS/OBSERVATIONS:\n  None reported\n"

    # Get running hours
    hours     = data.get("hours", {})
    hours_text = "\nRUNNING HOURS:\n"
    if hours:
        for equip, hrs in hours.items():
            hours_text += f"  {equip.upper()}: {hrs}h\n"
    else:
        hours_text += "  (not logged this watch)\n"

    report = f"""
WATCH HANDOVER REPORT
═══════════════════════════════════════════════
Vessel    : {get_vessel_name()}
Date      : {TODAY}
Time      : {NOW}
Watch     : ETO Handover
═══════════════════════════════════════════════

HANDOVER NOTES:
{format_notes(notes)}
{defect_text}
{hours_text}
OUTSTANDING ITEMS:
  Please check above defects list.

═══════════════════════════════════════════════
Outgoing Officer: ___________  Time: {NOW}
Incoming Officer: ___________  Time: ______
═══════════════════════════════════════════════
"""

    add_entry("handover", notes)

    filename = f"handover_{TODAY}_{NOW.replace(':','')}.txt"
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(report)

    return (f"✅ Handover report saved!\n\n"
            f"{report}\n"
            f"📄 File: {filename}")

# ── LOG DEFECT ────────────────────────────────
def log_defect(args: str) -> str:
    if not args.strip():
        return ("⚠️ Usage: log defect <description>\n"
                "Example: log defect gen2 high cooling water temp "
                "alarm at 85 degrees investigating")
    add_entry("defect", args.strip())
    return (f"✅ Defect logged at {NOW}:\n"
            f"   {args.strip()}\n"
            f"   Will appear in next handover report.")

def log_repair(args: str) -> str:
    if not args.strip():
        return ("⚠️ Usage: log repair <description>\n"
                "Example: log repair replaced gen2 thermostat "
                "cooling water temp now normal")
    add_entry("repair", args.strip())
    return (f"✅ Repair logged at {NOW}:\n"
            f"   {args.strip()}")

# ── SHOW TODAY'S LOG ──────────────────────────
def show_log_today(args: str = "") -> str:
    data   = load_today()
    result = f"\n📋 TODAY'S LOG — {TODAY}\n\n"

    if data.get("rounds"):
        result += "🔄 ROUNDS:\n"
        for e in data["rounds"]:
            result += f"  [{e['time']}] {e['text']}\n"
        result += "\n"

    if data.get("entries"):
        result += "📝 ENTRIES:\n"
        for e in data["entries"]:
            result += f"  [{e['time']}] {e['text']}\n"
        result += "\n"

    if data.get("defects"):
        result += "⚠️  DEFECTS:\n"
        for e in data["defects"]:
            result += f"  [{e['time']}] {e['text']}\n"
        result += "\n"

    if data.get("repairs"):
        result += "🔧 REPAIRS:\n"
        for e in data["repairs"]:
            result += f"  [{e['time']}] {e['text']}\n"
        result += "\n"

    if data.get("hours"):
        result += "⚙️  RUNNING HOURS:\n"
        for equip, hrs in data["hours"].items():
            result += f"  {equip.upper()}: {hrs}h\n"
        result += "\n"

    if data.get("handover"):
        result += "🔁 HANDOVER:\n"
        for e in data["handover"]:
            result += f"  [{e['time']}] {e['text']}\n"
        result += "\n"

    if not any([data.get("rounds"), data.get("entries"),
                data.get("defects"), data.get("repairs"),
                data.get("hours"), data.get("handover")]):
        result += "  (no entries yet today)\n"

    return result

# ── WEEKLY/MONTHLY REPORT ─────────────────────
def compile_report(days: int, label: str) -> str:
    result    = f"\n📊 {label} REPORT\n"
    result   += f"{'='*50}\n"
    result   += f"Vessel : {get_vessel_name()}\n"
    result   += f"Period : last {days} days\n"
    result   += f"Generated: {TODAY} {NOW}\n"
    result   += f"{'='*50}\n\n"

    all_defects = []
    all_repairs = []
    all_hours   = {}
    total_entries = 0

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)
                ).strftime("%Y-%m-%d")
        log_file = os.path.join(DAILY_DIR, f"{date}.json")
        if not os.path.exists(log_file):
            continue
        data = load_json(log_file, {})
        total_entries += len(data.get("entries", []))
        all_defects   += data.get("defects", [])
        all_repairs   += data.get("repairs", [])
        for equip, hrs in data.get("hours", {}).items():
            all_hours[equip] = hrs  # Latest reading

    result += f"SUMMARY:\n"
    result += f"  Total log entries : {total_entries}\n"
    result += f"  Defects reported  : {len(all_defects)}\n"
    result += f"  Repairs completed : {len(all_repairs)}\n\n"

    if all_hours:
        result += f"RUNNING HOURS (latest):\n"
        for equip, hrs in sorted(all_hours.items()):
            result += f"  {equip.upper()}: {hrs}h\n"
        result += "\n"

    if all_defects:
        result += f"DEFECTS ({len(all_defects)}):\n"
        for d in all_defects:
            result += f"  [{d.get('time','?')}] {d['text']}\n"
        result += "\n"

    if all_repairs:
        result += f"REPAIRS ({len(all_repairs)}):\n"
        for r in all_repairs:
            result += f"  [{r.get('time','?')}] {r['text']}\n"
        result += "\n"

    result += f"{'='*50}\n"
    result += f"Prepared by: ETO\n"
    result += f"{'='*50}\n"

    # Save report
    filename = (f"{label.lower().replace(' ','_')}"
                f"_{TODAY}.txt")
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(result)

    return result + f"\n📄 Saved: {filename}"

def weekly_report(args=""):
    return compile_report(7, "WEEKLY")

def monthly_report(args=""):
    return compile_report(30, "MONTHLY")

# ── HELPERS ───────────────────────────────────
def get_vessel_name() -> str:
    try:
        from jarvis import process_query
        memory_file = os.path.expanduser(
            "~/Jarvis/jarvis_logs/memory.json"
        )
        data = load_json(memory_file, {})
        for key in ["vessel", "ship", "vessel name"]:
            if key in data:
                v = data[key]
                return v["value"] if isinstance(v,dict) else v
    except:
        pass
    return "LPG VESSEL"

def format_notes(notes: str) -> str:
    """Format rough voice notes into structured text."""
    words    = notes.split()
    lines    = []
    current  = []
    keywords = [
        "gen", "generator", "pump", "compressor",
        "alarm", "defect", "normal", "running",
        "standby", "stopped", "checked", "completed",
        "purifier", "separator", "boiler", "cargo"
    ]
    for word in words:
        current.append(word)
        if word.lower() in keywords and len(current) > 3:
            lines.append("  • " + " ".join(current))
            current = []
    if current:
        lines.append("  • " + " ".join(current))
    return "\n".join(lines) if lines else f"  {notes}"

# ── ENTRY POINT ───────────────────────────────
def handle_command(query: str) -> str:
    q = query.strip().lower()

    if q.startswith("morning rounds"):
        return morning_rounds(query[14:].strip())
    if q.startswith("end of watch"):
        return end_of_watch(query[12:].strip())
    if q.startswith("log hours"):
        return log_hours(query[9:].strip())
    if q.startswith("log defect"):
        return log_defect(query[10:].strip())
    if q.startswith("log repair"):
        return log_repair(query[10:].strip())
    if q in ("show hours", "running hours"):
        return show_hours()
    if q in ("show log today", "log today",
             "today log", "show log"):
        return show_log_today()
    if q in ("weekly report", "show log week"):
        return weekly_report()
    if q in ("monthly report", "show log month"):
        return monthly_report()

    return "⚠️ Unknown daily_ops command."
