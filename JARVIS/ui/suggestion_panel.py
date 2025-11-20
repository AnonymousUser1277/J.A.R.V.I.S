"""
Proactive suggestion panel UI
"""
import tkinter as tk
from ai.proactive import get_suggestion_engine

def show_suggestions_panel(gui_handler):
    """Show panel with active suggestions"""
    suggestion_engine = get_suggestion_engine()
    
    if not suggestion_engine:
        return
    
    suggestions = suggestion_engine.get_suggestions()
    
    if not suggestions:
        gui_handler.show_terminal_output("💡 No active suggestions", color="cyan")
        return
    
    dialog = tk.Toplevel(gui_handler.root)
    dialog.title("Suggestions")
    dialog.configure(bg='#1e1e1e')
    dialog.geometry("500x400")
    dialog.attributes('-topmost', True)
    
    main_frame = tk.Frame(dialog, bg='#1e1e1e')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    tk.Label(
        main_frame,
        text="💡 Proactive Suggestions",
        font=("Arial", 14, "bold"),
        bg='#1e1e1e',
        fg='#ffff00'
    ).pack(pady=(0, 10))
    
    # Suggestions list
    for i, suggestion in enumerate(suggestions):
        card = tk.Frame(main_frame, bg='#2d2d2d', relief='raised', borderwidth=2)
        card.pack(fill=tk.X, pady=5)
        
        # Title
        tk.Label(
            card,
            text=suggestion.title,
            font=("Arial", 12, "bold"),
            bg='#2d2d2d',
            fg='#00ff00',
            anchor='w'
        ).pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Description
        tk.Label(
            card,
            text=suggestion.description,
            font=("Arial", 10),
            bg='#2d2d2d',
            fg='#ffffff',
            anchor='w',
            wraplength=450
        ).pack(fill=tk.X, padx=10, pady=5)
        
        # Confidence & Reason
        tk.Label(
            card,
            text=f"Confidence: {int(suggestion.confidence * 100)}% | {suggestion.reason}",
            font=("Arial", 8),
            bg='#2d2d2d',
            fg='#888888',
            anchor='w'
        ).pack(fill=tk.X, padx=10, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(card, bg='#2d2d2d')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def make_accept(sug):
            def accept():
                command = suggestion_engine.accept_suggestion(sug.suggestion_id)
                if command:
                    gui_handler.show_terminal_output(f"✅ Executing: {command}", color="green")
                    # Execute the command
                    from ai.instructions import generate_instructions
                    generate_instructions(command, gui_handler.client, gui_handler)
                dialog.destroy()
            return accept
        
        def make_dismiss(sug):
            def dismiss():
                suggestion_engine.dismiss_suggestion(sug.suggestion_id)
                gui_handler.show_terminal_output(f"❌ Dismissed: {sug.title}", color="yellow")
                card.destroy()
            return dismiss
        
        tk.Button(
            btn_frame,
            text="✅ Accept",
            font=("Arial", 9),
            bg='#4d4d4d',
            fg='#00ff00',
            command=make_accept(suggestion),
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Dismiss",
            font=("Arial", 9),
            bg='#4d4d4d',
            fg='#ff4444',
            command=make_dismiss(suggestion),
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
    
    # Close button
    tk.Button(
        main_frame,
        text="Close",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#ffffff',
        command=dialog.destroy,
        padx=20,
        pady=5
    ).pack(pady=20)