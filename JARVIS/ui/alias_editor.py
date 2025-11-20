"""
Alias editor UI
"""
import tkinter as tk
from tkinter import messagebox
from config.aliases import get_alias_manager

def show_alias_editor(gui_handler):
    """Show alias editor dialog"""
    alias_mgr = get_alias_manager()
    
    dialog = tk.Toplevel(gui_handler.root)
    dialog.title("Command Aliases")
    dialog.configure(bg='#1e1e1e')
    dialog.geometry("700x500")
    dialog.attributes('-topmost', True)
    
    main_frame = tk.Frame(dialog, bg='#1e1e1e')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    tk.Label(
        main_frame,
        text="⚡ Command Aliases",
        font=("Arial", 14, "bold"),
        bg='#1e1e1e',
        fg='#00ff00'
    ).pack(pady=(0, 10))
    
    # Alias list
    list_frame = tk.Frame(main_frame, bg='#2d2d2d')
    list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    listbox = tk.Listbox(
        list_frame,
        font=("Consolas", 10),
        bg='#1e1e1e',
        fg='#ffffff',
        selectmode=tk.SINGLE,
        yscrollcommand=scrollbar.set
    )
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)
    
    def refresh_list():
        """Refresh alias list"""
        listbox.delete(0, tk.END)
        for alias, command in sorted(alias_mgr.list_aliases().items()):
            listbox.insert(tk.END, f"{alias} → {command}")
    
    refresh_list()
    
    # Add/Edit frame
    edit_frame = tk.Frame(main_frame, bg='#2d2d2d')
    edit_frame.pack(fill=tk.X, pady=10)
    
    tk.Label(
        edit_frame,
        text="Alias:",
        font=("Arial", 10),
        bg='#2d2d2d',
        fg='#ffffff'
    ).grid(row=0, column=0, padx=5, pady=5, sticky='w')
    
    alias_entry = tk.Entry(
        edit_frame,
        font=("Arial", 10),
        bg='#1e1e1e',
        fg='#ffffff',
        insertbackground='#ffffff',
        width=20
    )
    alias_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
    
    tk.Label(
        edit_frame,
        text="Command:",
        font=("Arial", 10),
        bg='#2d2d2d',
        fg='#ffffff'
    ).grid(row=1, column=0, padx=5, pady=5, sticky='w')
    
    command_entry = tk.Entry(
        edit_frame,
        font=("Arial", 10),
        bg='#1e1e1e',
        fg='#ffffff',
        insertbackground='#ffffff',
        width=50
    )
    command_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
    
    edit_frame.columnconfigure(1, weight=1)
    
    # Buttons
    btn_frame = tk.Frame(main_frame, bg='#1e1e1e')
    btn_frame.pack(pady=10)
    
    def add_alias():
        alias = alias_entry.get().strip()
        command = command_entry.get().strip()
        
        if not alias or not command:
            messagebox.showwarning("Empty Fields", "Please enter both alias and command")
            return
        
        alias_mgr.add_alias(alias, command)
        refresh_list()
        alias_entry.delete(0, tk.END)
        command_entry.delete(0, tk.END)
        gui_handler.show_terminal_output(f"✅ Alias added: '{alias}'", color="green")
    
    def remove_alias():
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alias to remove")
            return
        
        idx = selection[0]
        text = listbox.get(idx)
        alias = text.split(" → ")[0]
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Remove alias '{alias}'?"
        )
        
        if confirm:
            alias_mgr.remove_alias(alias)
            refresh_list()
            gui_handler.show_terminal_output(f"❌ Alias removed: '{alias}'", color="yellow")
    
    def edit_selected():
        selection = listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        text = listbox.get(idx)
        parts = text.split(" → ")
        if len(parts) == 2:
            alias_entry.delete(0, tk.END)
            alias_entry.insert(0, parts[0])
            command_entry.delete(0, tk.END)
            command_entry.insert(0, parts[1])
    
    # Double-click to edit
    listbox.bind('<Double-Button-1>', lambda e: edit_selected())
    
    tk.Button(
        btn_frame,
        text="➕ Add",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#00ff00',
        command=add_alias,
        padx=15,
        pady=5,
        relief='flat',
        cursor='hand2'
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="✏️ Edit",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#66ccff',
        command=edit_selected,
        padx=15,
        pady=5,
        relief='flat',
        cursor='hand2'
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="🗑️ Remove",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#ff4444',
        command=remove_alias,
        padx=15,
        pady=5,
        relief='flat',
        cursor='hand2'
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="❌ Close",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#ffffff',
        command=dialog.destroy,
        padx=15,
        pady=5,
        relief='flat',
        cursor='hand2'
    ).pack(side=tk.LEFT, padx=5)
    
    # Info label
    tk.Label(
        main_frame,
        text="💡 Tip: Aliases allow you to create shortcuts for common commands",
        font=("Arial", 9),
        bg='#1e1e1e',
        fg='#888888'
    ).pack(pady=5)
    
    # Center dialog
    dialog.update_idletasks()
    x = (gui_handler.root.winfo_screenwidth() - dialog.winfo_width()) // 2
    y = (gui_handler.root.winfo_screenheight() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")