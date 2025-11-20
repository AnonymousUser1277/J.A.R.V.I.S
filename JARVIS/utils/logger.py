"""
Enhanced logging system with proper levels and filtering
"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from config.settings import LOG_DIR

class ColoredFormatter(logging.Formatter):
    """Colored console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class ExcludedMessagesFilter(logging.Filter):
    """Filter out noisy log messages"""
    
    EXCLUDED_PATTERNS = [
        "User Speaking:",
        "YOU SAID:",
        "Listening...",
        "🎤 Listening for",
        "Processing...",
        # "[TERMINAL]",  # Don't log terminal outputs to file
    ]
    
    def filter(self, record):
        message = record.getMessage()
        return not any(pattern in message for pattern in self.EXCLUDED_PATTERNS)


def setup_logging(level=logging.INFO):
    """
    Setup comprehensive logging system
    
    Features:
    - Daily rotating file logs
    - Size-based rotation (5MB per file)
    - Separate error log
    - Colored console output
    - Noise filtering
    """
    # Create logs directory
    log_dir = LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Daily log file
    today = datetime.now().strftime("%Y-%m-%d")
    main_log = log_dir / f"{today}.log"
    error_log = log_dir / f"{today}_errors.log"
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter in handlers
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # === File Handler (INFO and above) ===
    file_handler = RotatingFileHandler(
        main_log,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    file_handler.addFilter(ExcludedMessagesFilter())
    root_logger.addHandler(file_handler)
    
    # === Error File Handler (ERROR and above) ===
    error_handler = RotatingFileHandler(
        error_log,
        maxBytes=5*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d\n%(message)s\n',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(error_handler)
    
    # === Console Handler (WARNING and above) ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter(
        '%(levelname)s | %(message)s'
    ))
    console_handler.addFilter(ExcludedMessagesFilter())
    root_logger.addHandler(console_handler)
    
    # === Daily Rotation Handler (archives old logs) ===
    # daily_handler = TimedRotatingFileHandler(
    #     log_dir / "jarvis.log",
    #     when='midnight',
    #     interval=1,
    #     backupCount=30,  # Keep 30 days
    #     encoding='utf-8'
    # )
    # daily_handler.setLevel(logging.DEBUG)
    # daily_handler.setFormatter(logging.Formatter(
    #     '%(asctime)s | %(levelname)-8s | %(message)s'
    # ))
    # root_logger.addHandler(daily_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('WDM').setLevel(logging.ERROR)
    
    logger = logging.getLogger("JARVIS")
    logger.info("=" * 60)
    logger.info(f"🚀 JARVIS Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📁 Log Directory: {log_dir}")
    logger.info("=" * 60)
    
    return logger


class GuiLogger:
    """Redirect output to GUI terminal (unchanged)"""
    
    def __init__(self, gui_handler):
        self.gui_handler = gui_handler
    
    def write(self, message):
        msg = message.strip()
        if msg:
            try:
                # Don't show debug prints in terminal
                if not msg.startswith('[DEBUG]'):
                    self.gui_handler.show_terminal_output(msg, color="white")
            except:
                pass
    
    def flush(self):
        pass