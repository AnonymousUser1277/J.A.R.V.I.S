"""
Monitor selection dialog
Lets user choose which monitor to use for UI elements
"""
import tkinter as tk
from config.monitor_config import get_monitor_config

def show_monitor_selector(gui_handler):
    """Show dialog to select preferred monitor"""
    monitors = gui_handler._get_monitors()
    
    if not monitors or len(monitors) <= 1:
        tk.messagebox.showinfo(
            "Single Monitor",
            "You only have one monitor detected."
        )
        return
    
    dialog = tk.Toplevel(gui_handler.root)
    dialog.title("Select Monitor")
    dialog.configure(bg='#1e1e1e')
    dialog.geometry("400x300")
    
    tk.Label(
        dialog,
        text="Select Preferred Monitor",
        font=("Arial", 14, "bold"),
        bg='#1e1e1e',
        fg='#00ff00'
    ).pack(pady=10)
    
    tk.Label(
        dialog,
        text="JARVIS UI elements will appear on this monitor",
        font=("Arial", 10),
        bg='#1e1e1e',
        fg='#ffffff'
    ).pack(pady=5)
    
    # Monitor list
    listbox = tk.Listbox(
        dialog,
        font=("Arial", 11),
        bg='#2d2d2d',
        fg='#ffffff',
        selectmode=tk.SINGLE,
        height=len(monitors)
    )
    listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    for i, mon in enumerate(monitors):
        primary_tag = " (Primary)" if mon.get('is_primary') else ""
        text = f"Monitor {i+1}: {mon['width']}x{mon['height']}{primary_tag}"
        listbox.insert(tk.END, text)
    
    # Pre-select current preference
    config = get_monitor_config()
    current = config.get_preferred_monitor()
    if current is not None:
        listbox.selection_set(current)
    
    def on_select():
        selection = listbox.curselection()
        if selection:
            idx = selection[0]
            config.set_preferred_monitor(idx)
            gui_handler.show_terminal_output(
                f"✅ Monitor {idx+1} selected. Restart JARVIS to apply.",
                color="green"
            )
            dialog.destroy()
    
    def on_auto():
        config.set_preferred_monitor(None)
        gui_handler.show_terminal_output(
            "✅ Auto-detection enabled. Restart JARVIS to apply.",
            color="green"
        )
        dialog.destroy()
    
    btn_frame = tk.Frame(dialog, bg='#1e1e1e')
    btn_frame.pack(pady=10)
    
    tk.Button(
        btn_frame,
        text="Select",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#00ff00',
        command=on_select,
        padx=20,
        pady=5
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="Auto-Detect",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#66ccff',
        command=on_auto,
        padx=20,
        pady=5
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="Cancel",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#ff4444',
        command=dialog.destroy,
        padx=20,
        pady=5
    ).pack(side=tk.LEFT, padx=5)