Jarvis AI Assistant
A Python-based voice-activated AI assistant and automation tool built on resource-constrained hardware (ARM64 Android via Termux). Designed and developed entirely on a mobile device as a demonstration of system integration, API orchestration, and self-directed software engineering.
🎯 Project Purpose
Jarvis was built to solve a real personal need — having an intelligent, voice-controlled assistant available without relying on cloud-dependent commercial tools. It also serves as a practical portfolio project demonstrating Python development, AI API integration, and modular system design.
✨ Features
🎤 Voice Activation — Wake word detection and voice command processing
🤖 AI Conversation — Natural language responses powered by Groq LLaMA and Google Gemini
🌐 Flask Web Interface — Local browser-based control panel and chat interface
📄 OCR Document Processing — Extract and process text from images and documents
🔊 Text-to-Speech — Spoken responses for hands-free operation
📝 Logging System — Conversation and activity logs for review and debugging
🧠 Knowledge Base — Local knowledge files for domain-specific queries
🛠️ Tech Stack
Category
Technology
Language
Python 3
Web Framework
Flask
AI APIs
Groq (LLaMA 3.1), Google Gemini, Anthropic Claude
Voice Input
Android microphone via Termux API
Text-to-Speech
Termux TTS / Android TTS engine
OCR
Tesseract via pytesseract
Platform
Android (Termux) — ARM64
Shell
Bash
📁 Project Structure
Jarvis/
├── jarvis.py              # Main application entry point
├── app.py                 # Flask web interface
├── config.py              # API keys and configuration
├── modules/
│   ├── voice.py           # Voice recording and recognition
│   ├── ai_handler.py      # AI API integration and routing
│   ├── ocr.py             # Document and image processing
│   └── tts.py             # Text-to-speech output
├── knowledge/             # Local knowledge base files
├── jarvis_logs/           # Conversation and activity logs
├── templates/             # Flask HTML templates
└── requirements.txt       # Python dependencies
⚙️ Installation
Note: This project is designed to run on Android via Termux (ARM64). Some Python packages that require Rust compilation are not compatible and are intentionally avoided.
Requirements:
Android device with Termux installed
Termux:API add-on
Python 3.x
Active API keys for Groq and/or Google Gemini
Setup:
# Clone the repository
git clone https://github.com/MarkFrencerLozada/jarvis.git
cd jarvis

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config.example.py config.py
# Edit config.py with your API keys

# Run Jarvis
python jarvis.py
🔑 API Keys Required
Groq API — Free tier available
Google Gemini API — Free tier available
Anthropic Claude API — Optional
API keys are stored in config.py which is excluded from this repository via .gitignore.
💡 Design Decisions
No Rust-compiled packages — pymupdf, pdfplumber, faster-whisper, and groq SDK are intentionally excluded due to ARM64 compilation failures. HTTP requests are used directly instead.
Lightweight architecture — Designed to run efficiently on a mid-range Android device with limited RAM
Modular design — Each feature is isolated in its own module for easy debugging and expansion
🚧 Current Status
Active development. Core features are functional. Ongoing improvements to voice pipeline stability and AI response handling.
👤 Author
Mark Frencer Lozada — Registered Electrical Engineer | ETO | Python Developer
🔗 LinkedIn (update with actual URL)
🐙 GitHub
📄 License
This project is licensed under the MIT License — see the LICENSE file for details.
