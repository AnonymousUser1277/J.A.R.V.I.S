# 🤖 JARVIS - Just A Rather Very Intelligent System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**A powerful AI-powered voice assistant inspired by Iron Man's JARVIS**

[Features](#-features) • [Installation](#-installation) • [Configuration](#-configuration) • [Usage](#-usage) • [Documentation](#-documentation)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Advanced Features](#-advanced-features)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

JARVIS is a sophisticated desktop AI assistant for Windows that combines voice recognition, natural language processing, and system automation. Built with Python, it offers a modular architecture supporting multiple AI providers and extensive customization options.

### What Makes JARVIS Special?

- **🎯 Multi-AI Provider Support** - Seamlessly switches between Cohere, Groq, HuggingFace, OpenRouter, Mistral, and Gemini
- **🎤 Advanced Voice Control** - Wake word detection, real-time speech-to-text, and natural text-to-speech
- **👁️ Vision Capabilities** - Screen capture and camera analysis using Gemini Vision
- **🧠 Context Awareness** - Monitors browser, clipboard, file explorer, system performance, and more
- **🎨 Modern UI** - Dark-themed interface with animated control orb and persistent terminal
- **📊 Proactive Notifications** - Smart alerts for battery, downloads, network, devices, and system resources
- **🔐 Face Recognition** - Secure authentication using facial recognition

---

## ✨ Features

### Core Capabilities

#### 🎙️ Voice Interaction
- **Wake Word Detection** - Activate with "Hey JARVIS" (customizable)
- **Real-time Speech Recognition** - Browser-based STT with automatic fallback
- **Natural Text-to-Speech** - Windows SAPI with multiple voice options
- **Volume Auto-Ducking** - Automatically lowers system volume during listening

#### 🤖 AI Integration
- **Multi-Provider Architecture** - Automatic failover between AI providers
- **Smart Caching System** - Redis-based response caching with acceptance workflow
- **Code Generation** - Generates and executes Python code for complex tasks
- **Vision Processing** - Analyzes screen content and camera input

#### 📊 Context Monitoring
- **Browser Tracking** - Current URL via extension + UI automation fallback
- **File Explorer** - Active folder monitoring
- **Clipboard** - Event-driven clipboard tracking
- **System Metrics** - CPU, RAM, disk, temperature monitoring
- **Network Status** - WiFi SSID and connectivity tracking
- **Device Detection** - USB, HDMI, Bluetooth device monitoring
- **Battery Status** - Level and charging state tracking

#### 🛠️ Automation Features
- **Task Scheduling** - Schedule commands with natural language ("remind me in 2 hours")
- **OCR Integration** - Click and interact with screen text via Tesseract
- **Document Generation** - Create Word, Markdown, and text documents
- **Image Generation** - Generate images using HuggingFace models
- **Command Aliases** - Create shortcuts for frequently used commands
- **File Management** - Handle multiple files in prompts with content reading

#### 🎨 User Interface
- **Animated Control Orb** - Dynamic visual states (idle/listening/processing)
- **Persistent Terminal** - Scrolling message display with auto-fade
- **Code Viewer** - View generated code with syntax highlighting
- **Cache Editor** - Visual JSON editor for response cache
- **Settings Dialog** - Comprehensive configuration interface
- **Theme System** - Multiple color schemes (Dark, Light, Matrix, Cyberpunk)
- **System Tray** - Background operation with quick access menu

---

## 🏗️ Architecture

```
JARVIS/
├── ai/                      # AI processing core
│   ├── providers.py         # Multi-provider management with failover
│   ├── instructions.py      # Prompt generation and code execution
│   ├── vision.py            # Gemini-based vision processing
│   ├── redis_cache.py       # Response caching system
│   ├── ImageGeneration.py   # HuggingFace image generation
│   └── proactive.py         # Proactive suggestion engine
│
├── audio/                   # Audio processing
│   ├── stt.py               # Speech-to-text (Selenium-based)
│   ├── stt_fallback.py      # Backup STT system
│   ├── tts_native.py        # Windows SAPI TTS
│   ├── volume.py            # Volume control
│   └── coordinator.py       # STT/TTS coordination
│
├── automation/              # System automation
│   ├── executor.py          # Code execution engine
│   ├── screen.py            # OCR and screen interaction
│   └── hotkeys.py           # Global hotkey management
│
├── core/                    # Core functionality
│   ├── context_manager.py   # System context tracking
│   ├── notification.py      # Proactive notifications
│   ├── task_scheduler.py    # Task scheduling system
│   ├── auth.py              # Face recognition auth
│   └── local_server.py      # Browser extension server
│
├── monitors/                # Context monitors
│   ├── browser.py           # Browser URL tracking
│   ├── clipboard.py         # Clipboard monitoring
│   ├── explorer.py          # File explorer tracking
│   ├── system.py            # System metrics
│   └── devices.py           # Device detection
│
├── ui/                      # User interface
│   ├── gui.py               # Main GUI handler
│   ├── terminal.py          # Persistent terminal
│   ├── startup.py           # Startup screen
│   ├── settings_dialog.py   # Configuration UI
│   ├── cache_editor.py      # Cache management UI
│   └── theme_manager.py     # Theme system
│
├── config/                  # Configuration
│   ├── loader.py            # Config file loader
│   ├── api_keys.py          # API key management
│   └── settings.py          # Settings constants
│
├── integrations/            # External integrations
│   ├── gmail_integration.py # Gmail IMAP/SMTP
│   └── calendar_integration.py # iCal calendar
│
├── utils/                   # Utilities
│   ├── setup_wizard.py      # First-time setup
│   ├── logger.py            # Logging system
│   └── file_manager.py      # File handling
│
├── browser_extension/       # Chrome extension
│   ├── manifest.json        # Extension manifest
│   └── background.js        # URL tracking script
│
├── main.py                  # Application entry point
├── config.ini               # Configuration file
└── .env                     # API keys (not in repo)
```

---

## 📦 Prerequisites

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for installation + cache
- **Internet**: Required for AI providers and features

### Required Software
1. **Python 3.8+** - [Download](https://www.python.org/downloads/)
2. **Redis** - [Download](https://github.com/microsoftarchive/redis/releases)
3. **Tesseract OCR** - [Download](https://github.com/UB-Mannheim/tesseract/wiki)
4. **Chrome/Edge Browser** - For speech recognition

---

## 🚀 Installation

### Method 1: Automated Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/JARVIS.git
cd JARVIS

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Redis (Windows)
# Download and install from: https://github.com/microsoftarchive/redis/releases
# Or use Chocolatey:
choco install redis-64

# 4. Start Redis server
redis-server

# 5. Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Default path: C:\Program Files\Tesseract-OCR\tesseract.exe

# 6. Run setup wizard
python main.py
```

The setup wizard will guide you through:
- ✅ API key configuration
- ✅ System settings
- ✅ Face registration
- ✅ Audio preferences
- ✅ Startup configuration

### Method 2: Manual Setup

1. **Create `.env` file** in project root:
```env
# Cohere API Keys
COHERE_KEY_1=your_key_here
COHERE_KEY_2=
COHERE_KEY_3=

# Groq API Keys
GROQ_KEY_1=your_key_here
GROQ_KEY_2=
GROQ_KEY_3=

# HuggingFace API Keys
HUGGINGFACE_KEY_1=your_key_here
HUGGINGFACE_KEY_2=
HUGGINGFACE_KEY_3=

# OpenRouter API Keys
OPENROUTER_KEY_1=your_key_here
OPENROUTER_KEY_2=
OPENROUTER_KEY_3=

# Mistral API Key
MISTRAL_KEY_1=your_key_here

# Gemini API Keys
GEMINI_KEY_1=your_key_here
GEMINI_KEY_2=
GEMINI_KEY_3=
```

2. **Create `config.ini`** (see `config.ini.example` for template)

3. **Install browser extension** (optional but recommended):
   - Open Chrome/Edge
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `JARVIS/browser_extension/` folder

---

## ⚙️ Configuration

### Essential Settings

Edit `config.ini`:

```ini
[Paths]
Program_path = C:\path\to\JARVIS
tesseract_cmd = C:\Program Files\Tesseract-OCR\tesseract.exe

[Audio]
enable_stt = true
enable_tts = true
stt_website_url = https://realtime-stt-devs-do-code.netlify.app/
stt_language = en-IN
TTS_Voice = Ryan
Wake_word = jarvis

[Behavior]
confirm_ai_execution = false
auto_tts_output = true
dev_mode = false
hide_console_window = true

[Integrations]
calendar_url = https://calendar.google.com/calendar/ical/.../basic.ics
google_app_password = your_app_password
your_email_address = your.email@gmail.com
```

### Getting API Keys

| Provider | Free Tier | Get Key |
|----------|-----------|---------|
| Cohere | ✅ Yes | [cohere.com](https://cohere.com/) |
| Groq | ✅ Yes | [groq.com](https://groq.com/) |
| HuggingFace | ✅ Yes | [huggingface.co](https://huggingface.co/) |
| OpenRouter | ⚠️ Paid | [openrouter.ai](https://openrouter.ai/) |
| Mistral | ⚠️ Paid | [mistral.ai](https://mistral.ai/) |
| Gemini | ✅ Free tier | [ai.google.dev](https://ai.google.dev/) |

**Recommendation**: At minimum, configure Cohere + Groq + Gemini for free usage.

---

## 🎯 Usage

### Starting JARVIS

```bash
# Method 1: Direct execution
python main.py

# Method 2: Use batch file
Jarvis.bat

# Method 3: Run as admin (for full features)
# Right-click Jarvis.bat → Run as administrator
```

### Basic Voice Commands

```
"Hey JARVIS" or "JARVIS"          - Wake word activation
"Open Chrome"                     - Launch applications
"What's the weather today?"       - Information queries
"Create a Python script to..."    - Code generation
"What do you see on my screen?"   - Vision analysis
"Click on Submit button"          - UI automation
"Generate an image of a sunset"   - Image generation
"Remind me in 1 hour to..."       - Task scheduling
"Search for Python tutorials"     - Web searches
"Send email to john@example.com"  - Email operations
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Win + Enter` | Toggle microphone |
| `Win + Space` | Open text input dialog |
| `Alt + Shift + C` | View generated code |
| `Escape` | Exit fullscreen dialogs |

### System Tray Menu

Right-click the system tray icon for quick access to:
- 📅 Show scheduled tasks
- 📊 View current context
- 📺 Select monitor
- 📝 Edit cache
- 💻 Open project in VS Code
- 🗄️ View logs
- 💡 Suggestions
- ⚙️ Settings
- 🔄 Restart
- ❌ Exit

---

## 🔥 Advanced Features

### Task Scheduling

Schedule commands with natural language:

```python
# Voice commands
"Remind me to call mom in 2 hours"
"Every day at 9 AM open my email"
"Schedule a meeting tomorrow at 3 PM"
"Every Monday at 10 AM run backup"
```

### Command Aliases

Create shortcuts for frequently used commands:

1. Open system tray → "Command Aliases"
2. Add alias: `email` → `open gmail`
3. Use: Just say "email"

### Vision Analysis

JARVIS can analyze:
- **Screen content** - "What's on my screen?"
- **Camera input** - "What do you see?"
- **Specific regions** - Programmatically specify areas
- **Code review** - "Review this code" (with code on screen)

### Proactive Suggestions

JARVIS learns your patterns and suggests:
- ⏰ Time-based actions (morning emails, EOD tasks)
- 🔋 Battery management (save work when low)
- 📊 Workflow optimization (common app sequences)
- 🎯 Context-aware actions (create charts from data)

### Parallel Task Processing

Queue multiple commands:

```
"Background search for Python tutorials"
"Background download that file"
"Normal priority: send this email"
```

---

## 🐛 Troubleshooting

### Common Issues

#### STT Not Working
```bash
# Check Chrome/ChromeDriver processes
tasklist | findstr chrome

# Kill stuck processes
taskkill /F /IM chrome.exe /T
taskkill /F /IM chromedriver.exe /T

# Clear temp files
cd %TEMP%
del /s /q jarvis_stt_*
```

#### TTS Not Speaking
```bash
# Verify Windows SAPI voices
powershell "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices().VoiceInfo.Name"

# Reinstall if needed
# Control Panel → Speech → Text to Speech
```

#### API Errors
```bash
# Check Redis is running
redis-cli ping

# View logs
cd JARVIS/Data/logs
type 2024-01-01.log

# Test API keys
python -c "from config.api_keys import *; print(COHERE_KEYS)"
```

#### Cache Issues
```bash
# Clear Redis cache
redis-cli FLUSHDB

# Or use GUI: System Tray → Edit Cache → Clear All
```

### Performance Optimization

1. **Reduce Monitor Polling** - Edit `config.ini` [Monitors] section
2. **Disable Unused Features** - Set `enable_stt=false` or `enable_tts=false`
3. **Increase Cache** - Adjust `redis.conf` maxmemory setting
4. **Close Background Apps** - JARVIS works best with available RAM

### Debug Mode

Enable detailed logging:

```ini
[Behavior]
dev_mode = true
hide_console_window = false
```

Logs location: `JARVIS/Data/logs/YYYY-MM-DD.log`

---

## 📚 Documentation

### AI Instruction Customization

Edit AI behavior in Settings → AI Instruction tab:

```python
# Current instruction template in ai/instructions.py
full_prompt = f"""
You are a python code generator for {operating_system} OS.
Return ONLY pure python code without comments.
... [customize behavior here]
"""
```

### Adding Custom Settings

Use the Settings Dialog → "+Add Setting" tab to dynamically create new configuration options without editing code.

### MCP Integration

JARVIS supports Model Context Protocol (MCP) for extended capabilities. Tools are automatically detected and integrated.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/AmazingFeature`
3. **Commit changes**: `git commit -m 'Add AmazingFeature'`
4. **Push to branch**: `git push origin feature/AmazingFeature`
5. **Open a Pull Request**

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Enable dev mode
# In config.ini: dev_mode = true

# Code will auto-reload on save
```

### Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to functions
- Keep functions under 50 lines
- Write descriptive commit messages

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - For AI research and inspiration
- **Cohere, Groq, HuggingFace** - For AI model APIs
- **Tesseract** - For OCR capabilities
- **Redis** - For caching system
- **Python Community** - For amazing libraries

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/JARVIS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/JARVIS/discussions)
- **Email**: your.email@example.com

---

## 🗺️ Roadmap

- [ ] Linux/macOS support
- [ ] Mobile companion app
- [ ] Custom wake word training
- [ ] Plugin system for extensions
- [ ] Cloud sync for settings
- [ ] Multi-language support
- [ ] Voice cloning for TTS
- [ ] Advanced automation workflows

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by [Your Name]

</div>
