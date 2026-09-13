"""
Altron - Android entry point
Developer: Abbas

What this does:
  1. Starts the existing Flask chat UI (jarvis_ui.py / altron_ui.py) in a background thread.
  2. Shows it inside a full-screen Android WebView, so the app looks like a normal app.
  3. If the WebView is unavailable (e.g. running on a desktop), it falls back to Kivy
     showing the local address, and opens the system browser.

Buildozer uses this file as the app entry point.
"""

import os
import sys
import socket
import threading
import time

APP_NAME = "Altron"
DEVELOPER = "Abbas"
PORT = 5000

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ----------------------------------------------------------------------
# 1. Locate the Flask app
# ----------------------------------------------------------------------
def get_flask_app():
    for module_name in ("altron_ui", "jarvis_ui"):
        try:
            module = __import__(module_name)
            app = getattr(module, "app", None)
            if app is not None:
                return app
        except Exception as exc:  # pragma: no cover - device side
            print(f"[{APP_NAME}] could not load {module_name}: {exc}")

    # Fallback: minimal built-in Altron chat so the APK always runs.
    from flask import Flask, request, jsonify

    fallback = Flask(__name__)

    PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Altron</title><style>
    body{margin:0;background:#050d1a;color:#c8e8ff;font-family:monospace;
         display:flex;flex-direction:column;height:100dvh}
    header{padding:14px;border-bottom:1px solid #0e2a4a;color:#00c8ff;
           letter-spacing:3px;font-weight:700}
    #log{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px}
    .m{padding:10px 12px;border-radius:10px;max-width:85%;white-space:pre-wrap}
    .u{background:#0d2137;align-self:flex-end}.a{background:#071520;align-self:flex-start}
    form{display:flex;gap:8px;padding:12px;border-top:1px solid #0e2a4a}
    input{flex:1;padding:12px;border-radius:10px;border:1px solid #0e2a4a;
          background:#0a1628;color:#c8e8ff}
    button{padding:12px 16px;border:0;border-radius:10px;background:#00c8ff;color:#041018;font-weight:700}
    </style></head><body>
    <header>ALTRON &middot; by Abbas</header>
    <div id="log"><div class="m a">Altron online. Ask me anything.</div></div>
    <form onsubmit="send(event)">
      <input id="q" placeholder="Type a message..." autocomplete="off">
      <button>Send</button>
    </form>
    <script>
    const log=document.getElementById('log');
    function add(t,c){const d=document.createElement('div');d.className='m '+c;
      d.textContent=t;log.appendChild(d);log.scrollTop=log.scrollHeight;}
    async function send(e){e.preventDefault();const i=document.getElementById('q');
      const t=i.value.trim();if(!t)return;i.value='';add(t,'u');
      const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({message:t})});const j=await r.json();add(j.reply,'a');}
    </script></body></html>"""

    @fallback.route("/")
    def index():
        return PAGE

    @fallback.route("/chat", methods=["POST"])
    def chat():
        text = (request.get_json(silent=True) or {}).get("message", "")
        reply = f"Altron received: {text}"
        try:
            import brain  # the repo's own brain, if it imports cleanly

            for fn in ("respond", "think", "handle", "ask"):
                if hasattr(brain, fn):
                    reply = str(getattr(brain, fn)(text))
                    break
        except Exception as exc:
            reply = f"{reply}\n(offline mode: {exc})"
        return jsonify({"reply": reply})

    return fallback


# ----------------------------------------------------------------------
# 2. Run Flask in a background thread
# ----------------------------------------------------------------------
def start_server():
    app = get_flask_app()

    def run():
        app.run(host="127.0.0.1", port=PORT, threaded=True,
                debug=False, use_reloader=False)

    threading.Thread(target=run, daemon=True).start()

    for _ in range(100):  # wait up to ~10s for the port to open
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.1)
    return False


# ----------------------------------------------------------------------
# 3. Show it
# ----------------------------------------------------------------------
def show_webview(url):
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread  # noqa

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    WebView = autoclass("android.webkit.WebView")
    WebViewClient = autoclass("android.webkit.WebViewClient")
    activity = PythonActivity.mActivity

    @run_on_ui_thread
    def create():
        webview = WebView(activity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        settings.setMediaPlaybackRequiresUserGesture(False)
        webview.setWebViewClient(WebViewClient())
        activity.setContentView(cast("android.view.View", webview))
        webview.loadUrl(url)

    create()


def show_kivy(url, ok):
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button

    class AltronApp(App):
        title = APP_NAME

        def build(self):
            box = BoxLayout(orientation="vertical", padding=24, spacing=16)
            box.add_widget(Label(text=f"[b]ALTRON[/b]\nby {DEVELOPER}",
                                 markup=True, halign="center"))
            box.add_widget(Label(text=("Assistant running at\n" + url) if ok
                                 else "Assistant failed to start."))
            btn = Button(text="Open Altron", size_hint_y=0.25)
            btn.bind(on_release=lambda *_: open_browser(url))
            box.add_widget(btn)
            return box

    AltronApp().run()


def open_browser(url):
    try:
        import webbrowser

        webbrowser.open(url)
    except Exception as exc:
        print(f"[{APP_NAME}] cannot open browser: {exc}")


if __name__ == "__main__":
    started = start_server()
    target = f"http://127.0.0.1:{PORT}/"
    print(f"[{APP_NAME}] server started={started} url={target}")
    try:
        show_webview(target)
        while True:  # keep the Python side alive behind the WebView
            time.sleep(1)
    except Exception as exc:
        print(f"[{APP_NAME}] WebView unavailable ({exc}); using Kivy screen")
        show_kivy(target, started)
