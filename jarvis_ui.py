"""
jarvis_ui.py - Browser Chatbot UI
Open in Chrome: http://localhost:5000
Has text input AND mic button
Works offline - Flask runs on your phone
"""

from flask import Flask, request, jsonify
import os, sys, json, subprocess, tempfile

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>JARVIS</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');
:root {
  --bg:#050d1a; --surface:#0a1628; --border:#0e2a4a;
  --accent:#00c8ff; --accent2:#0077aa; --text:#c8e8ff;
  --muted:#4a7a9b; --user-bg:#0d2137; --jar-bg:#071520;
  --red:#ff4455; --green:#00ff88;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{
  background:var(--bg);color:var(--text);
  font-family:'Share Tech Mono',monospace;
  height:100dvh;display:flex;flex-direction:column;overflow:hidden;
}
#header{
  background:var(--surface);border-bottom:1px solid var(--border);
  padding:12px 16px;display:flex;align-items:center;
  justify-content:space-between;flex-shrink:0;
}
#header-title{
  font-family:'Orbitron',sans-serif;font-size:18px;
  font-weight:700;color:var(--accent);letter-spacing:3px;
  text-shadow:0 0 20px var(--accent);
}
#brain-status{font-size:11px;color:var(--muted);display:flex;align-items:center;gap:6px;}
.dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}
#chat{
  flex:1;overflow-y:auto;padding:16px;
  display:flex;flex-direction:column;gap:12px;scroll-behavior:smooth;
}
#chat::-webkit-scrollbar{width:4px;}
#chat::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
.wrap{display:flex;flex-direction:column;}
.wrap.user{align-items:flex-end;}
.wrap.jar{align-items:flex-start;}
.label{font-size:10px;color:var(--muted);margin-bottom:4px;letter-spacing:1px;}
.msg{
  max-width:88%;padding:10px 14px;border-radius:12px;
  font-size:13px;line-height:1.6;word-break:break-word;
  animation:fadeIn 0.2s ease;
}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
.user-msg{background:var(--user-bg);border:1px solid var(--accent2);border-bottom-right-radius:3px;color:var(--accent);}
.jar-msg{background:var(--jar-bg);border:1px solid var(--border);border-bottom-left-radius:3px;color:var(--text);white-space:pre-wrap;}
.thinking{color:var(--muted);font-style:italic;}
#correction{
  text-align:center;font-size:11px;color:var(--accent);
  padding:4px 12px;background:rgba(0,200,255,0.07);
  border-top:1px solid var(--border);display:none;flex-shrink:0;
}
#input-area{
  background:var(--surface);border-top:1px solid var(--border);
  padding:10px 12px;display:flex;gap:8px;align-items:center;flex-shrink:0;
}
#text-in{
  flex:1;background:var(--bg);border:1px solid var(--border);
  border-radius:8px;padding:10px 14px;color:var(--text);
  font-family:'Share Tech Mono',monospace;font-size:13px;
  outline:none;transition:border 0.2s;
}
#text-in:focus{border-color:var(--accent);}
#text-in::placeholder{color:var(--muted);}
.btn{
  border:none;border-radius:8px;width:42px;height:42px;
  font-size:16px;cursor:pointer;display:flex;
  align-items:center;justify-content:center;
  transition:all 0.15s;flex-shrink:0;
}
#send-btn{background:var(--accent);color:var(--bg);font-weight:700;}
#send-btn:active{transform:scale(0.92);}
#mic-btn{background:var(--bg);color:var(--accent);border:1.5px solid var(--accent);font-size:18px;}
#mic-btn.recording{background:var(--red);border-color:var(--red);color:white;animation:pulse 0.8s infinite;}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(255,68,85,0.4);}50%{box-shadow:0 0 0 8px rgba(255,68,85,0);}}
body::after{
  content:'';position:fixed;top:0;left:0;width:100%;height:100%;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,200,255,0.015) 2px,rgba(0,200,255,0.015) 4px);
  pointer-events:none;z-index:999;
}
</style>
</head>
<body>
<div id="header">
  <div id="header-title">◈ JARVIS</div>
  <div id="brain-status"><div class="dot"></div><span id="blabel">READY</span></div>
</div>
<div id="chat">
  <div class="wrap jar">
    <div class="label">JARVIS</div>
    <div class="msg jar-msg">System online. Maritime Assistant ready.
Type a command or press mic to speak.
Type 'help' for all commands.</div>
  </div>
</div>
<div id="correction"></div>
<div id="input-area">
  <input type="text" id="text-in" placeholder="Command or question..."
         autocomplete="off" autocorrect="off" autocapitalize="off"/>
  <button class="btn" id="mic-btn">🎤</button>
  <button class="btn" id="send-btn" onclick="sendMsg()">▶</button>
  <button class="btn" id="dbg-btn" onclick="testMic()" style="background:#333;color:#0f0;border:1px solid #0f0;font-size:10px;width:52px">TEST</button>
</div>
<script>
const chat=document.getElementById('chat');
const textIn=document.getElementById('text-in');
const micBtn=document.getElementById('mic-btn');

// Use proper event listeners to prevent double firing on Android
// touchstart/touchend for mobile, mousedown/mouseup for desktop
let micLocked=false;

micBtn.addEventListener('touchstart',function(e){
  e.preventDefault(); // prevents mousedown also firing
  e.stopPropagation();
  if(micLocked)return;
  startRec(e);
},{passive:false});

micBtn.addEventListener('touchend',function(e){
  e.preventDefault();
  e.stopPropagation();
  stopRec(e);
},{passive:false});

micBtn.addEventListener('mousedown',function(e){
  // Only fire on desktop (no touch)
  if(e.sourceCapabilities && e.sourceCapabilities.firesTouchEvents)return;
  startRec(e);
});

micBtn.addEventListener('mouseup',function(e){
  if(e.sourceCapabilities && e.sourceCapabilities.firesTouchEvents)return;
  stopRec(e);
});
const correction=document.getElementById('correction');
const blabel=document.getElementById('blabel');
let mediaRecorder,audioChunks=[],recording=false;

textIn.addEventListener('keypress',e=>{
  if(e.key==='Enter' && !e.repeat){
    e.preventDefault();
    sendMsg();
  }
});

function addMsg(text,who){
  const wrap=document.createElement('div');
  wrap.className=`wrap ${who}`;
  const label=document.createElement('div');
  label.className='label';
  label.textContent=who==='user'?'YOU':'JARVIS';
  const bubble=document.createElement('div');
  bubble.className=`msg ${who}-msg`;
  if(text==='...') bubble.classList.add('thinking');
  bubble.id=text==='...'?'thinking':'';
  bubble.textContent=text;
  wrap.appendChild(label);
  wrap.appendChild(bubble);
  chat.appendChild(wrap);
  chat.scrollTop=chat.scrollHeight;
  return bubble;
}

let lastSend=0;
async function sendMsg(text=null,skipBubble=false){
  const now=Date.now();
  if(now-lastSend < 3000)return;
  lastSend=now;
  const q=text||textIn.value.trim();
  if(!q)return;
  textIn.value='';
  if(!skipBubble)addMsg(q,'user');
  addMsg('...','jar');
  blabel.textContent='THINKING';
  try{
    const res=await fetch('/query',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query:q})
    });
    const data=await res.json();
    document.getElementById('thinking')?.parentElement?.remove();
    if(data.response)addMsg(data.response,'jar');
    blabel.textContent=data.brain||'READY';
    if(data.corrected&&data.corrected!==q){
      correction.textContent=`📝 Understood as: "${data.corrected}"`;
      correction.style.display='block';
      setTimeout(()=>correction.style.display='none',4000);
    }
  }catch(e){
    document.getElementById('thinking')?.parentElement?.remove();
    addMsg('Connection error. Is Jarvis server running?','jar');
    blabel.textContent='ERROR';
  }
}

async function startRec(e){
  e.preventDefault();
  e.stopPropagation();
  if(recording||micLocked)return;
  micLocked=true;
  recording=true;
  micBtn.classList.add('recording');
  micBtn.textContent='⏹';
  blabel.textContent='RECORDING';
  try{
    await fetch('/voice_start',{method:'POST'});
  }catch(err){
    addMsg('Could not start microphone.','jar');
    recording=false;
    micBtn.classList.remove('recording');
    micBtn.textContent='🎤';
    blabel.textContent='READY';
  }
}

async function testMic(){
  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  const rec = new MediaRecorder(stream);
  const chunks = [];
  rec.ondataavailable = e => chunks.push(e.data);
  rec.onstop = async () => {
    const blob = new Blob(chunks, {type: "audio/webm"});
    const fd = new FormData();
    fd.append("audio", blob, "test.webm");
    const res = await fetch("/voice_debug", {method:"POST", body:fd});
    const data = await res.json();
    alert(JSON.stringify(data, null, 2));
  };
  rec.start();
  setTimeout(() => rec.stop(), 2000);
  alert("Recording 2 seconds... say something!");
}
async function stopRec(e){
  e.preventDefault();
  e.stopPropagation();
  if(!recording)return;
  recording=false;
  setTimeout(()=>{micLocked=false;},3000);
  micBtn.classList.remove('recording');
  micBtn.textContent='⏳';
  blabel.textContent='PROCESSING';
  await new Promise(r=>setTimeout(r,400));
  addMsg('🎤 Processing...','user');
  try{
    const res=await fetch('/voice_stop',{method:'POST'});
    const data=await res.json();
    const msgs=document.querySelectorAll('.user-msg');
    if(data.text && data.text.trim()){
      msgs[msgs.length-1].textContent=data.text;
      micBtn.textContent='🎤';
      blabel.textContent='READY';
      sendMsg(data.text,true);
    }else{
      msgs[msgs.length-1].textContent='(unclear - try again)';
      micBtn.textContent='🎤';
      blabel.textContent='READY';
    }
  }catch(err){
    addMsg('Voice processing failed.','jar');
    micBtn.textContent='🎤';
    blabel.textContent='ERROR';
  }
}
</script>
</body>
</html>"""

@app.route("/")
def home():
    return HTML

@app.route("/query", methods=["POST"])
def handle_query():
    try:
        data  = request.get_json()
        query = data.get("query","").strip()
        import time
        if not query:
            return jsonify({"response":"Empty query.","brain":"READY"})
        jarvis_dir = os.path.dirname(os.path.abspath(__file__))
        if jarvis_dir not in sys.path:
            sys.path.insert(0, jarvis_dir)
        from jarvis import process_query, load_plugins, loaded_plugins
        if not loaded_plugins:
            load_plugins()
        from brain  import is_online
        response = process_query(query)
        brain    = "GROQ" if is_online() else "LOCAL"
        return jsonify({"response": response or "Done.", "brain": brain})
    except Exception as e:
        return jsonify({"response": f"❌ Error: {str(e)}", "brain":"ERROR"})

@app.route("/voice_start", methods=["POST"])
def voice_start():
    """Start termux microphone recording."""
    try:
        import os, subprocess
        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "jarvis_logs"
        )
        # termux-microphone-record saves to its own location
        termux_log = os.path.expanduser(
            "~/termux_organized/projects/Jarvis/jarvis_logs"
        )
        os.makedirs(termux_log, exist_ok=True)
        raw_file = os.path.join(termux_log, "voice_raw.wav")
        # Remove old file
        try: os.remove(raw_file)
        except: pass
        # Start recording
        subprocess.Popen(
            ["termux-microphone-record", "-f", raw_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({"status": "recording"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/voice_stop", methods=["POST"])
def voice_stop():
    """Stop recording and transcribe."""
    try:
        import speech_recognition as sr
        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "jarvis_logs"
        )
        # termux-microphone-record saves to its own path
        # regardless of what path we give it
        termux_log = os.path.expanduser(
            "~/termux_organized/projects/Jarvis/jarvis_logs"
        )
        raw_file  = os.path.join(termux_log, "voice_raw.wav")
        # Fallback to local path
        if not os.path.exists(raw_file):
            raw_file = os.path.join(log_dir, "voice_raw.wav")
        conv_file = os.path.join(log_dir, "voice_conv.wav")

        # Stop recording
        subprocess.run(
            ["termux-microphone-record", "-q"],
            capture_output=True
        )
        import time
        time.sleep(0.5)

        if not os.path.exists(raw_file):
            return jsonify({"text": "", "error": "No recording found"})

        size = os.path.getsize(raw_file)
        if size < 5000:
            return jsonify({"text": "", "error": "Recording too short"})

        # Convert
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", raw_file,
             "-ar", "16000", "-ac", "1",
             "-acodec", "pcm_s16le", conv_file],
            capture_output=True
        )

        if r.returncode != 0:
            return jsonify({"text": "", "error": "Conversion failed"})

        # Transcribe
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        with sr.AudioFile(conv_file) as source:
            audio = recognizer.record(source)

        text = ""
        try:
            text = recognizer.recognize_google(
                audio, language="en-PH"
            )
        except sr.UnknownValueError:
            text = ""
        except Exception as e:
            text = ""

        # Cleanup
        for f in [raw_file, conv_file]:
            try: os.remove(f)
            except: pass

        # Autocorrect
        try:
            from voice import autocorrect
            text = autocorrect(text)
        except:
            pass

        # Filipino accent finetune
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from voice_finetune import apply_finetune
            text = apply_finetune(text)
        except:
            pass

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"text": "", "error": str(e)})

@app.route("/voice", methods=["POST"])
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
        return jsonify({"text": "", "error": str(e)})

def run_ui():
    print("\n🌐 Jarvis UI ready!")
    print("   Open Chrome → http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_ui()

@app.route("/voice_debug", methods=["POST"])
def voice_debug():
    """Debug route to see exactly what audio arrives and what fails."""
    try:
        audio_file = request.files.get("audio")
        if not audio_file:
            return jsonify({"error": "no audio received"})

        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "jarvis_logs"
        )
        tmp_webm = os.path.join(log_dir, "debug_voice.webm")
        audio_file.save(tmp_webm)
        size = os.path.getsize(tmp_webm)

        # Try ffmpeg and capture full error
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_webm,
             "-ar", "16000", "-ac", "1",
             "-acodec", "pcm_s16le",
             os.path.join(log_dir, "debug_voice.wav")],
            capture_output=True
        )

        return jsonify({
            "file_size_bytes" : size,
            "ffmpeg_returncode": r.returncode,
            "ffmpeg_stderr"   : r.stderr.decode()[:500],
            "ffmpeg_stdout"   : r.stdout.decode()[:200],
            "wav_exists"      : os.path.exists(
                os.path.join(log_dir, "debug_voice.wav")
            )
        })
    except Exception as e:
        return jsonify({"exception": str(e)})
