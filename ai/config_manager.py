import json
import os

class ConfigManager:
    def __init__(self, config_file_path="config.json"):
        self.config_file_path = config_file_path
        self.default_config = {
            "system_prompts": {
                "Default": "You are an expert Python programmer and mentor. Always provide correct and efficient code."
            },
            "default_prompt": "Default",
            "font_size": 12,
            "foreground_color": "#FFFFFF",
            "background_color": "#23272A",
            "utility_tools": {}  # Add default empty dictionary for utility tools
        }
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "r") as f:
                return json.load(f)
        else:
            return self.default_config

    def save_config(self):
        with open(self.config_file_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
