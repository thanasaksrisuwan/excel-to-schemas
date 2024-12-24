import logging
import os
from datetime import datetime
import tkinter as tk

class TkinterHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.configure(state='disabled')
        self.text_widget.see(tk.END)

def setup_logging(config_manager, gui_handler=None):
    """Setup logging configuration"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Create logs directory if it doesn't exist
    logs_dir = config_manager.get_logs_dir()
    os.makedirs(logs_dir, exist_ok=True)

    # Create file handler
    log_file = os.path.join(logs_dir, f'app_{datetime.now():%Y%m%d_%H%M%S}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Add GUI handler if provided
    if gui_handler:
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)

    return logger
