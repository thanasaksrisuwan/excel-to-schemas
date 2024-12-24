import os
import json
import logging
import sys
from pathlib import Path

class ConfigManager:
    def __init__(self, app_name="ExcelToSchemas"):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self._ensure_config_dir()
        self.config = self.load_config()

    def _get_config_dir(self):
        """Get the appropriate config directory based on the OS"""
        if hasattr(sys, '_MEIPASS'):  # Check if running as compiled exe
            if sys.platform == 'win32':
                base_dir = os.path.join(os.environ['LOCALAPPDATA'], self.app_name)
            elif sys.platform == 'darwin':  # macOS
                base_dir = os.path.expanduser(f'~/Library/Application Support/{self.app_name}')
            else:  # Linux and others
                base_dir = os.path.expanduser(f'~/.config/{self.app_name}')
        else:
            # Development mode - use local directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return base_dir

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        os.makedirs(self.config_dir, exist_ok=True)

    def get_default_config(self):
        """Return default configuration"""
        return {
            "database": {
                "driver": "ODBC Driver 17 for SQL Server",
                "server": "",
                "database": "",
                "username": "",
                "password": ""
            },
            "file_path": "",
            "batch_size": 1000,
            "timeout": 30,
            "retry_attempts": 3,
            "log_level": "INFO",
            "selected_sheets": [],
            "export_type": "database"
        }

    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Update with any missing default values
                default_config = self.get_default_config()
                self._update_dict_recursive(default_config, config)
                return default_config
            else:
                return self.get_default_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return self.get_default_config()

    def _update_dict_recursive(self, base_dict, update_dict):
        """Recursively update dictionary while preserving existing values"""
        for key, value in base_dict.items():
            if key in update_dict:
                if isinstance(value, dict) and isinstance(update_dict[key], dict):
                    self._update_dict_recursive(value, update_dict[key])
                else:
                    base_dict[key] = update_dict[key]

    def save_config(self, config_data):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            logging.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            return False

    def get_logs_dir(self):
        """Get the logs directory path"""
        logs_dir = os.path.join(self.config_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
