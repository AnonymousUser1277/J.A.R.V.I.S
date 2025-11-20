"""
Main GUI handler - Enhanced with typing and code view buttons
"""

import logging
import queue
import threading
import time
import tkinter as tk
import ctypes
from ctypes import byref, c_int, windll
from ctypes import wintypes
from audio.volume import VolumeController
from automation.hotkeys import HotkeyManager
from core.context_manager import OptimizedContextManager
from core.notification import ProactiveNotifier
from core.local_server import start_local_server
from monitors import start_all_monitors
from utils.logger import GuiLogger
from audio.stt_fallback import STTManager
from config.settings import ENABLE_STT
from .terminal import PersistentTerminal
from .tray import create_tray_icon
from config.loader import settings
from ui.theme_manager import get_theme_manager
from integrations.mobile_companion import start_mobile_companion
logger = logging.getLogger(__name__)

class AIAssistantGUI:
    """Main GUI handler with enhanced controls"""
    
    def __init__(self, client, listener, startup_ui=None):
        self.state_lock = threading.RLock()
        self.client = client
        self.listener = listener
        self.volume_controller = VolumeController()
        self.show_context_in_terminal = False
        
        # Context Manager
        self.context_manager = OptimizedContextManager()
        start_local_server(self.context_manager)
        # Root window
        self.root = tk.Tk()
        self.root.withdraw()
        self.stt_manager = STTManager(listener, gui_handler=self)
        # Terminal
        self.terminal = PersistentTerminal(self.root)
        self.terminal.gui_handler = self
        self.theme_manager = get_theme_manager()
        self.theme = self.theme_manager.get_theme()
        # Start all monitoring threads
        start_all_monitors(self.context_manager)
        
        # Proactive notifier
        self.notifier = ProactiveNotifier(self.context_manager, self)
        self.mobile_companion = start_mobile_companion(self, port=5555)
        # Main control dialog (mic button)
        self.control_dialog = None
        # self.mic_button = None
        self.processing_animation_job = None
        # ✅ NEW: Enhanced button controls
        self.code_view_fade_job = None
        self.generated_code_text = None  # Store generated code
        self.hover_dialog = None  # Separate dialog for hover buttons
        self._hide_buttons_job = None
        self.create_control_dialog()
        
        # Input/Response dialogs
        self.input_dialog = None
        self.input_visible = False
        self.response_dialog = None
        
        # Command history
        from config.settings import HISTORY_FILE
        self.command_history = self.load_history()
        self.history_index = -1
        self.last_command = None
        # Wake word detection
        self.wake_word_active = True
        self.auto_turn_off_mic = False
        self.wake_word_thread = None
        self.start_wake_word_detection()
        from ai.task_queue import get_processor

        self.ai_processor = get_processor(self.client, self)
        # Task queue
        self.task_queue = queue.Queue()
        self.process_task_queue()
        
        # Hotkey manager
        self.hotkey_manager = HotkeyManager(self)
        
        # System tray
        create_tray_icon(self)
        from audio.coordinator import AudioCoordinator
        self.audio_coordinator = AudioCoordinator()
        # Redirect output
        import sys
        sys.stdout = GuiLogger(self)
        sys.stderr = GuiLogger(self)
    
    # ============= ENHANCED CONTROL DIALOG =============
        try:
            import keyboard
            keyboard.add_hotkey('alt+shift+c', lambda: self.queue_gui_task(lambda: self.show_generated_code_dialog()))
        except Exception as e:
            logger.warning(f"keyboard hotkeys failed: {e}")
    # In ui/gui.py, replace the entire function

    def create_control_dialog(self):
        """Create a dynamic, animated JARVIS orb."""
        self.control_dialog = tk.Toplevel(self.root)
        self.control_dialog.title("AI Assistant")
        # Use a pure black background for the best visual effects
        self.bg_color = self.theme.get('bg_primary')
        self.control_dialog.configure(bg=self.bg_color)
        self.control_dialog.attributes('-transparentcolor', self.bg_color)
        self.control_dialog.attributes('-topmost', True)
        self.control_dialog.overrideredirect(True)
        
        # --- NEW: Canvas for advanced drawing ---
        self.canvas_size = 100
        self.canvas = tk.Canvas(
            self.control_dialog,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack()

        # --- NEW: Animation state variables ---
        self.pulse_job = None
        self.pulse_direction = 1
        self.current_glow_radius = 5
        self.state = "idle" # States: idle, listening, processing, speaking

        # --- NEW: Draw the initial orb layers ---
        self.glow_outer = self.canvas.create_oval(5, 5, 95, 95, fill="", outline="#003a3a", width=3)
        self.glow_inner = self.canvas.create_oval(15, 15, 85, 85, fill="", outline="#005f5f", width=4)
        self.main_ring = self.canvas.create_oval(25, 25, 75, 75, fill="#050505", outline="#00ffff", width=3)
        self.center_icon = self.canvas.create_polygon(45, 40, 60, 50, 45, 60, fill="#00ffff", outline="")

        # --- Bind events to the canvas ---
        self.canvas.bind('<ButtonRelease-1>', self.on_mic_click) # Was '<Button-1>'
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<Enter>', self._on_hover_enter)
        self.canvas.bind('<Leave>', self._on_hover_leave)
        self.canvas.bind('<ButtonPress-1>', self.start_drag)
        # Position at bottom-right of a secondary monitor (to the right of primary)
        try:
            monitor = self._choose_display_for_control()
            x = monitor['left'] + monitor['width'] - self.canvas_size - 60
            y = monitor['top'] + monitor['height'] - self.canvas_size - 80
        except Exception:
            # fallback to primary screen
            x = self.root.winfo_screenwidth() - self.canvas_size - 60
            y = self.root.winfo_screenheight() - self.canvas_size - 80

        self.control_dialog.geometry(f"{self.canvas_size}x{self.canvas_size}+{x}+{y}")
        
        # Start the idle animation
        self._pulse_animation()

    def _update_button_state(self, new_state: str):
        """Changes the visual state and manages animations for the JARVIS orb."""
        # --- Stop any and all previous animations ---
        if self.pulse_job:
            self.root.after_cancel(self.pulse_job)
            self.pulse_job = None
        if self.processing_animation_job:
            self.root.after_cancel(self.processing_animation_job)
            self.processing_animation_job = None
        
        # --- Update state and visuals ---
        self.state = new_state
        if self.center_icon:
            self.canvas.delete(self.center_icon)
        
        if self.state == "idle":
            self.canvas.itemconfig(self.main_ring, outline="#00ffff", width=3)
            self.center_icon = self.canvas.create_polygon(45, 40, 60, 50, 45, 60, fill="#00ffff", outline="")
            self._pulse_animation() # Start new idle animation

        elif self.state == "listening":
            self.canvas.itemconfig(self.main_ring, outline="#ff4444", width=4) # Changed to red for listening
            self.center_icon = self.canvas.create_rectangle(43, 43, 57, 57, fill="#ff4444", outline="")

        elif self.state == "processing":
            self.canvas.itemconfig(self.main_ring, outline="#ffff00", width=4)
            self.center_icon = None # Clear it before starting animation
            self._start_processing_animation() # Start new processing animation

    def _pulse_animation(self):
        """Creates a gentle pulsing effect for the idle state."""
        if self.state != "idle":
            return # Stop the animation if not idle

        # Animate the outer glow
        new_width = self.current_glow_radius
        self.canvas.itemconfig(self.glow_outer, width=new_width)
        
        # Change direction at boundaries
        if self.current_glow_radius >= 8: self.pulse_direction = -1
        elif self.current_glow_radius <= 3: self.pulse_direction = 1
        
        self.current_glow_radius += self.pulse_direction * 0.5

        self.pulse_job = self.root.after(50, self._pulse_animation)

    def _get_monitors(self):
        """Return a list of monitors with geometry and primary flag using Win32 APIs."""
        monitors = []
        user32 = windll.user32

        class MONITORINFOEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
                ("szDevice", wintypes.WCHAR * 32),
            ]

        # Use generic pointer types for compatibility across Python versions
        MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(wintypes.RECT), ctypes.c_long)

        def _callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            mi = MONITORINFOEXW()
            mi.cbSize = ctypes.sizeof(mi)
            res = windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi))
            if res:
                left = mi.rcMonitor.left
                top = mi.rcMonitor.top
                right = mi.rcMonitor.right
                bottom = mi.rcMonitor.bottom
                monitors.append({
                    'left': left,
                    'top': top,
                    'right': right,
                    'bottom': bottom,
                    'width': right - left,
                    'height': bottom - top,
                    'is_primary': bool(mi.dwFlags & 1),
                    'device': mi.szDevice,
                })
            return True

        enum_proc = MonitorEnumProc(_callback)
        windll.user32.EnumDisplayMonitors(0, 0, enum_proc, 0)
        return monitors

    def _choose_display_for_control(self):
        """
        Choose monitor for control dialog
        Uses user preference if set, otherwise auto-detects
        """
        from config.monitor_config import get_monitor_config
        
        monitors = self._get_monitors()
        if not monitors:
            # Fallback
            return {
                'left': 0,
                'top': 0,
                'width': self.root.winfo_screenwidth(),
                'height': self.root.winfo_screenheight(),
                'right': self.root.winfo_screenwidth(),
                'bottom': self.root.winfo_screenheight(),
                'is_primary': True,
            }
        
        # Check user preference
        config = get_monitor_config()
        preferred_idx = config.get_preferred_monitor()
        
        if preferred_idx is not None and 0 <= preferred_idx < len(monitors):
            logger.info(f"📺 Using preferred monitor #{preferred_idx}")
            return monitors[preferred_idx]
        
        # Auto-detect: find secondary monitor to the right
        primary = next((m for m in monitors if m.get('is_primary')), monitors[0])
        right_monitors = [m for m in monitors if m['left'] >= primary['right']]
        
        if right_monitors:
            chosen = min(right_monitors, key=lambda m: m['left'])
            logger.info(f"📺 Auto-selected secondary monitor")
            return chosen
        
        # Fallback to primary
        logger.info(f"📺 Using primary monitor")
        return primary

    def _on_hover_enter(self, event):
        """Make the orb brighter on hover."""
        if self.state == "idle":
            self.canvas.itemconfig(self.main_ring, outline="#ffffff")
            self.canvas.itemconfig(self.glow_inner, outline="#00ffff")

    def _on_hover_leave(self, event):
        """Return the orb to normal when not hovering."""
        if self.state == "idle":
            self.canvas.itemconfig(self.main_ring, outline="#00ffff")
            self.canvas.itemconfig(self.glow_inner, outline="#005f5f")
    
    def show_code_view_button(self, code_text):
        """Enhanced with hint notification"""
        self.generated_code_text = code_text
        
        # Show hint in terminal
        # self.show_terminal_output(
        #     "💡 Code generated! Press Alt+Shift+C to view",
        #     color="cyan"
        # )
        
        # Show temporary overlay hint (first time only)
        if not hasattr(self, '_code_hint_shown'):
            self._show_code_view_hint()
            self._code_hint_shown = True


    def _show_code_view_hint(self):
        """Show temporary overlay with keyboard shortcut hint"""
        import tkinter as tk
        
        hint = tk.Toplevel(self.root)
        hint.overrideredirect(True)
        hint.attributes('-topmost', True)
        hint.attributes('-alpha', 0.9)
        hint.configure(bg='#1e1e1e')
        
        frame = tk.Frame(hint, bg='#2d2d2d', padx=20, pady=15)
        frame.pack(padx=3, pady=3)
        
        tk.Label(
            frame,
            text="💡 Tip",
            font=("Arial", 12, "bold"),
            bg='#2d2d2d',
            fg='#ffff00'
        ).pack()
        
        tk.Label(
            frame,
            text="Press Alt+Shift+C to view generated code",
            font=("Arial", 11),
            bg='#2d2d2d',
            fg='#ffffff'
        ).pack(pady=5)
        
        # Position near control orb
        try:
            orb_x = self.control_dialog.winfo_x()
            orb_y = self.control_dialog.winfo_y()
            
            hint.update_idletasks()
            x = orb_x - hint.winfo_width() - 20
            y = orb_y
            hint.geometry(f"+{x}+{y}")
        except:
            # Center as fallback
            hint.update_idletasks()
            x = (self.root.winfo_screenwidth() - hint.winfo_width()) // 2
            y = 100
            hint.geometry(f"+{x}+{y}")
        
        # Auto-close after 5 seconds
        def fade_out():
            alpha = 0.9
            while alpha > 0:
                try:
                    hint.attributes('-alpha', alpha)
                    hint.update()
                    alpha -= 0.1
                    time.sleep(0.05)
                except:
                    break
            try:
                hint.destroy()
            except:
                pass
        
        import threading
        threading.Thread(target=lambda: (time.sleep(5), fade_out()), daemon=True).start()
    def show_generated_code_dialog(self):
        """Show generated code in dialog"""
        
        if not self.generated_code_text:
            return
        
        # Create code dialog (reuse existing show_response but with code styling)
        self._create_code_dialog(self.generated_code_text)
    # In AIAssistantGUI class
    def _start_processing_animation(self, angle=0):
        """Creates a smooth, spinning arc for the processing state."""
        # Stop the animation if the state has changed
        if self.state != "processing":
            return

        # Clear the previous arc
        if self.center_icon:
            self.canvas.delete(self.center_icon)

        # Draw the new arc at a new angle
        self.center_icon = self.canvas.create_arc(
            30, 30, 70, 70, 
            start=angle, 
            extent=150, # A nice long arc
            style=tk.ARC, 
            outline="#ffff00", 
            width=4
        )
        
        # Schedule the next frame of the animation
        new_angle = (angle + 10) % 360
        self.processing_animation_job = self.root.after(
            15, # Approx 66 FPS
            lambda: self._start_processing_animation(new_angle)
        )
    def _create_code_dialog(self, code_text):
        """Create dialog to display generated code"""
        # Close existing response dialog
        if hasattr(self, 'response_dialog') and self.response_dialog:
            try:
                self.response_dialog.destroy()
                self.response_dialog = None
            except:
                pass
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Generated Code")
        dialog.configure(bg='#1e1e1e')
        dialog.attributes('-topmost', True)
        dialog.overrideredirect(True)
        
        # Make draggable only from the header (so inner widgets like the code Text
        # are selectable without moving the window)

        header_frame = tk.Frame(dialog, bg='#2d2d2d')
        header_frame.pack(fill=tk.X, side=tk.TOP)

        header_label = tk.Label(
            header_frame,
            text="Generated Code",
            bg='#2d2d2d',
            fg='#ffffff',
            font=("Arial", 11, "bold")
        )
        header_label.pack(side=tk.LEFT, padx=8, pady=6)

        # optional close button on header
        def _close_dialog():
            try:
                dialog.destroy()
            except:
                pass

        close_btn = tk.Button(header_frame, text='✕', command=_close_dialog, bg='#2d2d2d', fg='#ffaaaa', bd=0, relief='flat', padx=6)
        close_btn.pack(side=tk.RIGHT, padx=6, pady=4)

        def start_drag(event):
            """Start dragging the code dialog (record root coords)."""
            try:
                self._code_dialog_drag_root_x = event.x_root
                self._code_dialog_drag_root_y = event.y_root
            except Exception:
                self._code_dialog_drag_root_x = event.x
                self._code_dialog_drag_root_y = event.y

            try:
                self._code_dialog_start_x = dialog.winfo_x()
                self._code_dialog_start_y = dialog.winfo_y()
            except Exception:
                self._code_dialog_start_x = 0
                self._code_dialog_start_y = 0

        def on_drag(event):
            """Handle dragging of the code dialog using absolute screen coordinates."""
            try:
                dx = (event.x_root - getattr(self, '_code_dialog_drag_root_x', event.x))
                dy = (event.y_root - getattr(self, '_code_dialog_drag_root_y', event.y))
                x = int(getattr(self, '_code_dialog_start_x', dialog.winfo_x()) + dx)
                y = int(getattr(self, '_code_dialog_start_y', dialog.winfo_y()) + dy)
                dialog.geometry(f"+{x}+{y}")
            except Exception:
                # fallback: no-op
                pass

        # Bind drag only to header so inner text remains selectable
        header_frame.bind('<Button-1>', start_drag)
        header_frame.bind('<B1-Motion>', on_drag)
        
        # Frame
        frame = tk.Frame(dialog, bg='#1e1e1e', padx=15, pady=15)
        frame.pack()
        
        # Text widget with code styling
        text_widget = tk.Text(
            frame,
            font=("Consolas", 14),
            bg='#0a0a0a',
            fg='#00ff00',
            relief='flat',
            width=80,
            height=20,
            wrap=tk.WORD
        )
        text_widget.pack()
        text_widget.insert('1.0', code_text)
        text_widget.config(state='disabled')
        
        # Position
        dialog.update_idletasks()
        x = 1
        y = 1
        dialog.geometry(f"+{x}+{y}")
        
        # Apply effects
        dialog.attributes('-alpha', 0.90)
        dialog.after(100, lambda: self.apply_blur_effect(dialog))
        
        # Hover handlers
        hover_state = {'hover': False}
        
        def on_hover(event):
            hover_state['hover'] = True
            if hasattr(self, 'response_fade_job') and self.response_fade_job:
                self.root.after_cancel(self.response_fade_job)
                self.response_fade_job = None
            dialog.attributes('-alpha', 0.95)
        
        def on_leave(event):
            hover_state['hover'] = False
            schedule_fade()
        
        def schedule_fade():
            if hasattr(self, 'response_fade_job') and self.response_fade_job:
                self.root.after_cancel(self.response_fade_job)
            self.response_fade_job = self.root.after(3000, start_fade)
        
        def start_fade():
            if not hover_state['hover']:
                fade_out(1.0)
        
        def fade_out(alpha):
            if not hover_state['hover']:
                if alpha > 0:
                    try:
                        dialog.attributes('-alpha', alpha)
                        self.root.after(50, lambda: fade_out(alpha - 0.07))
                    except:
                        pass
                else:
                    try:
                        dialog.destroy()
                    except:
                        pass
        
        dialog.bind('<Enter>', on_hover)
        dialog.bind('<Leave>', on_leave)
        frame.bind('<Enter>', on_hover)
        frame.bind('<Leave>', on_leave)
        text_widget.bind('<Enter>', on_hover)
        text_widget.bind('<Leave>', on_leave)
        
        schedule_fade()
        
        self.response_dialog = dialog
    
    def start_drag(self, event):
        """Start dragging"""
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_drag(self, event):
        """Handle dragging"""
        x = self.control_dialog.winfo_x() + event.x - self.drag_x
        y = self.control_dialog.winfo_y() + event.y - self.drag_y
        self.control_dialog.geometry(f"+{x}+{y}")
    
    # ============= MIC CONTROL (keep existing) =============

    def on_mic_click(self, event=None):
        """Toggle microphone OR Stop TTS if speaking"""
        if self.listener is None:
            self.show_terminal_output("⚠️ Voice control unavailable", color="yellow")
            return

        # 1. STOP SPEAKING if currently talking
        if self.audio_coordinator.is_speaking:
            from audio.tts import stop_speaking
            stop_speaking()
            # Also cancel any queued code execution output
            self.queue_gui_task(lambda: self._update_button_state("idle"))
            return

        # 2. Normal Toggle Logic
        if not self.listener.is_listening:
            # Start Listening
            self._update_button_state("listening")
            self.stop_wake_word_detection()
            self.auto_turn_off_mic = False
            self.volume_controller.lower_volume(target_percent=5)
            threading.Thread(target=self.record_speech, daemon=True).start()
        else:
            # Stop Listening manually
            self._update_button_state("idle")
            self.listener.stop_recording()
            self.volume_controller.restore_volume()
    
    def toggle_mic(self):
        """Toggle mic with hotkey"""
        self.on_mic_click()
    
    def record_speech(self):
        """Record speech and process - WITH PARALLEL OPTION"""
        from config.settings import IGNORE_WORDS, STOP_WORDS
        
        try:
            while not self.listener.stop_listening:
                speech = self.audio_coordinator.listen(
                    self.listener,
                    check_stop_words=False,
                    stop_words=None
                )
                
                if speech == "STOP_COMMAND":
                    self.show_terminal_output("Ok.")
                    self.play_stop_melody()
                    break
                
                if speech and not self.listener.stop_listening:
                    speech_lower = speech.lower().strip()
                    if speech_lower in IGNORE_WORDS:
                        continue
                    
                    # Check background processing
                    if speech_lower.startswith("background "):
                        from ai.task_queue import TaskPriority
                        actual_prompt = speech[11:]
                        self.ai_processor.submit_task(
                            actual_prompt,
                            priority=TaskPriority.LOW
                        )
                        self.show_terminal_output(f"📋 Queued: {actual_prompt}", color="cyan")
                        continue
                    
                    # --- VISUAL STATE UPDATE: PROCESSING ---
                    self.queue_gui_task(lambda: self._update_button_state("processing"))
                    
                    # Execute the logic
                    from ai.instructions import generate_instructions
                    generate_instructions(speech, self.client, self)
                    
                    # --- [FIX ADDED HERE] VISUAL STATE UPDATE: IDLE ---
                    # This ensures the ring turns blue again before listening starts
                    self.queue_gui_task(lambda: self._update_button_state("idle"))
                    
                    if self.auto_turn_off_mic:
                        self.listener.stop_recording()
                        break
        
        except Exception as e:
            self.show_terminal_output(f"Error: {str(e)}")
        
        finally:
            # Cleanup logic (remains the same)
            self.listener.is_listening = False
            self.listener.stop_listening = False
            self.queue_gui_task(lambda: self._update_button_state("idle"))
            self.volume_controller.restore_volume()
            
            time.sleep(0.1)
            if not self.wake_word_active:
                self.start_wake_word_detection()

    def start_wake_word_detection(self):
        """Start wake word monitoring"""
        # Only start wake word detection if STT is enabled and listener is available
        if not ENABLE_STT or self.listener is None:
            return
            
        if not self.listener.is_listening:
            if not self.wake_word_thread or not self.wake_word_thread.is_alive():
                self.wake_word_active = True
                self.wake_word_thread = threading.Thread(
                    target=self.monitor_wake_word,
                    daemon=True
                )
                self.wake_word_thread.start()
    
    def stop_wake_word_detection(self):
        """Stop wake word monitoring"""
        self.wake_word_active = False
        if self.listener is not None:
            self.listener.stop_wake_word_listening()
    
    def monitor_wake_word(self):
        """Monitor for wake word"""
        while self.wake_word_active:
            try:
                # Check if listener is available and STT is enabled
                if self.listener is None or not ENABLE_STT:
                    self.wake_word_active = False
                    break
                    
                if not self.listener.is_listening and self.wake_word_active:
                    # The listener might return False if it had to restart, the loop will just try again.
                    detected = self.listener.listen_for_wake_word(settings.Wake_word)

                    if detected and self.wake_word_active:
                        self.wake_word_active = False
                        self.listener.stop_wake_word_listening()

                        self.root.after(0, self.activate_mic_from_wake_word)

                        threading.Thread(target=self.play_activation_melody, daemon=True).start()
                        threading.Thread(
                            target=lambda: (time.sleep(0.5), self.volume_controller.lower_volume(5)),
                            daemon=True
                        ).start()

                        max_wait = 50
                        waited = 0
                        while self.listener is not None and not self.listener.is_listening and waited < max_wait:
                            time.sleep(0.1)
                            waited += 1

                        if self.listener is not None and not self.listener.is_listening:
                            time.sleep(1)
                            self.wake_word_active = True

                        break # Exit the loop once activated
                else:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Wake word error in GUI loop: {e}")
                time.sleep(1) # Wait a second before retrying
    
    def activate_mic_from_wake_word(self):
        """Activate mic from wake word"""
        try:
            # ✅ Fix: Guard against None listener
            if self.listener is None:
                return

            if not self.listener.is_listening:
                self.auto_turn_off_mic = True
                
                # ✅ FIX: Update button in main thread
                # self.root.after(0, lambda: self.mic_button.config(bg='#2d2d2d', text="⏸"))
                self.queue_gui_task(lambda: self._update_button_state("listening"))
                # ✅ FIX: Set listening state properly
                self.listener.is_listening = True
                self.listener.stop_listening = False
                
                threading.Thread(target=self.record_speech, daemon=True).start()
        except Exception as e:
            logger.error(f"Mic activation error: {e}")
    
    def toggle_input_dialog(self):
        """Toggle input dialog"""
        if not self.input_visible:
            from .dialogs import create_input_dialog
            self.input_dialog = create_input_dialog(self)
            self.input_visible = True
        else:
            if self.input_dialog:
                self.input_dialog.withdraw()
            self.input_visible = False
    
    def show_response(self, response_text):
        """Show response dialog - NOW STORES CODE AND SHOWS BUTTON"""
        # Store the generated code
        self.generated_code_text = response_text
        
        # Show code view button
        self.show_code_view_button(response_text)
        
        # Don't show the code dialog immediately anymore
        # User must click the button to see it
    
    def show_terminal_output(self, message, color="green"):
        """Enhanced with optional context info display + logging (with filtering) + message filtering"""
        
        EXCLUDED_TERMINAL_PATTERNS = [
            "User Speaking:",
            "YOU SAID:",
            "Listening...",
            "Processing:",
            "Processing..."
            "🎤 Listening for",
        ]
        
        should_hide = False
        for pattern in EXCLUDED_TERMINAL_PATTERNS:
            if pattern in message:
                should_hide = True
                break
        
        if should_hide:
            EXCLUDED_LOG_PATTERNS = [
                "User Speaking:",
                "YOU SAID:",
                "Listening...",
                "Processing:",
            ]
            
            should_log = True
            for pattern in EXCLUDED_LOG_PATTERNS:
                if pattern in message:
                    should_log = False
                    break
            
            if should_log:
                if color == "red":
                    logger.error(f"[TERMINAL] {message}")
                elif color == "yellow":
                    logger.warning(f"[TERMINAL] {message}")
                elif color == "cyan":
                    logger.info(f"[TERMINAL] {message}")
                else:
                    logger.info(f"[TERMINAL] {message}")
            
            return
        
        EXCLUDED_LOG_PATTERNS = [
            "User Speaking:",
            "YOU SAID:",
            "Listening...",
            "🎤 Listening for",
            "Processing:",
        ]
        
        should_log = True
        for pattern in EXCLUDED_LOG_PATTERNS:
            if pattern in message:
                should_log = False
                break
        
        if should_log:
            if color == "red":
                logger.error(f"[TERMINAL] {message}")
            elif color == "yellow":
                logger.warning(f"[TERMINAL] {message}")
            elif color == "cyan":
                logger.info(f"[TERMINAL] {message}")
            else:
                logger.info(f"[TERMINAL] {message}")
        
        if not hasattr(self, 'terminal') or self.terminal is None:
            print(f"[{color.upper()}] {message}")
            return
        
        if self.show_context_in_terminal:
            context_info = self.context_manager.get_context_string()
            
            if context_info != "No context" and not message.startswith("💡"):
                if not any(x in message for x in ["⏱️", "Generating", "Running"]):
                    message += f"\n💡 {context_info}"
        
        self.terminal.show_message(message, color)
    
    def force_context_refresh(self):
        """Ultra-fast context refresh"""
        with self.state_lock:
            from monitors.clipboard import get_clipboard_content
            from monitors.explorer import get_explorer_path
            from monitors.window import get_active_window_title
            
            try:
                results = {}
                
                
                def get_folder():
                    try:
                        results['folder'] = get_explorer_path(self.context_manager)
                    except:
                        pass
                
                def get_window():
                    try:
                        results['window'] = get_active_window_title()
                    except:
                        pass
                
                def get_clipboard_data():
                    try:
                        results['clipboard'] = get_clipboard_content()
                    except:
                        pass
                
                threads = [
                    threading.Thread(target=get_folder, daemon=True),
                    threading.Thread(target=get_window, daemon=True),
                    threading.Thread(target=get_clipboard_data, daemon=True)
                ]
                
                for t in threads:
                    t.start()
                
                for t in threads:
                    try:
                    # Reduce timeout to prevent hanging UI if clipboard is locked
                        t.join(timeout=0.2) 
                    except Exception: pass
                
                if 'folder' in results and results['folder']:
                    self.context_manager.update_folder(results['folder'])
                if 'window' in results and results['window']:
                    self.context_manager.update_window(results['window'])
                if 'clipboard' in results and results['clipboard']:
                    self.context_manager.update_clipboard(results['clipboard'])
            
            except Exception as e:
                logger.error(f"Context refresh error: {e}")
    
    def apply_blur_effect(self, window):
        """Apply blur effect to window"""
        try:
            hwnd = windll.user32.GetParent(window.winfo_id())
            accent_state = 4
            accent_flags = 0
            color = 0x01000000
            
            accent_policy = c_int * 4
            accent = accent_policy(accent_state, accent_flags, color, 0)
            
            data = c_int * 6
            window_composition_attribute_data = data(19, byref(accent), 16, 0, 0, 0)
            
            windll.user32.SetWindowCompositionAttribute(hwnd, byref(window_composition_attribute_data))
        except:
            pass
    
    def make_window_round(self, window, width, height, radius=40):
        """Make window corners rounded"""
        try:
            hwnd = windll.user32.GetParent(window.winfo_id())
            region = windll.gdi32.CreateRoundRectRgn(0, 0, width, height, radius, radius)
            windll.user32.SetWindowRgn(hwnd, region, True)
        except:
            pass
    
    def play_activation_melody(self):
        """Play activation sound"""
        import winsound
        threading.Thread(target=lambda: self._play_melody("activation"), daemon=True).start()
    
    def play_stop_melody(self):
        """Play stop sound"""
        import winsound
        threading.Thread(target=lambda: self._play_melody("stop"), daemon=True).start()
    
    def _play_melody(self, melody_type):
        """Play melody in background"""
        import winsound
        try:
            if melody_type == "activation":
                winsound.Beep(523, 80)
                winsound.Beep(659, 80)
                winsound.Beep(784, 120)
            elif melody_type == "stop":
                winsound.Beep(784, 80)
                winsound.Beep(523, 120)
        except:
            pass
    
    def process_task_queue(self):
        """Process queued GUI tasks"""
        try:
            while not self.task_queue.empty():
                task = self.task_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_task_queue)
    
    def queue_gui_task(self, func):
        """Thread-safe GUI task scheduling"""
        self.task_queue.put(func)
    
    def load_history(self):
        """Load command history"""
        import json
        import os

        from config.settings import HISTORY_FILE
        
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE) as f:
                    return json.load(f)[-50:]
            except:
                return []
        return []
    
    def save_history(self):
        """Save command history"""
        import json

        from config.settings import HISTORY_FILE
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.command_history[-50:], f, indent=2)
    
    def cleanup(self):
        """Comprehensive cleanup"""
        logger.info("🧹 Starting cleanup...")
        
        try:
            if hasattr(self, 'mobile_companion'):
                try:
                    self.mobile_companion.shutdown()
                except Exception as e:
                    logger.error(f"Mobile companion cleanup failed: {e}")
            self.wake_word_active = False
            if self.listener:
                self.listener.stop_wake_word_listening()
                self.listener.stop_recording()
            if hasattr(self, 'stt_manager'):
                try:
                    self.stt_manager.stop()
                except Exception as e:
                    logger.error(f"STT manager stop failed: {e}")
            if hasattr(self, 'volume_controller'):
                try:
                    self.volume_controller.restore_volume()
                    logger.info("🔊 Volume restored")
                except Exception as e:
                    logger.error(f"Volume restore failed: {e}")
            
            if hasattr(self, 'notifier'):
                try:
                    self.notifier.stop()
                except Exception as e:
                    logger.error(f"Notifier stop failed: {e}")
            
            if hasattr(self, 'audio_coordinator'):
                try:
                    self.audio_coordinator.cleanup()
                except Exception as e:
                    logger.error(f"Audio coordinator cleanup failed: {e}")
            
            # Then cleanup STT (coordinator already cleaned TTS)
            if self.listener and hasattr(self.listener, 'cleanup'):
                try:
                    logger.info("🌐 Closing STT ChromeDriver...")
                    self.listener.cleanup()
                except Exception as e:
                    logger.error(f"STT cleanup failed: {e}")
            try:
                import os

                import psutil
                current_pid = os.getpid()
                
                killed_count = 0
                for proc in psutil.process_iter(['pid', 'name', 'ppid']):
                    try:
                        proc_name = proc.info['name'].lower()
                        if proc.info['ppid'] == current_pid and \
                        ('chrome' in proc_name or 'chromedriver' in proc_name):
                            proc.kill()
                            killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                if killed_count > 0:
                    logger.info(f"🔪 Killed {killed_count} orphaned Chrome processes")
            except Exception as e:
                logger.error(f"Process cleanup failed: {e}")
            
            if hasattr(self, 'hotkey_manager'):
                try:
                    self.hotkey_manager.stop()
                except Exception as e:
                    logger.error(f"Hotkey stop failed: {e}")
            
            dialogs = [
                ('control_dialog', self.control_dialog),
                ('input_dialog', self.input_dialog),
                ('response_dialog', self.response_dialog)
            ]
            
            for name, dialog in dialogs:
                if dialog:
                    try:
                        dialog.destroy()
                    except:
                        pass
            
            if hasattr(self, 'terminal'):
                try:
                    self.terminal.clear_all()
                except:
                    pass
             
            logger.info("✅ Cleanup completed")
        
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    def run(self):
        """Start main loop"""
        self.root.mainloop()
