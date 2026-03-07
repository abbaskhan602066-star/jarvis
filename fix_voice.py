# Run this to patch the voice route in jarvis_ui.py
import re

with open("jarvis_ui.py", "r") as f:
    content = f.read()

old = '''@app.route("/voice", methods=["POST"])
def handle_voice():
    try:
        import speech_recognition as sr
        audio_file = request.files.get("audio")
        if not audio_file:
            return jsonify({"text":""})
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"jarvis_logs")
        os.makedirs(log_dir, exist_ok=True)
        tmp_webm = os.path.join(log_dir,"temp_voice.webm")
        tmp_wav  = os.path.join(log_dir,"temp_voice.wav")
        audio_file.save(tmp_webm)
        subprocess.run(
            ["ffmpeg","-i",tmp_webm,"-ar","16000","-ac","1",tmp_wav,"-y"],
            capture_output=True
        )
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_wav) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language="en-PH")
        except:
            text = ""
        for f in [tmp_webm, tmp_wav]:
            try: os.remove(f)
            except: pass
        from voice import autocorrect
        text = autocorrect(text)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"text":"","error":str(e)})'''

new = '''@app.route("/voice", methods=["POST"])
def handle_voice():
    try:
        import speech_recognition as sr
        import wave, struct, math

        audio_file = request.files.get("audio")
        if not audio_file:
            return jsonify({"text": "", "error": "no audio"})

        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "jarvis_logs"
        )
        os.makedirs(log_dir, exist_ok=True)

        # Save original webm
        tmp_webm = os.path.join(log_dir, "temp_voice.webm")
        tmp_wav  = os.path.join(log_dir, "temp_voice.wav")
        tmp_mp4  = os.path.join(log_dir, "temp_voice.mp4")
        audio_file.save(tmp_webm)

        # Try multiple conversion methods
        converted = False

        # Method 1 — ffmpeg webm to wav
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_webm,
             "-ar", "16000", "-ac", "1",
             "-acodec", "pcm_s16le", tmp_wav],
            capture_output=True
        )
        if r.returncode == 0 and os.path.exists(tmp_wav):
            converted = True

        # Method 2 — try as mp4/ogg format
        if not converted:
            r = subprocess.run(
                ["ffmpeg", "-y", "-f", "ogg", "-i", tmp_webm,
                 "-ar", "16000", "-ac", "1",
                 "-acodec", "pcm_s16le", tmp_wav],
                capture_output=True
            )
            if r.returncode == 0 and os.path.exists(tmp_wav):
                converted = True

        # Method 3 — force decode
        if not converted:
            r = subprocess.run(
                ["ffmpeg", "-y", "-f", "webm", "-i", tmp_webm,
                 "-ar", "16000", "-ac", "1", tmp_wav],
                capture_output=True
            )
            if r.returncode == 0 and os.path.exists(tmp_wav):
                converted = True

        if not converted:
            # Cleanup
            for f in [tmp_webm, tmp_wav]:
                try: os.remove(f)
                except: pass
            return jsonify({
                "text": "",
                "error": "Audio conversion failed. Try typing instead.",
                "debug": r.stderr.decode()[:200]
            })

        # Transcribe
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_threshold = True

        with sr.AudioFile(tmp_wav) as source:
            audio = recognizer.record(source)

        text = ""
        # Try Google STT online
        try:
            text = recognizer.recognize_google(
                audio, language="en-PH"
            )
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError:
            # Try offline sphinx
            try:
                text = recognizer.recognize_sphinx(audio)
            except:
                text = ""

        # Cleanup
        for f in [tmp_webm, tmp_wav, tmp_mp4]:
            try: os.remove(f)
            except: pass

        # Autocorrect
        try:
            from voice import autocorrect
            text = autocorrect(text)
        except:
            pass

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"text": "", "error": str(e)})'''

if old in content:
    content = content.replace(old, new)
    with open("jarvis_ui.py", "w") as f:
        f.write(content)
    print("✅ Voice route patched successfully")
else:
    print("⚠️  Could not find old route - may already be patched")
    print("   Will rewrite jarvis_ui.py voice section manually")
