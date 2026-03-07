"""
voice.py - Jarvis Voice Module
Uses termux-microphone-record (reliable on Android)
Then converts and transcribes with Google STT
"""

import os
import subprocess
import time
import speech_recognition as sr
from gtts import gTTS

LOG_DIR = os.path.expanduser("~/Jarvis/jarvis_logs")
os.makedirs(LOG_DIR, exist_ok=True)

RAW_FILE  = os.path.join(LOG_DIR, "voice_raw.wav")
CONV_FILE = os.path.join(LOG_DIR, "voice_converted.wav")

MARITIME_FIXES = {
    "jenerator"   : "generator",
    "generaitor"  : "generator",
    "kompressor"  : "compressor",
    "compressa"   : "compressor",
    "swichboard"  : "switchboard",
    "turbeen"     : "turbine",
    "puryfier"    : "purifier",
    "seperator"   : "separator",
    "preschure"   : "pressure",
    "temprachure" : "temperature",
    "wessel"      : "vessel",
    "injin"       : "engine",
    "olerm"       : "alarm",
    "mantenance"  : "maintenance",
    "emerjency"   : "emergency",
    "sirkuit"     : "circuit",
    "braker"      : "breaker",
    "po"          : "",
    "nga"         : "",
    "rert"        : "report",
    "riport"      : "report",
    "refort"      : "report",
    "repor"       : "report",
    "reportt"     : "report",
    "repportt"    : "report",
    "fixit"       : "fix it",
    "troblesoot"  : "troubleshoot",
    "trobulshoot" : "troubleshoot",
    "remane"      : "remind",
    "rimind"      : "remind",
    "loog"        : "log",
    "logg"        : "log",
    "helpp"       : "help",
    "finde"       : "find",
}

def autocorrect(text: str) -> str:
    if not text:
        return text

    corrected = text.lower()

    # Step 1 — Fix maritime specific words first
    for wrong, right in MARITIME_FIXES.items():
        corrected = corrected.replace(wrong, right)

    # Step 2 — Fix doubled letters at end of words
    # Example: reportt → report, helpp → help
    import re
    corrected = re.sub(r'(\w)(\1)\b', r'\1', corrected)

    # Step 3 — TextBlob general spelling correction
    try:
        from textblob import TextBlob
        blob    = TextBlob(corrected)
        tb_fix  = str(blob.correct())

        # Only use TextBlob fix if it didn't break maritime words
        maritime_words = set(MARITIME_FIXES.values())
        maritime_words.update([
            "generator", "compressor", "vessel", "engine",
            "report", "maintenance", "alarm", "circuit",
            "breaker", "pressure", "temperature", "voltage",
            "frequency", "purifier", "separator", "turbine",
            "jarvis", "remind", "recall", "remember", "log",
            "defect", "handover", "incident", "rounds","stores"
        ])

        # Check if TextBlob broke any maritime word
        broke_word = False
        for word in maritime_words:
            if word in corrected and word not in tb_fix:
                broke_word = True
                break

        if not broke_word:
            corrected = tb_fix

    except Exception:
        pass  # TextBlob failed, keep manual fixes

    # Clean up spaces
    corrected = " ".join(corrected.split())

    if corrected != text.lower():
        print(f"📝 Corrected: '{text}' → '{corrected}'")

    return corrected

def record_audio(seconds: int = 5) -> bool:
    """Record audio using termux-microphone-record."""
    try:
        # Remove old files
        for f in [RAW_FILE, CONV_FILE]:
            try: os.remove(f)
            except: pass

        # Start recording
        subprocess.Popen(
            ["termux-microphone-record", "-f", RAW_FILE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for specified seconds
        print(f"🎤 Recording {seconds}s... speak now!")
        time.sleep(seconds)

        # Stop recording
        subprocess.run(
            ["termux-microphone-record", "-q"],
            capture_output=True
        )
        time.sleep(0.5)

        # Check file exists and has content
        if os.path.exists(RAW_FILE) and os.path.getsize(RAW_FILE) > 10000:
            return True
        else:
            print("❌ Recording too short or empty")
            return False

    except Exception as e:
        print(f"❌ Record error: {e}")
        return False

def transcribe_audio() -> str:
    """Convert and transcribe the recorded audio."""
    try:
        # Convert to proper wav format
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", RAW_FILE,
             "-ar", "16000", "-ac", "1",
             "-acodec", "pcm_s16le", CONV_FILE],
            capture_output=True
        )

        if r.returncode != 0 or not os.path.exists(CONV_FILE):
            print("❌ Audio conversion failed")
            return ""

        # Transcribe
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_threshold = True

        with sr.AudioFile(CONV_FILE) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(
                audio, language="en-PH"
            )
            print(f"🎤 Heard: {text}")
            return autocorrect(text)
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
            return ""
        except sr.RequestError:
            print("📡 Google STT offline, trying sphinx...")
            try:
                text = recognizer.recognize_sphinx(audio)
                return autocorrect(text)
            except:
                return ""

    except Exception as e:
        print(f"❌ Transcribe error: {e}")
        return ""
    finally:
        # Cleanup
        for f in [RAW_FILE, CONV_FILE]:
            try: os.remove(f)
            except: pass

def listen(seconds: int = 5) -> str:
    """Record and transcribe in one call."""
    if record_audio(seconds):
        return transcribe_audio()
    return ""

def speak(text: str):
    """Convert text to speech."""
    if not text:
        return
    speech_text = text[:500]
    for symbol in ["*", "#", "─", "═", "✅", "❌",
                   "📋", "🔧", "💾", "🤖", "▄", "█"]:
        speech_text = speech_text.replace(symbol, "")
    try:
        tmp = os.path.join(LOG_DIR, "speech.mp3")
        tts = gTTS(text=speech_text, lang="en", slow=False)
        tts.save(tmp)
        try:
            subprocess.run(
                ["termux-media-player", "play", tmp],
                timeout=30, capture_output=True
            )
            time.sleep(0.5)
        except:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", tmp],
                capture_output=True, timeout=30
            )
    except Exception as e:
        print(f"⚠️ Speech error: {e}")

def speak_or_print(text: str, voice_mode: bool = False):
    print(f"\n🤖 Jarvis: {text}\n")
    if voice_mode:
        speak(text)
