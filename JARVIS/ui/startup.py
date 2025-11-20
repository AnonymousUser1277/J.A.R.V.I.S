"""
Startup UI window with output redirection
"""

import sys
import tkinter as tk

class StartupUI:
    """Custom startup UI window with output redirection"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS Startup")
        self.root.configure(bg='#0a0a0a')
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f"800x600+{x}+{y}")
        
        # Remove window decorations
        self.root.overrideredirect(True)
        
        # Make window always on top
        # self.root.attributes('-topmost', True)
        
        # Main container
        main_frame = tk.Frame(
            self.root,
            bg='#0a0a0a',
            bd=2,
            relief='solid',
            highlightbackground='#00ff00',
            highlightthickness=2
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Header
        header = tk.Label(
            main_frame,
            text="J.A.R.V.I.S",
            font=("Consolas", 32, "bold"),
            bg='#0a0a0a',
            fg='#00ff00'
        )
        header.pack(pady=(20, 10))
        
        subtitle = tk.Label(
            main_frame,
            text="Just A Rather Very Intelligent System",
            font=("Consolas", 12),
            bg='#0a0a0a',
            fg='#00ff00'
        )
        subtitle.pack(pady=(0, 20))
        
        # Status section
        status_frame = tk.Frame(main_frame, bg='#1a1a1a', bd=1, relief='solid')
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(
            status_frame,
            text="📊 CURRENT STATUS",
            font=("Consolas", 11, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(anchor='w', padx=10, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="Initializing...",
            font=("Consolas", 12),
            bg='#1a1a1a',
            fg='#ffffff',
            anchor='w',
            justify='left'
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Console log section
        log_frame = tk.Frame(main_frame, bg='#1a1a1a', bd=1, relief='solid')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        tk.Label(
            log_frame,
            text="📋 SYSTEM LOG",
            font=("Consolas", 16, "bold"),
            bg='#1a1a1a',
            fg='#00ff00'
        ).pack(anchor='w', padx=10, pady=5)
        
        self.log_text = tk.Text(
            log_frame,
            font=("Consolas", 12),
            bg='#0a0a0a',
            fg='#00ff00',
            relief='flat',
            wrap=tk.WORD,
            height=15,
            state='normal'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.redirect_output()
    
    def redirect_output(self):
        """Redirect print statements to UI"""
        class OutputRedirector:
            def __init__(self, text_widget, tag):
                self.text_widget = text_widget
                self.tag = tag
            
            def write(self, message):
                if message.strip():
                    try:
                        self.text_widget.insert(tk.END, message, self.tag)
                        self.text_widget.see(tk.END)
                        self.text_widget.update_idletasks()
                        
                        try:
                            self.text_widget.winfo_toplevel().update()
                        except:
                            pass
                    except:
                        pass
            
            def flush(self):
                pass
        
        # Redirect stdout and stderr
        sys.stdout = OutputRedirector(self.log_text, 'stdout')
        sys.stderr = OutputRedirector(self.log_text, 'stderr')
        
        # Configure tags
        self.log_text.tag_config('stdout', foreground="#cc00ff")
        self.log_text.tag_config('stderr', foreground="#51ff44")
    
    def log(self, message, color='#00ff00'):
        """Add message to log"""
        try:
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.tag_add('colored', 'end-2l', 'end-1l')
            self.log_text.tag_config('colored', foreground=color)
            self.log_text.see(tk.END)
            self.root.update()
        except:
            pass
    
    def update_status(self, status):
        """Update current status with forced UI refresh"""
        try:
            self.status_label.config(text=status)
            self.root.update_idletasks()
            self.root.update()
        except:
            pass
    
    def close(self):
        """Close the startup UI"""
        import time
        import logging
        logger = logging.getLogger(__name__)
        time.sleep(2)
        
        try:
            self.root.destroy()
        except Exception as e:
            logging.error(e)