"""
JARVIS First-Time Setup Wizard
Guides new users through initial configuration
File: utils/setup_wizard.py

⚠️ IMPORTANT: This module must NOT import any JARVIS config modules
to avoid circular dependencies during first-time setup.
"""

import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import configparser
from typing import Dict, List, Tuple
import subprocess 
import threading 
import queue 

class SetupWizard:
    """Interactive setup wizard for first-time users"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 JARVIS Setup Wizard")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.configure(bg='#0a0a0a')
        self.root.geometry("900x700")
        self.root.resizable(False,False)
        
        # Center window
        self._center_window()
        
        # Data storage
        self.api_keys = {}
        self.config_values = {}
        self.current_step = 0  # This will now be an index for our steps list
        self.install_queue = queue.Queue() # Queue for thread communication
        self.is_installing = False #  Flag to track installation status
        # Project paths
        self.project_root = Path(__file__).parent.parent
        self.env_path = self.project_root / '.env'
        self.config_path = self.project_root / 'config.ini'
        self.face_path = self.project_root / 'known_face.npy'
        self.req_path = self.project_root / 'requirements.txt'
        self._load_existing_env_file()
        # --- Build a dynamic list of steps to run ---
        self.steps_to_run = [self._show_welcome]
        if self.req_path.exists():
            self.steps_to_run.append(self._show_requirements_install)
        if not self.env_path.exists():
            self.steps_to_run.append(self._show_api_keys)
        if not self.config_path.exists():
            self.steps_to_run.append(self._show_settings)
        # The face setup screen has its own check, but we can skip the whole step
        if not self.face_path.exists():
            self.steps_to_run.append(self._show_face_setup)
        self.steps_to_run.append(self._show_startup_setup)
        self.steps_to_run.append(self._show_finish)
        
        self.total_steps = len(self.steps_to_run)
        
        # Setup UI
        self._create_ui()
        
        # Start with welcome
        self._show_welcome()
    def _escape_ini_value(self, value: str) -> str:
        """Escape % characters in config.ini values to prevent parser errors"""
        return value.replace('%', '%%')
    def _show_startup_setup(self):
        """Show the startup preference screen."""
        self._clear_content()
        self._update_progress()
        self.skip_btn.pack_forget()  # This step is not optional

        tk.Label(
            self.content_frame,
            text="🚀 Run on Startup",
            font=("Arial", 18, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        ).pack(pady=(20, 10))

        tk.Label(
            self.content_frame,
            text="Would you like JARVIS to start automatically when you log in to Windows?",
            font=("Arial", 11),
            bg='#0a0a0a',
            fg='#cccccc',
            wraplength=700
        ).pack(pady=(0, 30))

        # Checkbox for the decision, defaulted to 'Yes'
        self.run_on_startup_var = tk.BooleanVar(value=True)
        
        cb = tk.Checkbutton(
            self.content_frame,
            text="Yes, add JARVIS to my startup programs.",
            variable=self.run_on_startup_var,
            font=("Arial", 12, "bold"),
            bg='#1a1a1a',
            fg='#cccccc',
            selectcolor='#0a0a0a',
            activebackground='#1a1a1a',
            activeforeground='#00ff00',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        cb.pack(pady=20)
    
    def _handle_startup_choice(self):
        """Creates a true .lnk shortcut file and places it in the startup folder."""
        try:
            # We need the winshell library to create .lnk files
            import winshell

            # Path to the Windows Startup folder
            startup_folder = Path(winshell.startup())
            
            # Path to the original .bat file in your project
            source_bat_file = self.project_root / 'Jarvis.bat'
            
            # Define the name for the .lnk shortcut file
            shortcut_name = 'JARVIS.lnk'
            destination_shortcut_file = startup_folder / shortcut_name

            if self.run_on_startup_var.get():
                # --- User wants to ADD to startup ---

                # 1. Check if the original Jarvis.bat exists
                if not source_bat_file.exists():
                    messagebox.showwarning("File Not Found", f"Could not find 'Jarvis.bat' in the project root:\n{source_bat_file}", parent=self.root)
                    return

                # 2. Get the full, absolute path to the original .bat file
                absolute_path_to_original = str(source_bat_file.resolve())

                # 3. Create the .lnk shortcut
                with winshell.shortcut(str(destination_shortcut_file)) as shortcut:
                    shortcut.path = absolute_path_to_original
                    shortcut.working_directory = str(self.project_root)
                    shortcut.description = "Starts the JARVIS application."
                    # You can even assign an icon if you have one
                    # shortcut.icon_location = (str(self.project_root / 'icon.ico'), 0)
                
                print(f"✅ Created startup shortcut at: {destination_shortcut_file}")

            else:
                # --- User does NOT want to add to startup, so we REMOVE the shortcut if it exists ---
                if destination_shortcut_file.exists():
                    os.remove(destination_shortcut_file)
                    print(f"🗑️ Removed startup shortcut: {destination_shortcut_file}")

        except ImportError:
             messagebox.showerror("Missing Library", "The 'winshell' library is required to create startup shortcuts.\nPlease install it by running: pip install winshell", parent=self.root)
        except Exception as e:
            messagebox.showerror("Startup Error", f"An error occurred while configuring startup settings:\n{e}", parent=self.root)
    def _center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = 900
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_ui(self):
        """Create main UI structure"""
        # Header
        header = tk.Frame(self.root, bg='#1a1a1a', height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🤖 JARVIS Setup Wizard",
            font=("Arial", 24, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(pady=30)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.root, bg='#0a0a0a', height=60)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Step 1 of 4",
            font=("Arial", 11),
            bg='#0a0a0a',
            fg='#cccccc'
        )
        self.progress_label.pack(pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            length=800,
            mode='determinate',
            maximum=self.total_steps
        )
        self.progress_bar.pack(pady=5)
        
        # Content area (scrollable)
        self.content_canvas = tk.Canvas(self.root, bg='#0a0a0a', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.content_canvas.yview)
        self.content_frame = tk.Frame(self.content_canvas, bg='#0a0a0a')
        
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        )
        
        self.content_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.content_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Button frame with better visibility
        self.button_frame = tk.Frame(self.root, bg='#1a1a1a', height=80)
        # --- CORRECTION: Pack the bottom frame FIRST ---
        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # --- CORRECTION: Now pack the canvas and scrollbar to fill the middle ---
        scrollbar.pack(side="right", fill="y")
        self.content_canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.button_frame.pack_propagate(False)
        
        # Add a separator line
        separator = tk.Frame(self.button_frame, bg='#00ff00', height=2)
        separator.pack(fill=tk.X, side=tk.TOP)
        
        btn_style = {
            'font': ("Arial", 12, "bold"),
            'relief': 'flat',
            'cursor': 'hand2',
            'padx': 30,
            'pady': 12,
            'borderwidth': 2
        }
        
        # Button container for centering
        btn_container = tk.Frame(self.button_frame, bg='#1a1a1a')
        btn_container.pack(expand=True, fill=tk.BOTH)
        
        self.back_btn = tk.Button(
            btn_container,
            text="← Back",
            bg='#2d2d2d',
            fg='#cccccc',
            activebackground='#3d3d3d',
            activeforeground='#ffffff',
            command=self._go_back,
            **btn_style
        )
        self.back_btn.pack(side=tk.LEFT, padx=20, pady=20)
        
        self.skip_btn = tk.Button(
            btn_container,
            text="Skip (Optional)",
            bg='#2d2d2d',
            fg='#ffaa00',
            activebackground='#ffaa00',
            activeforeground='#000000',
            command=self._skip_step,
            **btn_style
        )
        self.skip_btn.pack(side=tk.RIGHT, padx=5, pady=20)
        
        self.next_btn = tk.Button(
            btn_container,
            text="Next →",
            bg='#00ff00',
            fg='#000000',
            activebackground='#00cc00',
            activeforeground='#000000',
            command=self._go_next,
            **btn_style
        )
        self.next_btn.pack(side=tk.RIGHT, padx=20, pady=20)
    def _load_existing_env_file(self):
        """If a .env file already exists, load its contents into self.api_keys."""
        if not self.env_path.exists():
            return  # Do nothing if the file isn't there
        
        print(f"✅ Found existing .env file, loading keys...")
        try:
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.api_keys[key.strip()] = value.strip()
            print(f"   -> Loaded {len(self.api_keys)} API keys.")
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing .env file. Error: {e}")
    def _clear_content(self):
        """Clear content area"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _update_progress(self):
        """Update progress bar and label"""
        # --- CHANGE THIS LINE to use current_step + 1 for the value ---
        self.progress_bar['value'] = self.current_step + 1
        self.progress_label.config(text=f"Step {self.current_step + 1} of {self.total_steps}")
        
        # Update button states
        self.back_btn.config(state='normal' if self.current_step > 0 else 'disabled')
        
        # --- CHANGE THIS LINE to check if the current step is the last one ---
        if self.current_step == self.total_steps - 1:
            self.next_btn.config(text="Finish 🎉", bg='#00ff00', fg='#000000')
        else:
            self.next_btn.config(text="Next →", bg='#00ff00', fg='#000000')
    
    # =============== STEP 0: WELCOME ===============
    
    def _show_welcome(self):
        """Show welcome screen"""
        self._clear_content()
        self._update_progress()
        
        # Welcome message
        welcome_frame = tk.Frame(self.content_frame, bg='#1a1a1a', padx=40, pady=40)
        welcome_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        tk.Label(
            welcome_frame,
            text="👋 Welcome to JARVIS!",
            font=("Arial", 20, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(pady=(0, 20))
        
        tk.Label(
            welcome_frame,
            text="This wizard will help you set up JARVIS for the first time.\n\n"
                 "We'll configure:\n"
                 "• API Keys for AI providers\n"
                 "• System settings\n"
                 "• Audio preferences\n"
                 "• Face recognition for authentication\n\n"
                 "The process takes about 5 minutes.\n"
                 "You can skip optional steps if needed.",
            font=("Arial", 12),
            bg='#1a1a1a',
            fg='#cccccc',
            justify=tk.LEFT
        ).pack(pady=10)
        
        # Requirements check
        self._show_requirements_check(welcome_frame)
        
        self.skip_btn.pack_forget()  # Hide skip on welcome
    
    def _show_requirements_check(self, parent):
        """Check and display requirements status"""
        check_frame = tk.Frame(parent, bg='#0a0a0a', padx=20, pady=20)
        check_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(
            check_frame,
            text="📋 Pre-flight Check:",
            font=("Arial", 12, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        ).pack(anchor='w', pady=(0, 10))
        
        checks = [
            (".env file", self.env_path.exists()),
            ("config.ini file", self.config_path.exists()),
            ("Face recognition", self.face_path.exists()),
        ]
        
        for name, exists in checks:
            status = "✅ Found" if exists else "❌ Missing"
            color = "#00ff00" if exists else "#ff4444"
            
            tk.Label(
                check_frame,
                text=f"{status} - {name}",
                font=("Arial", 11),
                bg='#0a0a0a',
                fg=color
            ).pack(anchor='w', pady=2)
    def _show_requirements_install(self):
        """Show requirements installation screen (Mandatory)"""
        self._clear_content()
        self._update_progress()
        
        # ⛔ MANDATORY: Hide skip button, Disable next button
        self.skip_btn.pack_forget() 
        self.next_btn.config(state='disabled')
        
        tk.Label(
            self.content_frame,
            text="📦 Install Dependencies",
            font=("Arial", 18, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        ).pack(pady=(20, 10))
        
        tk.Label(
            self.content_frame,
            text="JARVIS requires external libraries to function.\n"
                 "This step is mandatory and will install packages from requirements.txt.",
            font=("Arial", 11),
            bg='#0a0a0a',
            fg='#cccccc'
        ).pack(pady=(0, 20))

        # Install Button
        self.install_btn = tk.Button(
            self.content_frame,
            text="⬇️ Start Installation",
            font=("Arial", 12, "bold"),
            bg='#00ff00',
            fg='#000000',
            relief='flat',
            cursor='hand2',
            command=self._start_installation
        )
        self.install_btn.pack(pady=10)

        # Progress Bar
        self.install_progress = ttk.Progressbar(
            self.content_frame,
            length=600,
            mode='determinate'
        )
        self.install_progress.pack(pady=10)
        
        # Terminal Output Window
        output_container = tk.Frame(self.content_frame, bg='#1a1a1a', padx=2, pady=2)
        output_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        tk.Label(output_container, text="Installation Log:", bg='#1a1a1a', fg='#888888', font=("Arial", 8)).pack(anchor='nw')
        
        self.terminal_output = scrolledtext.ScrolledText(
            output_container,
            height=12,
            bg='#000000',
            fg='#00ff00',
            font=("Consolas", 9),
            state='disabled'
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True)
        
        # Estimate progress max based on line count of requirements.txt
        try:
            with open(self.req_path, 'r') as f:
                # Count non-empty lines that aren't comments
                lines = [line for line in f if line.strip() and not line.startswith('#')]
                # Multiply by 2 (download + install steps roughly)
                self.install_progress['maximum'] = len(lines) * 2 + 5
        except Exception:
            self.install_progress['maximum'] = 100

    def _start_installation(self):
        """Start the pip install process in a background thread"""
        self.install_btn.config(state='disabled', text="⏳ Installing... Please Wait")
        self.back_btn.config(state='disabled') # Lock navigation
        self.is_installing = True
        
        self._append_terminal("🚀 Starting installation process...\n")
        self._append_terminal(f"📂 Using requirements: {self.req_path}\n")
        self._append_terminal("-" * 40 + "\n")
        
        # Start thread
        threading.Thread(target=self._run_pip_install, daemon=True).start()
        
        # Start monitoring queue
        self.root.after(100, self._check_install_queue)

    def _run_pip_install(self):
        """Run pip install in subprocess and pipe output to queue"""
        # Use sys.executable to ensure we install in the CURRENT python environment
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(self.req_path)]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=self.project_root
            )
            
            # Read stdout line by line real-time
            for line in process.stdout:
                self.install_queue.put(("output", line))
                
            process.wait()
            
            if process.returncode == 0:
                self.install_queue.put(("done", True))
            else:
                self.install_queue.put(("done", False))
                
        except Exception as e:
            self.install_queue.put(("output", f"\n❌ Critical Error: {str(e)}\n"))
            self.install_queue.put(("done", False))

    def _check_install_queue(self):
        """Monitor the installation queue to update UI"""
        try:
            while True:
                msg_type, content = self.install_queue.get_nowait()
                
                if msg_type == "output":
                    self._append_terminal(content)
                    # Heuristic progress update based on keywords
                    lower_content = content.lower()
                    if "collecting" in lower_content or "installing" in lower_content or "satisfied" in lower_content:
                        try:
                            self.install_progress.step(1)
                        except: pass
                        
                elif msg_type == "done":
                    self.is_installing = False
                    success = content
                    
                    if success:
                        self._append_terminal("\n✅ ALL DEPENDENCIES INSTALLED SUCCESSFULLY!\n")
                        self.install_progress['value'] = self.install_progress['maximum']
                        self.install_btn.config(text="✅ Installed", bg='#2d2d2d', fg='#00ff00')
                        
                        # Enable navigation
                        self.next_btn.config(state='normal')
                        self.back_btn.config(state='normal')
                        
                        messagebox.showinfo("Success", "Dependencies installed successfully!\nYou may now proceed.", parent=self.root)
                    else:
                        self._append_terminal("\n❌ INSTALLATION FAILED.\nCheck the log above for errors.\n")
                        self.install_btn.config(state='normal', text="🔄 Retry Installation", bg='#ff4444')
                        self.back_btn.config(state='normal')
                        # Next button remains disabled
                    
                    return # Stop the loop

        except queue.Empty:
            pass
        
        if self.is_installing:
            self.root.after(100, self._check_install_queue)

    def _append_terminal(self, text: str):
        """Safely append text to the scrolled text widget"""
        self.terminal_output.config(state='normal')
        self.terminal_output.insert(tk.END, text)
        self.terminal_output.see(tk.END) # Auto scroll to bottom
        self.terminal_output.config(state='disabled')
    # =============== STEP 1: API KEYS ===============
    
    def _show_api_keys(self):
        """Show API keys configuration"""
        self._clear_content()
        self._update_progress()
        self.skip_btn.pack(side=tk.RIGHT, padx=5, pady=20)
        
        tk.Label(
            self.content_frame,
            text="🔑 Configure API Keys",
            font=("Arial", 18, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        ).pack(pady=(20, 10))
        
        tk.Label(
            self.content_frame,
            text="Enter your API keys for AI providers (at least one provider required):",
            font=("Arial", 11),
            bg='#0a0a0a',
            fg='#cccccc'
        ).pack(pady=(0, 20))
        
        # API key sections
        providers = {
            'COHERE': 3,
            'GROQ': 3,
            'HUGGINGFACE': 3,
            'OPENROUTER': 3,
            'MISTRAL': 1,
            'GEMINI': 3
        }
        
        self.api_entries = {}
        
        for provider, count in providers.items():
            self._create_provider_section(provider, count)
    
    def _create_provider_section(self, provider: str, key_count: int):
        """Create API key input section for a provider"""
        section = tk.Frame(self.content_frame, bg='#1a1a1a', padx=20, pady=15)
        section.pack(fill=tk.X, padx=30, pady=10)
        
        # Provider header
        tk.Label(
            section,
            text=f"🔸 {provider}",
            font=("Arial", 13, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(anchor='w', pady=(0, 10))
        
        # Key entries
        for i in range(1, key_count + 1):
            key_name = f"{provider}_KEY_{i}"
            
            row = tk.Frame(section, bg='#1a1a1a')
            row.pack(fill=tk.X, pady=5)
            
            tk.Label(
                row,
                text=f"Key {i}:",
                font=("Arial", 10),
                bg='#1a1a1a',
                fg='#cccccc',
                width=8,
                anchor='w'
            ).pack(side=tk.LEFT)
            
            entry = tk.Entry(
                row,
                font=("Arial", 10),
                bg='#0a0a0a',
                fg='#ffffff',
                insertbackground='#00ff00',
                relief='flat',
                show='*'
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
            
            # Show/hide button
            show_btn = tk.Button(
                row,
                text="👁",
                font=("Arial", 10),
                bg='#2d2d2d',
                fg='#cccccc',
                relief='flat',
                width=3,
                command=lambda e=entry: e.config(show='' if e.cget('show') == '*' else '*')
            )
            show_btn.pack(side=tk.LEFT, padx=5)
            
            self.api_entries[key_name] = entry
    
    def _validate_api_keys(self) -> bool:
        """Validate that at least one provider has keys"""
        providers_with_keys = set()
        
        for key_name, entry in self.api_entries.items():
            value = entry.get().strip()
            if value:
                provider = key_name.split('_KEY_')[0]
                providers_with_keys.add(provider)
                self.api_keys[key_name] = value
        
        if not providers_with_keys:
            messagebox.showwarning(
                "API Keys Required",
                "Please enter at least one API key from any provider.\n\n"
                "JARVIS requires at least one AI provider to function.",
                parent=self.root
            )
            return False
        
        return True
    
    # =============== STEP 2: SETTINGS ===============
    
    def _show_settings(self):
        """Show config.ini settings"""
        self._clear_content()
        self._update_progress()
        self.skip_btn.pack_forget()  # Settings are required
        
        tk.Label(
            self.content_frame,
            text="⚙️ System Settings",
            font=("Arial", 18, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        ).pack(pady=(20, 10))
        
        tk.Label(
            self.content_frame,
            text="Configure basic system settings:",
            font=("Arial", 11),
            bg='#0a0a0a',
            fg='#cccccc'
        ).pack(pady=(0, 20))
        
        self.setting_entries = {}
        
        # Paths section
        self._create_settings_section("Paths", [
            ("Program Path", "Program_path", str(self.project_root)),
            ("Tesseract OCR Path", "tesseract_cmd", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"),
        ])
        
        # Audio section
        self._create_settings_section("Audio", [
            ("STT Website URL", "stt_website_url", "https://realtime-stt-devs-do-code.netlify.app/"),
            ("STT Language", "stt_language", "en-IN"),
            ("TTS Voice", "TTS_Voice", "Ryan"),
            ("Wake Word", "Wake_word", "jarvis"),
        ])
        self._create_checkbox_section("Audio", [
            ("Enable Speech-to-Text (STT)", "enable_stt", True),
            ("Enable Text-to-Speech (TTS)", "enable_tts", True),
        ])
        # Behavior section (checkboxes)
        self._create_checkbox_section("Behavior", [
            ("Auto TTS Output", "auto_tts_output", True),
            ("Hide Console Window", "hide_console_window", True),
            ("Development Mode", "dev_mode", False),
        ])
    
        
        self._create_settings_section("Integrations", [
            ("calendar url", "calendar_url", "EnterYourUrl.ics"),
        
            ("Google app password", "google_app_password", "app pass"),
            ("Your email address", "your_email_address", "example@gmail.com"),])

    def _create_settings_section(self, section: str, settings: List[Tuple[str, str, str]]):
        """Create settings input section"""
        frame = tk.Frame(self.content_frame, bg='#1a1a1a', padx=20, pady=15)
        frame.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(
            frame,
            text=f"📁 {section}",
            font=("Arial", 13, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(anchor='w', pady=(0, 10))
        
        for label, key, default in settings:
            row = tk.Frame(frame, bg='#1a1a1a')
            row.pack(fill=tk.X, pady=5)
            
            tk.Label(
                row,
                text=f"{label}:",
                font=("Arial", 10),
                bg='#1a1a1a',
                fg='#cccccc',
                width=20,
                anchor='w'
            ).pack(side=tk.LEFT)
            
            entry = tk.Entry(
                row,
                font=("Arial", 10),
                bg='#0a0a0a',
                fg='#ffffff',
                insertbackground='#00ff00',
                relief='flat'
            )
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
            
            self.setting_entries[f"{section}.{key}"] = entry
    
    def _create_checkbox_section(self, section: str, settings: List[Tuple[str, str, bool]]):
        """Create checkbox settings section"""
        frame = tk.Frame(self.content_frame, bg='#1a1a1a', padx=20, pady=15)
        frame.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(
            frame,
            text=f"⚡ {section}",
            font=("Arial", 13, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(anchor='w', pady=(0, 10))
        
        for label, key, default in settings:
            var = tk.BooleanVar(value=default)
            
            cb = tk.Checkbutton(
                frame,
                text=label,
                variable=var,
                font=("Arial", 10),
                bg='#1a1a1a',
                fg='#cccccc',
                selectcolor='#0a0a0a',
                activebackground='#1a1a1a',
                activeforeground='#00ff00'
            )
            cb.pack(anchor='w', pady=3)
            
            self.setting_entries[f"{section}.{key}"] = var
    
    def _validate_settings(self) -> bool:
        """Validate settings"""
        # Check required paths
        program_path = self.setting_entries.get("Paths.Program_path")
        if program_path and not program_path.get().strip():
            messagebox.showwarning(
                "Required Field",
                "Program Path is required.",
                parent=self.root
            )
            return False
        
        # Store values
        for key, widget in self.setting_entries.items():
            if isinstance(widget, tk.BooleanVar):
                self.config_values[key] = widget.get()
            else:
                self.config_values[key] = widget.get().strip()
        
        return True
    
    # =============== STEP 3: FACE RECOGNITION ===============
    
    def _show_face_setup(self):
        """Show face recognition setup"""
        self._clear_content()
        self._update_progress()
        self.skip_btn.pack_forget()
        
        tk.Label(
            self.content_frame,
            text="📸 Face Recognition Setup",
            font=("Arial", 18, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        ).pack(pady=(20, 10))
        
        if self.face_path.exists():
            tk.Label(
                self.content_frame,
                text="✅ Face recognition is already configured.\n\n"
                     "Click Next to proceed to the final step.",
                font=("Arial", 12),
                bg='#0a0a0a',
                fg='#00ff00',
                justify=tk.CENTER
            ).pack(pady=40)
        else:
            tk.Label(
                self.content_frame,
                text="JARVIS will register your face for authentication.\n\n"
                     "When you click 'Register Face', your camera will activate.\n"
                     "Please look directly at the camera with clear Lightining or else It'll fail to Register.\n\n"
                     "This ensures only you can access JARVIS.",
                font=("Arial", 12),
                bg='#0a0a0a',
                fg='#cccccc',
                justify=tk.CENTER
            ).pack(pady=30)
            
            self.face_btn = tk.Button(
                self.content_frame,
                text="📷 Register Face",
                font=("Arial", 14, "bold"),
                bg='#00ff00',
                fg='#000000',
                relief='flat',
                cursor='hand2',
                padx=40,
                pady=20,
                command=self._register_face
            )
            self.face_btn.pack(pady=20)
            
            self.face_status = tk.Label(
                self.content_frame,
                text="",
                font=("Arial", 11),
                bg='#0a0a0a',
                fg='#ffaa00'
            )
            self.face_status.pack(pady=10)
    
    def _register_face(self):
        """Register user's face"""
        self.face_btn.config(state='disabled', text="📷 Registering...")
        self.face_status.config(text="Please look at the camera...", fg='#ffaa00')
        self.root.update()
        
        try:
            # Import and run face registration
            from core.auth import register_face
            
            if register_face():
                self.face_status.config(text="✅ Face registered successfully!", fg='#00ff00')
                self.face_btn.config(text="✅ Completed")
            else:
                self.face_status.config(text="❌ Registration failed. Try again.", fg='#ff4444')
                self.face_btn.config(state='normal', text="📷 Retry")
        
        except Exception as e:
            self.face_status.config(text=f"❌ Error: {str(e)}", fg='#ff4444')
            self.face_btn.config(state='normal', text="📷 Retry")
    
    # =============== STEP 4: FINISH ===============
    
    def _show_finish(self):
        """Show completion screen"""
        self._clear_content()
        self._update_progress()
        self.skip_btn.pack_forget()
        
        finish_frame = tk.Frame(self.content_frame, bg='#1a1a1a', padx=40, pady=40)
        finish_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        tk.Label(
            finish_frame,
            text="🎉 Setup Complete!",
            font=("Arial", 22, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(pady=(0, 20))
        
        tk.Label(
            finish_frame,
            text="JARVIS is ready to launch!\n\n"
                 "Review your configuration below:",
            font=("Arial", 12),
            bg='#1a1a1a',
            fg='#cccccc',
            justify=tk.CENTER
        ).pack(pady=10)
        
        # Summary
        summary_frame = tk.Frame(finish_frame, bg='#0a0a0a', padx=20, pady=20)
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        summary_text = scrolledtext.ScrolledText(
            summary_frame,
            font=("Consolas", 10),
            bg='#0a0a0a',
            fg='#00ff00',
            relief='flat',
            height=15,
            wrap=tk.WORD
        )
        summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Build summary
        summary = []
        summary.append("=" * 60)
        summary.append("CONFIGURATION SUMMARY")
        summary.append("=" * 60)
        summary.append("")
        
        # API keys
        providers = set(k.split('_KEY_')[0] for k in self.api_keys.keys())
        summary.append(f"✅ Configured AI Providers: {', '.join(providers)}")
        summary.append(f"   Total API Keys: {len(self.api_keys)}")
        summary.append("")
        
        # Settings
        summary.append("⚙️ Settings Configured:")
        for key, value in self.config_values.items():
            if isinstance(value, bool):
                value = "Enabled" if value else "Disabled"
            summary.append(f"   • {key}: {value}")
        summary.append("")
        
        # Face recognition
        if self.face_path.exists():
            summary.append("✅ Face Recognition: Configured")
        else:
            summary.append("⚠️ Face Recognition: Skipped (will prompt on first run)")
        
        summary.append("")
        summary.append("=" * 60)
        summary.append("Click 'Finish' to save and launch JARVIS!")
        summary.append("=" * 60)
        
        summary_text.insert('1.0', '\n'.join(summary))
        summary_text.config(state='disabled')
    
    # =============== NAVIGATION ===============
    
    def _go_next(self):
        """Go to next step using the dynamic step list"""
        # Validate current step based on its function
        current_step_func = self.steps_to_run[self.current_step]
        
        if current_step_func == self._show_api_keys:
            if not self._validate_api_keys(): return
            self._save_env_file()
        elif current_step_func == self._show_settings:
            if not self._validate_settings(): return
            self._save_config_file()
        elif current_step_func == self._show_startup_setup:
            self._handle_startup_choice()
        # Move to the next step's index
        self.current_step += 1
        
        # If we've completed the last step (clicked "Finish" on the summary screen)
        if self.current_step >= self.total_steps:
            self._finish_setup()
            return
        
        # Show the next step from our dynamic list
        self.steps_to_run[self.current_step]()
    
    def _go_back(self):
        """Go to the previous step in the dynamic list"""
        if self.current_step > 0:
            self.current_step -= 1
            self.steps_to_run[self.current_step]()
    
    def _skip_step(self):
        """Skip the current optional step"""
        current_step_func = self.steps_to_run[self.current_step]
        if current_step_func == self._show_requirements_install:
             return
        if current_step_func == self._show_api_keys:  # API keys
            result = messagebox.askyesno(
                "Skip API Keys?",
                "Warning: JARVIS requires at least one API key to function.\n\n"
                "You can add them later by editing the .env file.\n\n"
                "Continue without API keys?",
                parent=self.root
            )
            if result:
                self._go_next()
    
    def _finish_setup(self):
        """Save configuration and finish"""
        try:
            # Show progress
            progress_win = tk.Toplevel(self.root)
            progress_win.title("Saving...")
            progress_win.geometry("400x150")
            progress_win.configure(bg='#0a0a0a')
            progress_win.transient(self.root)
            
            tk.Label(
                progress_win,
                text="💾 Saving configuration...",
                font=("Arial", 12, "bold"),
                bg='#0a0a0a',
                fg='#00ff00'
            ).pack(pady=30)
            
            status_label = tk.Label(
                progress_win,
                text="",
                font=("Arial", 10),
                bg='#0a0a0a',
                fg='#cccccc'
            )
            status_label.pack()
            
            progress_win.update()
            
            # Save .env
            status_label.config(text="Writing .env file...")
            progress_win.update()
            self._save_env_file()
            
            # Save config.ini
            status_label.config(text="Writing config.ini...")
            progress_win.update()
            self._save_config_file()
            
            progress_win.destroy()
            
            # Success message
            messagebox.showinfo(
                "Setup Complete! 🎉",
                "Configuration saved successfully!\n\n"
                "JARVIS will now launch.\n\n"
                "Welcome aboard!",
                parent=self.root
            )
            
            self.root.destroy()
        
        except Exception as e:
            messagebox.showerror(
                "Setup Error",
                f"Failed to save configuration:\n{str(e)}\n\n"
                f"Please check file permissions and try again.",
                parent=self.root
            )
    
    def _save_env_file(self):
        """Save API keys to .env"""
        lines = []
        
        for key, value in self.api_keys.items():
            lines.append(f"{key}={value}")
        
        with open(self.env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _save_config_file(self):
        """Save settings to config.ini"""
        config = configparser.ConfigParser()
        config.optionxform = str
        # Organize by section
        sections = {}
        
        # --- MODIFIED LOGIC TO HANDLE THE CALENDAR URL ---
        skipped_keys = []
        for key, value in self.config_values.items():
            # Check for the specific problematic setting
            if key == "Integrations.calendar_url" and '%' in str(value):
                print(f"⚠️  WARNING: The 'calendar_url' contains special characters and will be skipped.")
                print(f"   You will need to add it to the config.ini file manually after setup.")
                print(f"   URL: {value}")
                skipped_keys.append(key)
                continue # This skips the current setting and moves to the next one

            section, option = key.split('.', 1)
            
            if section not in sections:
                sections[section] = {}
            
            if isinstance(value, bool):
                sections[section][option] = 'true' if value else 'false'
            else:
                # Use the original replace method for all other safe values
                sections[section][option] = str(value).replace('%', '%%')
        
        # --- END OF MODIFIED LOGIC ---

        # Add default monitor settings if not present
        if 'Monitors' not in sections:
            sections['Monitors'] = {
                'browser_url_poll': '1.0',
                'explorer_path_poll': '1.0',
                'clipboard_poll': '2.0',
                'active_window_poll': '1.0',
                'downloads_poll': '2.0',
                'performance_poll': '10.0',
                'idle_time_poll': '10.0',
                'network_poll': '5.0',
                'usb_ports_poll': '5.0',
                'bluetooth_poll': '5.0',
                'battery_poll': '10.0',
            }
        
        # Add default behavior settings if missing
        if 'Behavior' not in sections:
            sections['Behavior'] = {}
        
        if 'confirm_ai_execution' not in sections['Behavior']:
            sections['Behavior']['confirm_ai_execution'] = 'false'
        if 'notifier_grace_period' not in sections['Behavior']:
            sections['Behavior']['notifier_grace_period'] = '50.0'
        if 'TERMINAL_MAX_MESSAGES' not in sections['Behavior']:
            sections['Behavior']['TERMINAL_MAX_MESSAGES'] = '5.0'
        if 'TERMINAL_MESSAGE_LIFETIME' not in sections['Behavior']:
            sections['Behavior']['TERMINAL_MESSAGE_LIFETIME'] = '8000.0'
        
        # Ensure Audio section has all required fields
        if 'Audio' not in sections:
            sections['Audio'] = {}
        
        audio_defaults = {
            'enable_stt': 'true',
            'enable_tts': 'true',
            'stt_website_url': 'https://realtime-stt-devs-do-code.netlify.app/',
            'stt_language': 'en-IN',
            'TTS_Voice': 'Ryan',
            'Wake_word': 'jarvis'
        }
        
        for key, default_val in audio_defaults.items():
            if key not in sections['Audio']:
                sections['Audio'][key] = default_val
        
        # Write to config
        for section, options in sections.items():
            config[section] = options
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    def _on_closing(self):
        """
        Handles the event when the user clicks the close ('X') button.
        This function ensures the entire application terminates.
        """
        # Optionally, show a confirmation message
        if messagebox.askokcancel("Quit", "Are you sure you want to exit the setup?\nThe application will not start."):
            print("❌ Setup aborted by user. Terminating application.")
            self.root.destroy()
            sys.exit(0) # This forces the entire script to stop
    def run(self):
        """Run the setup wizard"""
        self.root.mainloop()

def check_first_time_setup() -> bool:
    """
    Check if first-time setup is needed. This is now more robust.
    It checks for existence AND validity of the config file.
    Returns True if setup was run, False if not needed.
    
    ⚠️ Called BEFORE any config imports to avoid circular dependencies
    """
    # Use absolute path resolution
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        project_root = Path(sys._MEIPASS)
    else:
        # Running as script - go up from utils/ to project root
        project_root = Path(__file__).parent.parent
    
    env_path = project_root / '.env'
    config_path = project_root / 'config.ini'
    
    needs_setup = False
    if not env_path.exists() or not config_path.exists():
        needs_setup = True
    else:
        # --- MORE ROBUST CHECK ---
        # If the file exists, make sure it's not empty and is a valid config file.
        try:
            config = configparser.ConfigParser(interpolation=None)
            files_read = config.read(config_path)
            # If read is successful but produces no sections, it's an empty file.
            if not files_read or not config.sections():
                print("⚠️ Found an empty or invalid config.ini. Forcing setup.")
                needs_setup = True
            # Also check for a fundamental section to be sure.
            elif not config.has_section('Paths'):
                print("⚠️ config.ini is missing the [Paths] section. Forcing setup.")
                needs_setup = True
        except configparser.Error as e:
            # The file is malformed and cannot be parsed.
            print(f"⚠️ Could not parse config.ini. Error: {e}. Forcing setup.")
            needs_setup = True

    if needs_setup:
        print("🚀 First-time setup required...")
        print(f"📁 Project root: {project_root}")
        
        # Clean up potentially corrupt files before starting the wizard
        if config_path.exists():
            try:
                os.remove(config_path)
            except OSError:
                pass
        
        wizard = SetupWizard()
        wizard.run()
        return True
    
    return False


# =============== INTEGRATION WITH MAIN.PY ===============

def integrate_with_main():
    """
    Add this to main.py BEFORE any other initialization:
    
    ```python
    # At the top of main.py, after imports:
    from utils.setup_wizard import check_first_time_setup
    
    # In main() function, BEFORE startup_ui:
    if check_first_time_setup():
        # Setup wizard ran, now continue with normal startup
        pass
    ```
    """
    pass


if __name__ == "__main__":
    # Test the wizard
    wizard = SetupWizard()
    wizard.run()
