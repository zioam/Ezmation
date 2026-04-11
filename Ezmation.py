#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ezmation
=================
Tired of those macros that don't have the functions you looking for? I was one of you, and that motivated me to create "Ezmation".
In this automation software you can set from a simple autoclicker to an hybrid macro system, and more.
I'll keep adding more features in the future so stay in touch for the upcoming updates.

"Automation refers to the broader process of using technology to perform tasks with minimal human intervention."

Author:    Maximilian <therealzioam@gmail.com>
GitHub:    https://github.com/zioam/macroZ
License: CC BY-NC 4.0 — Free to use, not for sale
Copyright (c) 2026 zioam
"""

"""
AutoClicker + Macro Tool  |  requires: pip install pynput
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import threading
import time
import json
import os
import sys

try:
    from pynput import keyboard as kb, mouse as ms
    from pynput.keyboard import Key, Controller as KbController
    from pynput.mouse import Button, Controller as MsController
except ImportError:
    print("Missing pynput. Installing...")
    os.system(f"{sys.executable} -m pip install pynput")
    from pynput import keyboard as kb, mouse as ms
    from pynput.keyboard import Key, Controller as KbController
    from pynput.mouse import Button, Controller as MsController

# ─────────────────────────────────────────────
#  CONFIG FILE
# ─────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".automator_config.json")

DEFAULT_CONFIG = {
    "shortcut_play": "F6",
    "shortcut_stop": "F7",
    "theme": "dark",
    "default_interval_ms": 100,
    "start_delay_ms": 0,
    "repeat_count": 0,          # 0 = infinite
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                c = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    c.setdefault(k, v)
                return c
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ─────────────────────────────────────────────
#  COLORS / THEME
# ─────────────────────────────────────────────
DARK = {
    "bg":        "#0d0d0f",
    "surface":   "#17171b",
    "surface2":  "#1e1e24",
    "border":    "#2a2a35",
    "accent":    "#6c63ff",
    "accent2":   "#ff6584",
    "text":      "#e8e8f0",
    "subtext":   "#7070a0",
    "green":     "#3ddc84",
    "red":       "#ff4757",
    "yellow":    "#ffd32a",
    "entry_bg":  "#12121a",
}

LIGHT = {
    "bg":        "#f0f0f5",
    "surface":   "#ffffff",
    "surface2":  "#e8e8f0",
    "border":    "#ccccdd",
    "accent":    "#5a52e0",
    "accent2":   "#e05270",
    "text":      "#1a1a2e",
    "subtext":   "#6060a0",
    "green":     "#1a9c50",
    "red":       "#e03040",
    "yellow":    "#c09000",
    "entry_bg":  "#f8f8ff",
}

# ─────────────────────────────────────────────
#  KEY HELPER
# ─────────────────────────────────────────────
def _safe_key(attr):
    try:
        return getattr(Key, attr)
    except AttributeError:
        return None

SPECIAL_KEYS = {
    "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
    "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
    "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    "enter": Key.enter, "space": Key.space, "tab": Key.tab,
    "backspace": Key.backspace, "delete": Key.delete, "escape": Key.esc,
    "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    "ctrl": Key.ctrl, "shift": Key.shift, "alt": Key.alt,
    "ctrl_l": Key.ctrl_l, "ctrl_r": Key.ctrl_r,
    "shift_l": Key.shift_l, "shift_r": Key.shift_r,
    "alt_l": Key.alt_l, "alt_r": Key.alt_r,
    "home": Key.home, "end": Key.end, "page_up": Key.page_up,
    "page_down": _safe_key("page_down"),
    "insert":    _safe_key("insert"),
    "caps_lock": Key.caps_lock,
    "num_lock":  _safe_key("num_lock"),
}

# filter non-supported ones in current OS
SPECIAL_KEYS = {k: v for k, v in SPECIAL_KEYS.items() if v is not None}

MOUSE_BUTTONS = {
    "left click":   Button.left,
    "right click":  Button.right,
    "middle click": Button.middle,
}

def parse_key(s):
    s = s.strip().lower()
    if s in SPECIAL_KEYS:
        return SPECIAL_KEYS[s]
    if len(s) == 1:
        return s
    return None

# ─────────────────────────────────────────────
#  ACTION MODEL
# ─────────────────────────────────────────────
class Action:
    """Represents one step in a macro sequence."""
    def __init__(self, action_type="key", value="", interval_ms=100, looped=False, repeat=1, parallel=False):
        self.action_type = action_type   # "key" | "mouse" | "hybrid"
        self.value       = value         # key string or mouse button string or "key+mouse"
        self.interval_ms = interval_ms
        self.looped      = looped
        self.repeat      = repeat        # times to fire (if not looped)
        self.parallel    = parallel      # True = fires in own thread, independent of sequence

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        a = cls()
        a.__dict__.update(d)
        return a


# ─────────────────────────────────────────────
#  EXECUTOR
# ─────────────────────────────────────────────
class Executor:
    def __init__(self, on_status):
        self._kb  = KbController()
        self._ms  = MsController()
        self._stop_event = threading.Event()
        self._thread = None
        self.on_status = on_status

    def _press_action(self, action: Action):
        atype = action.action_type
        val   = action.value

        if atype == "key":
            k = parse_key(val)
            if k:
                self._kb.press(k)
                self._kb.release(k)

        elif atype == "mouse":
            btn = MOUSE_BUTTONS.get(val.lower(), Button.left)
            self._ms.click(btn)

        elif atype == "hybrid":
            # val = "key|mouse_btn"
            parts = val.split("|")
            k_str = parts[0] if len(parts) > 0 else ""
            m_str = parts[1] if len(parts) > 1 else "left click"
            k = parse_key(k_str)
            btn = MOUSE_BUTTONS.get(m_str.lower(), Button.left)
            if k:
                self._kb.press(k)
            self._ms.click(btn)
            if k:
                self._kb.release(k)

    def run_autoclicker(self, button_str, interval_ms, looped, repeat_count, start_delay_ms=0):
        self._stop_event.clear()
        def _task():
            if start_delay_ms > 0:
                time.sleep(start_delay_ms / 1000)
            btn = MOUSE_BUTTONS.get(button_str.lower(), Button.left)
            count = 0
            while not self._stop_event.is_set():
                self._ms.click(btn)
                count += 1
                self.on_status(f"Clicks: {count}")
                time.sleep(interval_ms / 1000)
                if not looped and count >= repeat_count:
                    break
            self.on_status("Stopped")
        self._thread = threading.Thread(target=_task, daemon=True)
        self._thread.start()

    def run_macro(self, actions: list, looped: bool, global_repeat: int, start_delay_ms=0):
        """Mixed mode: parallel actions fire in their own threads; sequential ones run in order."""
        self._stop_event.clear()

        def _parallel_worker(action: Action):
            """Runs a single parallel action independently forever (or until stop/repeat)."""
            count = 0
            effective_inf = looped or action.looped
            reps = action.repeat if not action.looped else float('inf')
            while not self._stop_event.is_set():
                self._press_action(action)
                count += 1
                time.sleep(action.interval_ms / 1000)
                if not effective_inf and count >= reps:
                    break

        def _task():
            if start_delay_ms > 0:
                time.sleep(start_delay_ms / 1000)

            # Separate actions into parallel and sequential groups
            parallel_actions  = [a for a in actions if a.parallel]
            seq_actions       = [a for a in actions if not a.parallel]

            # Launch all parallel workers immediately — they run independently
            par_threads = []
            for action in parallel_actions:
                t = threading.Thread(target=_parallel_worker, args=(action,), daemon=True)
                t.start()
                par_threads.append(t)

            # Run sequential actions in order, looping if needed
            loop_count = 0
            while not self._stop_event.is_set():
                loop_count += 1
                self.on_status(f"Loop #{loop_count}")
                for action in seq_actions:
                    if self._stop_event.is_set():
                        break
                    reps = action.repeat if not action.looped else float('inf')
                    rep_count = 0
                    while not self._stop_event.is_set():
                        self._press_action(action)
                        rep_count += 1
                        time.sleep(action.interval_ms / 1000)
                        if not action.looped and rep_count >= reps:
                            break
                # If no sequential actions, just hold until stop (parallel-only macro)
                if not seq_actions:
                    if not looped:
                        # Wait for all parallel threads to finish
                        for t in par_threads:
                            while t.is_alive() and not self._stop_event.is_set():
                                time.sleep(0.05)
                        break
                    else:
                        while not self._stop_event.is_set():
                            time.sleep(0.1)
                        break
                if not looped and loop_count >= global_repeat:
                    break
                if not looped:
                    break

            self._stop_event.set()  # stop all parallel workers too
            self.on_status("Stopped")

        self._thread = threading.Thread(target=_task, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()


# ─────────────────────────────────────────────
#  GLOBAL HOTKEY LISTENER
# ─────────────────────────────────────────────
class HotkeyListener:
    def __init__(self, play_cb, stop_cb, get_keys):
        self.play_cb  = play_cb
        self.stop_cb  = stop_cb
        self.get_keys = get_keys   # callable -> (play_key_str, stop_key_str)
        self._listener = None
        self._pressed  = set()

    def _normalize(self, key):
        try:
            return key.char.lower() if hasattr(key, 'char') and key.char else str(key).replace("Key.", "").lower()
        except:
            return str(key).replace("Key.", "").lower()

    def _on_press(self, key):
        n = self._normalize(key)
        self._pressed.add(n)
        play_k, stop_k = self.get_keys()
        if n == play_k.lower():
            self.play_cb()
        elif n == stop_k.lower():
            self.stop_cb()

    def _on_release(self, key):
        n = self._normalize(key)
        self._pressed.discard(n)

    def start(self):
        self._listener = kb.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class AutomatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.C = DARK if self.config_data.get("theme", "dark") == "dark" else LIGHT
        self.running = False
        self.executor = Executor(self._on_status_update)
        self.macro_actions: list[Action] = []
        self._capture_target = None   # for keybind capture
        self._capture_var    = None

        self.title("AUTOMATOR")
        self.geometry("860x620")
        self.minsize(780, 560)
        self.configure(bg=self.C["bg"])
        self.resizable(True, True)

        self._setup_styles()
        self._build_ui()
        self._setup_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ──────── STYLES ────────
    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        C = self.C
        self.style.configure("TNotebook",
            background=C["bg"], borderwidth=0, tabmargins=[0,0,0,0])
        self.style.configure("TNotebook.Tab",
            background=C["surface2"], foreground=C["subtext"],
            padding=[18, 8], font=("Courier New", 9, "bold"),
            borderwidth=0)
        self.style.map("TNotebook.Tab",
            background=[("selected", C["surface"]), ("active", C["surface"])],
            foreground=[("selected", C["accent"]), ("active", C["text"])])
        self.style.configure("TFrame", background=C["bg"])
        self.style.configure("Surface.TFrame", background=C["surface"])
        self.style.configure("Surface2.TFrame", background=C["surface2"])
        self.style.configure("TLabel",
            background=C["bg"], foreground=C["text"],
            font=("Courier New", 9))
        self.style.configure("Sub.TLabel",
            background=C["surface"], foreground=C["subtext"],
            font=("Courier New", 8))
        self.style.configure("Title.TLabel",
            background=C["bg"], foreground=C["accent"],
            font=("Courier New", 13, "bold"))
        self.style.configure("Status.TLabel",
            background=C["surface2"], foreground=C["green"],
            font=("Courier New", 9))
        self.style.configure("TCombobox",
            fieldbackground=C["entry_bg"], background=C["surface"],
            foreground=C["text"], selectbackground=C["accent"],
            borderwidth=1, relief="flat")
        self.style.configure("TCheckbutton",
            background=C["surface"], foreground=C["text"],
            font=("Courier New", 9))
        self.style.map("TCheckbutton",
            background=[("active", C["surface"])])
        self.style.configure("TSpinbox",
            fieldbackground=C["entry_bg"], background=C["surface"],
            foreground=C["text"], borderwidth=1)

    # ──────── TOP BAR ────────
    def _build_ui(self):
        C = self.C

        # Top bar
        topbar = tk.Frame(self, bg=C["surface2"], height=48)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="⚡ AUTOMATOR", bg=C["surface2"],
                 fg=C["accent"], font=("Courier New", 14, "bold")).pack(side="left", padx=16, pady=10)

        # Status pill
        self.status_var = tk.StringVar(value="● IDLE")
        self.status_lbl = tk.Label(topbar, textvariable=self.status_var,
            bg=C["surface2"], fg=C["subtext"], font=("Courier New", 9))
        self.status_lbl.pack(side="left", padx=8)

        # Play / Stop buttons top right
        btn_frame = tk.Frame(topbar, bg=C["surface2"])
        btn_frame.pack(side="right", padx=12, pady=6)

        self.play_btn = tk.Button(btn_frame, text="▶  PLAY",
            bg=C["green"], fg=C["bg"], font=("Courier New", 9, "bold"),
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self._play)
        self.play_btn.pack(side="left", padx=4)

        self.stop_btn = tk.Button(btn_frame, text="■  STOP",
            bg=C["red"], fg="#fff", font=("Courier New", 9, "bold"),
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        shortcut_info = tk.Label(topbar,
            text=f"[{self.config_data['shortcut_play']}] play  [{self.config_data['shortcut_stop']}] stop",
            bg=C["surface2"], fg=C["subtext"], font=("Courier New", 8))
        shortcut_info.pack(side="right", padx=8)
        self._shortcut_info_lbl = shortcut_info

        # Notebook
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=0, pady=0)

        self._tab_autoclicker = ttk.Frame(self.nb, style="TFrame")
        self._tab_macro       = ttk.Frame(self.nb, style="TFrame")
        self._tab_settings    = ttk.Frame(self.nb, style="TFrame")

        self.nb.add(self._tab_autoclicker, text=" 🖱  AUTO CLICKER ")
        self.nb.add(self._tab_macro,       text=" ⌨  MACRO ")
        self.nb.add(self._tab_settings,    text=" ⚙  SETTINGS ")

        self._build_autoclicker_tab()
        self._build_macro_tab()
        self._build_settings_tab()

        # Bottom status bar
        statusbar = tk.Frame(self, bg=C["surface2"], height=24)
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)
        self._detail_var = tk.StringVar(value="Ready")
        tk.Label(statusbar, textvariable=self._detail_var,
                 bg=C["surface2"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=10, pady=3)

    # ──────── AUTOCLICKER TAB ────────
    def _build_autoclicker_tab(self):
        C = self.C
        tab = self._tab_autoclicker
        tab.configure(style="TFrame")

        outer = tk.Frame(tab, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        # Title
        tk.Label(outer, text="AUTO CLICKER", bg=C["bg"], fg=C["accent"],
                 font=("Courier New", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,12))

        card = tk.Frame(outer, bg=C["surface"], bd=0, relief="flat",
                        highlightbackground=C["border"], highlightthickness=1)
        card.grid(row=1, column=0, columnspan=4, sticky="ew", padx=0, pady=4)
        outer.columnconfigure(0, weight=1)

        # ── Mouse button
        row = 0
        tk.Label(card, text="Mouse Button", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=0, sticky="w", padx=16, pady=(14,2))
        self.ac_button_var = tk.StringVar(value="Left Click")
        btn_combo = ttk.Combobox(card, textvariable=self.ac_button_var,
                                  values=["Left Click", "Right Click", "Middle Click"],
                                  state="readonly", width=18)
        btn_combo.grid(row=row+1, column=0, sticky="w", padx=16, pady=(0,10))

        # ── Interval
        tk.Label(card, text="Interval (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=1, sticky="w", padx=16, pady=(14,2))
        self.ac_interval_var = tk.IntVar(value=self.config_data["default_interval_ms"])
        ac_spin = tk.Spinbox(card, from_=1, to=999999, textvariable=self.ac_interval_var,
                              width=10, bg=C["entry_bg"], fg=C["text"],
                              buttonbackground=C["surface2"],
                              relief="flat", font=("Courier New", 10))
        ac_spin.grid(row=row+1, column=1, sticky="w", padx=16)

        # ── Start delay
        tk.Label(card, text="Start Delay (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=2, sticky="w", padx=16, pady=(14,2))
        self.ac_delay_var = tk.IntVar(value=self.config_data["start_delay_ms"])
        ac_delay = tk.Spinbox(card, from_=0, to=999999, textvariable=self.ac_delay_var,
                               width=10, bg=C["entry_bg"], fg=C["text"],
                               buttonbackground=C["surface2"],
                               relief="flat", font=("Courier New", 10))
        ac_delay.grid(row=row+1, column=2, sticky="w", padx=16)

        # ── Loop / Repeat
        row = 2
        self.ac_loop_var = tk.BooleanVar(value=True)
        loop_chk = tk.Checkbutton(card, text="Loop (infinite)", variable=self.ac_loop_var,
                                   bg=C["surface"], fg=C["text"], selectcolor=C["entry_bg"],
                                   activebackground=C["surface"], activeforeground=C["accent"],
                                   font=("Courier New", 9), command=self._ac_loop_toggle)
        loop_chk.grid(row=row, column=0, sticky="w", padx=16, pady=(8,4))

        tk.Label(card, text="Repeat Count (if not looped)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=1, sticky="w", padx=16)
        self.ac_repeat_var = tk.IntVar(value=10)
        self.ac_repeat_spin = tk.Spinbox(card, from_=1, to=999999, textvariable=self.ac_repeat_var,
                                          width=10, bg=C["entry_bg"], fg=C["text"],
                                          buttonbackground=C["surface2"],
                                          relief="flat", font=("Courier New", 10),
                                          state="disabled")
        self.ac_repeat_spin.grid(row=row, column=2, sticky="w", padx=16, pady=(8,4))

        # padding bottom
        tk.Label(card, text="", bg=C["surface"]).grid(row=row+1, column=0, pady=8)

    def _ac_loop_toggle(self):
        if self.ac_loop_var.get():
            self.ac_repeat_spin.config(state="disabled")
        else:
            self.ac_repeat_spin.config(state="normal")

    # ──────── MACRO TAB ────────
    def _build_macro_tab(self):
        C = self.C
        tab = self._tab_macro

        outer = tk.Frame(tab, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        # Title row
        title_row = tk.Frame(outer, bg=C["bg"])
        title_row.pack(fill="x")
        tk.Label(title_row, text="MACRO SEQUENCE", bg=C["bg"], fg=C["accent"],
                 font=("Courier New", 12, "bold")).pack(side="left")

        # Global loop options
        gopt = tk.Frame(outer, bg=C["surface"], highlightbackground=C["border"], highlightthickness=1)
        gopt.pack(fill="x", pady=(8,0))

        tk.Label(gopt, text="Global:", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=10, pady=6)
        self.macro_loop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(gopt, text="Loop Macro", variable=self.macro_loop_var,
                       bg=C["surface"], fg=C["text"], selectcolor=C["entry_bg"],
                       activebackground=C["surface"],
                       font=("Courier New", 9), command=self._macro_loop_toggle).pack(side="left", padx=6)

        tk.Label(gopt, text="Repeat:", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=(16,4))
        self.macro_repeat_var = tk.IntVar(value=1)
        self.macro_repeat_spin = tk.Spinbox(gopt, from_=1, to=9999,
                                             textvariable=self.macro_repeat_var,
                                             width=6, bg=C["entry_bg"], fg=C["text"],
                                             buttonbackground=C["surface2"],
                                             relief="flat", font=("Courier New", 9),
                                             state="disabled")
        self.macro_repeat_spin.pack(side="left")

        tk.Label(gopt, text="Start Delay (ms):", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=(16,4))
        self.macro_delay_var = tk.IntVar(value=0)
        tk.Spinbox(gopt, from_=0, to=999999, textvariable=self.macro_delay_var,
                   width=7, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"],
                   relief="flat", font=("Courier New", 9)).pack(side="left")

        # Action list
        list_frame = tk.Frame(outer, bg=C["surface"], highlightbackground=C["border"], highlightthickness=1)
        list_frame.pack(fill="both", expand=True, pady=(6,0))

        # Header
        hdr = tk.Frame(list_frame, bg=C["surface2"])
        hdr.pack(fill="x")
        for txt, w in [("#", 3), ("TYPE", 8), ("VALUE", 18), ("INTERVAL ms", 11), ("LOOP", 5), ("REPEAT", 7), ("PARALLEL", 8)]:
            tk.Label(hdr, text=txt, bg=C["surface2"], fg=C["subtext"],
                     font=("Courier New", 8, "bold"), width=w, anchor="w").pack(side="left", padx=4, pady=4)

        # Scrollable list
        canvas = tk.Canvas(list_frame, bg=C["surface"], highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.macro_list_inner = tk.Frame(canvas, bg=C["surface"])

        self.macro_list_inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.macro_list_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._macro_canvas = canvas

        # Add action area
        add_frame = tk.Frame(outer, bg=C["surface2"], highlightbackground=C["border"], highlightthickness=1)
        add_frame.pack(fill="x", pady=(4,0))

        tk.Label(add_frame, text="+ ADD ACTION", bg=C["surface2"], fg=C["accent"],
                 font=("Courier New", 9, "bold")).grid(row=0, column=0, padx=10, pady=(8,2), sticky="w", columnspan=6)

        # Type
        tk.Label(add_frame, text="Type", bg=C["surface2"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=1, column=0, padx=8, pady=2, sticky="w")
        self.add_type_var = tk.StringVar(value="key")
        type_combo = ttk.Combobox(add_frame, textvariable=self.add_type_var,
                                   values=["key", "mouse", "hybrid"],
                                   state="readonly", width=10)
        type_combo.grid(row=2, column=0, padx=8, pady=(0,8), sticky="w")
        type_combo.bind("<<ComboboxSelected>>", self._add_type_changed)

        # Value
        tk.Label(add_frame, text="Key / Button", bg=C["surface2"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=1, column=1, padx=8, pady=2, sticky="w")
        self.add_value_frame = tk.Frame(add_frame, bg=C["surface2"])
        self.add_value_frame.grid(row=2, column=1, padx=8, pady=(0,8), sticky="w")
        self._build_value_input()

        # Interval
        tk.Label(add_frame, text="Interval (ms)", bg=C["surface2"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=1, column=2, padx=8, sticky="w")
        self.add_interval_var = tk.IntVar(value=100)
        tk.Spinbox(add_frame, from_=1, to=999999, textvariable=self.add_interval_var,
                   width=9, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface"], relief="flat",
                   font=("Courier New", 9)).grid(row=2, column=2, padx=8, pady=(0,8), sticky="w")

        # Loop
        tk.Label(add_frame, text="Loop", bg=C["surface2"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=1, column=3, padx=8, sticky="w")
        self.add_loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(add_frame, variable=self.add_loop_var,
                       bg=C["surface2"], selectcolor=C["entry_bg"],
                       activebackground=C["surface2"]).grid(row=2, column=3, padx=8, pady=(0,8))

        # Repeat
        tk.Label(add_frame, text="Repeat", bg=C["surface2"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=1, column=4, padx=8, sticky="w")
        self.add_repeat_var = tk.IntVar(value=1)
        tk.Spinbox(add_frame, from_=1, to=9999, textvariable=self.add_repeat_var,
                   width=7, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface"], relief="flat",
                   font=("Courier New", 9)).grid(row=2, column=4, padx=8, pady=(0,8), sticky="w")

        # Parallel
        tk.Label(add_frame, text="Parallel", bg=C["surface2"], fg=C["yellow"],
                 font=("Courier New", 8, "bold")).grid(row=1, column=5, padx=8, sticky="w")
        self.add_parallel_var = tk.BooleanVar(value=False)
        tk.Checkbutton(add_frame, variable=self.add_parallel_var,
                       bg=C["surface2"], selectcolor=C["entry_bg"],
                       activebackground=C["surface2"],
                       fg=C["yellow"]).grid(row=2, column=5, padx=8, pady=(0,8))

        # Add btn
        tk.Button(add_frame, text="ADD ➕", bg=C["accent"], fg="#fff",
                  font=("Courier New", 9, "bold"), relief="flat",
                  padx=12, pady=4, cursor="hand2",
                  command=self._add_action).grid(row=2, column=6, padx=12, pady=(0,8))

    def _build_value_input(self):
        C = self.C
        for w in self.add_value_frame.winfo_children():
            w.destroy()
        atype = self.add_type_var.get()
        if atype == "key":
            self.add_key_var = tk.StringVar(value="space")
            e = tk.Entry(self.add_value_frame, textvariable=self.add_key_var,
                         bg=C["entry_bg"], fg=C["text"], insertbackground=C["text"],
                         relief="flat", font=("Courier New", 10), width=14)
            e.pack(side="left")
            tk.Label(self.add_value_frame, text="(e.g. space, f5, a)",
                     bg=C["surface2"], fg=C["subtext"], font=("Courier New", 7)).pack(side="left", padx=4)
        elif atype == "mouse":
            self.add_mouse_var = tk.StringVar(value="left click")
            ttk.Combobox(self.add_value_frame, textvariable=self.add_mouse_var,
                         values=list(MOUSE_BUTTONS.keys()),
                         state="readonly", width=14).pack(side="left")
        elif atype == "hybrid":
            self.add_key_var   = tk.StringVar(value="ctrl")
            self.add_mouse_var = tk.StringVar(value="left click")
            tk.Label(self.add_value_frame, text="Key:", bg=C["surface2"],
                     fg=C["subtext"], font=("Courier New", 8)).pack(side="left")
            tk.Entry(self.add_value_frame, textvariable=self.add_key_var,
                     bg=C["entry_bg"], fg=C["text"], insertbackground=C["text"],
                     relief="flat", font=("Courier New", 9), width=8).pack(side="left", padx=2)
            tk.Label(self.add_value_frame, text="+", bg=C["surface2"],
                     fg=C["accent"], font=("Courier New", 10, "bold")).pack(side="left", padx=2)
            ttk.Combobox(self.add_value_frame, textvariable=self.add_mouse_var,
                         values=list(MOUSE_BUTTONS.keys()),
                         state="readonly", width=12).pack(side="left")

    def _add_type_changed(self, event=None):
        self._build_value_input()

    def _add_action(self):
        atype = self.add_type_var.get()
        if atype == "key":
            val = self.add_key_var.get().strip()
        elif atype == "mouse":
            val = self.add_mouse_var.get().strip()
        else:
            val = f"{self.add_key_var.get().strip()}|{self.add_mouse_var.get().strip()}"

        if not val:
            messagebox.showwarning("Invalid", "Please specify a value.")
            return

        action = Action(
            action_type=atype,
            value=val,
            interval_ms=self.add_interval_var.get(),
            looped=self.add_loop_var.get(),
            repeat=self.add_repeat_var.get(),
            parallel=self.add_parallel_var.get()
        )
        self.macro_actions.append(action)
        self._refresh_macro_list()

    def _refresh_macro_list(self):
        C = self.C
        for w in self.macro_list_inner.winfo_children():
            w.destroy()
        for i, action in enumerate(self.macro_actions):
            row_bg = C["surface"] if i % 2 == 0 else C["surface2"]
            row = tk.Frame(self.macro_list_inner, bg=row_bg)
            row.pack(fill="x")

            def mk_lbl(text, w=12, fg=None):
                return tk.Label(row, text=str(text), bg=row_bg,
                                fg=fg or C["text"], font=("Courier New", 9),
                                width=w, anchor="w")

            # Highlight row if parallel
            if getattr(action, "parallel", False):
                row_bg = C["entry_bg"] if i % 2 == 0 else "#0f0f1a"
                row.configure(bg=row_bg)

            mk_lbl(i+1, 3).pack(side="left", padx=4, pady=3)
            color = {"key": C["accent"], "mouse": C["accent2"], "hybrid": C["yellow"]}.get(action.action_type, C["text"])
            mk_lbl(action.action_type.upper(), 8, color).pack(side="left", padx=4)
            mk_lbl(action.value, 18).pack(side="left", padx=4)
            mk_lbl(action.interval_ms, 11).pack(side="left", padx=4)
            mk_lbl("✓" if action.looped else "—", 5, C["green"] if action.looped else C["subtext"]).pack(side="left", padx=4)
            mk_lbl(action.repeat if not action.looped else "∞", 7).pack(side="left", padx=4)
            is_par = getattr(action, "parallel", False)
            mk_lbl("⚡ PAR" if is_par else "— SEQ", 8, C["yellow"] if is_par else C["subtext"]).pack(side="left", padx=4)

            # Delete btn
            idx = i
            tk.Button(row, text="✕", bg=row_bg, fg=C["red"],
                      font=("Courier New", 9, "bold"), relief="flat",
                      cursor="hand2",
                      command=lambda x=idx: self._delete_action(x)).pack(side="right", padx=8)

            # Move up/down
            tk.Button(row, text="↓", bg=row_bg, fg=C["subtext"],
                      font=("Courier New", 9), relief="flat", cursor="hand2",
                      command=lambda x=idx: self._move_action(x, 1)).pack(side="right", padx=2)
            tk.Button(row, text="↑", bg=row_bg, fg=C["subtext"],
                      font=("Courier New", 9), relief="flat", cursor="hand2",
                      command=lambda x=idx: self._move_action(x, -1)).pack(side="right", padx=2)

    def _delete_action(self, idx):
        if 0 <= idx < len(self.macro_actions):
            self.macro_actions.pop(idx)
            self._refresh_macro_list()

    def _move_action(self, idx, direction):
        new = idx + direction
        if 0 <= new < len(self.macro_actions):
            self.macro_actions[idx], self.macro_actions[new] = \
                self.macro_actions[new], self.macro_actions[idx]
            self._refresh_macro_list()

    def _macro_loop_toggle(self):
        if self.macro_loop_var.get():
            self.macro_repeat_spin.config(state="disabled")
        else:
            self.macro_repeat_spin.config(state="normal")

    # ──────── SETTINGS TAB ────────
    def _build_settings_tab(self):
        C = self.C
        tab = self._tab_settings

        outer = tk.Frame(tab, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(outer, text="SETTINGS", bg=C["bg"], fg=C["accent"],
                 font=("Courier New", 12, "bold")).pack(anchor="w", pady=(0,12))

        # Keybinds section
        kb_card = tk.LabelFrame(outer, text="  KEYBINDS  ", bg=C["surface"],
                                 fg=C["accent"], font=("Courier New", 9, "bold"),
                                 labelanchor="nw",
                                 highlightbackground=C["border"], highlightthickness=1,
                                 bd=0, relief="flat", padx=14, pady=10)
        kb_card.pack(fill="x", pady=(0,10))

        # Play
        self._build_keybind_row(kb_card, "Play Shortcut", "shortcut_play", row=0)
        # Stop
        self._build_keybind_row(kb_card, "Stop Shortcut", "shortcut_stop", row=1)

        # General section
        gen_card = tk.LabelFrame(outer, text="  GENERAL  ", bg=C["surface"],
                                  fg=C["accent"], font=("Courier New", 9, "bold"),
                                  labelanchor="nw",
                                  highlightbackground=C["border"], highlightthickness=1,
                                  bd=0, relief="flat", padx=14, pady=10)
        gen_card.pack(fill="x", pady=(0,10))

        # Theme
        tk.Label(gen_card, text="Theme", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=0, column=0, sticky="w", pady=4)
        self.theme_var = tk.StringVar(value=self.config_data.get("theme", "dark"))
        ttk.Combobox(gen_card, textvariable=self.theme_var,
                     values=["dark", "light"], state="readonly", width=12).grid(row=0, column=1, padx=12, sticky="w")

        # Default interval
        tk.Label(gen_card, text="Default Interval (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=1, column=0, sticky="w", pady=4)
        self.def_interval_var = tk.IntVar(value=self.config_data["default_interval_ms"])
        tk.Spinbox(gen_card, from_=1, to=9999, textvariable=self.def_interval_var,
                   width=8, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9)).grid(row=1, column=1, padx=12, sticky="w")

        # Default start delay
        tk.Label(gen_card, text="Default Start Delay (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=2, column=0, sticky="w", pady=4)
        self.def_delay_var = tk.IntVar(value=self.config_data["start_delay_ms"])
        tk.Spinbox(gen_card, from_=0, to=99999, textvariable=self.def_delay_var,
                   width=8, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9)).grid(row=2, column=1, padx=12, sticky="w")

        # Save btn
        tk.Button(outer, text="💾  SAVE SETTINGS", bg=C["accent"], fg="#fff",
                  font=("Courier New", 10, "bold"), relief="flat",
                  padx=16, pady=6, cursor="hand2",
                  command=self._save_settings).pack(anchor="w", pady=8)

        tk.Label(outer, text="Note: Theme changes require restart",
                 bg=C["bg"], fg=C["subtext"], font=("Courier New", 8)).pack(anchor="w")

    def _build_keybind_row(self, parent, label, cfg_key, row):
        C = self.C
        tk.Label(parent, text=label, bg=C["surface"], fg=C["text"],
                 font=("Courier New", 9), width=22, anchor="w").grid(
                     row=row, column=0, padx=4, pady=6, sticky="w")

        var = tk.StringVar(value=self.config_data[cfg_key])
        entry = tk.Entry(parent, textvariable=var, bg=C["entry_bg"], fg=C["accent"],
                         insertbackground=C["accent"], relief="flat",
                         font=("Courier New", 10, "bold"), width=12,
                         readonlybackground=C["entry_bg"])
        entry.grid(row=row, column=1, padx=8, pady=6, sticky="w")

        capture_btn = tk.Button(parent, text="CAPTURE", bg=C["surface2"], fg=C["text"],
                                 font=("Courier New", 8), relief="flat", padx=8,
                                 cursor="hand2")
        capture_btn.grid(row=row, column=2, padx=4)
        capture_btn.configure(command=lambda e=entry, v=var, b=capture_btn, k=cfg_key:
                               self._start_capture(e, v, b, k))

        # Store var reference
        setattr(self, f"_kbvar_{cfg_key}", var)

    def _start_capture(self, entry, var, btn, cfg_key):
        C = self.C
        btn.config(text="Press any key...", bg=C["yellow"], fg=C["bg"])
        self._capture_target = cfg_key
        self._capture_var    = var
        self._capture_btn    = btn

        def on_key(key):
            name = str(key).replace("Key.", "").replace("'", "").strip()
            var.set(name.upper())
            self.config_data[cfg_key] = name.upper()
            btn.config(text="CAPTURE", bg=C["surface2"], fg=C["text"])
            self._capture_target = None
            return False  # stop listener

        listener = kb.Listener(on_press=on_key)
        listener.daemon = True
        listener.start()

    def _save_settings(self):
        C = self.C
        for k in ["shortcut_play", "shortcut_stop"]:
            var = getattr(self, f"_kbvar_{k}", None)
            if var:
                self.config_data[k] = var.get()
        self.config_data["theme"]                = self.theme_var.get()
        self.config_data["default_interval_ms"]  = self.def_interval_var.get()
        self.config_data["start_delay_ms"]        = self.def_delay_var.get()
        save_config(self.config_data)
        self._update_shortcut_label()
        self._setup_hotkeys()
        messagebox.showinfo("Saved", "Settings saved successfully!")

    def _update_shortcut_label(self):
        self._shortcut_info_lbl.config(
            text=f"[{self.config_data['shortcut_play']}] play  [{self.config_data['shortcut_stop']}] stop")

    # ──────── HOTKEYS ────────
    def _setup_hotkeys(self):
        if hasattr(self, '_hotkey_listener') and self._hotkey_listener:
            self._hotkey_listener.stop()
        def get_keys():
            return (self.config_data["shortcut_play"], self.config_data["shortcut_stop"])
        self._hotkey_listener = HotkeyListener(
            play_cb=self._play,
            stop_cb=self._stop,
            get_keys=get_keys
        )
        self._hotkey_listener.start()

    # ──────── PLAY / STOP ────────
    def _play(self):
        if self.running:
            return
        tab = self.nb.index(self.nb.select())
        self.running = True
        self._set_ui_running(True)

        if tab == 0:  # autoclicker
            btn_str = self.ac_button_var.get().lower()
            interval = max(1, self.ac_interval_var.get())
            looped   = self.ac_loop_var.get()
            repeat   = self.ac_repeat_var.get()
            delay    = self.ac_delay_var.get()
            self.executor.run_autoclicker(btn_str, interval, looped, repeat, delay)

        elif tab == 1:  # macro
            if not self.macro_actions:
                messagebox.showwarning("Empty Macro", "Add at least one action to the macro.")
                self.running = False
                self._set_ui_running(False)
                return
            looped  = self.macro_loop_var.get()
            repeat  = self.macro_repeat_var.get()
            delay   = self.macro_delay_var.get()
            self.executor.run_macro(self.macro_actions, looped, repeat, delay)

        # Poll for completion
        self._poll_running()

    def _poll_running(self):
        if self.running and self.executor._thread and not self.executor._thread.is_alive():
            self.running = False
            self._set_ui_running(False)
        elif self.running:
            self.after(200, self._poll_running)

    def _stop(self):
        self.executor.stop()
        self.running = False
        self._set_ui_running(False)

    def _set_ui_running(self, running):
        C = self.C
        if running:
            self.play_btn.config(state="disabled", bg=C["subtext"])
            self.stop_btn.config(state="normal", bg=C["red"])
            self.status_var.set("● RUNNING")
            self.status_lbl.config(fg=C["green"])
        else:
            self.play_btn.config(state="normal", bg=C["green"])
            self.stop_btn.config(state="disabled", bg=C["subtext"])
            self.status_var.set("● IDLE")
            self.status_lbl.config(fg=C["subtext"])

    def _on_status_update(self, msg):
        self.after(0, lambda: self._detail_var.set(msg))

    def _on_close(self):
        self.executor.stop()
        if hasattr(self, '_hotkey_listener'):
            self._hotkey_listener.stop()
        self.destroy()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = AutomatorApp()
    app.mainloop()
