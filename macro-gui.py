import threading
import time
import json
import os
import keyboard
from collections import deque
import pydirectinput
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# Ensure pydirectinput is configured properly
pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0.01

class MacroStep:
    def __init__(self, action, **params):
        self.action = action
        self.params = params
        
    def execute(self):
        try:
            if self.action == "mouse_move":
                pydirectinput.moveTo(self.params['x'], self.params['y'])
            elif self.action == "mouse_click":
                pydirectinput.click(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
            elif self.action == "mouse_double_click":
                pydirectinput.doubleClick(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
            elif self.action == "mouse_down":
                pydirectinput.mouseDown(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
            elif self.action == "mouse_up":
                pydirectinput.mouseUp(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
            elif self.action == "key_press":
                pydirectinput.press(self.params['key'])
            elif self.action == "key_down":
                pydirectinput.keyDown(self.params['key'])
            elif self.action == "key_up":
                pydirectinput.keyUp(self.params['key'])
            elif self.action == "wait":
                time.sleep(self.params['duration'])
        except Exception as e:
            print(f"Error executing step: {e}")
    
    def to_dict(self):
        return {"action": self.action, "params": self.params}
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["action"], **data["params"])
    
    def __str__(self):
        if self.action == "wait":
            return f"Wait: {self.params['duration']} seconds"
        elif self.action == "key_press":
            return f"Key Press: {self.params['key']}"
        elif self.action == "mouse_click":
            return f"Mouse Click: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')} button"
        elif self.action == "mouse_double_click":
            return f"Mouse Double Click: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')} button"
        elif self.action == "mouse_move":
            return f"Mouse Move: ({self.params['x']}, {self.params['y']})"
        elif self.action == "key_down":
            return f"Key Down: {self.params['key']}"
        elif self.action == "key_up":
            return f"Key Up: {self.params['key']}"
        elif self.action == "mouse_down":
            return f"Mouse Down: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')} button"
        elif self.action == "mouse_up":
            return f"Mouse Up: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')} button"
        return f"{self.action}: {self.params}"

class Macro:
    def __init__(self, name, hotkey, steps=None, enabled=True, loop_count=1, stop_hotkey=None):
        self.name = name
        self.hotkey = hotkey
        self.stop_hotkey = stop_hotkey
        self.steps = steps or []
        self.is_playing = False
        self.enabled = enabled
        self.loop_count = loop_count
        self.thread = None
        self.last_execution_time = 0
        
    def play(self):
        if self.is_playing or not self.enabled:
            return False
            
        self.is_playing = True
        self.last_execution_time = time.time()
        self.thread = threading.Thread(target=self._play)
        self.thread.start()
        return True
        
    def stop(self):
        was_playing = self.is_playing
        self.is_playing = False
        if self.thread:
            self.thread.join()
        return was_playing
            
    def _play(self):
        # Release all keys before starting to prevent stuck keys
        self._release_all_keys()
        
        try:
            if self.loop_count == 0:  # Infinite loop
                while self.is_playing:
                    for step in self.steps:
                        if not self.is_playing:
                            break
                        step.execute()
            else:  # Finite loop count
                for _ in range(self.loop_count):
                    if not self.is_playing:
                        break
                    for step in self.steps:
                        if not self.is_playing:
                            break
                        step.execute()
        except Exception as e:
            print(f"Error during macro execution: {e}")
        
        # Release all keys after finishing to prevent stuck keys
        self._release_all_keys()
        self.is_playing = False
        
    def _release_all_keys(self):
        """Release all modifier keys to prevent them from getting stuck"""
        try:
            # Release common modifier keys that might get stuck
            modifier_keys = ['alt', 'ctrl', 'shift', 'windows']
            for key in modifier_keys:
                try:
                    pydirectinput.keyUp(key)
                except:
                    pass
        except Exception as e:
            print(f"Error releasing keys: {e}")
        
    def toggle_enabled(self):
        self.enabled = not self.enabled
        return self.enabled
        
    def to_dict(self):
        return {
            "name": self.name,
            "hotkey": self.hotkey,
            "stop_hotkey": self.stop_hotkey,
            "steps": [step.to_dict() for step in self.steps],
            "enabled": self.enabled,
            "loop_count": self.loop_count
        }
    
    @classmethod
    def from_dict(cls, data):
        macro = cls(data["name"], data["hotkey"], 
                   enabled=data.get("enabled", True),
                   loop_count=data.get("loop_count", 1),
                   stop_hotkey=data.get("stop_hotkey"))
        macro.steps = [MacroStep.from_dict(step) for step in data["steps"]]
        return macro

class MacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyDirectInput Macro Recorder")
        self.root.geometry("900x600")
        
        self.macros = []
        self.current_profile = "default"
        self.profiles = {}
        self.current_macro_index = -1
        self.editing_step_index = -1
        self.global_stop_hotkey = "ctrl+shift+q"
        
        # Hotkey state tracking
        self.ignore_hotkeys_until = 0
        self.last_hotkey_check_time = 0
        self.hotkey_states = {}  # Track state of each hotkey to detect presses
        
        self.setup_ui()
        self.load_profiles()
        
        # Start a thread to handle hotkeys
        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()
        
    def setup_ui(self):
        # Main frames
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel for macro list
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.N, tk.S), padx=(0, 10))
        
        ttk.Label(left_frame, text="Macros").grid(row=0, column=0, sticky=tk.W)
        self.macro_listbox = tk.Listbox(left_frame, width=30, height=15)
        self.macro_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.macro_listbox.bind('<<ListboxSelect>>', self.on_macro_select)
        
        # Buttons for macro management
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(btn_frame, text="Add", command=self.add_macro).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="Remove", command=self.remove_macro).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="Duplicate", command=self.duplicate_macro).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="Toggle On/Off", command=self.toggle_macro).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Right panel for macro editing
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Macro details
        detail_frame = ttk.LabelFrame(right_frame, text="Macro Details", padding="5")
        detail_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        
        ttk.Label(detail_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(detail_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.name_entry.bind('<FocusOut>', self.update_macro_name)
        
        ttk.Label(detail_frame, text="Start Hotkey:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.hotkey_var = tk.StringVar()
        self.hotkey_entry = ttk.Entry(detail_frame, textvariable=self.hotkey_var)
        self.hotkey_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.hotkey_entry.bind('<FocusOut>', self.update_macro_hotkey)
        
        ttk.Label(detail_frame, text="Stop Hotkey:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.stop_hotkey_var = tk.StringVar()
        self.stop_hotkey_entry = ttk.Entry(detail_frame, textvariable=self.stop_hotkey_var)
        self.stop_hotkey_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.stop_hotkey_entry.bind('<FocusOut>', self.update_macro_stop_hotkey)
        
        # Loop count
        ttk.Label(detail_frame, text="Loop Count:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.loop_var = tk.StringVar(value="1")
        self.loop_entry = ttk.Entry(detail_frame, textvariable=self.loop_var)
        self.loop_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.loop_entry.bind('<FocusOut>', self.update_macro_loop)
        
        # Loop count help label
        ttk.Label(detail_frame, text="0 = infinite, 1 = once, 2+ = specific count", 
                 font=("Arial", 8), foreground="gray").grid(row=4, column=1, sticky=tk.W, pady=(0, 2))
        
        # Enabled checkbox
        self.enabled_var = tk.BooleanVar(value=True)
        self.enabled_check = ttk.Checkbutton(detail_frame, text="Macro Enabled", variable=self.enabled_var,
                                           command=self.toggle_macro_enabled)
        self.enabled_check.grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # Hotkey help label
        ttk.Label(detail_frame, text="Format: ctrl+shift+a, f1, alt+f2, etc.", 
                 font=("Arial", 8), foreground="gray").grid(row=6, column=1, sticky=tk.W, pady=(0, 5))
        
        # Global stop hotkey
        global_stop_frame = ttk.Frame(detail_frame)
        global_stop_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(global_stop_frame, text="Global Stop Hotkey:").pack(side=tk.LEFT)
        self.global_stop_var = tk.StringVar(value=self.global_stop_hotkey)
        self.global_stop_entry = ttk.Entry(global_stop_frame, textvariable=self.global_stop_var, width=15)
        self.global_stop_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.global_stop_entry.bind('<FocusOut>', self.update_global_stop_hotkey)
        
        ttk.Button(global_stop_frame, text="Stop All Now", command=self.stop_all_macros).pack(side=tk.LEFT, padx=(10, 0))
        
        # Steps list
        steps_frame = ttk.LabelFrame(right_frame, text="Steps", padding="5")
        steps_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Steps listbox with scrollbar
        steps_container = ttk.Frame(steps_frame)
        steps_container.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.steps_listbox = tk.Listbox(steps_container, height=10)
        self.steps_scrollbar = ttk.Scrollbar(steps_container, orient=tk.VERTICAL, command=self.steps_listbox.yview)
        self.steps_listbox.configure(yscrollcommand=self.steps_scrollbar.set)
        
        self.steps_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.steps_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Step buttons
        steps_btn_frame = ttk.Frame(steps_frame)
        steps_btn_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(steps_btn_frame, text="Add Step", command=self.add_step).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(steps_btn_frame, text="Remove Step", command=self.remove_step).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(steps_btn_frame, text="Duplicate Step", command=self.duplicate_step).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(steps_btn_frame, text="Move Up", command=self.move_step_up).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(steps_btn_frame, text="Move Down", command=self.move_step_down).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(steps_btn_frame, text="Edit Step", command=self.edit_step).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(right_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # Profile management
        profile_frame = ttk.LabelFrame(main_frame, text="Profiles", padding="5")
        profile_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(profile_frame, text="Current Profile:").grid(row=0, column=0, sticky=tk.W)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, state="readonly")
        self.profile_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_change)
        
        ttk.Button(profile_frame, text="New Profile", command=self.new_profile).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(profile_frame, text="Save Profile", command=self.save_profile).grid(row=0, column=3, padx=(5, 0))
        ttk.Button(profile_frame, text="Delete Profile", command=self.delete_profile).grid(row=0, column=4, padx=(5, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        steps_container.columnconfigure(0, weight=1)
        steps_container.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(1, weight=1)
        profile_frame.columnconfigure(1, weight=1)
        
    def hotkey_listener(self):
        """Background thread to handle hotkey presses"""
        # Initialize hotkey states
        all_hotkeys = set()
        for macro in self.macros:
            if macro.hotkey:
                all_hotkeys.add(macro.hotkey)
            if macro.stop_hotkey:
                all_hotkeys.add(macro.stop_hotkey)
        all_hotkeys.add(self.global_stop_hotkey)
        
        for hotkey in all_hotkeys:
            self.hotkey_states[hotkey] = False
        
        while True:
            time.sleep(0.02)  # Very fast polling for better responsiveness
            
            current_time = time.time()
            
            # Check global stop hotkey first (highest priority)
            global_stop_pressed = self._check_hotkey_press(self.global_stop_hotkey, "global_stop")
            if global_stop_pressed:
                self.stop_all_macros()
                self.ignore_hotkeys_until = current_time + 1.0  # Ignore for 1 second after stop
                continue
            
            # Skip if we're ignoring hotkeys
            if current_time < self.ignore_hotkeys_until:
                continue
            
            # Check individual macro stop hotkeys (medium priority)
            stop_hotkey_triggered = False
            for macro in self.macros:
                if macro.is_playing and macro.stop_hotkey:
                    stop_pressed = self._check_hotkey_press(macro.stop_hotkey, f"stop_{macro.name}")
                    if stop_pressed:
                        if macro.stop():
                            self.status_var.set(f"Stopped macro: {macro.name}")
                            self.root.after(2000, lambda: self.status_var.set(""))
                            self.ignore_hotkeys_until = current_time + 0.5
                            stop_hotkey_triggered = True
                            break
            
            if stop_hotkey_triggered:
                continue
            
            # Check macro start hotkeys (lowest priority)
            for macro in self.macros:
                if not macro.is_playing and macro.enabled and macro.hotkey:
                    start_pressed = self._check_hotkey_press(macro.hotkey, f"start_{macro.name}")
                    if start_pressed:
                        if macro.play():
                            loop_text = "infinite" if macro.loop_count == 0 else f"{macro.loop_count} times"
                            self.status_var.set(f"Playing macro: {macro.name} ({loop_text})")
                            self.root.after(2000, lambda: self.status_var.set(""))
                            # Ignore hotkeys for a moment after starting to prevent retriggering
                            self.ignore_hotkeys_until = current_time + 0.3
                            break
        
    def _check_hotkey_press(self, hotkey, hotkey_id):
        """Check if a hotkey was pressed (edge detection)"""
        if not hotkey:
            return False
            
        try:
            current_state = keyboard.is_pressed(hotkey)
            previous_state = self.hotkey_states.get(hotkey_id, False)
            
            # Update state
            self.hotkey_states[hotkey_id] = current_state
            
            # Return True only on rising edge (key was just pressed)
            return current_state and not previous_state
        except Exception as e:
            print(f"Error checking hotkey {hotkey}: {e}")
            return False
        
    def stop_all_macros(self):
        """Stop all currently running macros"""
        stopped_count = 0
        for macro in self.macros:
            if macro.stop():
                stopped_count += 1
        
        if stopped_count > 0:
            self.status_var.set(f"Stopped {stopped_count} macro(s)")
            self.root.after(2000, lambda: self.status_var.set(""))
        
    def load_profiles(self):
        # Load profiles from disk
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
            
        # Load global settings if they exist
        global_settings_path = os.path.join("profiles", "global_settings.json")
        if os.path.exists(global_settings_path):
            try:
                with open(global_settings_path, 'r') as f:
                    global_settings = json.load(f)
                    self.global_stop_hotkey = global_settings.get("global_stop_hotkey", "ctrl+shift+q")
                    self.global_stop_var.set(self.global_stop_hotkey)
            except:
                pass
            
        profiles = {}
        for filename in os.listdir("profiles"):
            if filename.endswith(".json") and filename != "global_settings.json":
                profile_name = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join("profiles", filename), 'r') as f:
                        profiles[profile_name] = json.load(f)
                except:
                    pass
                    
        self.profiles = profiles
        self.profile_combo['values'] = list(self.profiles.keys()) + ["default"]
        
        if "default" in self.profiles:
            self.current_profile = "default"
            self.profile_var.set("default")
            self.load_macros_from_profile()
        else:
            self.profile_var.set("")
            
    def save_profiles(self):
        # Save all profiles to disk
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
            
        # Save global settings
        global_settings = {
            "global_stop_hotkey": self.global_stop_hotkey
        }
        with open(os.path.join("profiles", "global_settings.json"), 'w') as f:
            json.dump(global_settings, f, indent=2)
            
        for profile_name, macros_data in self.profiles.items():
            with open(os.path.join("profiles", f"{profile_name}.json"), 'w') as f:
                json.dump(macros_data, f, indent=2)
                
    def on_profile_change(self, event):
        self.save_current_macros_to_profile()
        self.current_profile = self.profile_var.get()
        self.load_macros_from_profile()
        
    def load_macros_from_profile(self):
        # Load macros from current profile
        self.macros = []
        self.macro_listbox.delete(0, tk.END)
        
        if self.current_profile in self.profiles:
            for macro_data in self.profiles[self.current_profile]:
                macro = Macro.from_dict(macro_data)
                self.macros.append(macro)
                self.add_macro_to_listbox(macro)
                
    def add_macro_to_listbox(self, macro):
        """Add a macro to the listbox with proper formatting"""
        loop_text = "∞" if macro.loop_count == 0 else str(macro.loop_count)
        stop_text = f" [Stop: {macro.stop_hotkey}]" if macro.stop_hotkey else ""
        display_name = f"{'[ON] ' if macro.enabled else '[OFF] '}{macro.name} (x{loop_text}){stop_text}"
        self.macro_listbox.insert(tk.END, display_name)
                
    def save_current_macros_to_profile(self):
        # Save current macros to profile
        macros_data = [macro.to_dict() for macro in self.macros]
        self.profiles[self.current_profile] = macros_data
        self.save_profiles()
        
    def new_profile(self):
        profile_name = simpledialog.askstring("New Profile", "Enter profile name:")
        if profile_name and profile_name not in self.profiles:
            self.profiles[profile_name] = []
            self.profile_combo['values'] = list(self.profiles.keys())
            self.profile_var.set(profile_name)
            self.current_profile = profile_name
            self.macros = []
            self.macro_listbox.delete(0, tk.END)
            self.save_profiles()
            
    def save_profile(self):
        if self.current_profile:
            self.save_current_macros_to_profile()
            
    def delete_profile(self):
        if self.current_profile and self.current_profile != "default":
            if messagebox.askyesno("Delete Profile", f"Are you sure you want to delete profile '{self.current_profile}'?"):
                # Delete from memory
                del self.profiles[self.current_profile]
                
                # Delete from disk
                profile_path = os.path.join("profiles", f"{self.current_profile}.json")
                if os.path.exists(profile_path):
                    os.remove(profile_path)
                    
                # Update UI
                self.profile_combo['values'] = list(self.profiles.keys())
                if self.profiles:
                    self.current_profile = list(self.profiles.keys())[0]
                    self.profile_var.set(self.current_profile)
                    self.load_macros_from_profile()
                else:
                    self.current_profile = ""
                    self.profile_var.set("")
                    self.macros = []
                    self.macro_listbox.delete(0, tk.END)
                    
    def add_macro(self):
        macro_name = simpledialog.askstring("New Macro", "Enter macro name:")
        if macro_name:
            hotkey = simpledialog.askstring("Start Hotkey", "Enter start hotkey (e.g., ctrl+shift+a, f1, alt+f2):")
            if hotkey:
                stop_hotkey = simpledialog.askstring("Stop Hotkey", "Enter stop hotkey (optional, leave empty for none):")
                loop_count = simpledialog.askinteger("Loop Count", "Enter loop count (0=infinite, 1=once, 2+=specific):", initialvalue=1, minvalue=0)
                if loop_count is not None:
                    macro = Macro(macro_name, hotkey, loop_count=loop_count, stop_hotkey=stop_hotkey)
                    self.macros.append(macro)
                    self.add_macro_to_listbox(macro)
                    self.macro_listbox.selection_clear(0, tk.END)
                    self.macro_listbox.selection_set(tk.END)
                    self.on_macro_select(None)
                
    def remove_macro(self):
        selection = self.macro_listbox.curselection()
        if selection:
            index = selection[0]
            self.macros.pop(index)
            self.macro_listbox.delete(index)
            if self.macros:
                self.macro_listbox.selection_set(0)
                self.on_macro_select(None)
            else:
                self.name_var.set("")
                self.hotkey_var.set("")
                self.stop_hotkey_var.set("")
                self.loop_var.set("1")
                self.enabled_var.set(True)
                self.steps_listbox.delete(0, tk.END)
                self.current_macro_index = -1
            
    def duplicate_macro(self):
        selection = self.macro_listbox.curselection()
        if selection:
            index = selection[0]
            macro = self.macros[index]
            new_macro = Macro(f"{macro.name} Copy", macro.hotkey, macro.steps.copy(), macro.enabled, macro.loop_count, macro.stop_hotkey)
            self.macros.append(new_macro)
            self.add_macro_to_listbox(new_macro)
            
    def toggle_macro(self):
        selection = self.macro_listbox.curselection()
        if selection:
            index = selection[0]
            macro = self.macros[index]
            enabled = macro.toggle_enabled()
            self.update_macro_display_name(index)
            self.enabled_var.set(enabled)
            status = "enabled" if enabled else "disabled"
            self.status_var.set(f"Macro {status}: {macro.name}")
            self.root.after(2000, lambda: self.status_var.set(""))
            
    def toggle_macro_enabled(self):
        if self.current_macro_index >= 0:
            enabled = self.enabled_var.get()
            self.macros[self.current_macro_index].enabled = enabled
            self.update_macro_display_name(self.current_macro_index)
            
    def update_macro_display_name(self, index):
        """Update the display name for a specific macro index"""
        if 0 <= index < len(self.macros):
            macro = self.macros[index]
            loop_text = "∞" if macro.loop_count == 0 else str(macro.loop_count)
            stop_text = f" [Stop: {macro.stop_hotkey}]" if macro.stop_hotkey else ""
            display_name = f"{'[ON] ' if macro.enabled else '[OFF] '}{macro.name} (x{loop_text}){stop_text}"
            
            self.macro_listbox.delete(index)
            self.macro_listbox.insert(index, display_name)
            if index == self.current_macro_index:
                self.macro_listbox.selection_set(index)
    
    def update_macro_loop(self, event):
        if self.current_macro_index >= 0:
            try:
                new_loop = int(self.loop_var.get())
                if new_loop >= 0:
                    self.macros[self.current_macro_index].loop_count = new_loop
                    self.update_macro_display_name(self.current_macro_index)
                    loop_desc = "infinite" if new_loop == 0 else f"{new_loop} times"
                    self.status_var.set(f"Loop count set to: {loop_desc}")
                    self.root.after(2000, lambda: self.status_var.set(""))
            except ValueError:
                self.status_var.set("Error: Loop count must be a number")
                self.root.after(2000, lambda: self.status_var.set(""))
    
    def update_macro_stop_hotkey(self, event):
        if self.current_macro_index >= 0:
            new_stop_hotkey = self.stop_hotkey_var.get()
            self.macros[self.current_macro_index].stop_hotkey = new_stop_hotkey if new_stop_hotkey else None
            self.update_macro_display_name(self.current_macro_index)
            if new_stop_hotkey:
                self.status_var.set(f"Stop hotkey set to: {new_stop_hotkey}")
            else:
                self.status_var.set("Stop hotkey removed")
            self.root.after(2000, lambda: self.status_var.set(""))
            
    def update_global_stop_hotkey(self, event):
        new_global_stop = self.global_stop_var.get()
        if new_global_stop:
            self.global_stop_hotkey = new_global_stop
            self.save_profiles()  # Save immediately when changed
            self.status_var.set(f"Global stop hotkey set to: {new_global_stop}")
            self.root.after(2000, lambda: self.status_var.set(""))
            
    def on_macro_select(self, event):
        """Handle macro selection from the listbox"""
        if event is None or event.widget == self.macro_listbox:
            selection = self.macro_listbox.curselection()
            if selection:
                index = selection[0]
                self.current_macro_index = index
                macro = self.macros[index]
                self.name_var.set(macro.name)
                self.hotkey_var.set(macro.hotkey)
                self.stop_hotkey_var.set(macro.stop_hotkey or "")
                self.loop_var.set(str(macro.loop_count))
                self.enabled_var.set(macro.enabled)
                self.update_steps_listbox(macro)
            
    def update_macro_name(self, event):
        if self.current_macro_index >= 0:
            new_name = self.name_var.get()
            if new_name:
                self.macros[self.current_macro_index].name = new_name
                self.update_macro_display_name(self.current_macro_index)
                
    def update_macro_hotkey(self, event):
        if self.current_macro_index >= 0:
            new_hotkey = self.hotkey_var.get()
            if new_hotkey:
                self.macros[self.current_macro_index].hotkey = new_hotkey
                self.update_macro_display_name(self.current_macro_index)
                self.status_var.set(f"Start hotkey updated to: {new_hotkey}")
                self.root.after(2000, lambda: self.status_var.set(""))
                
    def update_steps_listbox(self, macro):
        self.steps_listbox.delete(0, tk.END)
        for step in macro.steps:
            self.steps_listbox.insert(tk.END, str(step))
            
    def add_step(self):
        if self.current_macro_index < 0:
            messagebox.showwarning("No Macro Selected", "Please select a macro first.")
            return
            
        # Create a dialog to select step type
        step_dialog = tk.Toplevel(self.root)
        step_dialog.title("Add Step")
        step_dialog.geometry("300x350")
        step_dialog.transient(self.root)
        step_dialog.grab_set()
        
        # Force focus on the dialog
        step_dialog.focus_force()
        
        ttk.Label(step_dialog, text="Select step type:").pack(pady=10)
        
        step_type = tk.StringVar(value="wait")
        
        step_frame = ttk.Frame(step_dialog)
        step_frame.pack(pady=10, fill=tk.X, padx=20)
        
        ttk.Radiobutton(step_frame, text="Wait", variable=step_type, value="wait").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Key Press", variable=step_type, value="key_press").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Key Down", variable=step_type, value="key_down").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Key Up", variable=step_type, value="key_up").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Mouse Click", variable=step_type, value="mouse_click").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Mouse Double Click", variable=step_type, value="mouse_double_click").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Mouse Down", variable=step_type, value="mouse_down").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Mouse Up", variable=step_type, value="mouse_up").pack(anchor=tk.W)
        ttk.Radiobutton(step_frame, text="Mouse Move", variable=step_type, value="mouse_move").pack(anchor=tk.W)
        
        def on_ok():
            step_dialog.destroy()
            self.root.after(100, lambda: self.create_step(step_type.get()))
            
        def on_cancel():
            step_dialog.destroy()
            
        btn_frame = ttk.Frame(step_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Set focus to OK button
        step_dialog.after(100, lambda: step_dialog.focus_force())
        
    def create_step(self, step_type):
        params = {}
        if step_type == "wait":
            duration = self.ask_input_with_focus("Wait Duration", "Enter duration in seconds:", float)
            if duration is not None:
                params["duration"] = duration
        elif step_type in ["key_press", "key_down", "key_up"]:
            key = self.ask_input_with_focus("Key Press", "Enter key to press:", str)
            if key:
                params["key"] = key
        elif step_type in ["mouse_click", "mouse_double_click", "mouse_down", "mouse_up"]:
            x = self.ask_input_with_focus("Mouse Click", "Enter X coordinate:", int)
            y = self.ask_input_with_focus("Mouse Click", "Enter Y coordinate:", int)
            button = self.ask_input_with_focus("Mouse Click", "Enter button (left/right/middle):", str) or "left"
            if x is not None and y is not None:
                params.update({"x": x, "y": y, "button": button})
        elif step_type == "mouse_move":
            x = self.ask_input_with_focus("Mouse Move", "Enter X coordinate:", int)
            y = self.ask_input_with_focus("Mouse Move", "Enter Y coordinate:", int)
            if x is not None and y is not None:
                params.update({"x": x, "y": y})
                
        if params:
            step = MacroStep(step_type, **params)
            if self.current_macro_index >= 0:
                # If we're editing an existing step, replace it
                if self.editing_step_index >= 0:
                    self.macros[self.current_macro_index].steps[self.editing_step_index] = step
                    self.editing_step_index = -1
                else:
                    # Otherwise, add a new step
                    self.macros[self.current_macro_index].steps.append(step)
                self.update_steps_listbox(self.macros[self.current_macro_index])
                
    def ask_input_with_focus(self, title, prompt, input_type):
        """Ask for input with proper focus handling"""
        # Create a custom dialog to ensure focus
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_force()
        
        ttk.Label(dialog, text=prompt).pack(pady=10, padx=20)
        
        entry_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=entry_var, width=30)
        entry.pack(pady=5, padx=20)
        entry.focus_force()
        
        result = [None]
        
        def on_ok():
            result[0] = entry_var.get()
            dialog.destroy()
            
        def on_cancel():
            dialog.destroy()
            
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Wait for the dialog to close
        self.root.wait_window(dialog)
        
        if result[0] is not None:
            try:
                if input_type == float:
                    return float(result[0])
                elif input_type == int:
                    return int(result[0])
                else:
                    return str(result[0])
            except ValueError:
                return None
        return None
                
    def remove_step(self):
        step_selection = self.steps_listbox.curselection()
        if self.current_macro_index >= 0 and step_selection:
            step_index = step_selection[0]
            self.macros[self.current_macro_index].steps.pop(step_index)
            self.update_steps_listbox(self.macros[self.current_macro_index])
            
    def duplicate_step(self):
        step_selection = self.steps_listbox.curselection()
        if self.current_macro_index >= 0 and step_selection:
            step_index = step_selection[0]
            step = self.macros[self.current_macro_index].steps[step_index]
            # Create a copy of the step
            import copy
            new_step = copy.deepcopy(step)
            self.macros[self.current_macro_index].steps.insert(step_index + 1, new_step)
            self.update_steps_listbox(self.macros[self.current_macro_index])
            self.steps_listbox.select_set(step_index + 1)
            
    def move_step_up(self):
        step_selection = self.steps_listbox.curselection()
        if self.current_macro_index >= 0 and step_selection:
            step_index = step_selection[0]
            if step_index > 0:
                steps = self.macros[self.current_macro_index].steps
                steps[step_index], steps[step_index-1] = steps[step_index-1], steps[step_index]
                self.update_steps_listbox(self.macros[self.current_macro_index])
                self.steps_listbox.select_set(step_index-1)
                
    def move_step_down(self):
        step_selection = self.steps_listbox.curselection()
        if self.current_macro_index >= 0 and step_selection:
            step_index = step_selection[0]
            steps = self.macros[self.current_macro_index].steps
            if step_index < len(steps) - 1:
                steps[step_index], steps[step_index+1] = steps[step_index+1], steps[step_index]
                self.update_steps_listbox(self.macros[self.current_macro_index])
                self.steps_listbox.select_set(step_index+1)
                
    def edit_step(self):
        step_selection = self.steps_listbox.curselection()
        if self.current_macro_index >= 0 and step_selection:
            step_index = step_selection[0]
            step = self.macros[self.current_macro_index].steps[step_index]
            self.editing_step_index = step_index
            
            # Create a dialog to edit the step
            step_dialog = tk.Toplevel(self.root)
            step_dialog.title("Edit Step")
            step_dialog.geometry("300x350")
            step_dialog.transient(self.root)
            step_dialog.grab_set()
            
            # Force focus on the dialog
            step_dialog.focus_force()
            
            ttk.Label(step_dialog, text="Select step type:").pack(pady=10)
            
            step_type = tk.StringVar(value=step.action)
            
            step_frame = ttk.Frame(step_dialog)
            step_frame.pack(pady=10, fill=tk.X, padx=20)
            
            ttk.Radiobutton(step_frame, text="Wait", variable=step_type, value="wait").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Key Press", variable=step_type, value="key_press").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Key Down", variable=step_type, value="key_down").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Key Up", variable=step_type, value="key_up").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Mouse Click", variable=step_type, value="mouse_click").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Mouse Double Click", variable=step_type, value="mouse_double_click").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Mouse Down", variable=step_type, value="mouse_down").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Mouse Up", variable=step_type, value="mouse_up").pack(anchor=tk.W)
            ttk.Radiobutton(step_frame, text="Mouse Move", variable=step_type, value="mouse_move").pack(anchor=tk.W)
            
            def on_ok():
                step_dialog.destroy()
                self.root.after(100, lambda: self.create_step(step_type.get()))
                
            def on_cancel():
                step_dialog.destroy()
                self.editing_step_index = -1
                
            btn_frame = ttk.Frame(step_dialog)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
            
            # Set focus to OK button
            step_dialog.after(100, lambda: step_dialog.focus_force())
            
    def on_closing(self):
        self.save_current_macros_to_profile()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()