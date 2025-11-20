# JARVIS - Just A Rather Very Intelligent System

<div align="center">

![JARVIS](https://img.shields.io/badge/JARVIS-AI%20Assistant-00ff00?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows)

**An advanced AI-powered desktop assistant with voice control, context awareness, and intelligent automation**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration) • [Architecture](#-architecture)

</div>

---

## 🌟 Features

### 🎤 Voice & Speech
- **Wake Word Detection**: Always-listening "Jarvis" wake word activation
- **Multi-Provider Speech-to-Text**: Web-based STT with automatic fallback system
- **Natural Text-to-Speech**: Microsoft Edge TTS with multiple voice options
- **Voice Commands**: Hands-free control with natural language processing

### 🧠 AI Intelligence
- **Multi-AI Provider Support**: Automatic failover between Cohere, Groq, Gemini, HuggingFace, OpenRouter, and Mistral
- **Vision Capabilities**: Screen and camera analysis using Gemini 2.0
- **Smart Caching**: SQLite-based cache system with acceptance workflow
- **Context-Aware**: Understands browser URLs, active windows, clipboard, and system state

### 🖥️ System Integration
- **12 Real-Time Monitors**:
  - Browser URL tracking (via Chrome/Edge extension)
  - File Explorer path monitoring
  - Clipboard content tracking
  - Active window detection
  - Downloads folder monitoring
  - System performance (CPU, RAM, Disk)
  - Battery status
  - Network connectivity & WiFi
  - USB/HDMI device detection
  - Bluetooth devices
  - User idle time detection

### 🎨 User Interface
- **Animated JARVIS Orb**: Dynamic, pulsing control interface with state indicators
- **Persistent Terminal**: Non-intrusive floating message system
- **Code View Dialog**: Alt+Shift+C to view generated code
- **System Tray Integration**: Quick access to settings and controls
- **Blur Effects**: Modern glassmorphism UI design

### 🤖 Automation
- **Code Generation**: AI generates Python code to execute tasks
- **OCR Integration**: Click/move cursor to any text on screen
- **Image Generation**: Text-to-image via HuggingFace models
- **Hotkeys**: Win+Space (input), Win+Enter (mic toggle)
- **File Upload**: Attach files to prompts for AI processing

### 🔒 Security
- **Face Recognition**: Optional facial authentication on startup
- **Admin Detection**: Runs with appropriate privileges
- **Destructive Command Warnings**: Confirmations for dangerous operations

---

## 📋 Requirements

- **OS**: Windows 10/11
- **Python**: 3.8 or higher
- **Hardware**: Webcam (for vision/auth), Microphone (for voice)
- **Software**: 
  - Tesseract OCR
  - Google Chrome/Edge (for STT/TTS)

---

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/JARVIS.git
cd JARVIS
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install External Dependencies

#### Tesseract OCR
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 4. Configure API Keys
Create a `.env` file in the project root:

```env
# AI Providers (add at least one)
COHERE_KEY_1=your_cohere_key
GROQ_KEY_1=your_groq_key
GEMINI_KEY_1=your_gemini_key
HUGGINGFACE_KEY_1=your_huggingface_key

# Optional: Additional keys for failover
COHERE_KEY_2=backup_key
GROQ_KEY_2=backup_key
```

### 5. Install Browser Extension (Optional)
Load the `browser_extension` folder as an unpacked extension in Chrome/Edge for automatic URL tracking.

**Chrome/Edge**: 
1. Navigate to `chrome://extensions` or `edge://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `JARVIS/browser_extension` folder

---

## 🎮 Usage

### First Run
```bash
python main.py
```

On first run, JARVIS will:
1. Request face registration for authentication
2. Initialize AI providers
3. Start all monitoring systems
4. Launch the control interface

### Voice Commands
Say **"Jarvis"** followed by your command:
- "Jarvis, open YouTube"
- "Jarvis, what's on my screen?"
- "Jarvis, bookmark this page"
- "Jarvis, send a message to John"

### Manual Input
- **Win + Space**: Open text input dialog
- **Click the orb**: Toggle voice recording
- **Alt + Shift + C**: View last generated code

### System Tray
Right-click the tray icon for:
- Edit cache
- Edit configuration
- Open logs folder
- Restart/Exit

---

## ⚙️ Configuration

Edit `config.ini` to customize behavior:

```ini
[Audio]
enable_stt = true
enable_tts = true
assistant_voice = en-GB-RyanNeural
stt_language = en-IN

[Behavior]
confirm_ai_execution = false
auto_tts_output = true
dev_mode = false

[Monitors]
# Polling intervals (seconds)
browser_url_poll = 1.0
clipboard_poll = 2.0
performance_poll = 10.0
```

### Key Settings:
- `enable_stt`: Voice input on/off
- `enable_tts`: Voice output on/off
- `confirm_ai_execution`: Require confirmation before running generated code
- `auto_tts_output`: Speak the last printed output from code
- `dev_mode`: Enable file watcher for auto-reload during development

---

## 🏗️ Architecture

### Project Structure
```
JARVIS/
├── main.py                 # Entry point
├── config.ini              # User configuration
├── requirements.txt        # Python dependencies
│
├── ai/                     # AI processing
│   ├── providers.py        # Multi-provider system with failover
│   ├── instructions.py     # Command processing & code generation
│   ├── vision.py           # Screen/camera analysis
│   ├── cache.py            # SQLite cache system
│   └── ImageGeneration.py  # Text-to-image
│
├── audio/                  # Audio systems
│   ├── stt.py              # Speech-to-Text (Selenium-based)
│   ├── stt_fallback.py     # Backup STT with auto-recovery
│   ├── tts_selenium.py     # Text-to-Speech engine
│   ├── coordinator.py      # Prevents STT/TTS conflicts
│   └── volume.py           # System volume control
│
├── ui/                     # User interface
│   ├── gui.py              # Main GUI with animated orb
│   ├── terminal.py         # Floating message system
│   ├── dialogs.py          # Input/response dialogs
│   ├── cache_editor.py     # Visual cache editor
│   └── tray.py             # System tray icon
│
├── core/                   # Core functionality
│   ├── context_manager.py  # Central context hub
│   ├── notification.py     # Proactive alerts
│   ├── auth.py             # Face recognition
│   └── local_server.py     # Browser extension server
│
├── monitors/               # System monitors
│   ├── clipboard.py
│   ├── explorer.py
│   ├── window.py
│   ├── system.py           # Performance, battery, network
│   └── devices.py          # USB, HDMI, Bluetooth
│
├── automation/             # Automation tools
│   ├── executor.py         # Safe code execution
│   ├── screen.py           # OCR & screen interaction
│   └── hotkeys.py          # Global hotkey manager
│
├── config/                 # Configuration
│   ├── settings.py
│   ├── api_keys.py
│   └── loader.py
│
└── utils/                  # Utilities
    ├── logger.py
    ├── file_manager.py
    └── decorators.py
```

### Key Components

#### Multi-AI Failover System
```python
# Automatic provider switching on failure
Cohere → Groq → HuggingFace → OpenRouter → Mistral → (cycle)
```

#### Context System
12 real-time monitors feed into a central `ContextManager` that provides AI with:
- Current browser page
- Active folder path
- Clipboard content
- System performance
- Connected devices
- And more...

#### Cache System
- SQLite-based for performance
- Acceptance workflow (accept/reject/edit)
- Prevents duplicate executions
- Visual JSON editor included

---

## 🧪 Advanced Features

### Vision Analysis
```python
# Say: "Jarvis, what do you see?"
# JARVIS captures screen + webcam → Gemini 2.0 analysis
```

### Code Generation
```python
# Say: "Jarvis, create a backup of my Downloads folder"
# JARVIS generates Python code → Executes safely → Reports result
```

### Proactive Notifications
- Low battery alerts
- Download completion notices
- Device connection/disconnection
- Network status changes

### File Upload Support
Attach files to prompts for:
- Code review
- Document analysis
- Data processing
- Image manipulation

---

## 🔧 Development

### File Watcher (Dev Mode)
Set `dev_mode = true` in `config.ini` to enable auto-reload on file changes.

### Logging
Logs saved to `Data/logs/YYYY-MM-DD.log` with rotation (5MB max, 5 backups).

### Cache Management
- **View**: System tray → Edit Cache
- **Format**: JSON with syntax highlighting
- **Search**: Ctrl+F, F3 (next), Shift+F3 (previous)

---

## 🐛 Troubleshooting

### STT Not Working
- Check `enable_stt = true` in config.ini
- Ensure microphone permissions granted
- Try restarting JARVIS

### TTS Not Working
- Check `enable_tts = true` in config.ini
- Verify internet connection (Edge TTS requires online)
- Check logs for ChromeDriver errors

### AI Provider Failures
- Verify API keys in `.env`
- Check rate limits on provider dashboards
- JARVIS will automatically try backup providers

### Vision Not Working
- Ensure webcam connected and accessible
- Check Gemini API keys
- Vision queries must include phrases like "see", "look at", "what's on screen"

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- **AI Providers**: Cohere, Groq, Google (Gemini), HuggingFace, OpenRouter, Mistral
- **TTS**: Microsoft Edge TTS
- **OCR**: Tesseract OCR
- **UI Inspiration**: Marvel's JARVIS

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs in `Data/logs/`

---

<div align="center">

**Built with ❤️ by Nandlal Pandit**

⭐ Star this repo if you find it helpful!

</div>