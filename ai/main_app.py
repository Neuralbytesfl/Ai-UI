import tkinter as tk
from config_manager import ConfigManager
from ollama_chat_app import OllamaChatApp

def main():
    root = tk.Tk()
    config_manager = ConfigManager()
    app = OllamaChatApp(root, config_manager)
    root.mainloop()

if __name__ == "__main__":
    main()
