"""
Redis Cache Editor - JSON based GUI editor
"""

import tkinter as tk
import json
from ai.redis_cache import cache   # make sure path is correct

def create_redis_cache_editor(gui_handler):

    editor = tk.Toplevel(gui_handler.root)
    editor.title("Cache Editor - Redis Cache")
    editor.configure(bg="#1e1e1e")
    editor.attributes("-fullscreen", True)
    editor.bind("<Escape>", lambda e: editor.attributes("-fullscreen", False))

    editor.attributes("-topmost", True)
    editor.after(1000, lambda: editor.attributes("-topmost", False))
    editor.after(100, lambda: gui_handler.apply_blur_effect(editor))

    main_frame = tk.Frame(editor, bg="#1e1e1e")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    stats = cache.get_stats()
    title_text = (
        f" Redis Cache Editor - {stats['total_entries']} entries "
        f"({stats['accepted']} accepted, {stats['pending']} pending)"
    )

    title_label = tk.Label(
        main_frame,
        text=title_text,
        font=("Arial", 16, "bold"),
        bg="#1e1e1e",
        fg="#00ff00"
    )
    title_label.pack(pady=(0, 10))

    # -------------------------------
    # Search bar
    # -------------------------------
    search_frame = tk.Frame(main_frame, bg="#1e1e1e")
    search_frame.pack(fill=tk.X, pady=(0, 10))

    tk.Label(
        search_frame,
        text=" Find:",
        font=("Arial", 11),
        bg="#1e1e1e",
        fg="#00ff00"
    ).pack(side=tk.LEFT, padx=(0, 5))

    search_entry = tk.Entry(
        search_frame,
        font=("Arial", 11),
        bg="#2d2d2d",
        fg="#00ff00",
        insertbackground="#00ff00",
        relief="flat",
        width=30
    )
    search_entry.pack(side=tk.LEFT, padx=5)

    search_state = {"matches": [], "current_index": 0}

    # -------------------------------
    # Text Widget
    # -------------------------------
    text_frame = tk.Frame(main_frame, bg="#2d2d2d")
    text_frame.pack(fill=tk.BOTH, expand=True)

    line_numbers = tk.Text(
        text_frame,
        font=("Consolas", 14),
        bg="#1e1e1e",
        fg="#888888",
        width=4,
        padx=5,
        pady=10,
        relief="flat",
        state="disabled",
        takefocus=0
    )
    line_numbers.pack(side=tk.LEFT, fill=tk.Y)

    scrollbar = tk.Scrollbar(text_frame, bg="#2d2d2d")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget = tk.Text(
        text_frame,
        font=("Consolas", 16),
        bg="#2d2d2d",
        fg="#00ff00",
        insertbackground="#00ff00",
        relief="flat",
        wrap=tk.NONE,
        yscrollcommand=lambda *args: [scrollbar.set(*args), line_numbers.yview_moveto(float(args[0]))],
        padx=10,
        pady=10
    )
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=lambda *args: [text_widget.yview(*args), line_numbers.yview(*args)])

    def update_line_numbers(event=None):
        line_numbers.config(state="normal")
        line_numbers.delete("1.0", tk.END)
        total = text_widget.get("1.0", tk.END).count("\n")
        nums = "\n".join(str(i) for i in range(1, total + 1))
        line_numbers.insert("1.0", nums)
        line_numbers.config(state="disabled")

    text_widget.bind("<KeyRelease>", update_line_numbers)

    # -------------------------------
    # Load Redis JSON
    # -------------------------------
    try:
        data = cache.export_to_dict(include_rejected=True)
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        text_widget.insert("1.0", formatted)
        update_line_numbers()
    except Exception as e:
        text_widget.insert("1.0", f"Error loading cache: {e}")

    # -------------------------------
    # Status
    # -------------------------------
    status_label = tk.Label(
        main_frame,
        text="Changes will be synced to Redis when you click Save",
        font=("Arial", 10),
        bg="#1e1e1e",
        fg="#ffff00"
    )
    status_label.pack(pady=(5, 0))

    # -------------------------------
    # Buttons
    # -------------------------------
    button_frame = tk.Frame(main_frame, bg="#1e1e1e")
    button_frame.pack(pady=10)

    # SAVE
    def save_cache():
        try:
            content = text_widget.get("1.0", tk.END).strip()
            data = json.loads(content)

            status_label.config(text="Syncing to Redis...", fg="#ffff00")
            editor.update()

            cache.import_from_dict(data, clear_existing=True)

            status_label.config(text="Saved!", fg="#00ff00")
            editor.after(2000, lambda: status_label.config(
                text="Changes will be synced to Redis when you click Save",
                fg="#ffff00"
            ))

        except Exception as e:
            status_label.config(text=f"Error: {e}", fg="#ff4444")

    # RELOAD
    def reload_cache():
        try:
            data = cache.export_to_dict(include_rejected=True)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)

            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", formatted)
            update_line_numbers()

            status_label.config(text="Reloaded from Redis!", fg="#00ff00")
        except Exception as e:
            status_label.config(text=f"Reload error: {e}", fg="#ff4444")

    # FORMAT JSON
    def format_json():
        try:
            content = text_widget.get("1.0", tk.END).strip()
            data = json.loads(content)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)

            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", formatted)
            update_line_numbers()
            status_label.config(text="JSON formatted!", fg="#00ff00")
        except Exception as e:
            status_label.config(text=f"Invalid JSON: {e}", fg="#ff4444")

    # CLEAR ALL
    def clear_all():
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", "{\n}")
        update_line_numbers()
        status_label.config(text="Cache cleared (not saved yet)", fg="#ff4444")

    # Buttons
    tk.Button(button_frame, text=" Save to Redis", font=("Arial", 11, "bold"),
              bg="#4d4d4d", fg="#00ff00", command=save_cache,
              padx=20, pady=5, relief="flat").pack(side=tk.LEFT, padx=5)

    tk.Button(button_frame, text=" Reload", font=("Arial", 11),
              bg="#4d4d4d", fg="#66ccff", command=reload_cache,
              padx=20, pady=5, relief="flat").pack(side=tk.LEFT, padx=5)

    tk.Button(button_frame, text=" Format", font=("Arial", 11),
              bg="#4d4d4d", fg="#66ccff", command=format_json,
              padx=20, pady=5, relief="flat").pack(side=tk.LEFT, padx=5)

    tk.Button(button_frame, text=" Clear All", font=("Arial", 11),
              bg="#4d4d4d", fg="#ffff66", command=clear_all,
              padx=20, pady=5, relief="flat").pack(side=tk.LEFT, padx=5)

    tk.Button(button_frame, text=" Close", font=("Arial", 11),
              bg="#4d4d4d", fg="#ff4444", command=editor.destroy,
              padx=20, pady=5, relief="flat").pack(side=tk.LEFT, padx=5)

    # Final tip
    tk.Label(
        main_frame,
        text=" Tip: Edit JSON then press Save",
        font=("Arial", 9),
        bg="#1e1e1e",
        fg="#888888"
    ).pack()
