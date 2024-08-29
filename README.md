# Ollama Chat Application

## Overview

The Ollama Chat Application is a Python-based user interface (UI) for chatting with AI models using the `ollama` library. The application is built using `tkinter` and provides a rich set of features including a scrollable chat history, customizable appearance, utility tools management, and code execution with tracking and error correction.

## Features

- **Chat Interface:** Allows users to interact with AI models, sending and receiving messages in a conversation format.
- **Utility Tools Management:** Users can add, edit, delete, and run utility tools (custom Python code) within the app.
- **System Prompts Management:** Manage predefined system prompts to customize AI behavior.
- **Customizable Appearance:** Users can change the font size, foreground color, and background color of the chat interface.
- **Clipboard Integration:** Copy AI responses to the clipboard for easy sharing.
- **Code Execution:** Run detected Python code blocks within the chat, with error tracking and automatic correction attempts.
- **Keyboard Shortcuts:** Quick actions using keyboard shortcuts like sending messages, clearing chat, and copying responses.

Usage
Sending Messages: Type your message in the input box and press Ctrl+Enter to send it. The AI's response will appear in the chat history.
Copying AI Responses: Use Ctrl+Shift+B to copy the AI's responses to the clipboard.
Managing Prompts: Access the system prompt management via the System Prompt menu to add or edit predefined prompts.
Utility Tools: Create or edit utility tools using the Utility Tools menu. Tools can be executed directly from the UI.
Appearance Customization: Change font size, foreground, and background colors via the Appearance menu.
Code Execution: If the AI suggests a Python code block, you will be prompted to execute it within the app.
Configuration
The application uses a configuration manager to persist user settings like background color, font size, and utility tools. These settings are saved automatically and reloaded on the next application start.

Shortcuts
Send Message: Ctrl+Enter
Stop Typing: Ctrl+S
Clear Chat: Ctrl+D
Copy AI Responses: Ctrl+Shift+B
