"""
Safe code execution with auto-import fixing
"""
import os
import sys
import types
import threading
import logging
from utils.logger import GuiLogger
logger = logging.getLogger(__name__)
def _get_script_path():
    try:
        return os.path.abspath(__file__)
    except NameError:
        return os.path.abspath(sys.argv[0])

SCRIPT_PATH = _get_script_path()

def run_generated_code(code, gui_handler, script_path=None):
    """
    Execute generated code with:
    - Auto-TTS for print statements
    - Output redirection to GUI
    - Error handling
    """
    if script_path is None:
        script_path =  SCRIPT_PATH
    from audio.tts import speak
    from config.settings import AUTO_TTS, ENABLE_TTS
    
    # Custom print function that also speaks
    original_print = print
    # collect printed messages here so we can speak only the final one
    printed_messages = []
    
    def speaking_print(*args, **kwargs):
        """Print that also speaks the output"""
        message = ' '.join(str(arg) for arg in args)
        original_print(*args, **kwargs)
        # collect printed messages and speak only the last one after execution
        try:
            if message.strip():
                printed_messages.append(message)
        except Exception:
            # fail-safe: don't let TTS collection break the executed code
            pass
    
    # Direct output to GUI — but wrap it so we also capture raw writes
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    class _CaptureStdout:
        def __init__(self, gui_handler, storage_list):
            self._gui_logger = GuiLogger(gui_handler)
            self._storage = storage_list

        def write(self, message):
            try:
                if message is None:
                    return
                txt = str(message)
                if txt.strip():
                    # store non-empty writes
                    self._storage.append(txt.strip())
                # forward to GUI
                self._gui_logger.write(message)
            except Exception:
                pass

        def flush(self):
            try:
                self._gui_logger.flush()
            except Exception:
                pass

    sys.stdout = _CaptureStdout(gui_handler, printed_messages)
    sys.stderr = GuiLogger(gui_handler)

    # Optional confirmation before running AI-generated code
    try:
        from config.settings import CONFIRM_AI_EXECUTION, AUTO_TTS
    except Exception:
        CONFIRM_AI_EXECUTION = False
        AUTO_TTS = True

    if CONFIRM_AI_EXECUTION:
        # Use GUI thread to ask the user; wait for response with timeout
        confirm_event = threading.Event()
        confirm_result = {'ok': False}

        def _ask_user_confirm():
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = getattr(gui_handler, 'root', None)
                # messagebox needs a parent window; if missing, create temp root
                if root:
                    answer = messagebox.askyesno("Confirm Execution", "AI-generated code requests to run. Allow execution?")
                else:
                    # fallback: create a temporary hidden root
                    tmp = tk.Tk()
                    tmp.withdraw()
                    answer = messagebox.askyesno("Confirm Execution", "AI-generated code requests to run. Allow execution?")
                    tmp.destroy()
                confirm_result['ok'] = bool(answer)
            except Exception:
                confirm_result['ok'] = False
            finally:
                confirm_event.set()

        try:
            gui_handler.queue_gui_task(_ask_user_confirm)
            # wait up to 30 seconds for user to respond
            confirm_event.wait(30)
        except Exception:
            pass

        if not confirm_result.get('ok'):
            try:
                gui_handler.show_terminal_output("Execution cancelled by user or timed out.", color="yellow")
            except Exception:
                print("Execution cancelled by user or timed out.")
            # restore streams and exit
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            return
    
    try:
        # Pre-import essential modules so AI doesn't have to
        import subprocess
        import webbrowser
        import time
        import pyautogui
        import json
        import re
        import threading
        import datetime
        # Try to import clipboard module (optional)
        try:
            import pyperclip as clipboard_module
        except ImportError:
            clipboard_module = None
        
        exec_globals = {
            '__builtins__': __builtins__,
            'gui_handler': gui_handler,
            '__name__': '__main__',
            '__file__': script_path,
            'print': speaking_print,  # 🔥 Override print with speaking version
            # Pre-imported modules (always available)
            'os': os,
            'sys': sys,
            'subprocess': subprocess,
            'webbrowser': webbrowser,
            'time': time,
            'pyautogui': pyautogui,
            'json': json,
            're': re,
            'threading': threading,
            'datetime': datetime,
        }
        
        # Add clipboard if available
        if clipboard_module:
            exec_globals['clipboard'] = clipboard_module
        
        if isinstance(code, str):
            exec(compile(code, "<AI_code>", "exec"),exec_globals)
        elif isinstance(code,types.CodeType):
            exec(code,exec_globals)
    
    except Exception as e:
        error_msg = f"⚠️ Error: {type(e).__name__}: {e}"
        gui_handler.show_terminal_output(error_msg, color="red")
        logger.error(error_msg)
    
    # In automation/executor.py

    finally:
        # 1. Restore output streams immediately
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        # 2. [CRITICAL FIX] Reset UI state UNCONDITIONALLY
        # Do this before speaking, so the visual state is correct even if TTS is silent
        try:
            if hasattr(gui_handler, 'queue_gui_task'):
                gui_handler.queue_gui_task(lambda: gui_handler._update_button_state("idle"))
        except Exception:
            pass

        # 3. [CRITICAL FIX] Restore volume UNCONDITIONALLY
        try:
            if hasattr(gui_handler, 'volume_controller'):
                gui_handler.volume_controller.restore_volume()
        except Exception:
            pass

        # 4. Speak the output (if any)
        try:
            if ENABLE_TTS and AUTO_TTS and printed_messages:
                last_msg = None
                for txt in reversed(printed_messages):
                    if txt and str(txt).strip():
                        last_msg = str(txt).strip()
                        break

                if last_msg:
                    speak(last_msg)
        except Exception:
            pass
