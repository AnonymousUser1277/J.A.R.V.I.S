"""
Safe Redis Cache Backup Manager (Hash-key-based)
"""

import os
import json
import tkinter as tk
from tkinter import messagebox
from ai.redis_cache import cache

from config.settings import DATA_DIR

BACKUP_FOLDER = os.path.join(DATA_DIR, "cache_backups")


def show_backup_manager(gui_handler):
    dialog = tk.Toplevel(gui_handler.root)
    dialog.title("Cache Backup Manager")
    dialog.configure(bg='#1e1e1e')
    dialog.geometry("600x440") # Adjusted height for better fit
    dialog.attributes('-topmost', True)

    main_frame = tk.Frame(dialog, bg='#1e1e1e')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(
        main_frame,
        text="💾 Cache Backups",
        font=("Arial", 14, "bold"),
        bg='#1e1e1e',
        fg='#00ff00'
    ).pack(pady=(0, 10))


    # ---------- BACKUP LIST ----------
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

    # Create folder
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)


    def load_backups():
        listbox.delete(0, tk.END)
        # Sort backups by name (newest first if timestamp is used)
        files = sorted(os.listdir(BACKUP_FOLDER), reverse=True)
        for filename in files:
            if filename.endswith(".json"):
                path = os.path.join(BACKUP_FOLDER, filename)
                try:
                    size_mb = round(os.path.getsize(path) / 1_000_000, 2)
                    listbox.insert(tk.END, f"{filename} - {size_mb} MB")
                except OSError:
                    # Handle cases where file might be deleted between listdir and getsize
                    pass

    load_backups()


    # ---------- CREATE BACKUP ----------
    def create_backup():
        backup_data = []

        # Get all HASH keys (your actual cache)
        # Keys are already strings due to decode_responses=True
        keys = [k for k in cache.db.keys("*") if cache.db.type(k) == "hash"]

        if not keys:
            messagebox.showinfo("Empty", "Cache is empty, nothing to back up.")
            return

        for key in keys:
            # key is already a string
            fields = cache.db.hgetall(key) # fields is a dict of str: str

            backup_data.append({
                "key": key,
                # FIX: No need to decode, fields are already strings
                "data": fields
            })

        # Use a more standard timestamp
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{ts}.json"
        path = os.path.join(BACKUP_FOLDER, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Success", f"Backup created:\n{os.path.basename(path)}")
            load_backups()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup:\n{e}")


    # ---------- RESTORE BACKUP ----------
    def restore_backup():
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup file.")
            return

        filename = listbox.get(selection[0]).split(" - ")[0]
        path = os.path.join(BACKUP_FOLDER, filename)

        confirm = messagebox.askyesno(
            "Confirm Restore",
            f"Restore backup:\n\n{filename}\n\n"
            "This will OVERWRITE the existing cache.\nAre you sure you want to proceed?"
        )

        if not confirm:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            # A safer way to clear existing hash keys
            with cache.db.pipeline() as pipe:
                existing_keys = [k for k in cache.db.keys("*") if cache.db.type(k) == 'hash']
                if existing_keys:
                    pipe.delete(*existing_keys)

                # Restore entries
                for entry in backup_data:
                    key = entry["key"]
                    data = entry["data"]
                    # Use HMSET for compatibility
                    pipe.hmset(key, data)
                pipe.execute()

            messagebox.showinfo("Success", "Backup restored successfully!")

        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Failed to read backup file (invalid JSON):\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore backup:\n{e}")


    # ---------- BUTTONS ----------
    btn_frame = tk.Frame(main_frame, bg='#1e1e1e')
    btn_frame.pack(pady=10)

    tk.Button(
        btn_frame,
        text="➕ Create Backup",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#00ff00',
        command=create_backup,
        padx=15,
        pady=5,
        relief="flat"
    ).pack(side=tk.LEFT, padx=5)

    tk.Button(
        btn_frame,
        text="♻️ Restore Selected",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#66ccff',
        command=restore_backup,
        padx=15,
        pady=5,
        relief="flat"
    ).pack(side=tk.LEFT, padx=5)

    tk.Button(
        btn_frame,
        text="❌ Close",
        font=("Arial", 11),
        bg='#4d4d4d',
        fg='#ff4444',
        command=dialog.destroy,
        padx=15,
        pady=5,
        relief="flat"
    ).pack(side=tk.LEFT, padx=5)

    tk.Label(
        main_frame,
        text="💡 Safe JSON backups — no Redis restart needed.",
        font=("Arial", 9),
        bg='#1e1e1e',
        fg='#888888'
    ).pack(pady=5)