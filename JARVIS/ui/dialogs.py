"""
Dialogs notifications
"""

import tkinter as tk
from tkinter import filedialog
import os
from utils.file_manager import FileManager

try:
    from spellchecker import SpellChecker 
    SPELL_CHECK_AVAILABLE = True
except ImportError:
    SPELL_CHECK_AVAILABLE = False
    print("⚠️ Install pyspellchecker for spell check: pip install pyspellchecker")

def create_input_dialog(gui_handler):
    """Create input dialog with file upload capability"""
    # Initialize file manager for this dialog
    file_manager = FileManager()
    
    # Main dialog
    dialog = tk.Toplevel(gui_handler.root)
    dialog.title("Enter Command")
    dialog.configure(bg='#1e1e1e')
    dialog.attributes('-topmost', True)
    dialog.overrideredirect(True)
    dialog.attributes('-alpha', 0.85)
    
    # Apply effects
    dialog.after(100, lambda: gui_handler.apply_blur_effect(dialog))
    search_mode = {'active': False, 'query': '', 'matches': [], 'index': 0}
    
    def enter_search_mode(event):
        """Enter reverse search mode"""
        search_mode['active'] = True
        search_mode['query'] = ''
        search_mode['matches'] = []
        search_mode['index'] = 0
        update_search_display()
    
    def exit_search_mode(event=None):
        """Exit reverse search mode"""
        search_mode['active'] = False
        canvas.itemconfig(rect, outline='#444444')  # Reset border
    
    def update_search_display():
        """Update display during search"""
        if not search_mode['active']:
            return
        
        # Visual feedback - change border color
        canvas.itemconfig(rect, outline='#ffff00')  # Yellow border
        
        # Update entry placeholder
        if search_mode['matches']:
            match = search_mode['matches'][search_mode['index']]
            text_entry.delete(0, tk.END)
            text_entry.insert(0, match)
        else:
            text_entry.delete(0, tk.END)
    
    def search_next(event):
        """Search for next match (Ctrl+R again)"""
        if not search_mode['active']:
            enter_search_mode(event)
            return
        
        if search_mode['matches'] and len(search_mode['matches']) > 1:
            search_mode['index'] = (search_mode['index'] + 1) % len(search_mode['matches'])
            update_search_display()
    
    def on_search_key(event):
        """Handle keys during search mode"""
        if not search_mode['active']:
            return
        
        char = event.char
        if char.isprintable():
            search_mode['query'] += char
            
            # Search history
            search_mode['matches'] = [
                cmd for cmd in reversed(gui_handler.command_history)
                if search_mode['query'].lower() in cmd.lower()
            ]
            search_mode['index'] = 0
            update_search_display()
    
    def on_backspace_in_search(event):
        """Handle backspace in search mode"""
        if search_mode['active'] and search_mode['query']:
            search_mode['query'] = search_mode['query'][:-1]
            
            # Update matches
            if search_mode['query']:
                search_mode['matches'] = [
                    cmd for cmd in reversed(gui_handler.command_history)
                    if search_mode['query'].lower() in cmd.lower()
                ]
            else:
                search_mode['matches'] = []
            
            search_mode['index'] = 0
            update_search_display()
            return "break"  # Prevent default backspace
    
    
    if SPELL_CHECK_AVAILABLE:
        spell = SpellChecker()
        suggestion_popup = None
        def show_suggestions(misspelled_word, suggestions):
            """Show a popup with spelling suggestions"""
            nonlocal suggestion_popup
            
            # Close existing popup
            if suggestion_popup:
                try:
                    suggestion_popup.destroy()
                except:
                    pass
            
            if not suggestions:
                return
            
            # Create popup window
            suggestion_popup = tk.Toplevel(dialog)
            suggestion_popup.overrideredirect(True)
            suggestion_popup.configure(bg='#2d2d2d')
            suggestion_popup.attributes('-topmost', True)
            
            # Frame for suggestions
            frame = tk.Frame(suggestion_popup, bg='#2d2d2d', padx=10, pady=8)
            frame.pack()
            
            # Title
            tk.Label(
                frame,
                text=f"Did you mean:",
                font=("Arial", 10, "bold"),
                bg='#2d2d2d',
                fg='#ffaa00'
            ).pack(anchor='w')
            
            # Suggestion buttons
            for suggestion in list(suggestions)[:5]:  # Show max 5 suggestions
                btn = tk.Button(
                    frame,
                    text=suggestion,
                    font=("Arial", 10),
                    bg='#3d3d3d',
                    fg='#ffffff',
                    relief='flat',
                    cursor='hand2',
                    padx=12,
                    pady=4,
                    command=lambda s=suggestion, w=misspelled_word: replace_word(w, s)
                )
                btn.pack(fill='x', pady=2)
                
                # Hover effect
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#4d4d4d'))
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#3d3d3d'))
            
            # Ignore button
            ignore_btn = tk.Button(
                frame,
                text="Ignore",
                font=("Arial", 9),
                bg='#2d2d2d',
                fg='#888888',
                relief='flat',
                cursor='hand2',
                command=close_suggestions
            )
            ignore_btn.pack(pady=(5, 0))
            
            # Position near the entry widget
            entry_x = text_entry.winfo_rootx()
            entry_y = text_entry.winfo_rooty()
            entry_height = text_entry.winfo_height()
            
            suggestion_popup.update_idletasks()
            popup_width = suggestion_popup.winfo_width()
            
            suggestion_popup.geometry(f"+{entry_x}+{entry_y + entry_height + 5}")
            
            # Auto-close after 10 seconds
            suggestion_popup.after(10000, close_suggestions)
        
        def close_suggestions():
            """Close suggestion popup"""
            nonlocal suggestion_popup
            if suggestion_popup:
                try:
                    suggestion_popup.destroy()
                except:
                    pass
                suggestion_popup = None
        
        def replace_word(old_word, new_word):
            """Replace misspelled word with suggestion"""
            text = text_entry.get()
            # Simple word replacement
            new_text = text.replace(old_word, new_word)
            text_entry.delete(0, tk.END)
            text_entry.insert(0, new_text)
            text_entry.config(bg='#2d2d2d')  # Reset background
            close_suggestions()
        
        def check_spelling(event=None):
            """Check spelling and highlight errors"""
            text = text_entry.get()
            if not text.strip():
                text_entry.config(bg='#2d2d2d')
                close_suggestions()
                return
            
            words = text.split()
            misspelled = spell.unknown(words)
            
            if misspelled:
                # Show visual feedback
                text_entry.config(bg='#3d2d2d')  # Slight red tint
                
                # Show suggestions for first misspelled word
                first_misspelled = list(misspelled)[0]
                suggestions = spell.candidates(first_misspelled)
                
                if suggestions:
                    show_suggestions(first_misspelled, suggestions)
            else:
                text_entry.config(bg='#2d2d2d')  # Normal
                close_suggestions()
        
        # Check spelling on key release (with debounce)
        spell_check_job = None
        def debounced_spell_check(event):
            nonlocal spell_check_job
            if spell_check_job:
                gui_handler.root.after_cancel(spell_check_job)
            spell_check_job = gui_handler.root.after(800, check_spelling)  # Increased delay
        
        
    # Make draggable
    def start_drag(event):
        dialog.drag_x = event.x
        dialog.drag_y = event.y
    
    def on_drag(event):
        x = dialog.winfo_x() + event.x - dialog.drag_x
        y = dialog.winfo_y() + event.y - dialog.drag_y
        dialog.geometry(f"+{x}+{y}")
    
    dialog.bind('<Button-1>', start_drag)
    dialog.bind('<B1-Motion>', on_drag)
    
    # Main container frame
    main_frame = tk.Frame(dialog, bg='#1e1e1e')
    main_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
    
    # ===== INPUT ROW (Text Entry + File Upload Button) =====
    input_row = tk.Frame(main_frame, bg='#1e1e1e')
    input_row.pack(fill=tk.X, padx=0, pady=0)
    
    # Canvas for rounded corners (input box)
    canvas = tk.Canvas(
        input_row,
        width=700,
        height=80,
        bg='#1e1e1e',
        highlightthickness=0
    )
    canvas.pack(side=tk.LEFT, padx=0, pady=5)
    
    # Draw rounded rectangle
    def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1+radius, y1,
            x1+radius, y1,
            x2-radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1+radius,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)
    
    rect = create_rounded_rectangle(
        canvas, 10, 10, 690, 70,
        radius=20,
        fill='#2d2d2d',
        outline='#444444',
        width=2
    )
    
    # Entry widget
    text_entry = tk.Entry(
        dialog,
        font=("Arial", 24),
        bg='#2d2d2d',
        fg='white',
        insertbackground='white',
        relief='flat',
        width=45,
        borderwidth=0,
        takefocus=1
    )
    text_entry.place(in_=canvas, x=30, y=30, width=630, height=40)
    if SPELL_CHECK_AVAILABLE:
        text_entry.bind('<KeyRelease>', debounced_spell_check)
    # Bind search keys
    text_entry.bind('<Control-r>', search_next)
    text_entry.bind('<Escape>', lambda e: exit_search_mode())
    text_entry.bind('<Key>', lambda e: on_search_key(e) if search_mode['active'] else None)
    text_entry.bind('<BackSpace>', on_backspace_in_search)
    text_entry.bind('<Return>', lambda e: (exit_search_mode(), on_submit(e)))
    # File upload button
    def on_file_select():
        """Open file dialog to select one or more files"""
        # Try to get a sensible initial directory
        initialdir = None
        try:
            if hasattr(gui_handler, 'context_manager') and gui_handler.context_manager:
                # Use current folder if available
                if hasattr(gui_handler.context_manager, 'current_folder') and gui_handler.context_manager.current_folder:
                    initialdir = gui_handler.context_manager.current_folder
        except Exception:
            pass
        
        # Fall back to user's home directory if nothing found
        if not initialdir:
            initialdir = os.path.expanduser("~")
        
        files = filedialog.askopenfilenames(
            title="Select File(s)",
            initialdir=initialdir
        )
        
        if files:
            successful, failed = file_manager.add_multiple_files(list(files))
            update_file_display()
            if successful > 0:
                gui_handler.show_terminal_output(
                    f"✅ Added {successful} file(s)" + (f" ({failed} failed)" if failed > 0 else ""),
                    color="green"
                )
    
    # File upload button styling
    file_btn = tk.Button(
        input_row,
        text="📁",
        font=("Arial", 12, "bold"),
        bg='#4d4d4d',
        fg="#ffffff",
        relief='flat',
        cursor='hand2',
        padx=8,
        pady=5,
        command=on_file_select,
        activebackground='#5d5d5d',
        activeforeground='#00ff00'
    )
    # Place the button to the right of the input canvas so it is visually outside the rounded input box
    file_btn.pack(side=tk.RIGHT, padx=(8, 10), pady=5)
    
    canvas.bind('<Button-1>', start_drag)
    canvas.bind('<B1-Motion>', on_drag)
    # ===== SELECTED FILES DISPLAY AREA =====
    # Create/destroy files area dynamically. No scrollbar or mouse-wheel behavior.
    dialog.files_frame = None

    def _center_window(win):
        win.update_idletasks()
        x = (gui_handler.root.winfo_screenwidth() - win.winfo_width()) // 2
        y = (gui_handler.root.winfo_screenheight() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def update_file_display():
        """Create or remove the files area depending on whether files exist.

        The files area is not created when there are no selected files. When files
        are present we create a simple Frame with one row per file. No scrollbar
        or mouse-wheel bindings are used so the dialog will grow to fit content.
        """
        selected = file_manager.get_valid_files()

        # If no selected files, destroy the area if it exists and return
        if not selected:
            if getattr(dialog, 'files_frame', None):
                try:
                    dialog.files_frame.destroy()
                except Exception:
                    pass
                dialog.files_frame = None
                # Re-center dialog after shrink
                dialog.update_idletasks()
                _center_window(dialog)
            return

        # Ensure files_frame exists
        if not getattr(dialog, 'files_frame', None):
            dialog.files_frame = tk.Frame(main_frame, bg='#1e1e1e')
            dialog.files_frame.pack(fill=tk.X, pady=(8, 0))

        # Clear current children
        for child in dialog.files_frame.winfo_children():
            child.destroy()

        # Create a simple row for each file (no scrollbar)
        for idx, file_obj in enumerate(selected):
            file_info_text = f"({idx+1}) {file_obj.display_name}"
            row = tk.Frame(dialog.files_frame, bg='#2d2d2d')
            lbl = tk.Label(row, text=file_info_text, anchor="w", bg='#2d2d2d', fg='#ffffff')
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=4)
            btn = tk.Button(row, text="✕", width=2, command=lambda p=file_obj.path: (file_manager.remove_file(p), update_file_display()), bg='#2d2d2d', fg='#ff6666', relief='flat')
            btn.pack(side=tk.RIGHT, padx=6)
            row.pack(fill=tk.X, pady=2, padx=6)

        # After adding rows, allow geometry to update, then re-center dialog
        dialog.update_idletasks()
        _center_window(dialog)
    
    # Submit handler
    def on_submit(event=None):
        text = text_entry.get().strip()
        if text:
            # Add to history
            if text not in gui_handler.command_history:
                gui_handler.command_history.append(text)
                gui_handler.save_history()
            
            gui_handler.history_index = -1
            text_entry.delete(0, tk.END)
            
            dialog.withdraw()
            gui_handler.input_visible = False
            
            # Execute command with file manager
            from ai.instructions import generate_instructions

            # Show processing and include file info if present
            try:
                if file_manager and file_manager.file_count > 0:
                    paths = [f.path for f in file_manager.get_valid_files()]
                    gui_handler.show_terminal_output(f"Processing: {text} (files: {len(paths)})", color="yellow")
                    print(f"[UI] Submitting prompt with files: {paths}")
                else:
                    gui_handler.show_terminal_output(f"Processing: {text}", color="yellow")
            except Exception as e:
                print(f"[UI] Processing message error: {e}")

            # Animate mic to processing state
            try:
                gui_handler.queue_gui_task(lambda: gui_handler._update_button_state("processing"))
            except Exception:
                pass

            import threading
            threading.Thread(
                target=generate_instructions,
                args=(text, gui_handler.client, gui_handler, file_manager),
                daemon=True
            ).start()
    
    # History navigation
    def navigate_up(event):
        if gui_handler.command_history and gui_handler.history_index < len(gui_handler.command_history) - 1:
            gui_handler.history_index += 1
            text_entry.delete(0, tk.END)
            text_entry.insert(0, gui_handler.command_history[-(gui_handler.history_index + 1)])
    
    def navigate_down(event):
        if gui_handler.history_index > 0:
            gui_handler.history_index -= 1
            text_entry.delete(0, tk.END)
            text_entry.insert(0, gui_handler.command_history[-(gui_handler.history_index + 1)])
        elif gui_handler.history_index == 0:
            gui_handler.history_index = -1
            text_entry.delete(0, tk.END)
    
    text_entry.bind('<Return>', on_submit)
    text_entry.bind('<Up>', navigate_up)
    text_entry.bind('<Down>', navigate_down)
    
    # Position at center
    dialog.update_idletasks()
    x = (gui_handler.root.winfo_screenwidth() - dialog.winfo_width()) // 2
    y = (gui_handler.root.winfo_screenheight() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")
    
    # Make rounded
    dialog.after(100, lambda: gui_handler.make_window_round(dialog, 800, 200, 30))
    
    # Initial file display update
    update_file_display()
    
    # Focus entry
    def focus_entry():
        try:
            import ctypes
            import win32process
            
            dialog.deiconify()
            dialog.lift()
            dialog.attributes('-topmost', True)
            
            hwnd = dialog.winfo_id()
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 5)
            user32.BringWindowToTop(hwnd)
            
            foreground_hwnd = user32.GetForegroundWindow()
            current_thread = win32process.GetWindowThreadProcessId(foreground_hwnd)[0]
            target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
            
            if current_thread != target_thread:
                user32.AttachThreadInput(current_thread, target_thread, True)
            
            user32.SetForegroundWindow(hwnd)
            user32.SetActiveWindow(hwnd)
            user32.SetFocus(hwnd)
            
            if current_thread != target_thread:
                user32.AttachThreadInput(current_thread, target_thread, False)
            
            text_entry.focus_force()
            text_entry.focus_set()
            dialog.focus_force()
            
            gui_handler.root.after(100, lambda: text_entry.focus_force())
            gui_handler.root.after(200, lambda: text_entry.focus_set())
            gui_handler.root.after(500, lambda: dialog.attributes('-topmost', False))
        except Exception as e:
            print(f"[Focus Error] {e}")
    
    dialog.bind('<Map>', lambda e: focus_entry())
    dialog.after(100, focus_entry)
    
    # Store file_manager reference for access if needed
    dialog.file_manager = file_manager
    
    return dialog

def create_response_dialog(gui_handler, response_text):
    """Create response dialog with typing animation"""
    # Cancel old fade job
    if hasattr(gui_handler, 'response_fade_job') and gui_handler.response_fade_job:
        try:
            gui_handler.root.after_cancel(gui_handler.response_fade_job)
            gui_handler.response_fade_job = None
        except:
            pass
    
    # Close existing dialog
    if hasattr(gui_handler, 'response_dialog') and gui_handler.response_dialog:
        try:
            gui_handler.response_dialog.destroy()
            gui_handler.response_dialog = None
        except:
            pass
    
    dialog = tk.Toplevel(gui_handler.root)
    dialog.title("Response")
    dialog.configure(bg='#1e1e1e')
    dialog.attributes('-topmost', True)
    dialog.overrideredirect(True)
    
    # Make draggable
    def start_drag(event):
        dialog.drag_x = event.x
        dialog.drag_y = event.y
    
    def on_drag(event):
        x = dialog.winfo_x() + event.x - dialog.drag_x
        y = dialog.winfo_y() + event.y - dialog.drag_y
        dialog.geometry(f"+{x}+{y}")
    
    dialog.bind('<Button-1>', start_drag)
    dialog.bind('<B1-Motion>', on_drag)
    
    # Frame
    frame = tk.Frame(dialog, bg='#1e1e1e', padx=15, pady=15)
    frame.pack()
    
    # Text widget
    text_widget = tk.Text(
        frame,
        font=("Consolas", 16),
        bg='#2d2d2d',
        fg='#00ff00',
        relief='flat',
        width=60,
        height=15,
        wrap=tk.WORD
    )
    text_widget.pack()
    
    # Non-blocking typing animation
    def animate_text(index=0):
        try:
            if index < len(response_text):
                text_widget.insert(tk.END, response_text[index])
                text_widget.see(tk.END)
                text_widget.update_idletasks()
                gui_handler.root.after(5, lambda: animate_text(index + 1))
        except tk.TclError:
            pass
    
    animate_text()
    
    # Position
    dialog.update_idletasks()
    x = 1
    y = 1
    dialog.geometry(f"+{x}+{y}")
    
    # Apply effects
    dialog.attributes('-alpha', 0.90)
    dialog.after(100, lambda: gui_handler.apply_blur_effect(dialog))
    
    # Hover handlers
    hover_state = {'hover': False}
    
    def on_hover(event):
        hover_state['hover'] = True
        if hasattr(gui_handler, 'response_fade_job') and gui_handler.response_fade_job:
            gui_handler.root.after_cancel(gui_handler.response_fade_job)
            gui_handler.response_fade_job = None
        dialog.attributes('-alpha', 0.95)
    
    def on_leave(event):
        hover_state['hover'] = False
        schedule_fade()
    
    def schedule_fade():
        if hasattr(gui_handler, 'response_fade_job') and gui_handler.response_fade_job:
            gui_handler.root.after_cancel(gui_handler.response_fade_job)
        gui_handler.response_fade_job = gui_handler.root.after(2000, start_fade)
    
    def start_fade():
        if not hover_state['hover']:
            fade_out(1.0)
    
    def fade_out(alpha):
        if not hover_state['hover']:
            if alpha > 0:
                try:
                    dialog.attributes('-alpha', alpha)
                    gui_handler.root.after(50, lambda: fade_out(alpha - 0.07))
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
    
    gui_handler.response_dialog = dialog