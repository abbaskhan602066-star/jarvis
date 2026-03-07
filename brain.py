"""
brain.py - Jarvis AI Brain Switcher
Priority: Groq → Gemini → Claude Export File
Mistral removed (was corrupted, caused errors)
"""

import os
import json
import requests
from datetime import datetime

# ── Load Keys ─────────────────────────────────
def load_key(name):
    try:
        with open(os.path.expanduser("~/Jarvis/keys.txt")) as f:
            for line in f:
                if f"{name}=" in line:
                    return line.strip().split("=", 1)[1].strip()
    except:
        pass
    return ""

GROQ_KEY     = load_key("GROQ_KEY")
GEMINI_KEY   = load_key("GEMINI_KEY")

GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"
GEMINI_URL   = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

EXPORT_DIR   = os.path.expanduser("~/Jarvis/claude_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

SYSTEM_PROMPT = """You are Jarvis, an intelligent personal assistant
for a Filipino seafarer working as ETO (Electro-Technical Officer)
on an LPG vessel.
Specialties: maritime reports, ship troubleshooting,
personal organizer, reminders, general questions.
Be friendly, concise, and safety-first.
Never recommend bypassing safety systems."""

# Groq uses OpenAI format (list of role/content)
groq_history = [{"role": "system", "content": SYSTEM_PROMPT}]

# Gemini uses its own format (list of role/parts)
gemini_history = []

# ── Connection Check ──────────────────────────
def is_online() -> bool:
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except:
        return False

# ── BRAIN 1: Groq ─────────────────────────────
def search_local_knowledge(query: str) -> str:
    """Search local manual files before asking AI."""
    base = os.path.expanduser("~/Jarvis/knowledge")
    knowledge_dirs = [base]
    # Add all subdirectories automatically
    try:
        for item in os.listdir(base):
            subdir = os.path.join(base, item)
            if os.path.isdir(subdir):
                knowledge_dirs.append(subdir)
                # One more level deep
                for sub2 in os.listdir(subdir):
                    subdir2 = os.path.join(subdir, sub2)
                    if os.path.isdir(subdir2):
                        knowledge_dirs.append(subdir2)
    except:
        pass
    keywords  = query.lower().split()
    stopwords = {
        "what","is","the","for","of","a","an","my","our",
        "in","on","at","to","how","please","check","sir",
        "vessel","ship","tell","me","look","through","can",
        "you","i","want","need","find","get","show","list",
        "all","files","folder","local","manual","manuals"
    }
    keywords = [k for k in keywords
                if k not in stopwords and len(k) > 2]

    if not keywords:
        return ""

    results = []
    for base_dir in knowledge_dirs:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for fname in sorted(files):
                if not fname.endswith(".txt"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    lines = open(fpath).readlines()
                    for i, line in enumerate(lines):
                        ll = line.lower()
                        if any(kw in ll for kw in keywords):
                            start   = max(0, i-2)
                            end     = min(len(lines), i+6)
                            context = "".join(
                                lines[start:end]
                            ).strip()
                            if context and len(context) > 15:
                                results.append(
                                    f"[{fname}]:\n{context}"
                                )
                except:
                    continue

    if not results:
        return ""

    # Deduplicate
    seen   = set()
    unique = []
    for r in results:
        key = r[:80]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return "\n\n---\n\n".join(unique[:4])[:2500]


def is_maritime_query(text: str) -> bool:
    """Check if query needs manual search."""
    maritime_keywords = [
        "manual","motor","generator","pump","valve","alarm",
        "insulation","resistance","voltage","current","ampere",
        "circuit","breaker","switchboard","transformer","cable",
        "bearing","winding","maintenance","inspection","repair",
        "troubleshoot","fault","defect","ohm","megaohm","watt",
        "kilowatt","frequency","hertz","alternator","starter",
        "contactor","relay","fuse","battery","charger","radar",
        "gyro","gps","compass","echo sounder","navtex","vhf",
        "uhf","inmarsat","gmdss","epirb","sart","bnwas","ssas",
        "fire alarm","gas alarm","cargo","ballast","boiler",
        "compressor","refrigerating","air condition","sewage",
        "cathodic","impressed current","propulsion","rudder",
        "speed log","anemometer","clock","wiper","intercom",
        "e-30","e-31","e-32","e-33","e-34","e-35","e-36",
        "e-37","e-38","e-39","e-40","e-41","specification",
        "procedure","how to","what is the","minimum","maximum",
        "allowable","tolerance","setting","parameter","check",
        "test","measure","reading","value","table of contents",
        "list","manual","instruction","book"
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in maritime_keywords)

def build_groq_prompt(user_input: str) -> str:
    """Build prompt using local files first."""
    # Only search manuals for maritime/technical queries
    local_data = ""
    if is_maritime_query(user_input):
        local_data = search_local_knowledge(user_input)

    if local_data:
        return f"""You are Jarvis, maritime AI assistant for ETO
on LPG vessel Siam Lucky Athena.

FOUND IN VESSEL MANUALS:
{'='*45}
{local_data}
{'='*45}

STRICT RULES:
1. Answer ONLY using the manual text above
2. If a value is NOT in the text, say:
   "Not specified in this excerpt - check original PDF"
3. NEVER invent numbers, values, or page references
4. Quote exact words from manual when possible
5. State which file info came from
6. Label any general knowledge as [General knowledge]
7. Be concise - no filler, no "by the way", no padding
8. Do not add unrelated ship operation comments

Question: {user_input}"""

    else:
        return f"""You are Jarvis, a helpful AI assistant for ETO
on LPG vessel Siam Lucky Athena.

INSTRUCTIONS:
- Answer helpfully and concisely
- For coding: write working code directly
- For general questions: answer conversationally
- For maritime questions: give best general knowledge
  labeled as [General knowledge]
- NO filler text at end of replies
- NO "by the way" or unrelated ship comments
- NO padding or unnecessary sentences
- Keep replies focused and practical

Question: {user_input}"""


def ask_groq(user_input: str) -> str:
    if not GROQ_KEY:
        return None  # No key, try next brain

    try:
        # Build prompt with local knowledge
        prompt = build_groq_prompt(user_input)

        groq_history.append({
            "role": "user",
            "content": prompt
        })

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model"      : GROQ_MODEL,
                "messages"   : groq_history[-20:],
                "max_tokens" : 1000,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code == 401:
            print("⚠️  Groq key invalid, trying Gemini...")
            return None
        if response.status_code == 429:
            print("⚠️  Groq quota exceeded, trying Gemini...")
            return None
        if response.status_code != 200:
            print(f"⚠️  Groq error {response.status_code}, trying Gemini...")
            return None

        reply = response.json()["choices"][0]["message"]["content"]
        groq_history.append({"role": "assistant", "content": reply})
        return reply

    except requests.exceptions.Timeout:
        print("⚠️  Groq timeout, trying Gemini...")
        return None
    except Exception as e:
        print(f"⚠️  Groq failed: {e}, trying Gemini...")
        return None

# ── BRAIN 2: Gemini ───────────────────────────
def ask_gemini(user_input: str) -> str:
    if not GEMINI_KEY:
        return None  # No key, try next brain

    try:
        gemini_history.append({
            "role" : "user",
            "parts": [{"text": user_input}]
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": gemini_history[-20:],
            "generationConfig": {
                "maxOutputTokens": 1000,
                "temperature"    : 0.7
            }
        }

        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        if response.status_code == 429:
            print("⚠️  Gemini quota exceeded, trying Claude export...")
            return None
        if response.status_code == 403:
            print("⚠️  Gemini key invalid, trying Claude export...")
            return None
        if response.status_code != 200:
            print(f"⚠️  Gemini error {response.status_code}, trying Claude export...")
            return None

        reply = (response.json()
                 ["candidates"][0]
                 ["content"]["parts"][0]["text"])

        gemini_history.append({
            "role" : "model",
            "parts": [{"text": reply}]
        })
        return reply

    except requests.exceptions.Timeout:
        print("⚠️  Gemini timeout, trying Claude export...")
        return None
    except Exception as e:
        print(f"⚠️  Gemini failed: {e}, trying Claude export...")
        return None

# ── BRAIN 3: Claude Export File ───────────────
def ask_via_claude_export(user_input: str) -> str:
    """
    When all APIs fail, generate a text file
    that the user can paste into Claude.ai
    and get an answer back.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"ask_claude_{timestamp}.txt"
    filepath  = os.path.join(EXPORT_DIR, filename)

    # Build recent conversation context
    context = ""
    for m in groq_history[-6:]:
        if m["role"] == "system":
            continue
        role = "Me" if m["role"] == "user" else "Jarvis"
        context += f"{role}: {m['content']}\n"

    content = f"""==================================================
JARVIS → CLAUDE EXPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
==================================================

Hi Claude! I am a Filipino ETO on an LPG vessel.
My Jarvis AI assistant has no working API right now
(ship network blocks everything, quota exceeded, etc.)

Please answer this question for me as Jarvis would:

QUESTION:
{user_input}

RECENT CONVERSATION CONTEXT:
{context if context else "(no previous context)"}

JARVIS PERSONALITY:
- Maritime assistant for LPG vessel ETO
- Helpful with reports, troubleshooting, reminders
- Friendly, concise, safety-first
- Understands Filipino seafarer context

Please answer the question above.
When done, I will paste your reply back into Jarvis.
==================================================
"""

    try:
        with open(filepath, "w") as f:
            f.write(content)

        # Also save to Downloads for easy access
        downloads = os.path.expanduser("~/storage/downloads")
        if os.path.exists(downloads):
            dl_path = os.path.join(downloads, filename)
            with open(dl_path, "w") as f:
                f.write(content)
            print(f"\n📁 Also saved to Downloads: {filename}")

        return f"""❌ All AI brains unavailable right now.

📄 I created a file for you:
   {filepath}
   Also in: Downloads/{filename}

HOW TO USE:
1. Open the file
2. Copy everything inside
3. Paste it into Claude.ai chat
4. Claude will answer as Jarvis
5. Copy Claude's reply
6. Come back here and type:
   jarvis reply <paste Claude's answer here>

Or just ask Claude directly:
→ claude.ai is free to use in browser
→ No API key needed"""

    except Exception as e:
        return f"""❌ All AI brains offline.
Export file failed: {e}

MANUAL OPTION:
Open claude.ai in your browser and ask:
"{user_input}"
Tell Claude you are an ETO on an LPG vessel."""

# ── Save Claude Reply Back To Jarvis ──────────
def save_claude_reply(reply: str) -> str:
    """Save a reply from Claude back into conversation history."""
    groq_history.append({"role": "assistant", "content": reply})
    gemini_history.append({
        "role" : "model",
        "parts": [{"text": reply}]
    })

    # Save to knowledge base
    knowledge_file = os.path.expanduser(
        "~/Jarvis/knowledge/from_claude.txt"
    )
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        with open(knowledge_file, "a") as f:
            f.write(f"\n[{timestamp}]\n{reply}\n{'─'*40}\n")
        return "✅ Claude's reply saved to memory and knowledge base."
    except:
        return "✅ Claude's reply saved to conversation memory."

# ── Master Brain Selector ─────────────────────
def ask_ai(user_input: str, force: str = "auto") -> str:

    # Handle saved Claude reply
    if user_input.lower().startswith("jarvis reply "):
        reply = user_input[13:].strip()
        return save_claude_reply(reply)

    # Force specific brain
    if force == "groq":
        print("🌐 Groq (forced)")
        result = ask_groq(user_input)
        return result or "❌ Groq not available."

    if force == "gemini":
        print("🌐 Gemini (forced)")
        result = ask_gemini(user_input)
        return result or "❌ Gemini not available."

    # Auto mode
    if is_online():
        # Try Groq first
        if GROQ_KEY:
            print("🌐 Trying Groq...")
            result = ask_groq(user_input)
            if result:
                return result

        # Try Gemini second
        if GEMINI_KEY:
            print("🌐 Trying Gemini...")
            result = ask_gemini(user_input)
            if result:
                return result

        # Both failed online
        print("⚠️  Both APIs failed, generating Claude export...")
        return ask_via_claude_export(user_input)

    else:
        # No internet at all
        print("📡 Offline, generating Claude export file...")
        return ask_via_claude_export(user_input)

def clear_memory():
    system = groq_history[0]
    groq_history.clear()
    groq_history.append(system)
    gemini_history.clear()

def brain_status() -> str:
    """Show which brains are available."""
    online = is_online()
    status = "\n🧠 Brain Status:\n\n"
    status += f"  Internet:  {'✅ Connected' if online else '❌ Offline'}\n"
    status += f"  Groq key:  {'✅ Loaded' if GROQ_KEY else '❌ Missing'}\n"
    status += f"  Gemini key:{'✅ Loaded' if GEMINI_KEY else '❌ Missing'}\n"
    status += f"  Mistral:   ❌ Removed (was corrupted)\n"
    status += f"  Claude:    ✅ Always available (export file)\n"
    status += f"\n  Export folder: ~/Jarvis/claude_exports/\n"
    return status
