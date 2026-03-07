"""
organizer.py - Personal Organizer Plugin
Memory, reminders, file finder, notes
"""

import os
import json
import threading
import time
import subprocess
from datetime import datetime

DESCRIPTION = "Memory, reminders, file finder, notes"
COMMANDS    = [
    "remember", "recall", "forget",
    "note", "show notes",
    "remind", "show reminders",
    "find", "patterns"
]

BASE_DIR       = os.path.expanduser("~/Jarvis")
MEMORY_FILE    = os.path.join(BASE_DIR, "jarvis_logs/memory.json")
NOTES_FILE     = os.path.join(BASE_DIR, "jarvis_logs/notes.json")
PATTERNS_FILE  = os.path.join(BASE_DIR, "jarvis_logs/patterns.json")
REMINDERS_FILE = os.path.join(BASE_DIR, "jarvis_logs/reminders.json")

def load_json(f):
    try:
        if os.path.exists(f):
            with open(f) as fp:
                return json.load(fp)
    except:
        pass
    return {}

def save_json(f, data):
    try:
        with open(f, "w") as fp:
            json.dump(data, fp, indent=2)
    except Exception as e:
        print(f"⚠️ Save error: {e}")

# ── MEMORY ────────────────────────────────────────
def remember(args: str) -> str:
    if not args.strip():
        return "⚠️ Usage: remember <key> is <value>"
    memory    = load_json(MEMORY_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for sep in [" is ", " = ", " are ", ":"]:
        if sep in args:
            parts = args.split(sep, 1)
            key   = parts[0].strip().lower()
            value = parts[1].strip()
            memory[key] = {"value": value, "saved_at": timestamp}
            save_json(MEMORY_FILE, memory)
            return f"✅ Remembered: '{key}' = '{value}'"
    key = args.strip().lower()[:50]
    memory[key] = {"value": args.strip(), "saved_at": timestamp}
    save_json(MEMORY_FILE, memory)
    return f"✅ Remembered: '{key}'"

def recall(args: str) -> str:
    memory = load_json(MEMORY_FILE)
    if not args.strip():
        if not memory:
            return "📭 Nothing in memory yet."
        result = "\n🧠 Everything I remember:\n\n"
        for key, val in memory.items():
            v = val["value"] if isinstance(val, dict) else val
            d = val.get("saved_at","") if isinstance(val,dict) else ""
            result += f"  📌 {key}\n     → {v}\n     ({d})\n\n"
        return result
    key     = args.strip().lower()
    if key in memory:
        val = memory[key]
        v   = val["value"] if isinstance(val,dict) else val
        d   = val.get("saved_at","") if isinstance(val,dict) else ""
        return f"🧠 {key}\n   → {v}\n   (saved: {d})"
    matches = [k for k in memory if key in k or k in key]
    if matches:
        result = f"🔍 Related memories:\n\n"
        for m in matches:
            val = memory[m]
            v   = val["value"] if isinstance(val,dict) else val
            result += f"  📌 {m} → {v}\n"
        return result
    return f"❓ Nothing remembered about '{key}'"

def forget(args: str) -> str:
    key    = args.strip().lower()
    memory = load_json(MEMORY_FILE)
    if key in memory:
        del memory[key]
        save_json(MEMORY_FILE, memory)
        return f"🗑️ Forgot: '{key}'"
    return f"❓ '{key}' not in memory"

# ── NOTES ─────────────────────────────────────────
def add_note(args: str) -> str:
    notes     = load_json(NOTES_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    note_id   = str(int(time.time()))
    notes[note_id] = {"text": args.strip(), "time": timestamp, "done": False}
    save_json(NOTES_FILE, notes)
    return f"📝 Note saved: {args.strip()}"

def show_notes(args: str = "") -> str:
    notes = load_json(NOTES_FILE)
    if not notes:
        return "📭 No notes yet."
    result = "\n📝 Your Notes:\n\n"
    for nid, note in sorted(notes.items(), reverse=True)[:20]:
        status = "✅" if note.get("done") else "📌"
        result += f"  {status} [{note['time']}]\n     {note['text']}\n\n"
    return result

# ── REMINDERS ─────────────────────────────────────
def set_reminder(args: str) -> str:
    """
    Natural language reminder. Examples:
      remind check generator in 30 minutes
      remind engine rounds in 2 hours
      remind morning checks at 08:30
      remind fire drill at 10pm
      remind lubrication at 14:00
    """
    import re
    args = args.strip()

    # Remove filler words
    args = re.sub(
        r"^(me to|me|to|i need to|please)\s+",
        "", args, flags=re.IGNORECASE
    )

    seconds = None
    message = args  # fallback

    # Pattern 1: "message in X minutes/hours"
    m = re.search(
        r"(.+?)\s+in\s+(\d+)\s*(min|minute|minutes|hour|hours|hr|hrs|sec|second|seconds)",
        args, re.IGNORECASE
    )
    if m:
        message = m.group(1).strip()
        num     = int(m.group(2))
        unit    = m.group(3).lower()
        if "sec" in unit:
            seconds = num
        elif "min" in unit:
            seconds = num * 60
        else:
            seconds = num * 3600

    # Pattern 2: "message at HH:MM or H:MM"
    if not seconds:
        m = re.search(
            r"(.+?)\s+at\s+(\d{1,2}):(\d{2})",
            args, re.IGNORECASE
        )
        if m:
            message = m.group(1).strip()
            h, mn   = int(m.group(2)), int(m.group(3))
            now     = datetime.now()
            target  = now.replace(hour=h, minute=mn, second=0)
            diff    = (target - now).total_seconds()
            if diff < 0:
                diff += 86400  # next day
            seconds = int(diff)

    # Pattern 3: "message at Xam/Xpm"
    if not seconds:
        m = re.search(
            r"(.+?)\s+at\s+(\d{1,2})(am|pm)",
            args, re.IGNORECASE
        )
        if m:
            message = m.group(1).strip()
            h       = int(m.group(2))
            ampm    = m.group(3).lower()
            if ampm == "pm" and h != 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
            now    = datetime.now()
            target = now.replace(hour=h, minute=0, second=0)
            diff   = (target - now).total_seconds()
            if diff < 0:
                diff += 86400
            seconds = int(diff)

    if not seconds:
        return ("⚠️ Could not understand time. Examples:\n"
                "  remind check generator in 30 minutes\n"
                "  remind engine rounds in 2 hours\n"
                "  remind morning checks at 08:30\n"
                "  remind fire drill at 10pm")
    reminders = load_json(REMINDERS_FILE)
    rid       = str(int(time.time()))
    fires_at  = datetime.fromtimestamp(
        time.time() + seconds
    ).strftime("%H:%M")
    reminders[rid] = {
        "message" : message,
        "set_at"  : datetime.now().strftime("%H:%M"),
        "fires_at": fires_at
    }
    save_json(REMINDERS_FILE, reminders)
    t = threading.Thread(
        target=_fire_reminder,
        args=(message, seconds, rid),
        daemon=True
    )
    t.start()
    return f"⏰ Reminder set: '{message}' at {fires_at}"

def _parse_time(t: str):
    try:
        if "min" in t:
            return int("".join(filter(str.isdigit, t))) * 60
        elif "hour" in t or "hr" in t:
            return int("".join(filter(str.isdigit, t))) * 3600
        elif "sec" in t:
            return int("".join(filter(str.isdigit, t)))
        elif ":" in t:
            from datetime import datetime as dt
            now    = dt.now()
            h, m   = t.split(":")
            target = now.replace(hour=int(h), minute=int(m), second=0)
            diff   = (target - now).total_seconds()
            return int(diff)
        else:
            return int(t) * 60
    except:
        return None

def _fire_reminder(message: str, seconds: int, rid: str):
    time.sleep(seconds)
    print(f"\n{'='*40}\n⏰ REMINDER: {message}\n{'='*40}\n")
    try:
        # Show notification with vibrate
        subprocess.run([
            "termux-notification",
            "--title", "⏰ Jarvis Reminder",
            "--content", message,
            "--vibrate", "500,200,500",
            "--priority", "high",
        ], capture_output=True)
        # Play notification sound
        sound = "/sdcard/Notifications/Yahoo - Chime.mp3"
        subprocess.Popen(
            ["termux-media-player", "play", sound]
        )
    except:
        pass
    try:
        from gtts import gTTS
        tts = gTTS(text=f"Reminder: {message}", lang="en")
        tmp = "/data/data/com.termux/files/home/Jarvis/jarvis_logs/reminder.mp3"
        tts.save(tmp)
        subprocess.run(
            ["termux-media-player", "play", tmp],
            capture_output=True
        )
    except:
        pass
    reminders = load_json(REMINDERS_FILE)
    if rid in reminders:
        del reminders[rid]
        save_json(REMINDERS_FILE, reminders)

def show_reminders(args: str = "") -> str:
    reminders = load_json(REMINDERS_FILE)
    if not reminders:
        return "⏰ No reminders set."
    result = "\n⏰ Pending Reminders:\n\n"
    for rid, r in reminders.items():
        result += f"  🔔 {r['message']}\n"
        result += f"     Set: {r['set_at']} → Fires: {r['fires_at']}\n\n"
    return result

# ── FILE FINDER ───────────────────────────────────
SEARCH_PATHS = [
    os.path.expanduser("~"),
    os.path.expanduser("~/storage/downloads"),
    os.path.expanduser("~/storage/shared"),
    os.path.expanduser("~/termux_organized"),
]

def find_file(args: str) -> str:
    if not args.strip():
        return "⚠️ Usage: find <filename>"
    search_term = args.strip().lower()
    results     = []
    print(f"🔍 Searching for '{search_term}'...")
    for path in SEARCH_PATHS:
        if not os.path.exists(path):
            continue
        try:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in
                           ["__pycache__",".git","node_modules","build",".local"]]
                for f in files:
                    if search_term in f.lower():
                        fp   = os.path.join(root, f)
                        size = os.path.getsize(fp)
                        results.append((fp, size))
        except:
            continue
    if not results:
        return f"❌ Nothing found for: '{search_term}'"
    result = f"\n📁 Found {len(results)} file(s):\n\n"
    for path, size in sorted(results)[:15]:
        s = (f"{size/1024/1024:.1f}MB" if size > 1024*1024
             else f"{size/1024:.1f}KB")
        result += f"  📄 {os.path.basename(path)}\n"
        result += f"     {path}\n"
        result += f"     {s}\n\n"
    if len(results) == 1:
        key    = os.path.basename(results[0][0]).lower()
        memory = load_json(MEMORY_FILE)
        memory[key] = {
            "value"   : results[0][0],
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_json(MEMORY_FILE, memory)
        result += f"💡 Auto-saved location to memory as '{key}'"
    return result

# ── PATTERNS ──────────────────────────────────────
def record_command(command: str):
    try:
        p = load_json(PATTERNS_FILE)
        if "commands" not in p:
            p["commands"] = []
        if "frequency" not in p:
            p["frequency"] = {}
        p["commands"].append({
            "cmd" : command,
            "time": datetime.now().strftime("%H:%M"),
            "day" : datetime.now().strftime("%A")
        })
        p["frequency"][command] = p["frequency"].get(command, 0) + 1
        if len(p["commands"]) > 500:
            p["commands"] = p["commands"][-500:]
        save_json(PATTERNS_FILE, p)
        if p["frequency"][command] == 3:
            print(f"\n💡 You use this often: '{command}'")
            print(f"   Type: remember shortcut_<name> is {command}\n")
    except:
        pass

def show_patterns(args: str = "") -> str:
    p    = load_json(PATTERNS_FILE)
    freq = p.get("frequency", {})
    if not freq:
        return "📊 No patterns yet."
    result = "\n📊 Most Used Commands:\n\n"
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    for cmd, count in top:
        bar = "█" * min(count, 15)
        result += f"  {count:3}x {bar} {cmd}\n"
    return result

# ── ENTRY POINT ───────────────────────────────────
def handle_command(query: str) -> str:
    q = query.strip()
    if q.startswith("remember "):
        return remember(q[9:])
    if q.startswith("recall"):
        return recall(q[7:].strip() if len(q) > 7 else "")
    if q.startswith("forget "):
        return forget(q[7:])
    if q.startswith("note "):
        return add_note(q[5:])
    if q in ("show notes", "notes"):
        return show_notes()
    if q.startswith("remind "):
        return set_reminder(q[7:])
    if q in ("show reminders", "reminders"):
        return show_reminders()
    if q.startswith("find "):
        return find_file(q[5:])
    if q in ("patterns", "show patterns"):
        return show_patterns()
    return "⚠️ Unknown organizer command."
