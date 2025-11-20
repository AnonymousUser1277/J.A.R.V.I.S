"""
Theme selector dialog
"""
import tkinter as tk
from ui.theme_manager import get_theme_manager

def show_theme_selector(gui_handler):
    """Show theme selection dialog"""
    theme_mgr = get_theme_manager()
    current_theme = theme_mgr.get_theme()
    
    dialog = tk.Toplevel(gui_handler.root)
    dialog.title("Select Theme")
    dialog.configure(bg=current_theme.get('bg_secondary'))
    dialog.geometry("400x350")
    dialog.attributes('-topmost', True)
    
    # Main frame
    main_frame = tk.Frame(dialog, bg=current_theme.get('bg_secondary'))
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    tk.Label(
        main_frame,
        text="🎨 Select Theme",
        font=("Arial", 16, "bold"),
        bg=current_theme.get('bg_secondary'),
        fg=current_theme.get('accent_green')
    ).pack(pady=(0, 20))
    
    # Theme buttons
    selected_theme = tk.StringVar(value=theme_mgr.current_theme_name)
    
    for theme_name in theme_mgr.get_theme_names():
        theme = theme_mgr.THEMES[theme_name]
        
        # Frame for each theme option
        theme_frame = tk.Frame(
            main_frame,
            bg=theme.get('bg_tertiary'),
            relief='solid',
            borderwidth=2
        )
        theme_frame.pack(fill=tk.X, pady=5)
        
        # Radio button
        radio = tk.Radiobutton(
            theme_frame,
            text=theme.name,
            variable=selected_theme,
            value=theme_name,
            font=("Arial", 12),
            bg=theme.get('bg_tertiary'),
            fg=theme.get('fg_primary'),
            selectcolor=theme.get('bg_button'),
            activebackground=theme.get('bg_button'),
            activeforeground=theme.get('accent_green')
        )
        radio.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Color preview
        preview_frame = tk.Frame(theme_frame, bg=theme.get('bg_tertiary'))
        preview_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        colors = [
            theme.get('accent_green'),
            theme.get('accent_cyan'),
            theme.get('accent_yellow'),
            theme.get('accent_red')
        ]
        
        for color in colors:
            color_box = tk.Label(
                preview_frame,
                bg=color,
                width=3,
                height=1
            )
            color_box.pack(side=tk.LEFT, padx=2)
    
    # Note
    tk.Label(
        main_frame,
        text="⚠️ Restart JARVIS to apply theme changes",
        font=("Arial", 9),
        bg=current_theme.get('bg_secondary'),
        fg=current_theme.get('accent_yellow')
    ).pack(pady=10)
    
    # Buttons
    btn_frame = tk.Frame(main_frame, bg=current_theme.get('bg_secondary'))
    btn_frame.pack(pady=20)
    
    def apply_theme():
        new_theme = selected_theme.get()
        theme_mgr.set_theme(new_theme)
        gui_handler.show_terminal_output(
            f"✅ Theme '{new_theme}' selected. Restart JARVIS to apply.",
            color="green"
        )
        dialog.destroy()
    
    tk.Button(
        btn_frame,
        text="✅ Apply",
        font=("Arial", 11),
        bg=current_theme.get('bg_button'),
        fg=current_theme.get('accent_green'),
        command=apply_theme,
        padx=20,
        pady=5,
        relief='flat',
        cursor='hand2'
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="❌ Cancel",
        font=("Arial", 11),
        bg=current_theme.get('bg_button'),
        fg=current_theme.get('accent_red'),
        command=dialog.destroy,
        padx=20,
        pady=5,
        relief='flat',
        cursor='hand2'
    ).pack(side=tk.LEFT, padx=5)
    
    # Center dialog
    dialog.update_idletasks()
    x = (gui_handler.root.winfo_screenwidth() - dialog.winfo_width()) // 2
    y = (gui_handler.root.winfo_screenheight() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")