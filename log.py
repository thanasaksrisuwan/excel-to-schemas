import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(config_manager, log_level=logging.INFO, gui_handler=None):
    """Setup logging configuration with both file and console output"""
    # Use config manager's logs directory
    logs_dir = config_manager.get_logs_dir()

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'app_{timestamp}.log')

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers = []

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # GUI handler if provided
    if gui_handler:
        gui_handler.setFormatter(file_formatter)
        root_logger.addHandler(gui_handler)

    logging.info(f"Logging initialized. Log file: {log_file}")
    return root_logger

class TkinterHandler(logging.Handler):
    """Custom logging handler for Tkinter text widget"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert('end', msg + '\n')
            self.text_widget.see('end')
            self.text_widget.configure(state='disabled')
        # Schedule in the main thread
        self.text_widget.after(0, append)
