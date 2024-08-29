import tkinter as tk
from tkinter import scrolledtext, Menu, messagebox, simpledialog, colorchooser, Listbox, Toplevel
import threading
import time
import ollama
from config_manager import ConfigManager
from utility import Utility
import os
import gc
import pyperclip  # Needed for copy to clipboard functionality

class OllamaChatApp:
    def __init__(self, root, config_manager):
        self.root = root
        self.config_manager = config_manager
        self.typing = True
        self.current_canvas = None
        self.history_index = -1
        self.input_history = []
        self.output_lock = threading.Lock()
        self.conversation_history = []  # For context history
        self.max_history_length =50  # Maximum number of history entries to retain
        self.utility_tools = self.config_manager.get("utility_tools", {})  # Load utility tools from config
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Ollama Chat")
        self.root.geometry("600x700")
        self.root.configure(bg=self.config_manager.get("background_color"))

        self.create_menu_bar()
        self.create_chat_widgets()
        self.create_buttons()

        self.update_text_widget_styles()

    def copy_to_clipboard(self):
      self.chat_history.configure(state=tk.NORMAL)
      text_lines = self.chat_history.get("1.0", tk.END).strip().split("\n")
    
      ai_responses = []
      collecting = False

      for line in text_lines:
          if line.startswith("You:"):
              collecting = True
              ai_responses = []  # Start collecting new AI responses after the last user query
          elif collecting and not line.startswith("You:"):
              ai_responses.append(line.strip())
    
      if ai_responses:
          pyperclip.copy("\n".join(ai_responses))
        # Optionally, show a messagebox:
        # messagebox.showinfo("Copy to Clipboard", "AI responses copied to clipboard.")
      else:
        # Optionally, show a warning if no AI response was found:
        # messagebox.showwarning("Copy to Clipboard", "No AI response found to copy.")
          pass

      self.chat_history.configure(state=tk.DISABLED)

    def create_menu_bar(self):
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.exit_app)
        menu_bar.add_cascade(label="File", menu=file_menu)

        prompt_menu = Menu(menu_bar, tearoff=0)
        prompt_menu.add_command(label="Manage System Prompts", command=self.manage_system_prompts)
        menu_bar.add_cascade(label="System Prompt", menu=prompt_menu)

        utility_menu = Menu(menu_bar, tearoff=0)
        utility_menu.add_command(label="Manage Utility Tools", command=self.manage_utility_tools)
        menu_bar.add_cascade(label="Utility Tools", menu=utility_menu)

        appearance_menu = Menu(menu_bar, tearoff=0)
        appearance_menu.add_command(label="Increase Font Size", command=self.increase_font_size)
        appearance_menu.add_command(label="Change Foreground Color", command=self.change_foreground_color)
        appearance_menu.add_command(label="Change Background Color", command=self.change_background_color)
        menu_bar.add_cascade(label="Appearance", menu=appearance_menu)

        help_menu = Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

    def create_chat_widgets(self):
        self.chat_history = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state=tk.DISABLED, font=('Courier', self.config_manager.get("font_size")), 
                                                      bg=self.config_manager.get("background_color"), fg=self.config_manager.get("foreground_color"))
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_history.tag_configure("user", foreground="#7289DA")
        self.chat_history.tag_configure("ollama", foreground="#99AAB5")
        self.chat_history.tag_configure("error", foreground="#FF5555")
        self.chat_history.tag_configure("result", foreground="#00FF00")

        self.input_text = tk.Text(self.root, height=4, font=('Courier', self.config_manager.get("font_size")), 
                                  bg=self.config_manager.get("background_color"), fg=self.config_manager.get("foreground_color"), insertbackground='white')
        self.input_text.pack(padx=10, pady=10, fill=tk.X)
        self.input_text.bind('<Up>', self.navigate_history)
        self.input_text.bind('<Down>', self.navigate_history)

    def create_buttons(self):
        button_frame = tk.Frame(self.root, bg='#2C2F33')
        button_frame.pack(padx=10, pady=10, fill=tk.X)

        send_button = tk.Button(button_frame, text="Send (Ctrl+Enter)", command=self.send_message, bg='#7289DA', fg='#FFFFFF', font=('Courier', 12))
        send_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.root.bind('<Control-Return>', lambda event: self.send_message())

        stop_button = tk.Button(button_frame, text="Stop (Ctrl+S)", command=self.stop_typing, bg='#FF5555', fg='#FFFFFF', font=('Courier', 12))
        stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.root.bind('<Control-s>', lambda event: self.stop_typing())

        clear_button = tk.Button(button_frame, text="Clear (Ctrl+D)", command=self.clear_chat, bg='#FFAA33', fg='#FFFFFF', font=('Courier', 12))
        clear_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.root.bind('<Control-d>', lambda event: self.clear_chat())

        copy_button = tk.Button(button_frame, text="Copy (Ctrl+Shift+B)", command=self.copy_to_clipboard, bg='#33AAFF', fg='#FFFFFF', font=('Courier', 12))
        copy_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.root.bind('<Control-Shift-B>', lambda event: self.copy_to_clipboard())


    def send_message(self):
        user_message = self.input_text.get("1.0", tk.END).strip()
        if not user_message:
            return
        self.input_history.append(user_message)
        self.history_index = -1
        self.input_text.delete("1.0", tk.END)
        self.input_text.config(state=tk.DISABLED)
        if self.current_canvas:
            self.current_canvas.get_tk_widget().pack_forget()
            self.current_canvas = None
        self.update_chat_history(f"You: {user_message}\n", "user")
        
        # Add user message to conversation history
        self.conversation_history.append({'role': 'user', 'content': user_message})
        # Trim conversation history if it exceeds the maximum length
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history.pop(0)

        self.typing = True
        threading.Thread(target=self.fetch_response, args=(user_message,)).start()

    def extract_error_line(self, error_message, code):
        try:
            parts = error_message.split("line")
            if len(parts) > 1:
                line_number_part = parts[1].split(":")[0].strip()
                if line_number_part.isdigit():
                    line_number = int(line_number_part)
                    code_lines = code.splitlines()
                    if 0 < line_number <= len(code_lines):
                        return code_lines[line_number - 1], line_number
                    else:
                        return f"Line number {line_number} is out of range for the provided code.", line_number
                else:
                    return "Could not determine the line number from the error message.", None
            else:
                return "Could not find the line number in the error message.", None
        except Exception as e:
            print(f"Error extracting line number: {str(e)}")
            return None, None

    def highlight_problematic_code(self, error_message, code):
        error_line, line_number = self.extract_error_line(error_message, code)
        if error_line and line_number:
            print(f"\nError in the following line (Line {line_number}):\n\n{error_line.strip()}\n\n")
            print("Suggested correction:")
            if "invalid syntax" in error_message:
                print("Check for missing or extra characters, such as a misplaced comma, parenthesis, or colon.")
            elif "must be dict" in error_message:
                print("Ensure that the 'globals' argument is passed as a dictionary and not None.")
        else:
            print("Could not determine the exact line of the error.")

    def track_error(self, error_message, code):
        # Log the error to a file
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error: {error_message}\n")
            log_file.write(f"Code: {code}\n")
            log_file.write("="*40 + "\n")
        # Extract and print the problematic part of the code
        error_line, line_number = self.extract_error_line(error_message, code)
        if error_line and line_number:
            print(f"Error in the following line (Line {line_number}):\n\n{error_line.strip()}\n\n")
            print("Suggested correction:")
            if "invalid syntax" in error_message:
                print("Check for missing or extra characters, such as a misplaced comma, parenthesis, or colon.")
            elif "must be dict" in error_message:
                print("Ensure that the 'globals' argument is passed as a dictionary and not None.")
            # Send the error details back to AI for correction
            self.correct_code(code, error_message, line_number, attempt=1)
        else:
            print("Could not determine the exact line of the error.")

    def correct_code(self, code, error_message, line_number, attempt):
        correction_prompt = f"The following code produced an error on line {line_number}:\n\n```python\n{code}\n```\nError message: {error_message}\n\nPlease provide a corrected version of the code."
        self.fetch_corrected_code(correction_prompt, attempt)

    def fetch_corrected_code(self, correction_prompt, attempt):
        try:
            system_message = {'role': 'system', 'content': self.config_manager.get("system_prompts").get(self.config_manager.get("default_prompt"))}
            messages = [system_message, {'role': 'user', 'content': correction_prompt}]
            response = ollama.chat(model='llama3.1', messages=messages, stream=True)
            full_reply = ""
            for part in response:
                if not self.typing:
                    break
                reply = part['message']['content']
                full_reply += reply
            code_block = Utility.extract_code_block(full_reply)
            if code_block:
                self.update_chat_history(f"AI provided a corrected code (Attempt {attempt}):\n", "ollama")
                self.prompt_code_execution(code_block)
            else:
                self.update_chat_history("AI failed to provide a corrected code.\n", "error")
        except Exception as e:
            self.update_chat_history(f"Error: {str(e)}\n", "error")

    def fetch_response(self, user_message):
        try:
            system_message = {'role': 'system', 'content': self.config_manager.get("system_prompts").get(self.config_manager.get("default_prompt"), "Default")}
            messages = [system_message] + self.conversation_history + [{'role': 'user', 'content': user_message}]
            
            response = ollama.chat(
                model='llama3.1',
                messages=messages,
                stream=True,
            )
            
            full_reply = ""
            for part in response:
                if not self.typing:
                    break
                reply = part['message']['content']
                for char in reply:
                    if not self.typing:
                        break
                    full_reply += char
                    self.root.after(0, self.update_chat_history, char)
                    time.sleep(0.01)
            self.root.after(0, self.update_chat_history, "\n")
            
            code_block = Utility.extract_code_block(full_reply)
            if code_block:
                self.root.after(0, self.prompt_code_execution, code_block)
            
            self.conversation_history.append({'role': 'assistant', 'content': full_reply})
            if len(self.conversation_history) > self.max_history_length:
                self.conversation_history.pop(0)
                
        except Exception as e:
            self.root.after(0, self.update_chat_history, f"Error: {str(e)}\n", "error")
        self.root.after(0, self.enable_input)

    def navigate_history(self, event):
        if self.input_history:
            if event.keysym == 'Up':
                if self.history_index == -1:
                    self.history_index = len(self.input_history) - 1
                elif self.history_index > 0:
                    self.history_index -= 1
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, self.input_history[self.history_index])
            elif event.keysym == 'Down':
                if self.history_index < len(self.input_history) - 1:
                    self.history_index += 1
                    self.input_text.delete("1.0", tk.END)
                    self.input_text.insert(tk.END, self.input_history[self.history_index])
                else:
                    self.history_index = -1
                    self.input_text.delete("1.0", tk.END)

    def prompt_code_execution(self, code_block):
        if messagebox.askyesno("Run Code", "A Python code block was detected. Do you want to run this code?"):
            thread = threading.Thread(target=self.execute_code_with_tracking, args=(code_block,))
            thread.start()

    def execute_code_with_tracking(self, code, attempt=1):
        temp_script = f"temp_script_{int(time.time())}.py"
        def cleanup():
            os.remove(temp_script)
            gc.collect()
        try:
            with open(temp_script, "w") as f:
                f.write(code)
            result = Utility.execute_code(open(temp_script).read(), globals(), cleanup)
            self.update_chat_history(f"Result:\n{result}\n", "result")
        except ModuleNotFoundError as e:
            package_name = str(e).split("'")[1]
            self.update_chat_history(f"Package '{package_name}' not found. Attempting to install...\n", "error")
            if Utility.install_package(package_name):
                self.execute_code_with_tracking(code)  # Retry executing the code after installation
            else:
                self.handle_missing_package(package_name, code)
        except Exception as e:
            self.update_chat_history(f"Error executing code: {str(e)}\n", "error")
            self.track_error(str(e), code)
            if attempt < 5:  # Maximum attempts
                self.correct_code(code, str(e), attempt + 1)
            else:
                self.update_chat_history("Maximum attempts reached. Could not correct the code.\n", "error")

    def handle_missing_package(self, package_name, code):
        correction_prompt = f"The package '{package_name}' could not be found. Please provide an alternative package or a different approach to achieve the same functionality.\n\nHere is the code that requires the package:\n\n```python\n{code}\n```"
        self.fetch_corrected_code(correction_prompt, attempt=1)

    def update_chat_history(self, text, tag="ollama"):
        with self.output_lock:
            self.chat_history.configure(state=tk.NORMAL)
            self.chat_history.insert(tk.END, text, tag)
            self.chat_history.configure(state=tk.DISABLED)
            self.chat_history.yview(tk.END)

    def stop_typing(self):
        self.typing = False
        self.enable_input()

    def clear_chat(self):
        self.chat_history.configure(state=tk.NORMAL)
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state=tk.DISABLED)
        if self.current_canvas:
            self.current_canvas.get_tk_widget().pack_forget()
            self.current_canvas = None

  



    def enable_input(self):
        self.input_text.config(state=tk.NORMAL)

    def exit_app(self):
        self.config_manager.save_config()
        self.root.quit()

    def show_about(self):
        messagebox.showinfo("About", "Ollama Chat\nVersion 1.0")

    def manage_system_prompts(self):
        prompt_window = Toplevel(self.root)
        prompt_window.title("Manage System Prompts")
        prompt_window.geometry("400x300")

        listbox = Listbox(prompt_window)
        listbox.pack(fill=tk.BOTH, expand=True)

        for prompt in self.config_manager.get("system_prompts").keys():
            listbox.insert(tk.END, prompt)

        def edit_prompt():
            selected = listbox.curselection()
            if selected:
                prompt_name = listbox.get(selected)
                new_text = simpledialog.askstring("Edit System Prompt", f"Edit the text for '{prompt_name}':", initialvalue=self.config_manager.get("system_prompts")[prompt_name])
                if new_text:
                    self.config_manager.get("system_prompts")[prompt_name] = new_text
                    self.config_manager.save_config()

        def delete_prompt():
            selected = listbox.curselection()
            if selected:
                prompt_name = listbox.get(selected)
                if messagebox.askyesno("Delete System Prompt", f"Are you sure you want to delete '{prompt_name}'?"):
                    del self.config_manager.get("system_prompts")[prompt_name]
                    listbox.delete(selected)
                    self.config_manager.save_config()

        def add_prompt():
            prompt_name = simpledialog.askstring("Add System Prompt", "Enter the name of the new system prompt:")
            if prompt_name:
                prompt_text = simpledialog.askstring("Add System Prompt", "Enter the text for the new system prompt:")
                if prompt_text:
                    self.config_manager.get("system_prompts")[prompt_name] = prompt_text
                    listbox.insert(tk.END, prompt_name)
                    self.config_manager.save_config()

        def set_default_prompt():
            selected = listbox.curselection()
            if selected:
                self.config_manager.set("default_prompt", listbox.get(selected))
                messagebox.showinfo("Default System Prompt", f"'{self.config_manager.get('default_prompt')}' is now the default system prompt.")

        button_frame = tk.Frame(prompt_window)
        button_frame.pack(fill=tk.X, pady=10)

        edit_button = tk.Button(button_frame, text="Edit", command=edit_prompt)
        edit_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(button_frame, text="Delete", command=delete_prompt)
        delete_button.pack(side=tk.LEFT, padx=5)

        add_button = tk.Button(button_frame, text="Add", command=add_prompt)
        add_button.pack(side=tk.LEFT, padx=5)

        default_button = tk.Button(button_frame, text="Set Default", command=set_default_prompt)
        default_button.pack(side=tk.LEFT, padx=5)

    def manage_utility_tools(self):
        utility_window = Toplevel(self.root)
        utility_window.title("Manage Utility Tools")
        utility_window.geometry("400x300")

        listbox = Listbox(utility_window)
        listbox.pack(fill=tk.BOTH, expand=True)

        # Populate listbox with utility tool names
        for tool_name in self.utility_tools.keys():
            listbox.insert(tk.END, tool_name)

        def edit_tool():
            selected = listbox.curselection()
            if selected:
                tool_name = listbox.get(selected)
                new_code = simpledialog.askstring("Edit Utility Tool", f"Edit the code for '{tool_name}':", initialvalue=self.utility_tools[tool_name])
                if new_code:
                    self.utility_tools[tool_name] = new_code
                    self.save_utility_tools()

        def delete_tool():
            selected = listbox.curselection()
            if selected:
                tool_name = listbox.get(selected)
                if messagebox.askyesno("Delete Utility Tool", f"Are you sure you want to delete '{tool_name}'?"):
                    del self.utility_tools[tool_name]
                    listbox.delete(selected)
                    self.save_utility_tools()

        def add_tool():
            tool_name = simpledialog.askstring("Add Utility Tool", "Enter the name of the new utility tool:")
            if tool_name:
                tool_code = simpledialog.askstring("Add Utility Tool", "Enter the code for the new utility tool:")
                if tool_code:
                    self.utility_tools[tool_name] = tool_code
                    listbox.insert(tk.END, tool_name)
                    self.save_utility_tools()

        def run_tool():
            selected = listbox.curselection()
            if selected:
                tool_name = listbox.get(selected)
                tool_code = self.utility_tools.get(tool_name)
                if tool_code:
                    self.run_utility_tool(tool_code)

        button_frame = tk.Frame(utility_window)
        button_frame.pack(fill=tk.X, pady=10)

        add_button = tk.Button(button_frame, text="Add", command=add_tool)
        add_button.pack(side=tk.LEFT, padx=5)

        edit_button = tk.Button(button_frame, text="Edit", command=edit_tool)
        edit_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(button_frame, text="Delete", command=delete_tool)
        delete_button.pack(side=tk.LEFT, padx=5)

        run_button = tk.Button(button_frame, text="Run", command=run_tool)
        run_button.pack(side=tk.LEFT, padx=5)

    def run_utility_tool(self, code):
        try:
            exec(code, globals())
            messagebox.showinfo("Success", "Utility Tool executed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute Utility Tool: {str(e)}")

    def save_utility_tools(self):
        self.config_manager.set("utility_tools", self.utility_tools)

    def increase_font_size(self):
        self.config_manager.set("font_size", self.config_manager.get("font_size") + 2)
        self.update_text_widget_styles()

    def change_foreground_color(self):
        color = colorchooser.askcolor(title="Choose Foreground Color")[1]
        if color:
            self.config_manager.set("foreground_color", color)
            self.update_text_widget_styles()

    def change_background_color(self):
        color = colorchooser.askcolor(title="Choose Background Color")[1]
        if color:
            self.config_manager.set("background_color", color)
            self.update_text_widget_styles()

    def update_text_widget_styles(self):
        self.chat_history.configure(font=('Courier', self.config_manager.get("font_size")), fg=self.config_manager.get("foreground_color"), bg=self.config_manager.get("background_color"))
        self.input_text.configure(font=('Courier', self.config_manager.get("font_size")), fg=self.config_manager.get("foreground_color"), bg=self.config_manager.get("background_color"))
        self.config_manager.save_config()

if __name__ == "__main__":
    root = tk.Tk()
    config_manager = ConfigManager()
    app = OllamaChatApp(root, config_manager)
    root.mainloop()
