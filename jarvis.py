"""
jarvis.py - Main Jarvis Entry Point
Maritime Personal Assistant for LPG Vessel ETO
"""

import os
import sys
import importlib
import traceback
import json
from datetime import datetime

PLUGINS_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins")
LOG_DIR        = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_logs")
ERROR_FILE     = os.path.join(LOG_DIR, "errors.json")
loaded_plugins = {}

os.makedirs(PLUGINS_DIR, exist_ok=True)
os.makedirs(LOG_DIR,     exist_ok=True)

# ==============================
# Plugin Loader
# ==============================
def load_plugins():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("\n🔌 Loading plugins...")
    for filename in sorted(os.listdir(PLUGINS_DIR)):
        if filename.endswith(".py") and not filename.startswith("_"):
            name = filename[:-3]
            try:
                module = importlib.import_module(f"plugins.{name}")
                loaded_plugins[name] = module
                desc = getattr(module, "DESCRIPTION", "")
                print(f"  ✅ {name}: {desc}")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
    print(f"\n  {len(loaded_plugins)} plugin(s) loaded.\n")

def list_plugins() -> str:
    if not loaded_plugins:
        return "No plugins loaded."
    result = "\n🔌 Loaded Plugins:\n\n"
    for name, module in loaded_plugins.items():
        desc = getattr(module, "DESCRIPTION", "")
        cmds = getattr(module, "COMMANDS", [])
        result += f"  📦 {name}\n"
        result += f"     {desc}\n"
        result += f"     Commands: {', '.join(cmds)}\n\n"
    return result

# ==============================
# Error Logger
# ==============================
def log_error(command: str, error: str):
    try:
        errors = []
        if os.path.exists(ERROR_FILE):
            with open(ERROR_FILE) as f:
                errors = json.load(f)
        errors.append({
            "command"  : command,
            "error"    : error,
            "traceback": traceback.format_exc(),
            "time"     : datetime.now().isoformat()
        })
        errors = errors[-20:]
        with open(ERROR_FILE, "w") as f:
            json.dump(errors, f, indent=2)
    except:
        pass

def diagnose() -> str:
    from brain import ask_ai
    if not os.path.exists(ERROR_FILE):
        return "✅ No errors recorded. Jarvis is healthy!"
    with open(ERROR_FILE) as f:
        errors = json.load(f)
    if not errors:
        return "✅ No errors. Jarvis is healthy!"
    recent  = errors[-3:]
    summary = json.dumps(recent, indent=2)
    prompt  = f"""These errors occurred in my Jarvis Python assistant on Android Termux:

{summary}

For each error:
1. Simple explanation of what caused it
2. Exact fix (command or code change)
3. How to prevent it

Be specific and practical."""
    print("🔍 Diagnosing...")
    return ask_ai(prompt)

# ==============================
# Help Menu
# ==============================
def show_help():
    print("""
╔══════════════════════════════════════════════════════════╗
║          JARVIS — Maritime Personal Assistant            ║
║               LPG Vessel ETO Edition 🚢                 ║
╚══════════════════════════════════════════════════════════╝

📋 REPORTS:
  report daily    <notes>    Daily Maintenance Report
  report defect   <notes>    Defect and Repair Report
  report handover <notes>    Watch Handover Report
  report incident <notes>    Incident/Near-Miss Report
  report stores   <notes>    Stores Consumption Report
  report rounds   <notes>    Engine Room Rounds Report

🔧 TROUBLESHOOTING:
  fix <problem>              Step-by-step diagnosis
  troubleshoot <problem>     Same as fix

📓 DAILY LOG:
  log <entry>                Add log entry
  show log                   View today's log
  show reports               List saved reports

🧠 MEMORY:
  remember <key> is <value>  Save to memory
  recall <key>               Retrieve from memory
  recall                     Show all memories
  forget <key>               Delete from memory

📝 NOTES:
  note <text>                Save a note
  show notes                 View all notes

⏰ REMINDERS:
  remind 30mins <message>    Reminder in 30 minutes
  remind 2hours <message>    Reminder in 2 hours
  remind 08:30 <message>     Reminder at specific time
  show reminders             View pending reminders

🔍 FILE FINDER:
  find <filename>            Search entire phone

💬 GENERAL:
  ask <question>             Ask Jarvis anything
  online <question>          Force Groq online brain
  offline <question>         Force Mistral offline brain
  clear                      Clear conversation memory
  diagnose                   Check and fix errors
  plugins                    List loaded plugins
  patterns                   Show most used commands
  voice on / voice off       Toggle voice mode
  ui                         Open browser chatbot
  help                       Show this menu
  exit / quit                Close Jarvis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES:
  report daily   gen2 4521h cleaned purifier all normal
  fix            cargo compressor high discharge temp
  remember       groq key is saved in ~/keys.txt
  find           manual.pdf
  remind         2hours check running generators
  ask            what causes VFD overcurrent fault?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# ==============================
# Command Processor
# ==============================
def process_query(query: str) -> str:
    q = query.strip().lower()

    # Finetune commands
    if q.startswith("finetune ") or q.startswith("learn "):
        # Format: "finetune <wrong> = <correct>"
        # Example: "finetune moon = megaohm"
        try:
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from voice_finetune import save_correction
            parts = query.split("=", 1)
            if len(parts) == 2:
                wrong   = parts[0].replace("finetune","").replace("learn","").strip()
                correct = parts[1].strip()
                if save_correction(wrong, correct):
                    return f"✅ Learned: \"{wrong}\" → \"{correct}\""
                return "❌ Could not save correction"
            return "Usage: finetune <wrong word> = <correct word>"
        except Exception as e:
            return f"❌ Finetune error: {e}"

    if q in ("list finetune", "show finetune", "my corrections"):
        try:
            from voice_finetune import list_corrections
            return list_corrections()
        except Exception as e:
            return f"❌ {e}"

    # Pass to original handler
    return process_query_original(query)

def process_query_original(query: str) -> str:
    q = query.strip()

    # Record pattern silently
    try:
        org = loaded_plugins.get("organizer")
        if org:
            org.record_command(q)
    except:
        pass

    # System commands
    if q in ("help", "?"):
        show_help()
        return ""
    if q in ("plugins", "list plugins"):
        return list_plugins()
    if q == "brain status":
        from brain import brain_status
        return brain_status()
    if q == "diagnose":
        return diagnose()
    if q == "clear":
        from brain import clear_memory
        clear_memory()
        return "🔄 Conversation memory cleared."
    if q in ("patterns", "show patterns"):
        org = loaded_plugins.get("organizer")
        if org:
            return org.show_patterns()
        return "Organizer plugin not loaded."

    # Force brain mode
    if q.startswith("online "):
        from brain import ask_ai
        return ask_ai(q[7:], force="online")
    if q.startswith("offline "):
        from brain import ask_ai
        return ask_ai(q[8:], force="offline")

    # Plugin commands
    for plugin_name, module in loaded_plugins.items():
        commands = getattr(module, "COMMANDS", [])
        for cmd in commands:
            if q.startswith(cmd):
                try:
                    return module.handle_command(q)
                except Exception as e:
                    log_error(q, str(e))
                    return f"❌ Plugin error: {e}"

    # Default — ask AI
    if q.startswith("ask "):
        q = q[4:]
    from brain import ask_ai
    return ask_ai(q)

# ==============================
# Main Loop
# ==============================
def main():
    load_plugins()
    print("""
╔══════════════════════════════════════════════════════════╗
║          JARVIS — Maritime Personal Assistant            ║
║               LPG Vessel ETO Edition 🚢                 ║
║                                                          ║
║  Type 'help' for all commands                            ║
║  Type 'ui' to open browser chatbot                       ║
║  Type 'exit' to quit                                     ║
╚══════════════════════════════════════════════════════════╝
""")

    voice_mode = False

    while True:
        try:
            if voice_mode:
                from voice import listen, speak_or_print
                query = listen()
                if not query:
                    continue
                print(f"🎤 You said: {query}")
            else:
                query = input("You: ").strip()

            if not query:
                continue

            if query.lower() in ("exit", "quit", "bye"):
                print("Jarvis: Goodbye! Stay safe on board. 🚢")
                break

            if query.lower() == "ui":
                print("🌐 Starting browser UI...")
                print("   Open Chrome → http://localhost:5000")
                import threading
                from jarvis_ui import run_ui
                t = threading.Thread(target=run_ui, daemon=True)
                t.start()
                continue

            if query.lower() == "voice on":
                voice_mode = True
                print("🎤 Voice mode ON")
                continue
            if query.lower() == "voice off":
                voice_mode = False
                print("⌨️  Voice mode OFF")
                continue

            response = process_query(query)

            if response:
                if voice_mode:
                    from voice import speak_or_print
                    speak_or_print(response, voice_mode=True)
                else:
                    print(f"\n🤖 Jarvis: {response}\n")

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted. Type 'exit' to quit.")
        except Exception as e:
            error_msg = str(e)
            log_error(query if 'query' in locals() else "unknown", error_msg)
            print(f"\n❌ Error: {error_msg}")
            print("💡 Type 'diagnose' to fix this.\n")

if __name__ == "__main__":
    main()
