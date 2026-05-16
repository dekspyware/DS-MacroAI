import threading
import time
import json
import os
import keyboard
import pydirectinput
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Ensure pydirectinput is configured properly
pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0.01

# Dark Theme Colors
COLORS = {
    'bg': '#1e1e1e',
    'fg': '#ffffff',
    'accent': '#0078d4',
    'accent_hover': '#106ebe',
    'border': '#3c3c3c',
    'entry_bg': '#2d2d2d',
    'entry_fg': '#ffffff',
    'button_bg': '#0e639c',
    'button_fg': '#ffffff',
    'listbox_bg': '#252526',
    'listbox_fg': '#cccccc',
    'listbox_select': '#094771',
    'delete': '#c42b1c',
    'delete_hover': '#e81123',
}

# Toggle action types
TOGGLE_ACTIONS = {
    0: "Single Press (Run once)",
    1: "Toggle (Press to start/stop)",
    2: "Hold (Run while holding)",
    3: "Loop X Times",
}

# Key mapping for special characters
KEY_MAPPINGS = {
    'plus': '+', 'minus': '-', 'equal': '=', 'bracketleft': '[', 'bracketright': ']',
    'backslash': '\\', 'semicolon': ';', 'apostrophe': "'", 'comma': ',', 'period': '.',
    'slash': '/', 'grave': '`', 'space': 'space', 'return': 'enter', 'backspace': 'backspace',
    'tab': 'tab', 'escape': 'esc', 'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
    'num_lock': 'numlock', 'num_divide': '/', 'num_multiply': '*', 'num_subtract': '-',
    'num_add': '+', 'num_enter': 'enter', 'num_decimal': '.', 'num_0': '0', 'num_1': '1',
    'num_2': '2', 'num_3': '3', 'num_4': '4', 'num_5': '5', 'num_6': '6', 'num_7': '7',
    'num_8': '8', 'num_9': '9',
}

class MacroStep:
    def __init__(self, action, **params):
        self.action = action
        self.params = params
        
    def execute(self, status_callback=None):
        try:
            if self.action == "mouse_move":
                if status_callback:
                    status_callback(f"Moving to ({self.params['x']}, {self.params['y']})")
                pydirectinput.moveTo(self.params['x'], self.params['y'])
            elif self.action == "mouse_click":
                if status_callback:
                    if 'x' in self.params and 'y' in self.params:
                        status_callback(f"Click at ({self.params['x']}, {self.params['y']})")
                        pydirectinput.click(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
                    else:
                        status_callback(f"Click at current position")
                        pydirectinput.click(button=self.params.get('button', 'left'))
            elif self.action == "mouse_double_click":
                if status_callback:
                    if 'x' in self.params and 'y' in self.params:
                        status_callback(f"Double click at ({self.params['x']}, {self.params['y']})")
                        pydirectinput.doubleClick(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
                    else:
                        status_callback(f"Double click at current position")
                        pydirectinput.doubleClick(button=self.params.get('button', 'left'))
            elif self.action == "mouse_down":
                if status_callback:
                    if 'x' in self.params and 'y' in self.params:
                        status_callback(f"Mouse down at ({self.params['x']}, {self.params['y']})")
                        pydirectinput.mouseDown(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
                    else:
                        status_callback(f"Mouse down at current position")
                        pydirectinput.mouseDown(button=self.params.get('button', 'left'))
            elif self.action == "mouse_up":
                if status_callback:
                    if 'x' in self.params and 'y' in self.params:
                        status_callback(f"Mouse up at ({self.params['x']}, {self.params['y']})")
                        pydirectinput.mouseUp(self.params['x'], self.params['y'], button=self.params.get('button', 'left'))
                    else:
                        status_callback(f"Mouse up at current position")
                        pydirectinput.mouseUp(button=self.params.get('button', 'left'))
            elif self.action == "key_press":
                if status_callback:
                    status_callback(f"Pressing key: {self.params['key']}")
                pydirectinput.press(self.params['key'])
            elif self.action == "key_down":
                if status_callback:
                    status_callback(f"Key down: {self.params['key']}")
                pydirectinput.keyDown(self.params['key'])
            elif self.action == "key_up":
                if status_callback:
                    status_callback(f"Key up: {self.params['key']}")
                pydirectinput.keyUp(self.params['key'])
            elif self.action == "wait":
                duration = self.params['duration']
                if status_callback:
                    status_callback(f"Waiting {duration}s...")
                time.sleep(duration)
                if status_callback:
                    status_callback(f"Wait complete")
        except Exception as e:
            print(f"Error: {e}")
    
    def to_dict(self):
        return {"action": self.action, "params": self.params}
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["action"], **data["params"])
    
    def get_display_text(self):
        if self.action == "wait":
            d = self.params['duration']
            return f"⏱ Wait: {int(d*1000)}ms" if d < 1 else f"⏱ Wait: {d}s"
        elif self.action == "key_press":
            return f"⌨ Press: {self.params['key']}"
        elif self.action == "key_down":
            return f"⌨ Key Down: {self.params['key']}"
        elif self.action == "key_up":
            return f"⌨ Key Up: {self.params['key']}"
        elif self.action == "mouse_click":
            if 'x' in self.params and 'y' in self.params:
                return f"🖱 Click: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')}"
            else:
                return f"🖱 Click (Current Pos): {self.params.get('button', 'left')}"
        elif self.action == "mouse_double_click":
            if 'x' in self.params and 'y' in self.params:
                return f"🖱 Double Click: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')}"
            else:
                return f"🖱 Double Click (Current Pos): {self.params.get('button', 'left')}"
        elif self.action == "mouse_down":
            if 'x' in self.params and 'y' in self.params:
                return f"🖱 Mouse Down: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')}"
            else:
                return f"🖱 Mouse Down (Current Pos): {self.params.get('button', 'left')}"
        elif self.action == "mouse_up":
            if 'x' in self.params and 'y' in self.params:
                return f"🖱 Mouse Up: ({self.params['x']}, {self.params['y']}) {self.params.get('button', 'left')}"
            else:
                return f"🖱 Mouse Up (Current Pos): {self.params.get('button', 'left')}"
        elif self.action == "mouse_move":
            return f"🖱 Move to: ({self.params['x']}, {self.params['y']})"
        return f"{self.action}: {self.params}"

class Macro:
    def __init__(self, name, hotkey="", steps=None, enabled=True, loop_count=1, stop_hotkey="", toggle_action=0):
        self.name = name
        self.hotkey = hotkey
        self.stop_hotkey = stop_hotkey
        self.steps = steps or []
        self.enabled = enabled
        self.loop_count = loop_count
        self.toggle_action = toggle_action
        self.is_playing = False
        self.is_holding = False
        self.hold_thread = None
        self.thread = None
        self.status_callback = None
        
    def set_callback(self, cb):
        self.status_callback = cb
        
    def play(self):
        if self.is_playing or not self.enabled:
            return False
            
        if self.toggle_action == 1:
            if self.is_playing:
                self.stop()
                return True
            else:
                self.is_playing = True
                self.thread = threading.Thread(target=self._run_toggle)
                self.thread.start()
                return True
        elif self.toggle_action == 2:
            if not self.is_holding:
                self.is_holding = True
                self.hold_thread = threading.Thread(target=self._hold_loop)
                self.hold_thread.start()
            return True
        else:
            if not self.is_playing:
                self.is_playing = True
                self.thread = threading.Thread(target=self._run)
                self.thread.start()
                return True
        return False
        
    def _run_toggle(self):
        self._release_keys()
        try:
            loop = 1
            while self.is_playing:
                self._status(f"Loop {loop} (∞)")
                self._execute_steps()
                loop += 1
        except Exception as e:
            self._status(f"Error: {e}")
        self._release_keys()
        if self.status_callback:
            self.status_callback("Stopped")
            
    def _run(self):
        self._release_keys()
        try:
            if self.toggle_action == 3:
                for i in range(self.loop_count):
                    if not self.is_playing:
                        break
                    self._status(f"Loop {i+1}/{self.loop_count}")
                    self._execute_steps()
            elif self.loop_count == 0:
                loop = 1
                while self.is_playing:
                    self._status(f"Loop {loop} (∞)")
                    self._execute_steps()
                    loop += 1
            else:
                self._execute_steps()
        except Exception as e:
            self._status(f"Error: {e}")
        self._release_keys()
        self.is_playing = False
        if self.status_callback:
            self.status_callback("Finished")
        
    def _hold_loop(self):
        self._release_keys()
        while self.is_holding:
            self._execute_steps()
            if not self.is_holding:
                break
        self._release_keys()
        if self.status_callback:
            self.status_callback("Stopped (hold released)")
        
    def _execute_steps(self):
        for i, step in enumerate(self.steps):
            if not self.is_playing and not self.is_holding:
                break
            self._status(f"Step {i+1}: {step.get_display_text()}")
            step.execute(self._status)
            
    def _release_keys(self):
        for k in ['alt', 'ctrl', 'shift', 'windows']:
            try:
                pydirectinput.keyUp(k)
            except:
                pass
                
    def _status(self, msg):
        if self.status_callback:
            self.status_callback(msg)
    
    def stop(self):
        was_playing = self.is_playing
        self.is_playing = False
        self.is_holding = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.hold_thread:
            self.hold_thread.join(timeout=1)
        return was_playing
    
    def to_dict(self):
        return {
            "name": self.name, "hotkey": self.hotkey, "stop_hotkey": self.stop_hotkey,
            "steps": [s.to_dict() for s in self.steps], "enabled": self.enabled,
            "loop_count": self.loop_count, "toggle_action": self.toggle_action
        }
    
    @classmethod
    def from_dict(cls, data):
        m = cls(data["name"], data.get("hotkey", ""), enabled=data.get("enabled", True),
                loop_count=data.get("loop_count", 1), stop_hotkey=data.get("stop_hotkey", ""),
                toggle_action=data.get("toggle_action", 0))
        m.steps = [MacroStep.from_dict(s) for s in data["steps"]]
        return m

class ModernMacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Recorder")
        self.root.geometry("1300x800")
        self.root.configure(bg=COLORS['bg'])
        
        self.macros = []
        self.selected_index = -1
        self.drag_start_index = None
        self.current_profile = "default"
        self.profiles = {}
        self.global_stop = "ctrl+shift+q"
        self.mouse_capture_key = "f12"
        self._ignore_select = False
        
        self._setup_styles()
        self._setup_ui()
        self._load_profiles()
        
        self.ignore_until = 0
        self.last_capture = 0
        self.hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self.hotkey_thread.start()
        
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TLabelframe', background=COLORS['bg'], foreground=COLORS['fg'], borderwidth=1, relief='solid')
        style.configure('TLabelframe.Label', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TButton', background=COLORS['button_bg'], foreground=COLORS['button_fg'], borderwidth=0)
        style.map('TButton', background=[('active', COLORS['accent_hover'])])
        style.configure('Delete.TButton', background=COLORS['delete'])
        style.map('Delete.TButton', background=[('active', COLORS['delete_hover'])])
        style.configure('TEntry', fieldbackground=COLORS['entry_bg'], foreground=COLORS['entry_fg'])
        style.configure('TCombobox', fieldbackground=COLORS['entry_bg'], foreground=COLORS['entry_fg'])
        
    def _setup_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # LEFT PANEL - Macros
        left = ttk.Frame(main, width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        left.pack_propagate(False)
        
        ttk.Label(left, text="MACROS", font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0,10))
        
        self.macro_listbox = tk.Listbox(left, bg=COLORS['listbox_bg'], fg=COLORS['listbox_fg'],
                                        selectbackground=COLORS['listbox_select'], font=('Segoe UI', 10),
                                        height=15, borderwidth=0, highlightthickness=0)
        self.macro_listbox.pack(fill=tk.BOTH, expand=True)
        self.macro_listbox.bind('<<ListboxSelect>>', self._on_macro_select)
        
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="+ Add", command=self._add_macro).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="− Remove", command=self._remove_macro).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="📋 Duplicate", command=self._duplicate_macro).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # RIGHT PANEL - Editor
        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Properties
        props = ttk.LabelFrame(right, text="Properties", padding="10")
        props.pack(fill=tk.X, pady=(0,10))
        
        name_frame = ttk.Frame(props)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Name:", width=12).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        self.name_entry.bind('<FocusOut>', self._update_name)
        
        start_frame = ttk.Frame(props)
        start_frame.pack(fill=tk.X, pady=5)
        ttk.Label(start_frame, text="Start Hotkey:", width=12).pack(side=tk.LEFT)
        self.start_var = tk.StringVar()
        self.start_entry = ttk.Entry(start_frame, textvariable=self.start_var)
        self.start_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,5))
        self.start_entry.bind('<FocusOut>', self._update_start_hotkey)
        ttk.Button(start_frame, text="🎤", width=3, command=lambda: self._record_hotkey("start")).pack(side=tk.LEFT)
        
        stop_frame = ttk.Frame(props)
        stop_frame.pack(fill=tk.X, pady=5)
        ttk.Label(stop_frame, text="Stop Hotkey:", width=12).pack(side=tk.LEFT)
        self.stop_var = tk.StringVar()
        self.stop_entry = ttk.Entry(stop_frame, textvariable=self.stop_var)
        self.stop_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,5))
        self.stop_entry.bind('<FocusOut>', self._update_stop_hotkey)
        ttk.Button(stop_frame, text="🎤", width=3, command=lambda: self._record_hotkey("stop")).pack(side=tk.LEFT)
        
        toggle_frame = ttk.Frame(props)
        toggle_frame.pack(fill=tk.X, pady=5)
        ttk.Label(toggle_frame, text="Trigger Mode:", width=12).pack(side=tk.LEFT)
        self.toggle_combo = ttk.Combobox(toggle_frame, state="readonly", width=30)
        self.toggle_combo['values'] = list(TOGGLE_ACTIONS.values())
        self.toggle_combo.current(0)
        self.toggle_combo.bind('<<ComboboxSelected>>', self._on_toggle_change)
        self.toggle_combo.pack(side=tk.LEFT, padx=(5,5))
        
        self.loop_frame = ttk.Frame(props)
        self.loop_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.loop_frame, text="Loop Count:", width=12).pack(side=tk.LEFT)
        self.loop_var = tk.StringVar(value="1")
        self.loop_spin = ttk.Spinbox(self.loop_frame, from_=1, to=999, textvariable=self.loop_var, width=10)
        self.loop_spin.pack(side=tk.LEFT, padx=(5,0))
        self.loop_spin.bind('<FocusOut>', self._update_loop)
        self.loop_frame.pack_forget()
        
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(props, text="Macro Enabled", variable=self.enabled_var, command=self._toggle_enabled).pack(anchor=tk.W, pady=5)
        
        # Steps
        steps_frame = ttk.LabelFrame(right, text="Steps (Drag to reorder)", padding="10")
        steps_frame.pack(fill=tk.BOTH, expand=True)
        
        self.steps_listbox = tk.Listbox(steps_frame, bg=COLORS['listbox_bg'], fg=COLORS['listbox_fg'],
                                        selectbackground=COLORS['listbox_select'], font=('Segoe UI', 10), height=14)
        self.steps_listbox.pack(fill=tk.BOTH, expand=True)
        self.steps_listbox.bind('<Double-Button-1>', self._edit_step)
        self.steps_listbox.bind('<Button-1>', self._on_step_click)
        self.steps_listbox.bind('<B1-Motion>', self._on_drag_motion)
        self.steps_listbox.bind('<ButtonRelease-1>', self._on_drag_end)
        
        # Step buttons - Row 1 (Mouse actions with position)
        btn_row1 = ttk.Frame(steps_frame)
        btn_row1.pack(fill=tk.X, pady=(10,5))
        
        ttk.Button(btn_row1, text="🖱 Click (Position)", command=lambda: self._add_mouse_step("mouse_click", with_position=True)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row1, text="🖱 Click (Current)", command=lambda: self._add_mouse_step("mouse_click", with_position=False)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row1, text="🖱 Double Click", command=lambda: self._add_mouse_step("mouse_double_click", with_position=True)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row1, text="🖱 Double (Current)", command=lambda: self._add_mouse_step("mouse_double_click", with_position=False)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        btn_row1b = ttk.Frame(steps_frame)
        btn_row1b.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_row1b, text="🖱 Down", command=lambda: self._add_mouse_step("mouse_down", with_position=True)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row1b, text="🖱 Down (Current)", command=lambda: self._add_mouse_step("mouse_down", with_position=False)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row1b, text="🖱 Up", command=lambda: self._add_mouse_step("mouse_up", with_position=True)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row1b, text="🖱 Up (Current)", command=lambda: self._add_mouse_step("mouse_up", with_position=False)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row1b, text="🖱 Move", command=lambda: self._add_mouse_step("mouse_move", with_position=True)).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Step buttons - Row 2 (Key actions)
        btn_row2 = ttk.Frame(steps_frame)
        btn_row2.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_row2, text="⌨ Press", command=lambda: self._add_key_step("key_press")).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row2, text="⌨ Down", command=lambda: self._add_key_step("key_down")).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row2, text="⌨ Up", command=lambda: self._add_key_step("key_up")).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row2, text="⏱ Delay", command=self._add_delay).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Edit/Move/Delete buttons
        btn_row3 = ttk.Frame(steps_frame)
        btn_row3.pack(fill=tk.X, pady=(10,0))
        
        ttk.Button(btn_row3, text="✏ Edit", command=self._edit_selected_step).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row3, text="▲ Up", command=self._move_up).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row3, text="▼ Down", command=self._move_down).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row3, text="🗑 Delete", style='Delete.TButton', command=self._delete_step).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_row3, text="📋 Duplicate", command=self._duplicate_step).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar()
        ttk.Label(right, textvariable=self.status_var, font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(10,0))
        
        # Bottom Panel
        bottom = ttk.Frame(main)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(10,0))
        
        prof_frame = ttk.Frame(bottom)
        prof_frame.pack(side=tk.LEFT)
        ttk.Label(prof_frame, text="Profile:").pack(side=tk.LEFT)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(prof_frame, textvariable=self.profile_var, state="readonly", width=15)
        self.profile_combo.pack(side=tk.LEFT, padx=(5,5))
        self.profile_combo.bind('<<ComboboxSelected>>', self._on_profile_change)
        ttk.Button(prof_frame, text="New", command=self._new_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(prof_frame, text="Save", command=self._save_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(prof_frame, text="Delete", command=self._delete_profile).pack(side=tk.LEFT, padx=2)
        
        global_frame = ttk.Frame(bottom)
        global_frame.pack(side=tk.RIGHT)
        ttk.Label(global_frame, text="Global Stop:").pack(side=tk.LEFT)
        self.global_var = tk.StringVar(value=self.global_stop)
        ttk.Entry(global_frame, textvariable=self.global_var, width=12).pack(side=tk.LEFT, padx=(5,5))
        self.global_var.trace('w', self._update_global)
        ttk.Button(global_frame, text="🎤", width=3, command=lambda: self._record_hotkey("global")).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(global_frame, text="🛑 Stop All", command=self._stop_all).pack(side=tk.LEFT)
        ttk.Button(global_frame, text="📌 Capture", command=self._quick_capture).pack(side=tk.LEFT, padx=(10,0))
        
        self._status("Ready")
        
    def _on_step_click(self, event):
        self._ignore_select = True
        self.root.after(100, lambda: setattr(self, '_ignore_select', False))
        
    def _update_macro_list(self):
        current_sel = self.selected_index
        
        self.macro_listbox.delete(0, tk.END)
        for i, macro in enumerate(self.macros):
            self.macro_listbox.insert(tk.END, f"{'✓' if macro.enabled else '✗'} {macro.name}")
        
        if current_sel >= 0 and current_sel < len(self.macros):
            self._ignore_select = True
            self.macro_listbox.selection_clear(0, tk.END)
            self.macro_listbox.selection_set(current_sel)
            self.macro_listbox.see(current_sel)
            self._ignore_select = False
            
    def _update_steps(self):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            macro = self.macros[self.selected_index]
            self.steps_listbox.delete(0, tk.END)
            for i, step in enumerate(macro.steps):
                self.steps_listbox.insert(tk.END, f"{i+1}. {step.get_display_text()}")
        else:
            self.steps_listbox.delete(0, tk.END)
            
    def _update_properties(self):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            macro = self.macros[self.selected_index]
            self.name_var.set(macro.name)
            self.start_var.set(macro.hotkey)
            self.stop_var.set(macro.stop_hotkey or "")
            self.loop_var.set(str(macro.loop_count))
            self.enabled_var.set(macro.enabled)
            
            toggle_text = TOGGLE_ACTIONS.get(macro.toggle_action, "Single Press (Run once)")
            if self.toggle_combo.get() != toggle_text:
                self.toggle_combo.set(toggle_text)
            
            if macro.toggle_action == 3:
                self.loop_frame.pack(fill=tk.X, pady=5)
            else:
                self.loop_frame.pack_forget()
        else:
            self.name_var.set("")
            self.start_var.set("")
            self.stop_var.set("")
            self.loop_var.set("1")
            self.enabled_var.set(True)
            self.toggle_combo.set("Single Press (Run once)")
            self.loop_frame.pack_forget()
            
    def _add_mouse_step(self, step_type, with_position=True):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        if not with_position:
            # Add mouse action at current position (no coordinates)
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Add {step_type.replace('_', ' ').title()} (Current Position)")
            dialog.geometry("300x280")
            dialog.configure(bg=COLORS['bg'])
            dialog.transient(self.root)
            dialog.grab_set()
            
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width()//2) - 150
            y = self.root.winfo_y() + (self.root.winfo_height()//2) - 100
            dialog.geometry(f"+{x}+{y}")
            
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            ttk.Label(frame, text=f"Add {step_type.replace('_', ' ').title()}", font=('Segoe UI', 11, 'bold')).pack(pady=10)
            
            ttk.Label(frame, text="This will click at the current mouse position").pack(pady=5)
            
            if step_type != "mouse_move":
                ttk.Label(frame, text="Button:").pack(pady=5)
                btn_var = tk.StringVar(value="left")
                btn_frame = ttk.Frame(frame)
                btn_frame.pack()
                for b in ["left", "right", "middle"]:
                    ttk.Radiobutton(btn_frame, text=b.title(), variable=btn_var, value=b).pack(side=tk.LEFT, padx=10)
            
            def add():
                if step_type != "mouse_move":
                    step = MacroStep(step_type, button=btn_var.get())
                else:
                    step = MacroStep(step_type, x=0, y=0)  # Move at current position
                self.macros[self.selected_index].steps.append(step)
                self._update_steps()
                dialog.destroy()
                self._status(f"Added {step_type} (current position)")
                
            btn_action = ttk.Frame(frame)
            btn_action.pack(pady=15)
            ttk.Button(btn_action, text="Add", command=add, width=15).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_action, text="Cancel", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=10)
            
        else:
            # Add mouse action with position selection
            self._capture_mouse_for_step(step_type)
            
    def _capture_mouse_for_step(self, step_type):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add {step_type.replace('_', ' ').title()} (Select Position)")
        dialog.geometry("410x570")
        dialog.configure(bg=COLORS['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()//2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height()//2) - 200
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Current position display
        pos_frame = ttk.LabelFrame(frame, text="Live Mouse Position", padding="10")
        pos_frame.pack(fill=tk.X, pady=10)
        
        current_x = tk.StringVar(value="0")
        current_y = tk.StringVar(value="0")
        coord_frame = ttk.Frame(pos_frame)
        coord_frame.pack()
        ttk.Label(coord_frame, text="X:", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Label(coord_frame, textvariable=current_x, font=('Segoe UI', 12, 'bold'), foreground=COLORS['accent']).pack(side=tk.LEFT, padx=5)
        ttk.Label(coord_frame, text="Y:", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Label(coord_frame, textvariable=current_y, font=('Segoe UI', 12, 'bold'), foreground=COLORS['accent']).pack(side=tk.LEFT, padx=5)
        
        def update_pos():
            try:
                px, py = pydirectinput.position()
                current_x.set(str(px))
                current_y.set(str(py))
                dialog.after(50, update_pos)
            except:
                pass
        update_pos()
        
        ttk.Label(pos_frame, text="Move your mouse to desired position", font=('Segoe UI', 9)).pack(pady=5)
        
        # Manual entry frame
        manual_frame = ttk.LabelFrame(frame, text="Manual Entry", padding="10")
        manual_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(manual_frame, text="X coordinate:").pack(anchor=tk.W)
        x_var = tk.StringVar()
        x_entry = ttk.Entry(manual_frame, textvariable=x_var, font=('Segoe UI', 10))
        x_entry.pack(fill=tk.X, pady=5)
        
        ttk.Label(manual_frame, text="Y coordinate:").pack(anchor=tk.W)
        y_var = tk.StringVar()
        y_entry = ttk.Entry(manual_frame, textvariable=y_var, font=('Segoe UI', 10))
        y_entry.pack(fill=tk.X, pady=5)
        
        btn_use = ttk.Button(manual_frame, text="Use Current Position", 
                            command=lambda: (x_var.set(current_x.get()), y_var.set(current_y.get())))
        btn_use.pack(pady=10)
        
        if step_type != "mouse_move":
            button_frame = ttk.LabelFrame(frame, text="Mouse Button", padding="10")
            button_frame.pack(fill=tk.X, pady=10)
            btn_var = tk.StringVar(value="left")
            btn_inner = ttk.Frame(button_frame)
            btn_inner.pack()
            for b in ["left", "right", "middle"]:
                ttk.Radiobutton(btn_inner, text=b.title(), variable=btn_var, value=b).pack(side=tk.LEFT, padx=15)
        
        action_frame = ttk.Frame(frame)
        action_frame.pack(pady=20)
        
        def add():
            try:
                x_val = int(x_var.get()) if x_var.get() else int(current_x.get())
                y_val = int(y_var.get()) if y_var.get() else int(current_y.get())
                if step_type != "mouse_move":
                    self.macros[self.selected_index].steps.append(MacroStep(step_type, x=x_val, y=y_val, button=btn_var.get()))
                else:
                    self.macros[self.selected_index].steps.append(MacroStep(step_type, x=x_val, y=y_val))
                self._update_steps()
                dialog.destroy()
                self._status(f"Added {step_type}: ({x_val},{y_val})")
            except ValueError:
                messagebox.showerror("Error", "Invalid coordinates")
                
        ttk.Button(action_frame, text="Add Step", command=add, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Cancel", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=10)
        
    def _add_delay(self):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Delay")
        dialog.geometry("280x280")
        dialog.configure(bg=COLORS['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()//2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height()//2) - 100
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        ttk.Label(frame, text="Delay duration (seconds):", font=('Segoe UI', 10)).pack()
        delay_var = tk.StringVar(value="1.0")
        entry = ttk.Entry(frame, textvariable=delay_var, font=('Segoe UI', 11), width=15)
        entry.pack(pady=15)
        ttk.Label(frame, text="Examples: 0.1, 0.5, 1.0, 2.5, 5.0, 10.0", font=('Segoe UI', 9), foreground='gray').pack()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        def add():
            try:
                d = float(delay_var.get())
                self.macros[self.selected_index].steps.append(MacroStep("wait", duration=d))
                self._update_steps()
                dialog.destroy()
                self._status(f"Added delay: {d}s")
            except:
                messagebox.showerror("Error", "Invalid number")
                
        ttk.Button(btn_frame, text="Add", command=add, width=12).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=10)
        
    def _add_key_step(self, step_type):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        def on_key(key):
            if key:
                self.macros[self.selected_index].steps.append(MacroStep(step_type, key=key))
                self._update_steps()
                self._status(f"Added {step_type}: {key}")
        KeyRecorder(self.root, on_key).show()
        
    def _edit_selected_step(self):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        sel = self.steps_listbox.curselection()
        if not sel:
            messagebox.showinfo("Edit", "Select a step to edit")
            return
            
        idx = sel[0]
        step = self.macros[self.selected_index].steps[idx]
        self._edit_step_dialog(step, idx)
        
    def _edit_step(self, event):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        sel = self.steps_listbox.curselection()
        if sel:
            idx = sel[0]
            step = self.macros[self.selected_index].steps[idx]
            self._edit_step_dialog(step, idx)
            
    def _edit_step_dialog(self, step, idx):
        step_type = step.action
        
        if step_type == "wait":
            dialog = tk.Toplevel(self.root)
            dialog.title("Edit Delay")
            dialog.geometry("280x280")
            dialog.configure(bg=COLORS['bg'])
            dialog.transient(self.root)
            dialog.grab_set()
            
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width()//2) - 200
            y = self.root.winfo_y() + (self.root.winfo_height()//2) - 100
            dialog.geometry(f"+{x}+{y}")
            
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
            
            ttk.Label(frame, text="Delay (seconds):", font=('Segoe UI', 10)).pack()
            delay_var = tk.StringVar(value=str(step.params['duration']))
            entry = ttk.Entry(frame, textvariable=delay_var, font=('Segoe UI', 11))
            entry.pack(pady=15)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=20)
            
            def save():
                try:
                    step.params['duration'] = float(delay_var.get())
                    self._update_steps()
                    self._status(f"Updated delay: {step.params['duration']}s")
                    dialog.destroy()
                except:
                    messagebox.showerror("Error", "Invalid number")
                    
            ttk.Button(btn_frame, text="Save", command=save, width=12).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=10)
            
        elif step_type in ["key_press", "key_down", "key_up"]:
            def on_key(key):
                if key:
                    step.params['key'] = key
                    self._update_steps()
                    self._status(f"Updated {step_type}: {key}")
            KeyRecorder(self.root, on_key).show()
            
        elif step_type in ["mouse_click", "mouse_double_click", "mouse_down", "mouse_up", "mouse_move"]:
            has_position = 'x' in step.params and 'y' in step.params
            
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Edit {step_type.replace('_', ' ').title()}")
            dialog.geometry("450x450")
            dialog.configure(bg=COLORS['bg'])
            dialog.transient(self.root)
            dialog.grab_set()
            
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width()//2) - 225
            y = self.root.winfo_y() + (self.root.winfo_height()//2) - 225
            dialog.geometry(f"+{x}+{y}")
            
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
            
            # Position mode selection
            mode_frame = ttk.LabelFrame(frame, text="Position Mode", padding="10")
            mode_frame.pack(fill=tk.X, pady=10)
            
            use_position = tk.BooleanVar(value=has_position)
            
            def on_mode_change():
                if use_position.get():
                    coord_frame.pack(fill=tk.X, pady=10)
                else:
                    coord_frame.pack_forget()
            
            ttk.Radiobutton(mode_frame, text="Use specific coordinates", variable=use_position, value=True, command=on_mode_change).pack(anchor=tk.W)
            ttk.Radiobutton(mode_frame, text="Use current mouse position", variable=use_position, value=False, command=on_mode_change).pack(anchor=tk.W)
            
            # Coordinate frame
            coord_frame = ttk.Frame(frame)
            if has_position:
                coord_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(coord_frame, text="X coordinate:").pack(anchor=tk.W)
            x_var = tk.StringVar(value=str(step.params.get('x', 0)) if has_position else "0")
            x_entry = ttk.Entry(coord_frame, textvariable=x_var, font=('Segoe UI', 10))
            x_entry.pack(fill=tk.X, pady=5)
            
            ttk.Label(coord_frame, text="Y coordinate:").pack(anchor=tk.W, pady=(10,0))
            y_var = tk.StringVar(value=str(step.params.get('y', 0)) if has_position else "0")
            y_entry = ttk.Entry(coord_frame, textvariable=y_var, font=('Segoe UI', 10))
            y_entry.pack(fill=tk.X, pady=5)
            
            if step_type != "mouse_move":
                button_frame = ttk.LabelFrame(frame, text="Mouse Button", padding="10")
                button_frame.pack(fill=tk.X, pady=10)
                btn_var = tk.StringVar(value=step.params.get('button', 'left'))
                btn_inner = ttk.Frame(button_frame)
                btn_inner.pack()
                for b in ["left", "right", "middle"]:
                    ttk.Radiobutton(btn_inner, text=b.title(), variable=btn_var, value=b).pack(side=tk.LEFT, padx=15)
                    
            btn_action = ttk.Frame(frame)
            btn_action.pack(pady=25)
            
            def save():
                if use_position.get():
                    try:
                        step.params['x'] = int(x_var.get())
                        step.params['y'] = int(y_var.get())
                    except ValueError:
                        messagebox.showerror("Error", "Invalid coordinates")
                        return
                else:
                    # Remove coordinates if they exist
                    step.params.pop('x', None)
                    step.params.pop('y', None)
                
                if step_type != "mouse_move":
                    step.params['button'] = btn_var.get()
                self._update_steps()
                self._status(f"Updated {step_type}")
                dialog.destroy()
                    
            ttk.Button(btn_action, text="Save", command=save, width=12).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_action, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=10)
            
    def _delete_step(self):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        sel = self.steps_listbox.curselection()
        if sel:
            self.macros[self.selected_index].steps.pop(sel[0])
            self._update_steps()
            self._status("Step deleted")
            
    def _duplicate_step(self):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        sel = self.steps_listbox.curselection()
        if sel:
            import copy
            step = self.macros[self.selected_index].steps[sel[0]]
            self.macros[self.selected_index].steps.insert(sel[0]+1, copy.deepcopy(step))
            self._update_steps()
            self.steps_listbox.select_set(sel[0]+1)
            self._status("Step duplicated")
            
    def _move_up(self):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        sel = self.steps_listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            steps = self.macros[self.selected_index].steps
            steps[idx], steps[idx-1] = steps[idx-1], steps[idx]
            self._update_steps()
            self.steps_listbox.select_set(idx-1)
            self.steps_listbox.see(idx-1)
            
    def _move_down(self):
        if self.selected_index < 0 or self.selected_index >= len(self.macros):
            messagebox.showwarning("No Macro", "Select a macro first")
            return
            
        sel = self.steps_listbox.curselection()
        if sel and sel[0] < len(self.macros[self.selected_index].steps)-1:
            idx = sel[0]
            steps = self.macros[self.selected_index].steps
            steps[idx], steps[idx+1] = steps[idx+1], steps[idx]
            self._update_steps()
            self.steps_listbox.select_set(idx+1)
            self.steps_listbox.see(idx+1)
            
    def _on_drag_motion(self, event):
        if self.drag_start_index is None:
            self.drag_start_index = self.steps_listbox.nearest(event.y)
            return
        current_index = self.steps_listbox.nearest(event.y)
        if current_index != self.drag_start_index and current_index >= 0 and self.drag_start_index >= 0:
            items = list(self.steps_listbox.get(0, tk.END))
            if self.drag_start_index < len(items) and current_index < len(items):
                items[self.drag_start_index], items[current_index] = items[current_index], items[self.drag_start_index]
                self.steps_listbox.delete(0, tk.END)
                for item in items:
                    self.steps_listbox.insert(tk.END, item)
                self.steps_listbox.selection_set(current_index)
                if self.selected_index >= 0 and self.selected_index < len(self.macros):
                    steps = self.macros[self.selected_index].steps
                    steps[self.drag_start_index], steps[current_index] = steps[current_index], steps[self.drag_start_index]
                self.drag_start_index = current_index
            
    def _on_drag_end(self, event):
        self.drag_start_index = None
        
    def _record_hotkey(self, htype):
        def on_key(key):
            if key:
                if htype == "start":
                    self.start_var.set(key)
                    self._update_start_hotkey(None)
                elif htype == "stop":
                    self.stop_var.set(key)
                    self._update_stop_hotkey(None)
                elif htype == "global":
                    self.global_var.set(key)
                    self._update_global(None)
                self._status(f"Hotkey set: {key}")
        KeyRecorder(self.root, on_key).show()
        
    def _quick_capture(self):
        x, y = pydirectinput.position()
        self.root.clipboard_clear()
        self.root.clipboard_append(f"{x},{y}")
        self._status(f"📌 Captured: ({x},{y}) - Copied!")
        
    def _update_global(self, *args):
        self.global_stop = self.global_var.get()
        self._save_profiles()
        
    def _stop_all(self):
        count = sum(1 for m in self.macros if m.stop())
        if count:
            self._status(f"Stopped {count} macro(s)")
            
    def _status(self, msg):
        self.status_var.set(f"[{time.strftime('%H:%M:%S')}] {msg}")
        self.root.after(5000, lambda: self.status_var.set("") if self.status_var.get().endswith(msg) else None)
        
    def _on_macro_select(self, event):
        if self._ignore_select:
            return
            
        sel = self.macro_listbox.curselection()
        if sel and sel[0] < len(self.macros):
            self.selected_index = sel[0]
            self._update_properties()
            self._update_steps()
            self._status(f"Selected: {self.macros[self.selected_index].name}")
            
    def _add_macro(self):
        name = simpledialog.askstring("New Macro", "Enter macro name:")
        if name:
            macro = Macro(name)
            self.macros.append(macro)
            self.selected_index = len(self.macros) - 1
            self._update_macro_list()
            self._update_properties()
            self._update_steps()
            self._status(f"Added macro: {name}")
            
    def _remove_macro(self):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            self.macros.pop(self.selected_index)
            if self.macros:
                self.selected_index = min(self.selected_index, len(self.macros)-1)
            else:
                self.selected_index = -1
            self._update_macro_list()
            self._update_properties()
            self._update_steps()
            self._status("Macro removed")
            
    def _duplicate_macro(self):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            import copy
            original = self.macros[self.selected_index]
            new = copy.deepcopy(original)
            new.name = f"{original.name} Copy"
            self.macros.append(new)
            self._update_macro_list()
            self._status(f"Duplicated: {new.name}")
            
    def _update_name(self, event):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            old = self.macros[self.selected_index].name
            self.macros[self.selected_index].name = self.name_var.get()
            self._update_macro_list()
            self._status(f"Renamed: {old} → {self.macros[self.selected_index].name}")
            
    def _update_start_hotkey(self, event):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            self.macros[self.selected_index].hotkey = self.start_var.get()
            
    def _update_stop_hotkey(self, event):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            self.macros[self.selected_index].stop_hotkey = self.stop_var.get()
            
    def _update_loop(self, event):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            try:
                self.macros[self.selected_index].loop_count = int(self.loop_var.get())
            except:
                pass
                
    def _toggle_enabled(self):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            self.macros[self.selected_index].enabled = self.enabled_var.get()
            self._update_macro_list()
            self._status(f"Macro {'enabled' if self.macros[self.selected_index].enabled else 'disabled'}")
            
    def _on_toggle_change(self, event):
        if self.selected_index >= 0 and self.selected_index < len(self.macros):
            selected_text = self.toggle_combo.get()
            for value, text in TOGGLE_ACTIONS.items():
                if text == selected_text:
                    self.macros[self.selected_index].toggle_action = value
                    if value == 3:
                        self.loop_frame.pack(fill=tk.X, pady=5)
                    else:
                        self.loop_frame.pack_forget()
                    self._status(f"Trigger mode: {selected_text}")
                    break
                    
    def _hotkey_listener(self):
        key_states = {}
        
        while True:
            time.sleep(0.02)
            now = time.time()
            if now < self.ignore_until:
                continue
            try:
                if keyboard.is_pressed(self.global_stop):
                    self.root.after(0, self._stop_all)
                    self.ignore_until = now + 0.5
                    continue
            except:
                pass
            try:
                if keyboard.is_pressed(self.mouse_capture_key):
                    if now - self.last_capture > 0.5:
                        self.last_capture = now
                        self.root.after(0, self._quick_capture)
                    self.ignore_until = now + 0.3
                    continue
            except:
                pass
            for m in self.macros:
                if not m.enabled:
                    continue
                try:
                    if m.is_playing and m.stop_hotkey:
                        if keyboard.is_pressed(m.stop_hotkey):
                            self.root.after(0, m.stop)
                            self.ignore_until = now + 0.3
                            continue
                    
                    if m.hotkey:
                        is_pressed = keyboard.is_pressed(m.hotkey)
                        prev_state = key_states.get(m.name, False)
                        key_states[m.name] = is_pressed
                        
                        if m.toggle_action == 2:
                            if is_pressed and not prev_state:
                                m.set_callback(lambda msg: self.root.after(0, lambda: self._status(f"[{m.name}] {msg}")))
                                self.root.after(0, m.play)
                                self.ignore_until = now + 0.1
                            elif not is_pressed and prev_state:
                                self.root.after(0, m.stop)
                                self.ignore_until = now + 0.1
                        elif m.toggle_action == 1:
                            if is_pressed and not prev_state:
                                m.set_callback(lambda msg: self.root.after(0, lambda: self._status(f"[{m.name}] {msg}")))
                                self.root.after(0, m.play)
                                self.ignore_until = now + 0.3
                        else:
                            if is_pressed and not prev_state:
                                if not m.is_playing:
                                    m.set_callback(lambda msg: self.root.after(0, lambda: self._status(f"[{m.name}] {msg}")))
                                    self.root.after(0, m.play)
                                    self.ignore_until = now + 0.3
                except:
                    continue
                    
    def _load_profiles(self):
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
        path = os.path.join("profiles", "global_settings.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    s = json.load(f)
                    self.global_stop = s.get("global_stop_hotkey", "ctrl+shift+q")
                    self.global_var.set(self.global_stop)
                    self.mouse_capture_key = s.get("mouse_capture_hotkey", "f12")
            except:
                pass
        profiles = {}
        for f in os.listdir("profiles"):
            if f.endswith(".json") and f != "global_settings.json":
                name = f[:-5]
                try:
                    with open(os.path.join("profiles", f)) as file:
                        profiles[name] = json.load(file)
                except:
                    pass
        self.profiles = profiles
        self.profile_combo['values'] = list(profiles.keys())
        if "default" in profiles:
            self.current_profile = "default"
            self.profile_var.set("default")
            self._load_macros()
        elif profiles:
            self.current_profile = list(profiles.keys())[0]
            self.profile_var.set(self.current_profile)
            self._load_macros()
            
    def _save_profiles(self):
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
        s = {"global_stop_hotkey": self.global_stop, "mouse_capture_hotkey": self.mouse_capture_key}
        with open(os.path.join("profiles", "global_settings.json"), 'w') as f:
            json.dump(s, f, indent=2)
        for name, data in self.profiles.items():
            with open(os.path.join("profiles", f"{name}.json"), 'w') as f:
                json.dump(data, f, indent=2)
                
    def _load_macros(self):
        self.macros = []
        if self.current_profile in self.profiles:
            for data in self.profiles[self.current_profile]:
                m = Macro.from_dict(data)
                self.macros.append(m)
        self.selected_index = -1
        self._update_macro_list()
        self._update_properties()
        self._update_steps()
        
    def _save_current(self):
        self.profiles[self.current_profile] = [m.to_dict() for m in self.macros]
        self._save_profiles()
        
    def _on_profile_change(self, event):
        self._save_current()
        self.current_profile = self.profile_var.get()
        self._load_macros()
        
    def _new_profile(self):
        name = simpledialog.askstring("New Profile", "Enter profile name:")
        if name and name not in self.profiles:
            self.profiles[name] = []
            self.profile_combo['values'] = list(self.profiles.keys())
            self.profile_var.set(name)
            self.current_profile = name
            self.macros = []
            self._update_macro_list()
            self._update_properties()
            self._update_steps()
            self._save_profiles()
            self._status(f"Created profile: {name}")
            
    def _save_profile(self):
        self._save_current()
        self._status(f"Saved: {self.current_profile}")
        
    def _delete_profile(self):
        if self.current_profile and messagebox.askyesno("Delete", f"Delete '{self.current_profile}'?"):
            del self.profiles[self.current_profile]
            p = os.path.join("profiles", f"{self.current_profile}.json")
            if os.path.exists(p):
                os.remove(p)
            self.profile_combo['values'] = list(self.profiles.keys())
            if self.profiles:
                self.current_profile = list(self.profiles.keys())[0]
                self.profile_var.set(self.current_profile)
                self._load_macros()
            else:
                self.current_profile = ""
                self.profile_var.set("")
                self.macros = []
                self._update_macro_list()
                self._update_properties()
                self._update_steps()
            self._status("Profile deleted")

class KeyRecorder:
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        self.dialog = None
        
    def show(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Record Key")
        self.dialog.geometry("400x220")
        self.dialog.configure(bg=COLORS['bg'])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width()//2) - 200
        y = self.parent.winfo_y() + (self.parent.winfo_height()//2) - 110
        self.dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        ttk.Label(frame, text="Press any key to record...", font=("Segoe UI", 12), justify="center").pack(pady=15)
        ttk.Label(frame, text="ESC to cancel", font=("Segoe UI", 10), foreground='gray').pack()
        
        self.key_label = ttk.Label(frame, text="Waiting...", font=("Segoe UI", 14, "bold"), foreground=COLORS['accent'])
        self.key_label.pack(pady=20)
        
        ttk.Label(frame, text="Supported: Letters, Numbers, F1-F12, Numpad, Symbols", 
                 font=('Segoe UI', 8), foreground='gray', wraplength=350).pack()
        
        ttk.Button(frame, text="Cancel", command=self.cancel, width=15).pack(pady=15)
        
        self.dialog.bind('<KeyPress>', self.on_key)
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.focus_force()
        
    def normalize(self, key):
        k = key.lower()
        if k in KEY_MAPPINGS:
            return KEY_MAPPINGS[k]
        if k.startswith('f') and k[1:].isdigit():
            return k
        return k
        
    def on_key(self, event):
        key = self.normalize(event.keysym)
        if key in ['shift', 'ctrl', 'alt', 'win']:
            self.key_label.config(text="Press a key (not modifier)...")
            return
        self.key_label.config(text=f"✓ {key}")
        self.dialog.after(200, self.finish, key)
        
    def finish(self, key):
        self.dialog.destroy()
        self.callback(key)
        
    def cancel(self):
        self.dialog.destroy()
        self.callback(None)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernMacroApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app._save_current(), root.destroy()))
    root.mainloop()