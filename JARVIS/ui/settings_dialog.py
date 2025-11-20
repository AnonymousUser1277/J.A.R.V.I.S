"""
JARVIS Settings Dialog - ENHANCED with Dynamic Settings Creator
File: ui/settings_dialog.py

NEW FEATURES:
✅ '+Add Setting' tab for creating custom settings
✅ Automatic integration into config.ini, setup_wizard.py, and loader.py
✅ Support for checkbox, text input, slider, and dropdown types
✅ Create new sections or add to existing ones
"""

import importlib
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
from pathlib import Path
from typing import Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)


class SettingsDialog:
    """Modern dark-themed settings dialog with dynamic settings creator"""
    
    def __init__(self, parent, config_path: Path = None):
        self.parent = parent
        self.config_path = config_path or Path(__file__).parent.parent / 'config.ini'
        self.temp_root = None
        
        # Store original values for cancel/revert
        self.original_values = {}
        self.current_values = {}
        self.widgets = {}
        self.changes_made = False
        
        # Load config FIRST
        self.config = configparser.ConfigParser(interpolation=None)
        if not self.config_path.exists():
            logger.error(f"Config file not found: {self.config_path}")
            messagebox.showerror("Error", f"Config file not found:\n{self.config_path}")
            return
        
        self.config.read(self.config_path, encoding='utf-8')
        logger.info(f"✅ Config loaded from: {self.config_path}")
        
        # Create dialog with proper parent handling
        self._create_dialog_window()
        
        if not self.dialog:
            logger.error("Failed to create dialog window")
            return
        
        self.dialog.title("⚙️ JARVIS Settings")
        self.dialog.configure(bg='#0a0a0a')
        self.dialog.geometry("1100x890")
        self.dialog.resizable(True, True)
        
        # Make sure dialog is on top
        self.dialog.attributes('-topmost', True)
        self.dialog.after(100, lambda: self.dialog.attributes('-topmost', False))
        
        # Center window
        self._center_window()
        
        # Configure styles BEFORE creating widgets
        self._configure_styles()
        
        # Build UI
        self._create_ui()
        
        # NOW load values into widgets
        self._load_current_values()
        
        # Store as original
        self.original_values = self.current_values.copy()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        logger.info("✅ Settings dialog initialized")
    
    def _create_dialog_window(self):
        """Create dialog window with proper parent handling"""
        try:
            if self.parent and hasattr(self.parent, 'winfo_exists'):
                try:
                    if self.parent.winfo_exists():
                        self.dialog = tk.Toplevel(self.parent)
                        logger.debug("Created dialog with valid parent")
                        return
                except tk.TclError:
                    pass
            
            logger.debug("Parent invalid, creating temporary root")
            self.temp_root = tk.Tk()
            self.temp_root.withdraw()
            self.temp_root.overrideredirect(True)
            self.temp_root.attributes('-alpha', 0)
            
            self.dialog = tk.Toplevel(self.temp_root)
            logger.debug("Created dialog with temporary hidden root")
            
        except Exception as e:
            logger.error(f"Failed to create dialog window: {e}")
            self.dialog = None
    
    def _center_window(self):
        """Center the dialog on screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _configure_styles(self):
        """Configure all ttk styles for modern dark theme"""
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure('TNotebook',
                       background='#0a0a0a',
                       borderwidth=0,
                       tabmargins=[2, 5, 2, 0])
        
        style.configure('TNotebook.Tab',
                       background='#1a1a1a',
                       foreground='#888888',
                       padding=[20, 10],
                       borderwidth=0,
                       font=('Arial', 10, 'bold'))
        
        style.map('TNotebook.Tab',
                 background=[('selected', '#2d2d2d'), ('active', '#252525')],
                 foreground=[('selected', '#00ff00'), ('active', '#cccccc')])
        
        style.configure('Vertical.TScrollbar',
                       background='#1a1a1a',
                       troughcolor='#0a0a0a',
                       borderwidth=0,
                       arrowcolor='#00ff00',
                       relief='flat')
        
        style.map('Vertical.TScrollbar',
                 background=[('active', '#2d2d2d'), ('pressed', '#00ff00')])
        
        style.configure('Dark.TCombobox',
                       fieldbackground='#1a1a1a',
                       background='#1a1a1a',
                       foreground='#ffffff',
                       arrowcolor='#00ff00',
                       borderwidth=0,
                       relief='flat')
        
        self.dialog.option_add('*TCombobox*Listbox.background', '#1a1a1a')
        self.dialog.option_add('*TCombobox*Listbox.foreground', '#ffffff')
        self.dialog.option_add('*TCombobox*Listbox.selectBackground', '#00ff00')
        self.dialog.option_add('*TCombobox*Listbox.selectForeground', '#000000')
    
    def _create_ui(self):
        """Build the complete UI structure"""
        main_frame = tk.Frame(self.dialog, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        header_frame = tk.Frame(main_frame, bg='#1a1a1a', height=70)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="⚙️ JARVIS Settings",
            font=("Arial", 20, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        )
        title_label.pack(pady=20)
        
        self.notebook = ttk.Notebook(main_frame, style='TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create standard tabs
        self._create_paths_tab()
        self._create_audio_tab()
        self._create_behavior_tab()
        self._create_monitors_tab()
        self._create_integrations_tab()
        self._create_api_keys_tab()
        self._create_ai_instruction_tab()
        
        # NEW: Dynamic settings creator tab
        self._create_add_setting_tab()
        
        self._create_buttons()
    
    def _create_buttons(self):
        button_frame = tk.Frame(self.dialog, bg='#0a0a0a')
        button_frame.pack(fill=tk.X, pady=10, padx=10)

        btn_style = {
            'font': ("Arial", 11, "bold"),
            'relief': 'flat',
            'cursor': 'hand2',
            'padx': 25,
            'pady': 10,
            'borderwidth': 0
        }

        cancel_btn = tk.Button(
            button_frame,
            text="❌ Cancel",
            bg='#2d2d2d',
            fg='#ff4444',
            activebackground='#ff4444',
            activeforeground='#000000',
            command=self._on_cancel,
            **btn_style
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        ok_btn = tk.Button(
            button_frame,
            text="✅ OK",
            bg='#2d2d2d',
            fg='#00ff00',
            activebackground='#00ff00',
            activeforeground='#000000',
            command=self._on_ok,
            **btn_style
        )
        ok_btn.pack(side=tk.RIGHT, padx=5)

        apply_btn = tk.Button(
            button_frame,
            text="💾 Apply",
            bg='#2d2d2d',
            fg='#66ccff',
            activebackground='#66ccff',
            activeforeground='#000000',
            command=self._on_apply,
            **btn_style
        )
        apply_btn.pack(side=tk.RIGHT, padx=5)

    def _create_setting_row(self, parent, label_text: str, widget_type: str,
                            section: str, key: str, **kwargs) -> str:
        """Create a modern setting row"""
        row_frame = tk.Frame(parent, bg='#1a1a1a', height=50)
        row_frame.pack(fill=tk.X, pady=3, padx=15)
        row_frame.pack_propagate(False)
        
        border = tk.Frame(row_frame, bg='#2d2d2d', height=1)
        border.pack(side=tk.BOTTOM, fill=tk.X)
        
        label = tk.Label(
            row_frame,
            text=label_text,
            font=("Arial", 11),
            bg='#1a1a1a',
            fg='#cccccc',
            anchor='w'
        )
        label.pack(side=tk.LEFT, padx=15, fill=tk.Y)
        
        widget_key = f"{section}.{key}"
        
        if widget_type == 'checkbox':
            var = tk.BooleanVar()
            widget = tk.Checkbutton(
                row_frame,
                variable=var,
                bg='#1a1a1a',
                fg='#00ff00',
                selectcolor='#0a0a0a',
                activebackground='#1a1a1a',
                activeforeground='#00ff00',
                highlightthickness=0,
                command=lambda: self._on_value_change(widget_key, var.get())
            )
            widget.pack(side=tk.RIGHT, padx=15)
            self.widgets[widget_key] = (widget, var)
        
        elif widget_type == 'slider':
            container = tk.Frame(row_frame, bg='#1a1a1a')
            container.pack(side=tk.RIGHT, padx=15, fill=tk.Y)
            
            var = tk.DoubleVar()
            value_label = tk.Label(
                container,
                text="0.0",
                bg='#1a1a1a',
                fg='#00ff00',
                font=("Arial", 10, "bold"),
                width=6
            )
            value_label.pack(side=tk.RIGHT, padx=(10, 0))
            
            def update_slider_label(v):
                value_label.config(text=f"{float(v):.1f}")
                self._on_value_change(widget_key, float(v))
            
            slider = tk.Scale(
                container,
                from_=kwargs.get('from_', 0),
                to=kwargs.get('to', 100),
                resolution=kwargs.get('resolution', 0.1),
                orient=tk.HORIZONTAL,
                variable=var,
                bg='#1a1a1a',
                fg='#00ff00',
                troughcolor='#0a0a0a',
                highlightthickness=0,
                sliderrelief='flat',
                sliderlength=20,
                width=15,
                length=200,
                showvalue=0,
                command=update_slider_label
            )
            slider.pack(side=tk.RIGHT)
            slider.value_label = value_label
            
            self.widgets[widget_key] = (slider, var)
        
        elif widget_type == 'entry':
            var = tk.StringVar()
            
            entry = tk.Entry(
                row_frame,
                font=("Arial", 10),
                bg='#0a0a0a',
                fg='#ffffff',
                insertbackground='#00ff00',
                relief='flat',
                highlightbackground='#2d2d2d',
                highlightcolor='#00ff00',
                highlightthickness=1,
                width=kwargs.get('width', 40)
            )
            entry.pack(side=tk.RIGHT, padx=15, ipady=5)
            
            def on_entry_change(event):
                self._on_value_change(widget_key, entry.get())
            entry.bind('<KeyRelease>', on_entry_change)
            
            self.widgets[widget_key] = (entry, var)
        
        elif widget_type == 'dropdown':
            var = tk.StringVar()
            dropdown = ttk.Combobox(
                row_frame,
                textvariable=var,
                values=kwargs.get('values', []),
                state='readonly',
                width=kwargs.get('width', 30),
                style='Dark.TCombobox'
            )
            dropdown.pack(side=tk.RIGHT, padx=15)
            dropdown.bind('<<ComboboxSelected>>',
                         lambda e: self._on_value_change(widget_key, var.get()))
            self.widgets[widget_key] = (dropdown, var)
        
        return widget_key
    
    def _create_scrollable_tab(self, tab_name: str, icon: str):
        """Create a scrollable tab with modern styling"""
        tab = tk.Frame(self.notebook, bg='#0a0a0a')
        self.notebook.add(tab, text=f"{icon} {tab_name}")
        
        canvas = tk.Canvas(tab, bg='#0a0a0a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview, style='Vertical.TScrollbar')
        scrollable_frame = tk.Frame(canvas, bg='#0a0a0a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(
            canvas.find_withtag("all")[0], width=e.width))
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
    
    def _create_paths_tab(self):
        """Paths settings"""
        frame = self._create_scrollable_tab("Paths", "📁")
        
        self._create_setting_row(
            frame, "Tesseract OCR Path:", 'entry', 'Paths', 'tesseract_cmd', width=50
        )
        self._create_setting_row(
            frame, "Program Path:", 'entry', 'Paths', 'Program_path', width=50
        )
    
    def _create_audio_tab(self):
        """Audio settings"""
        frame = self._create_scrollable_tab("Audio", "🎤")
        
        self._create_setting_row(frame, "Enable Speech-to-Text (STT):", 'checkbox', 'Audio', 'enable_stt')
        self._create_setting_row(frame, "Enable Text-to-Speech (TTS):", 'checkbox', 'Audio', 'enable_tts')
        self._create_setting_row(frame, "STT Website URL:", 'entry', 'Audio', 'stt_website_url', width=50)
        self._create_setting_row(frame, "TTS_Voice:", 'entry', 'Audio', 'TTS_Voice', width=30)
        self._create_setting_row(frame, "STT Language:", 'entry', 'Audio', 'stt_language', width=20)
        self._create_setting_row(frame, "Wake_word:", 'entry', 'Audio', 'Wake_word', width=20)
    
    def _create_behavior_tab(self):
        """Behavior settings"""
        frame = self._create_scrollable_tab("Behavior", "⚡")
        
        self._create_setting_row(frame, "Confirm AI Execution:", 'checkbox', 'Behavior', 'confirm_ai_execution')
        self._create_setting_row(frame, "Auto TTS Output:", 'checkbox', 'Behavior', 'auto_tts_output')
        self._create_setting_row(frame, "Notifier Grace Period (seconds):", 'slider', 'Behavior', 'notifier_grace_period', from_=10, to=300, resolution=10)
        self._create_setting_row(frame, "TERMINAL MAX MESSAGES:", 'slider', 'Behavior', 'TERMINAL_MAX_MESSAGES', from_=1, to=100, resolution=1)
        self._create_setting_row(frame, "TERMINAL MESSAGE LIFETIME (1000 = 1sec):", 'slider', 'Behavior', 'TERMINAL_MESSAGE_LIFETIME', from_=1000, to=30000, resolution=1000)
        self._create_setting_row(frame, "Development Mode:", 'checkbox', 'Behavior', 'dev_mode')
        self._create_setting_row(frame, "Hide Console Window:", 'checkbox', 'Behavior', 'hide_console_window')
    
    def _create_monitors_tab(self):
        """Monitors settings"""
        frame = self._create_scrollable_tab("Monitors", "📊")
        
        info = tk.Label(
            frame,
            text="⏱️ Polling intervals in seconds (lower = more responsive, higher CPU)",
            font=("Arial", 10, "italic"),
            bg='#0a0a0a',
            fg='#ffaa00',
            wraplength=800,
            justify=tk.LEFT
        )
        info.pack(pady=15, padx=15)
        
        monitors = [
            ('Browser URL Poll:', 'browser_url_poll', 0.5, 10),
            ('Explorer Path Poll:', 'explorer_path_poll', 0.5, 10),
            ('Clipboard Poll:', 'clipboard_poll', 1, 10),
            ('Active Window Poll:', 'active_window_poll', 0.5, 10),
            ('Downloads Poll:', 'downloads_poll', 1, 10),
            ('Performance Poll:', 'performance_poll', 5, 60),
            ('Idle Time Poll:', 'idle_time_poll', 5, 60),
            ('Network Poll:', 'network_poll', 2, 30),
            ('USB Ports Poll:', 'usb_ports_poll', 2, 30),
            ('Bluetooth Poll:', 'bluetooth_poll', 2, 30),
            ('Battery Poll:', 'battery_poll', 5, 60),
        ]
        
        for label, key, min_val, max_val in monitors:
            self._create_setting_row(frame, label, 'slider', 'Monitors', key, from_=min_val, to=max_val, resolution=0.5)

    def _create_integrations_tab(self):
        """Integrations settings"""
        frame = self._create_scrollable_tab("Integrations", "⚙️")
        self._create_setting_row(frame, "Google app password", 'entry', 'Integrations', 'google_app_password', width=40)
        self._create_setting_row(frame, "Your email address", 'entry', 'Integrations', 'your_email_address', width=40)
        self._create_setting_row(frame, "calendar url", 'entry', 'Integrations', 'calendar_url', width=40)

    def _create_api_keys_tab(self):
        """API Keys tab"""
        frame = self._create_scrollable_tab("API Keys", "🔑")
        
        info_frame = tk.Frame(frame, bg='#1a1a1a')
        info_frame.pack(fill=tk.X, pady=20, padx=15)
        
        info_label = tk.Label(
            info_frame,
            text="🔐 API Keys Management",
            font=("Arial", 14, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        )
        info_label.pack(pady=(0, 10))
        
        desc_label = tk.Label(
            info_frame,
            text="Edit your API keys in the .env file.\n"
                "The .env file contains sensitive information - keep it secure!",
            font=("Arial", 10),
            bg='#1a1a1a',
            fg='#cccccc',
            justify=tk.LEFT
        )
        desc_label.pack(pady=(0, 20))
        
        button_frame = tk.Frame(info_frame, bg='#1a1a1a')
        button_frame.pack()
        
        def open_env_file():
            try:
                import os
                env_path = Path(__file__).parent.parent / '.env'
                
                if not env_path.exists():
                    messagebox.showerror(
                        "File Not Found",
                        f".env file not found at:\n{env_path}",
                        parent=self.dialog
                    )
                    return
                
                os.startfile(str(env_path))
                messagebox.showinfo(
                    "File Opened",
                    ".env file opened in your default editor.\n\n"
                    "⚠️ Remember to restart JARVIS after making changes!",
                    parent=self.dialog
                )
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open .env file:\n{e}", parent=self.dialog)
        
        open_button = tk.Button(
            button_frame,
            text="📂 Open .env File",
            font=("Arial", 12, "bold"),
            bg='#2d2d2d',
            fg='#00ff00',
            activebackground='#00ff00',
            activeforeground='#000000',
            relief='flat',
            cursor='hand2',
            padx=30,
            pady=15,
            command=open_env_file
        )
        open_button.pack()
        
        warning_label = tk.Label(
            info_frame,
            text="⚠️ Never share your .env file or commit it to version control!",
            font=("Arial", 9, "italic"),
            bg='#1a1a1a',
            fg='#ff6666'
        )
        warning_label.pack(pady=(20, 0))
    
    def _load_ai_instructions(self):
        """Load AI instructions from ai/instructions.py"""
        try:
            import re
            file_path = Path(__file__).parent.parent / "ai" / "instructions.py"
            self.ai_instruction_path = file_path

            if not file_path.exists():
                return f"File not found:\n{file_path}"

            src = file_path.read_text(encoding="utf-8")
            m = re.search(
                r'full_prompt\s*=\s*(f)?([ruRUfF]*)(?P<quote>"""|\'\'\')(?P<body>.*?)(?P=quote)',
                src,
                flags=re.DOTALL
            )
            if not m:
                return "full_prompt not found"

            body = m.group("body")
            if body.startswith("\n"):
                body = body[1:]
            if body.endswith("\n"):
                body = body[:-1]

            return body

        except Exception as e:
            return f"Error loading instructions:\n{e}"

    def _save_ai_instructions(self, new_text):
        """Save AI instructions to ai/instructions.py"""
        try:
            import re

            if not hasattr(self, "ai_instruction_path"):
                return False

            file_path = self.ai_instruction_path
            src = file_path.read_text(encoding="utf-8")

            m = re.search(
                r'full_prompt\s*=\s*(?P<prefix>f?[ruRUfF]*)?(?P<quote>"""|\'\'\')(?P<body>.*?)(?P=quote)',
                src,
                flags=re.DOTALL
            )
            if not m:
                return False

            prefix = m.group("prefix") or "f"
            quote = m.group("quote")
            new_body = "\n" + new_text.rstrip() + "\n"
            replacement = f'full_prompt = {prefix}{quote}{new_body}{quote}'

            updated_src = re.sub(
                r'full_prompt\s*=\s*(?:f?[ruRUfF]*)?(?:"""|\'\'\').*?(?:"""|\'\'\')',
                replacement,
                src,
                flags=re.DOTALL
            )

            file_path.write_text(updated_src, encoding="utf-8")
            return True

        except Exception:
            return False

    def _create_ai_instruction_tab(self):
        """AI Instruction tab"""
        frame = self._create_scrollable_tab("AI Instruction", "🧠")

        text_value = self._load_ai_instructions()

        text_box = tk.Text(
            frame,
            bg="#0c0c0c",
            fg="#00ff00",
            insertbackground="#00ff00",
            font=("Consolas", 11),
            wrap="word",
            relief="flat",
            padx=15,
            pady=15
        )
        text_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        text_box.insert("1.0", text_value)

        # --- FIX: REMOVE THIS LINE ---
        # This widget is special and is not saved in config.ini, so it shouldn't be in the widgets dict.
        # self.widgets["AI.full_prompt"] = (text_box, None)

        def toggle_readonly():
            state = text_box.cget("state")
            new_state = "normal" if state == "disabled" else "disabled"
            text_box.config(state=new_state)
            toggle_btn.config(text="🔓 Unlock" if new_state == "disabled" else "🔒 Lock")

        toggle_btn = tk.Button(
            frame,
            text="🔒 Lock",
            font=("Arial", 10, "bold"),
            relief="flat",
            bg="#2d2d2d",
            fg="#ffaa00",
            command=toggle_readonly
        )
        toggle_btn.pack(pady=5)

        def save_instruction():
            content = text_box.get("1.0", tk.END).strip()
            if self._save_ai_instructions(content):
                messagebox.showinfo("Saved", "AI instructions updated!", parent=self.dialog)
            else:
                messagebox.showerror("Error", "Failed to save instructions.", parent=self.dialog)

        save_btn = tk.Button(
            frame,
            text="💾 Save Changes",
            font=("Arial", 11, "bold"),
            bg="#2d2d2d",
            fg="#00ff00",
            relief="flat",
            cursor="hand2",
            command=save_instruction
        )
        save_btn.pack(pady=10)
    
    def _create_add_setting_tab(self):
        """NEW: Dynamic settings creator tab"""
        frame = self._create_scrollable_tab("+Add Setting", "➕")
        
        # Header
        header = tk.Label(
            frame,
            text="➕ Create New Setting",
            font=("Arial", 16, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        )
        header.pack(pady=20)
        
        desc = tk.Label(
            frame,
            text="Add custom settings that will automatically integrate into all configuration files.",
            font=("Arial", 10),
            bg='#0a0a0a',
            fg='#cccccc'
        )
        desc.pack(pady=(0, 30))
        
        # Form container
        form_frame = tk.Frame(frame, bg='#1a1a1a', padx=30, pady=30)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)
        
        # Setting Name
        tk.Label(
            form_frame,
            text="Setting Display Name:",
            font=("Arial", 11, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        self.new_setting_name = tk.Entry(
            form_frame,
            font=("Arial", 11),
            bg='#0a0a0a',
            fg='#ffffff',
            insertbackground='#00ff00',
            relief='flat',
            width=40
        )
        self.new_setting_name.grid(row=1, column=0, sticky='ew', pady=(0, 20), ipady=5)
        
        tk.Label(
            form_frame,
            text="(e.g., 'Enable Dark Mode' or 'Max Retry Count')",
            font=("Arial", 9, "italic"),
            bg='#1a1a1a',
            fg='#888888'
        ).grid(row=2, column=0, sticky='w', pady=(0, 20))
        
        # Setting Type
        tk.Label(
            form_frame,
            text="Setting Type:",
            font=("Arial", 11, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).grid(row=3, column=0, sticky='w', pady=(0, 5))
        
        self.new_setting_type = ttk.Combobox(
            form_frame,
            values=['Checkbox (Boolean)', 'Text Input', 'Slider (Number)', 'Dropdown (List)'],
            state='readonly',
            font=("Arial", 11),
            style='Dark.TCombobox',
            width=38
        )
        self.new_setting_type.grid(row=4, column=0, sticky='ew', pady=(0, 20))
        self.new_setting_type.current(0)
        self.new_setting_type.bind('<<ComboboxSelected>>', self._on_type_change)
        
        # Default Value Frame (dynamic based on type)
        self.value_frame = tk.Frame(form_frame, bg='#1a1a1a')
        self.value_frame.grid(row=5, column=0, sticky='ew', pady=(0, 20))
        
        tk.Label(
            self.value_frame,
            text="Default Value:",
            font=("Arial", 11, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(anchor='w', pady=(0, 5))
        
        self.value_widget_frame = tk.Frame(self.value_frame, bg='#1a1a1a')
        self.value_widget_frame.pack(fill=tk.X)
        
        # Section Selection
        tk.Label(
            form_frame,
            text="Section:",
            font=("Arial", 11, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).grid(row=6, column=0, sticky='w', pady=(0, 5))
        
        section_frame = tk.Frame(form_frame, bg='#1a1a1a')
        section_frame.grid(row=7, column=0, sticky='ew', pady=(0, 20))
        
        # Get existing sections
        existing_sections = list(self.config.sections())
        
        self.section_choice = tk.StringVar(value='existing')
        
        tk.Radiobutton(
            section_frame,
            text="Add to existing section:",
            variable=self.section_choice,
            value='existing',
            font=("Arial", 10),
            bg='#1a1a1a',
            fg='#cccccc',
            selectcolor='#0a0a0a',
            activebackground='#1a1a1a',
            command=self._on_section_choice_change
        ).pack(anchor='w', pady=5)
        
        self.existing_section_dropdown = ttk.Combobox(
            section_frame,
            values=existing_sections,
            state='readonly',
            font=("Arial", 10),
            style='Dark.TCombobox',
            width=37
        )
        self.existing_section_dropdown.pack(anchor='w', padx=20, pady=5)
        if existing_sections:
            self.existing_section_dropdown.current(0)
        
        tk.Radiobutton(
            section_frame,
            text="Create new section:",
            variable=self.section_choice,
            value='new',
            font=("Arial", 10),
            bg='#1a1a1a',
            fg='#cccccc',
            selectcolor='#0a0a0a',
            activebackground='#1a1a1a',
            command=self._on_section_choice_change
        ).pack(anchor='w', pady=(15, 5))
        
        self.new_section_entry = tk.Entry(
            section_frame,
            font=("Arial", 10),
            bg='#0a0a0a',
            fg='#ffffff',
            insertbackground='#00ff00',
            relief='flat',
            state='disabled',
            width=40
        )
        self.new_section_entry.pack(anchor='w', padx=20, pady=5, ipady=3)
        
        # Additional options for slider and dropdown
        self.extra_options_frame = tk.Frame(form_frame, bg='#1a1a1a')
        self.extra_options_frame.grid(row=8, column=0, sticky='ew', pady=(0, 20))
        
        # Create button
        create_btn = tk.Button(
            form_frame,
            text="✨ Create Setting",
            font=("Arial", 13, "bold"),
            bg='#00ff00',
            fg='#000000',
            activebackground='#00cc00',
            activeforeground='#000000',
            relief='flat',
            cursor='hand2',
            padx=40,
            pady=15,
            command=self._create_new_setting
        )
        create_btn.grid(row=9, column=0, pady=30)
        
        form_frame.columnconfigure(0, weight=1)
        
        # Initialize value input for default type
        self._on_type_change(None)
    
    def _on_type_change(self, event):
        """Update value input based on selected type"""
        # Clear existing widgets
        for widget in self.value_widget_frame.winfo_children():
            widget.destroy()
        for widget in self.extra_options_frame.winfo_children():
            widget.destroy()
        
        setting_type = self.new_setting_type.get()
        
        if setting_type == 'Checkbox (Boolean)':
            self.new_value_var = tk.BooleanVar(value=True)
            tk.Checkbutton(
                self.value_widget_frame,
                text="Enabled",
                variable=self.new_value_var,
                font=("Arial", 10),
                bg='#1a1a1a',
                fg='#00ff00',
                selectcolor='#0a0a0a',
                activebackground='#1a1a1a'
            ).pack(anchor='w')
        
        elif setting_type == 'Text Input':
            self.new_value_var = tk.StringVar()
            tk.Entry(
                self.value_widget_frame,
                textvariable=self.new_value_var,
                font=("Arial", 10),
                bg='#0a0a0a',
                fg='#ffffff',
                insertbackground='#00ff00',
                relief='flat',
                width=40
            ).pack(anchor='w', ipady=5)
        
        elif setting_type == 'Slider (Number)':
            # Slider with min/max/resolution inputs
            self.new_value_var = tk.DoubleVar(value=50.0)
            
            slider_container = tk.Frame(self.value_widget_frame, bg='#1a1a1a')
            slider_container.pack(fill=tk.X)
            
            value_label = tk.Label(
                slider_container,
                text="50.0",
                bg='#1a1a1a',
                fg='#00ff00',
                font=("Arial", 10, "bold"),
                width=8
            )
            value_label.pack(side=tk.RIGHT)
            
            def update_label(v):
                value_label.config(text=f"{float(v):.1f}")
            
            slider = tk.Scale(
                slider_container,
                from_=0,
                to=100,
                resolution=1.0,
                orient=tk.HORIZONTAL,
                variable=self.new_value_var,
                bg='#1a1a1a',
                fg='#00ff00',
                troughcolor='#0a0a0a',
                highlightthickness=0,
                showvalue=0,
                command=update_label
            )
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Extra options for slider
            tk.Label(
                self.extra_options_frame,
                text="Slider Range Configuration:",
                font=("Arial", 10, "bold"),
                bg='#1a1a1a',
                fg='#ffaa00'
            ).pack(anchor='w', pady=(0, 10))
            
            range_frame = tk.Frame(self.extra_options_frame, bg='#1a1a1a')
            range_frame.pack(fill=tk.X)
            
            # Min value
            tk.Label(range_frame, text="Min:", font=("Arial", 9), bg='#1a1a1a', fg='#cccccc').grid(row=0, column=0, sticky='w', padx=(0, 5))
            self.slider_min = tk.Entry(range_frame, font=("Arial", 9), bg='#0a0a0a', fg='#ffffff', width=10)
            self.slider_min.insert(0, "0")
            self.slider_min.grid(row=0, column=1, padx=5)
            
            # Max value
            tk.Label(range_frame, text="Max:", font=("Arial", 9), bg='#1a1a1a', fg='#cccccc').grid(row=0, column=2, sticky='w', padx=(20, 5))
            self.slider_max = tk.Entry(range_frame, font=("Arial", 9), bg='#0a0a0a', fg='#ffffff', width=10)
            self.slider_max.insert(0, "100")
            self.slider_max.grid(row=0, column=3, padx=5)
            
            # Resolution
            tk.Label(range_frame, text="Step:", font=("Arial", 9), bg='#1a1a1a', fg='#cccccc').grid(row=0, column=4, sticky='w', padx=(20, 5))
            self.slider_resolution = tk.Entry(range_frame, font=("Arial", 9), bg='#0a0a0a', fg='#ffffff', width=10)
            self.slider_resolution.insert(0, "1.0")
            self.slider_resolution.grid(row=0, column=5, padx=5)
        
        elif setting_type == 'Dropdown (List)':
            self.new_value_var = tk.StringVar()
            
            dropdown_frame = tk.Frame(self.value_widget_frame, bg='#1a1a1a')
            dropdown_frame.pack(fill=tk.X)
            
            self.dropdown_combo = ttk.Combobox(
                dropdown_frame,
                textvariable=self.new_value_var,
                state='readonly',
                font=("Arial", 10),
                style='Dark.TCombobox',
                width=37
            )
            self.dropdown_combo.pack(side=tk.LEFT)
            
            # Extra options for dropdown
            tk.Label(
                self.extra_options_frame,
                text="Dropdown Options (comma-separated):",
                font=("Arial", 10, "bold"),
                bg='#1a1a1a',
                fg='#ffaa00'
            ).pack(anchor='w', pady=(0, 10))
            
            self.dropdown_options = tk.Entry(
                self.extra_options_frame,
                font=("Arial", 10),
                bg='#0a0a0a',
                fg='#ffffff',
                insertbackground='#00ff00',
                relief='flat',
                width=40
            )
            self.dropdown_options.pack(anchor='w', ipady=5)
            self.dropdown_options.insert(0, "Option1, Option2, Option3")
            
            # Update dropdown when options change
            def update_dropdown_options(*args):
                options = [opt.strip() for opt in self.dropdown_options.get().split(',') if opt.strip()]
                self.dropdown_combo['values'] = options
                if options:
                    self.dropdown_combo.current(0)
            
            self.dropdown_options.bind('<KeyRelease>', update_dropdown_options)
            update_dropdown_options()
    
    def _on_section_choice_change(self):
        """Enable/disable section inputs based on choice"""
        if self.section_choice.get() == 'existing':
            self.existing_section_dropdown.config(state='readonly')
            self.new_section_entry.config(state='disabled')
        else:
            self.existing_section_dropdown.config(state='disabled')
            self.new_section_entry.config(state='normal')
    
    def _sanitize_key_name(self, display_name: str) -> str:
        """Convert display name to valid config key (replace spaces with underscores, lowercase)"""
        # Remove special characters, replace spaces with underscores
        sanitized = re.sub(r'[^\w\s]', '', display_name)
        sanitized = sanitized.replace(' ', '_').lower()
        return sanitized
    
    def _create_new_setting(self):
        """Create and integrate a new setting"""
        try:
            # Validate inputs
            display_name = self.new_setting_name.get().strip()
            if not display_name:
                messagebox.showwarning("Missing Name", "Please enter a setting name.", parent=self.dialog)
                return
            
            setting_type = self.new_setting_type.get()
            
            # Get section
            if self.section_choice.get() == 'existing':
                section = self.existing_section_dropdown.get()
                if not section:
                    messagebox.showwarning("Missing Section", "Please select a section.", parent=self.dialog)
                    return
            else:
                section = self.new_section_entry.get().strip()
                if not section:
                    messagebox.showwarning("Missing Section", "Please enter a new section name.", parent=self.dialog)
                    return
            
            # Sanitize key name
            key_name = self._sanitize_key_name(display_name)
            
            # Check if key already exists in section
            if self.config.has_section(section) and self.config.has_option(section, key_name):
                if not messagebox.askyesno("Key Exists", 
                    f"Setting '{key_name}' already exists in [{section}].\n\nOverwrite?",
                    parent=self.dialog):
                    return
            
            # Get default value based on type
            if setting_type == 'Checkbox (Boolean)':
                default_value = 'true' if self.new_value_var.get() else 'false'
                widget_type = 'checkbox'
                widget_kwargs = {}
            
            elif setting_type == 'Text Input':
                default_value = self.new_value_var.get()
                widget_type = 'entry'
                widget_kwargs = {'width': 40}
            
            elif setting_type == 'Slider (Number)':
                default_value = str(self.new_value_var.get())
                widget_type = 'slider'
                
                try:
                    min_val = float(self.slider_min.get())
                    max_val = float(self.slider_max.get())
                    resolution = float(self.slider_resolution.get())
                    
                    if min_val >= max_val:
                        messagebox.showwarning("Invalid Range", "Min value must be less than Max value.", parent=self.dialog)
                        return
                    
                    widget_kwargs = {
                        'from_': min_val,
                        'to': max_val,
                        'resolution': resolution
                    }
                except ValueError:
                    messagebox.showwarning("Invalid Range", "Please enter valid numbers for slider range.", parent=self.dialog)
                    return
            
            elif setting_type == 'Dropdown (List)':
                options = [opt.strip() for opt in self.dropdown_options.get().split(',') if opt.strip()]
                if not options:
                    messagebox.showwarning("Missing Options", "Please enter dropdown options.", parent=self.dialog)
                    return
                
                default_value = self.new_value_var.get()
                if not default_value:
                    default_value = options[0]
                
                widget_type = 'dropdown'
                widget_kwargs = {'values': options, 'width': 30}
            
            # Confirm creation
            if not messagebox.askyesno("Confirm Creation",
                f"Create new setting?\n\n"
                f"Display Name: {display_name}\n"
                f"Key: {key_name}\n"
                f"Section: {section}\n"
                f"Type: {setting_type}\n"
                f"Default: {default_value}\n\n"
                f"This will update:\n"
                f"• config.ini\n"
                f"• setup_wizard.py\n"
                f"• settings_dialog.py\n"
                f"• loader.py",
                parent=self.dialog):
                return
            
            # Add to config.ini
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            self.config.set(section, key_name, default_value)
            self._save_to_config()
            
            # Update settings_dialog.py itself to reflect the change
            self._update_settings_dialog_file(section, key_name, display_name, widget_type, widget_kwargs)
            
            # Update setup_wizard.py
            self._update_setup_wizard(section, key_name, display_name, widget_type, default_value, widget_kwargs)
            
            # Update loader.py
            self._update_loader(section, key_name, widget_type)
            
            # Show success
            messagebox.showinfo("Success! 🎉",
                f"Setting '{display_name}' created successfully!\n\n"
                f"Added to:\n"
                f"✅ config.ini\n"
                f"✅ setup_wizard.py\n"
                f"✅ settings_dialog.py\n"
                f"✅ loader.py\n\n"
                f"Please restart JARVIS to apply changes.",
                parent=self.dialog)
            
            # Reload dialog to show new setting
            self.dialog.destroy()
            if self.temp_root:
                self.temp_root.destroy()
            
            # Reopen dialog
            open_settings_dialog(self.parent)
            
        except Exception as e:
            logger.error(f"Failed to create setting: {e}")
            messagebox.showerror("Error", f"Failed to create setting:\n{e}", parent=self.dialog)
    
    def _update_settings_dialog_file(self, section: str, key: str, display_name: str,
                                   widget_type: str, widget_kwargs: dict):
        """Dynamically update this file to add the new setting to the UI."""
        try:
            dialog_path = Path(__file__)
            content = dialog_path.read_text(encoding='utf-8')

            # 1. Sanitize section name for use in a Python method name.
            sanitized_section_name = re.sub(r'[^a-zA-Z0-9_]+', '_', section.strip()).lower()
            target_method_name = f"_create_{sanitized_section_name}_tab"

            # 2. Create the new line of code for the setting widget.
            # Note: `from_` is a keyword, so we handle it by removing the trailing underscore for kwargs.
            kwargs_str = ", ".join([f"{k.strip('_')}={repr(v)}" for k, v in widget_kwargs.items()])
            new_row_code = f"        self._create_setting_row(frame, \"{display_name}\", '{widget_type}', '{section}', '{key}', {kwargs_str})\n"

            # 3. Check if the tab creation method already exists.
            method_pattern = re.compile(rf"def {target_method_name}\(self\):", re.DOTALL)
            match = method_pattern.search(content)

            if match:
                # CASE 1: Method exists. Add the new setting to it.
                method_start_index = match.start()
                
                # Define the search area: from the start of our method to the start of the next one.
                next_method_match = re.search(r"\n\s*def _", content[method_start_index + 1:])
                if next_method_match:
                    search_area_end = method_start_index + 1 + next_method_match.start()
                else:
                    search_area_end = len(content) # It's the last method
                
                # Find the last setting row within this method to append after it.
                last_row_match = None
                for m in re.finditer(r"^\s*self\._create_setting_row\(.*\)\n", content[method_start_index:search_area_end], re.MULTILINE):
                    last_row_match = m

                if last_row_match:
                    # Insert the new code right after the last existing setting row.
                    insertion_point = method_start_index + last_row_match.end()
                    content = content[:insertion_point] + new_row_code + content[insertion_point:]
                else:
                    # Method exists but is empty. Insert after the "frame = ..." line.
                    frame_line_match = re.search(r"^\s*frame = .*\n", content[method_start_index:search_area_end], re.MULTILINE)
                    if frame_line_match:
                        insertion_point = method_start_index + frame_line_match.end()
                        content = content[:insertion_point] + new_row_code + content[insertion_point:]
                    else:
                        raise Exception(f"Could not find a place to insert the setting in method {target_method_name}")
            else:
                # CASE 2: New section. Create a new tab method and add a call to it in _create_ui.
                icon = "⚙️"  # Generic icon for new tabs
                
                new_method_code = f"""
    def {target_method_name}(self):
        \"\"\"{section} settings\"\"\"
        frame = self._create_scrollable_tab(\"{section}\", \"{icon}\")
{new_row_code}"""
                # Use a STATIC, reliable anchor to insert the new method definition.
                # We will place it right before the `_create_api_keys_tab` method.
                insertion_marker = "\n    def _create_api_keys_tab(self):"
                if insertion_marker not in content:
                    raise Exception(f"Code anchor '{insertion_marker.strip()}' not found in settings_dialog.py!")
                
                content = content.replace(insertion_marker, new_method_code + insertion_marker, 1)

                # Now, insert the call to the new method in the `_create_ui` method.
                ui_call_marker = "\n        self._create_api_keys_tab()"
                new_call_code = f"\n        self.{target_method_name}()"
                if ui_call_marker not in content:
                    raise Exception(f"Code anchor '{ui_call_marker.strip()}' not found in settings_dialog.py!")

                content = content.replace(ui_call_marker, new_call_code + ui_call_marker, 1)

            dialog_path.write_text(content, encoding='utf-8')
            logger.info(f"✅ Updated settings_dialog.py with new setting '{key}' in section '{section}'")

        except Exception as e:
            logger.error(f"Failed to self-update settings_dialog.py: {e}")
            raise
    
    def _update_setup_wizard(self, section: str, key: str, display_name: str, 
                            widget_type: str, default_value: str, widget_kwargs: dict):
        """Add new setting to setup_wizard.py"""
        try:
            wizard_path = Path(__file__).parent.parent / 'utils' / 'setup_wizard.py'
            
            if not wizard_path.exists():
                logger.warning("setup_wizard.py not found, skipping update")
                return
            
            with open(wizard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the appropriate _create_settings_section or _create_checkbox_section call
            if widget_type == 'checkbox':
                # Find _create_checkbox_section for this section
                pattern = rf"self\._create_checkbox_section\(['\"]({section})['\"],\s*\[(.*?)\]\)"
                match = re.search(pattern, content, re.DOTALL)
                
                if match:
                    # Add to existing checkbox section
                    settings_list = match.group(2)
                    new_entry = f'\n            ("{display_name}", "{key}", {default_value.lower() == "true"}),'
                    
                    # Insert before the closing bracket
                    insertion_point = match.end(2)
                    content = content[:insertion_point] + new_entry + content[insertion_point:]
                else:
                    # Create new checkbox section - find _show_settings method
                    settings_method_match = re.search(r'def _show_settings\(self\):.*?(?=\n    def |\Z)', content, re.DOTALL)
                    if settings_method_match:
                        method_end = settings_method_match.end()
                        new_section = f'\n        self._create_checkbox_section("{section}", [\n            ("{display_name}", "{key}", {default_value.lower() == "true"}),\n        ])\n'
                        content = content[:method_end] + new_section + content[method_end:]
            
            else:
                # Find _create_settings_section for this section
                pattern = rf"self\._create_settings_section\(['\"]({section})['\"],\s*\[(.*?)\]\)"
                match = re.search(pattern, content, re.DOTALL)
                
                if match:
                    # Add to existing settings section
                    settings_list = match.group(2)
                    new_entry = f'\n            ("{display_name}", "{key}", "{default_value}"),'
                    
                    insertion_point = match.end(2)
                    content = content[:insertion_point] + new_entry + content[insertion_point:]
                else:
                    # Create new settings section
                    settings_method_match = re.search(r'def _show_settings\(self\):.*?(?=\n    def |\Z)', content, re.DOTALL)
                    if settings_method_match:
                        method_end = settings_method_match.end()
                        new_section = f'\n        self._create_settings_section("{section}", [\n            ("{display_name}", "{key}", "{default_value}"),\n        ])\n'
                        content = content[:method_end] + new_section + content[method_end:]
            
            with open(wizard_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ Updated setup_wizard.py with {key}")
            
        except Exception as e:
            logger.error(f"Failed to update setup_wizard.py: {e}")
            raise
    
    def _update_loader(self, section: str, key: str, widget_type: str):
        """Add new setting to loader.py"""
        try:
            loader_path = Path(__file__).parent.parent / 'config' / 'loader.py'
            
            if not loader_path.exists():
                logger.warning("loader.py not found, skipping update")
                return
            
            with open(loader_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the Config class __init__ method
            init_match = re.search(r'def __init__\(self\):.*?(?=\n\n# Create a single|\Z)', content, re.DOTALL)
            
            if init_match:
                init_content = init_match.group(0)
                
                # Check if section comment exists
                section_comment = f"# [{section}]"
                
                # Determine the parser method based on widget type
                if widget_type == 'checkbox':
                    parser_method = 'getboolean'
                elif widget_type == 'slider':
                    # Sliders can be int or float, but getfloat is safer
                    parser_method = 'getfloat'
                else: # Text and Dropdown
                    parser_method = 'get'
                
                new_line = f"        self.{key} = parser.{parser_method}('{section}', '{key}')"
                
                # Find where to insert
                section_pattern = re.compile(rf"{re.escape(section_comment)}(.*?)(\n\s*# \[|\Z)", re.DOTALL)
                section_match = section_pattern.search(init_content)
                
                if section_match:
                    # Section exists, add to the end of it
                    insertion_point = section_match.end(1)
                    init_content = init_content[:insertion_point].rstrip() + '\n' + new_line + init_content[insertion_point:]
                else:
                    # Add new section at the end of the method
                    init_content = init_content.rstrip() + f"\n\n        {section_comment}\n{new_line}\n"
                
                # Replace the old __init__ with updated one
                content = content[:init_match.start()] + init_content + content[init_match.end():]
            
            with open(loader_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ Updated loader.py with {key}")
            
        except Exception as e:
            logger.error(f"Failed to update loader.py: {e}")
            raise
    
    def _load_current_values(self):
        """Load values from config"""
        logger.info("📄 Loading settings from config...")
        loaded_count = 0
        
        for widget_key, (widget, var) in self.widgets.items():
            section, key = widget_key.split('.')
            
            if not self.config.has_section(section):
                logger.warning(f"❌ Section '{section}' not found")
                continue
            
            if not self.config.has_option(section, key):
                logger.warning(f"❌ Key '{key}' not found in [{section}]")
                continue
            
            try:
                raw_value = self.config.get(section, key).strip()
                
                if isinstance(var, tk.BooleanVar):
                    value = raw_value.lower() in ('true', '1', 'yes', 'on')
                    var.set(value)
                    self.current_values[widget_key] = value
                
                elif isinstance(var, tk.DoubleVar):
                    value = float(raw_value)
                    var.set(value)
                    self.current_values[widget_key] = value
                
                elif isinstance(var, tk.IntVar):
                    value = int(float(raw_value))
                    var.set(value)
                    self.current_values[widget_key] = value
                
                elif isinstance(var, tk.StringVar):
                    value = raw_value
                    var.set(value)
                    self.current_values[widget_key] = value
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value)
                
                loaded_count += 1
            
            except Exception as e:
                logger.error(f"❌ Failed to load {widget_key}: {e}")
        
        self.dialog.update_idletasks()
        logger.info(f"✅ Successfully loaded {loaded_count}/{len(self.widgets)} settings")
        
        # Force refresh all widgets
        for widget_key, (widget, var) in self.widgets.items():
            try:
                if isinstance(widget, tk.Scale):
                    current_val = var.get()
                    widget.set(current_val)
                    if hasattr(widget, 'value_label'):
                        widget.value_label.config(text=f"{float(current_val):.1f}")
                elif isinstance(widget, tk.Checkbutton):
                    if var.get():
                        widget.select()
                    else:
                        widget.deselect()
                elif isinstance(widget, tk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, str(var.get()))
            except Exception as e:
                logger.debug(f"Widget refresh error for {widget_key}: {e}")
    
    def _on_value_change(self, widget_key: str, value: Any):
        """Track value changes"""
        self.current_values[widget_key] = value
        self.changes_made = (self.current_values != self.original_values)
    
    def _save_to_config(self):
        """Save to config.ini"""
        try:
            for widget_key, value in self.current_values.items():
                section, key = widget_key.split('.')
                
                if isinstance(value, bool):
                    self.config.set(section, key, 'true' if value else 'false')
                else:
                    # Escape % so configparser doesn't crash on read
                    safe_value = str(value).replace('%', '%%')
                    self.config.set(section, key, safe_value)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            logger.info("✅ Settings saved")
            return True
        
        except Exception as e:
            logger.error(f"❌ Save failed: {e}")
            messagebox.showerror("Save Error", f"Failed to save:\n{e}", parent=self.dialog)
            return False
    
    def _revert_changes(self):
        """Revert to original"""
        self.current_values = self.original_values.copy()
        for widget_key, (widget, var) in self.widgets.items():
            if widget_key in self.original_values:
                var.set(self.original_values[widget_key])
        self.changes_made = False
    
    def _on_cancel(self):
        """Cancel button"""
        if self.changes_made:
            if not messagebox.askyesno("Unsaved Changes", "Discard changes?", parent=self.dialog):
                return
        
        self._cleanup_and_close()
    
    def _on_apply(self):
        """Apply button"""
        if not self.changes_made:
            messagebox.showinfo("No Changes", "No changes to apply.", parent=self.dialog)
            return
        
        if self._save_to_config():
            self.original_values = self.current_values.copy()
            self.changes_made = False
            messagebox.showinfo("Applied", "Settings saved!\n\nSome may require restart.", parent=self.dialog)
    
    def _on_ok(self):
        """OK button"""
        if self.changes_made:
            if not self._save_to_config():
                return
            
            response = messagebox.askyesnocancel(
                "Restart Required",
                "Settings saved!\n\nRestart JARVIS now?",
                parent=self.dialog
            )
            
            if response is None:
                return
            
            self._cleanup_and_close()
            
            if response:
                self._restart_program()
        else:
            self._cleanup_and_close()
    
    def _cleanup_and_close(self):
        """Properly cleanup dialog and temp root"""
        try:
            if hasattr(self, 'dialog') and self.dialog:
                self.dialog.destroy()
        except:
            pass
        
        try:
            if hasattr(self, 'temp_root') and self.temp_root:
                self.temp_root.quit()
                self.temp_root.destroy()
                self.temp_root = None
                logger.debug("✅ Cleaned up temporary root window")
        except:
            pass
    
    def _restart_program(self):
        """Restart JARVIS"""
        try:
            import sys, os
            python = sys.executable
            os.execl(python, python, "main.py")
        except Exception as e:
            messagebox.showerror("Restart Failed", f"Failed to restart:\n{e}\n\nPlease restart manually.")


def open_settings_dialog(parent=None):
    """Open settings dialog"""
    dialog = SettingsDialog(parent)
    
    if hasattr(dialog, 'temp_root') and dialog.temp_root:
        try:
            if hasattr(dialog, 'dialog') and dialog.dialog:
                dialog.dialog.deiconify()
                dialog.dialog.focus_force()
            
            dialog.temp_root.mainloop()
        except:
            pass
