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
License:   CC BY-NC 4.0 — Free to use, not for sale
Copyright (c) 2026 zioam
"""

"""
AutoClicker + Macro Tool  |  requires: pip install pynput
"""

import tkinter as tk
from tkinter import ttk, messagebox
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

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".automator_config.json")

DEFAULT_CONFIG = {
    "shortcut_play": "F6",
    "shortcut_stop": "F7",
    "theme": "dark",
    "default_interval_ms": 100,
    "start_delay_ms": 0,
    "repeat_count": 0,
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


class Action:
    def __init__(self, action_type="key", value="", interval_ms=100,
                 looped=False, repeat=1, parallel=False,
                 true_seq=False, spam_count=1, spam_delay=0):
        self.action_type = action_type
        self.value       = value
        self.interval_ms = interval_ms
        self.looped      = looped
        self.repeat      = repeat
        self.parallel    = parallel
        self.true_seq    = true_seq
        self.spam_count  = spam_count
        self.spam_delay  = spam_delay

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        a = cls()
        a.__dict__.update(d)
        return a


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
        self._stop_event.clear()

        def _parallel_worker(action: Action):
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

            parallel_actions = [a for a in actions if a.parallel]
            seq_actions      = [a for a in actions if not a.parallel]

            par_threads = []
            for action in parallel_actions:
                t = threading.Thread(target=_parallel_worker, args=(action,), daemon=True)
                t.start()
                par_threads.append(t)

            loop_count = 0
            while not self._stop_event.is_set():
                loop_count += 1
                self.on_status(f"Loop #{loop_count}")
                for action in seq_actions:
                    if self._stop_event.is_set():
                        break
                    if getattr(action, "true_seq", False):
                        for _ in range(action.spam_count):
                            if self._stop_event.is_set():
                                break
                            self._press_action(action)
                            if action.spam_delay > 0:
                                time.sleep(action.spam_delay / 1000)
                        time.sleep(action.interval_ms / 1000)
                    else:
                        reps = action.repeat if not action.looped else float('inf')
                        rep_count = 0
                        while not self._stop_event.is_set():
                            self._press_action(action)
                            rep_count += 1
                            time.sleep(action.interval_ms / 1000)
                            if not action.looped and rep_count >= reps:
                                break

                if not seq_actions:
                    if not looped:
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

            self._stop_event.set()
            self.on_status("Stopped")

        self._thread = threading.Thread(target=_task, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()


class HotkeyListener:
    def __init__(self, play_cb, stop_cb, get_keys):
        self.play_cb  = play_cb
        self.stop_cb  = stop_cb
        self.get_keys = get_keys
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


class AutomatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.C = DARK if self.config_data.get("theme", "dark") == "dark" else LIGHT
        self.running = False
        self.executor = Executor(self._on_status_update)
        self.macro_actions: list[Action] = []
        self._capture_target = None
        self._capture_var    = None

        self.title("Ezmation")
        self.geometry("860x620")
        self.minsize(780, 560)
        self.configure(bg=self.C["bg"])
        self.resizable(True, True)

        self._setup_styles()
        self._build_ui()
        self._setup_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        self.style.configure("Surface2.TFrame",
            background=C["surface2"], bordercolor=C["border"],
            lightcolor=C["surface2"], darkcolor=C["surface2"])
        self.style.map("Surface2.TFrame",
            bordercolor=[("focus", C["border"]), ("active", C["border"])])

        self.style.configure("TLabel",
            background=C["bg"], foreground=C["text"], font=("Courier New", 9))
        self.style.configure("Sub.TLabel",
            background=C["surface"], foreground=C["subtext"], font=("Courier New", 8))
        self.style.configure("Title.TLabel",
            background=C["bg"], foreground=C["accent"], font=("Courier New", 13, "bold"))
        self.style.configure("Status.TLabel",
            background=C["surface2"], foreground=C["green"], font=("Courier New", 9))

        self.style.configure("TCombobox",
            fieldbackground=C["entry_bg"], background=C["entry_bg"],
            foreground=C["text"], arrowcolor="#ffffff", bordercolor=C["border"],
            lightcolor=C["entry_bg"], darkcolor=C["entry_bg"],
            focusfill=C["entry_bg"], selectbackground=C["entry_bg"])
        self.style.map("TCombobox",
            fieldbackground=[("readonly", C["entry_bg"]), ("focus", C["entry_bg"])],
            foreground=[("readonly", C["text"]), ("focus", C["text"])],
            bordercolor=[("focus", C["border"]), ("active", C["border"])],
            lightcolor=[("focus", C["entry_bg"])],
            darkcolor=[("focus", C["entry_bg"])])

        self.option_add("*TCombobox*Listbox*Background", C["entry_bg"])
        self.option_add("*TCombobox*Listbox*Foreground", C["text"])
        self.option_add("*TCombobox*Listbox*selectBackground", C["accent"])
        self.option_add("*TCombobox*Listbox*selectForeground", C["bg"])
        self.option_add("*TCombobox*Listbox*font", ("Courier New", 9))
        self.option_add("*TCombobox*Listbox*borderwidth", 0)

        self.style.configure("TCheckbutton",
            background=C["surface"], foreground=C["text"], font=("Courier New", 9))
        self.style.map("TCheckbutton",
            background=[("active", C["surface"])])
        self.style.configure("TSpinbox",
            fieldbackground=C["entry_bg"], background=C["surface"],
            foreground=C["text"], borderwidth=1)

    def _build_ui(self):
        C = self.C

        topbar = tk.Frame(self, bg=C["surface2"], height=48)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="Ezmation", bg=C["surface2"],
                 fg=C["accent"], font=("Courier New", 14, "bold")).pack(side="left", padx=16, pady=10)

        self.status_var = tk.StringVar(value="● IDLE")
        self.status_lbl = tk.Label(topbar, textvariable=self.status_var,
            bg=C["surface2"], fg=C["subtext"], font=("Courier New", 9))
        self.status_lbl.pack(side="left", padx=8)

        btn_frame = tk.Frame(topbar, bg=C["surface2"])
        btn_frame.pack(side="right", padx=12, pady=6)

        self.play_btn = tk.Button(btn_frame, text="▶  PLAY",
            bg=C["green"], fg=C["bg"], font=("Courier New", 9, "bold"),
            relief="flat", padx=14, pady=4, cursor="hand2", command=self._play)
        self.play_btn.pack(side="left", padx=4)

        self.stop_btn = tk.Button(btn_frame, text="■  STOP",
            bg=C["subtext"], fg="#fff", font=("Courier New", 9, "bold"),
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        shortcut_info = tk.Label(topbar,
            text=f"[{self.config_data['shortcut_play']}] play  [{self.config_data['shortcut_stop']}] stop",
            bg=C["surface2"], fg=C["subtext"], font=("Courier New", 8))
        shortcut_info.pack(side="right", padx=8)
        self._shortcut_info_lbl = shortcut_info

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self._tab_autoclicker = ttk.Frame(self.nb, style="TFrame")
        self._tab_macro       = ttk.Frame(self.nb, style="TFrame")
        self._tab_settings    = ttk.Frame(self.nb, style="TFrame")

        self.nb.add(self._tab_autoclicker, text=" 🖱  AUTO CLICKER ")
        self.nb.add(self._tab_macro,       text=" ⌨  MACRO ")
        self.nb.add(self._tab_settings,    text=" ⚙  SETTINGS ")

        self._build_autoclicker_tab()
        self._build_macro_tab()
        self._build_settings_tab()

        statusbar = tk.Frame(self, bg=C["surface2"], height=24)
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)
        self._detail_var = tk.StringVar(value="Ready")
        tk.Label(statusbar, textvariable=self._detail_var,
                 bg=C["surface2"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=10, pady=3)

    # ── AUTOCLICKER TAB ──
    def _build_autoclicker_tab(self):
        C = self.C
        tab = self._tab_autoclicker
        tab.configure(style="TFrame")

        outer = tk.Frame(tab, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(outer, text="AUTO CLICKER", bg=C["bg"], fg=C["accent"],
                 font=("Courier New", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,12))

        card = tk.Frame(outer, bg=C["surface"], bd=0, relief="flat",
                        highlightbackground=C["border"], highlightthickness=1)
        card.grid(row=1, column=0, columnspan=4, sticky="ew", padx=0, pady=4)
        outer.columnconfigure(0, weight=1)

        row = 0
        tk.Label(card, text="Mouse Button", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=0, sticky="w", padx=16, pady=(14,2))
        self.ac_button_var = tk.StringVar(value="Left Click")
        ttk.Combobox(card, textvariable=self.ac_button_var,
                     values=["Left Click", "Right Click", "Middle Click"],
                     state="readonly", width=18).grid(row=row+1, column=0, sticky="w", padx=16, pady=(0,10))

        tk.Label(card, text="Interval (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=1, sticky="w", padx=16, pady=(14,2))
        self.ac_interval_var = tk.IntVar(value=self.config_data["default_interval_ms"])
        tk.Spinbox(card, from_=1, to=999999, textvariable=self.ac_interval_var,
                   width=10, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 10)).grid(row=row+1, column=1, sticky="w", padx=16)

        tk.Label(card, text="Start Delay (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=2, sticky="w", padx=16, pady=(14,2))
        self.ac_delay_var = tk.IntVar(value=self.config_data["start_delay_ms"])
        tk.Spinbox(card, from_=0, to=999999, textvariable=self.ac_delay_var,
                   width=10, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 10)).grid(row=row+1, column=2, sticky="w", padx=16)

        row = 2
        self.ac_loop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(card, text="Loop (infinite)", variable=self.ac_loop_var,
                       bg=C["surface"], fg=C["text"], selectcolor=C["entry_bg"],
                       activebackground=C["surface"], activeforeground=C["accent"],
                       font=("Courier New", 9), command=self._ac_loop_toggle).grid(
                           row=row, column=0, sticky="w", padx=16, pady=(8,4))

        tk.Label(card, text="Repeat Count (if not looped)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=row, column=1, sticky="w", padx=16)
        self.ac_repeat_var = tk.IntVar(value=10)
        self.ac_repeat_spin = tk.Spinbox(card, from_=1, to=999999, textvariable=self.ac_repeat_var,
                                         width=10, bg=C["entry_bg"], fg=C["text"],
                                         buttonbackground=C["surface2"], relief="flat",
                                         font=("Courier New", 10), state="disabled")
        self.ac_repeat_spin.grid(row=row, column=2, sticky="w", padx=16, pady=(8,4))
        tk.Label(card, text="", bg=C["surface"]).grid(row=row+1, column=0, pady=8)

    def _ac_loop_toggle(self):
        if self.ac_loop_var.get():
            self.ac_repeat_spin.config(state="disabled")
        else:
            self.ac_repeat_spin.config(state="normal")

    # ── MACRO TAB ──
    def _build_macro_tab(self):
        C = self.C
        tab = self._tab_macro

        # All vars declared once here
        self.add_type_var       = tk.StringVar(value="key")
        self.add_interval_var   = tk.IntVar(value=100)
        self.add_repeat_var     = tk.IntVar(value=1)
        self.add_parallel_var   = tk.BooleanVar(value=False)
        self.add_true_seq_var   = tk.BooleanVar(value=False)
        self.add_loop_var       = tk.BooleanVar(value=False)
        self.add_spam_count_var = tk.IntVar(value=1)
        self.add_spam_delay_var = tk.IntVar(value=0)

        outer = tk.Frame(tab, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(outer, text="MACRO SEQUENCE", bg=C["bg"], fg=C["accent"],
                 font=("Courier New", 12, "bold")).pack(anchor="w")

        # Global options bar
        gopt = tk.Frame(outer, bg=C["surface"], highlightbackground=C["border"], highlightthickness=1)
        gopt.pack(fill="x", pady=(8,0))

        tk.Label(gopt, text="Global:", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=10, pady=6)
        self.macro_loop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(gopt, text="Loop Macro", variable=self.macro_loop_var,
                       bg=C["surface"], fg=C["text"], selectcolor=C["entry_bg"],
                       activebackground=C["surface"], font=("Courier New", 9),
                       command=self._macro_loop_toggle).pack(side="left", padx=6)
        tk.Label(gopt, text="Repeat:", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=(16,4))
        self.macro_repeat_var = tk.IntVar(value=1)
        self.macro_repeat_spin = tk.Spinbox(gopt, from_=1, to=9999,
                                            textvariable=self.macro_repeat_var, width=6,
                                            bg=C["entry_bg"], fg=C["text"],
                                            buttonbackground=C["surface2"], relief="flat",
                                            font=("Courier New", 9), state="disabled")
        self.macro_repeat_spin.pack(side="left")
        tk.Label(gopt, text="Start Delay (ms):", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).pack(side="left", padx=(16,4))
        self.macro_delay_var = tk.IntVar(value=0)
        tk.Spinbox(gopt, from_=0, to=999999, textvariable=self.macro_delay_var,
                   width=7, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9)).pack(side="left")

        # Action list
        list_frame = tk.Frame(outer, bg=C["surface"], highlightbackground=C["border"], highlightthickness=1)
        list_frame.pack(fill="both", expand=True, pady=(6,0))

        hdr = tk.Frame(list_frame, bg=C["surface2"])
        hdr.pack(fill="x")
        for txt, w in [("#", 3), ("TYPE", 8), ("VALUE", 18), ("INTERVAL", 11),
                       ("LOOP", 5), ("REPEAT", 7), ("MODE", 8)]:
            tk.Label(hdr, text=txt, bg=C["surface2"], fg=C["subtext"],
                     font=("Courier New", 8, "bold"), width=w, anchor="w").pack(side="left", padx=4, pady=4)

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

        # ── Add action area ──
        bp = {"highlightbackground": C["border"], "highlightthickness": 1,
              "highlightcolor": C["accent"], "bd": 0}

        add_frame = tk.Frame(outer, bg=C["surface2"],
                             highlightbackground=C["border"], highlightthickness=1)
        add_frame.pack(fill="x", pady=(4,0))

        def hdr_lbl(txt, r, c, color=None, anchor="sw"):
            tk.Label(add_frame, text=txt, bg=C["surface2"],
                     fg=color or C["subtext"], font=("Courier New", 8)).grid(
                         row=r, column=c, padx=8, pady=(4,0), sticky=anchor)

        # Col 0 — Type + Interval
        hdr_lbl("Type", 1, 0)
        _type_cb = ttk.Combobox(add_frame, textvariable=self.add_type_var,
                                values=["key", "mouse", "hybrid"],
                                state="readonly", width=10)
        _type_cb.grid(row=2, column=0, padx=8, pady=(0,2), sticky="nw")
        # FIX 1: bind type change to rebuild the value input widget
        _type_cb.bind("<<ComboboxSelected>>", self._add_type_changed)

        hdr_lbl("Interval (ms)", 3, 0)
        tk.Spinbox(add_frame, from_=1, to=999999, textvariable=self.add_interval_var,
                   width=9, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9), **bp).grid(row=4, column=0, padx=8, pady=(0,8), sticky="nw")

        # Col 1 — Key/Button (dynamic) + Repeat
        hdr_lbl("Key / Button", 1, 1)
        self.add_value_frame = tk.Frame(add_frame, bg=C["surface2"])
        self.add_value_frame.grid(row=2, column=1, padx=8, pady=(0,2), sticky="nw")
        # FIX 2: NO static widget here — _build_value_input() handles it

        hdr_lbl("Repeat", 3, 1)
        tk.Spinbox(add_frame, from_=1, to=9999, textvariable=self.add_repeat_var,
                   width=12, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9), **bp).grid(row=4, column=1, padx=8, pady=(0,8), sticky="nw")

        # Col 2 — Parallel + B-Seq
        hdr_lbl("Parallel", 1, 2, C["yellow"])
        tk.Checkbutton(add_frame, variable=self.add_parallel_var,
                       bg=C["entry_bg"], selectcolor=C["yellow"],
                       activebackground="#444444", indicatoron=0, width=4, height=1,
                       **bp).grid(row=2, column=2, padx=8, pady=(0,2))
        hdr_lbl("B-Seq", 3, 2, C["green"], anchor="n")
        tk.Checkbutton(add_frame, variable=self.add_true_seq_var,
                       bg=C["entry_bg"], selectcolor=C["green"],
                       activebackground="#444444", indicatoron=0, width=4, height=1,
                       **bp).grid(row=4, column=2, padx=8, pady=(0,8), sticky="n")

        # Col 3 — Spam Count + Spam Delay
        hdr_lbl("Spam Count", 1, 3)
        tk.Spinbox(add_frame, from_=1, to=50, textvariable=self.add_spam_count_var,
                   width=6, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9), **bp).grid(row=2, column=3, padx=8, pady=(0,2), sticky="nw")
        hdr_lbl("Spam Delay", 3, 3)
        tk.Spinbox(add_frame, from_=0, to=1000, textvariable=self.add_spam_delay_var,
                   width=6, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9), **bp).grid(row=4, column=3, padx=8, pady=(0,8), sticky="nw")

        # Col 4 — Loop + ADD button
        hdr_lbl("Loop", 1, 4, C["accent"], anchor="n")
        tk.Checkbutton(add_frame, variable=self.add_loop_var,
                       bg=C["entry_bg"], selectcolor=C["accent"],
                       activebackground="#444444", indicatoron=0, width=4, height=1,
                       **bp).grid(row=2, column=4, padx=20, pady=(0,2), sticky="n")
        tk.Button(add_frame, text="ADD ➕", bg=C["accent"], fg="#fff",
                  font=("Courier New", 9, "bold"), relief="flat", padx=10, pady=2,
                  command=self._add_action).grid(row=4, column=4, padx=20, pady=(0,8), sticky="we")

        add_frame.grid_columnconfigure(5, weight=1)

        # FIX 3: initialize with the default "key" input
        self._build_value_input()

    def _build_value_input(self):
        """Rebuild the Key/Button input widget based on current action type."""
        C = self.C
        for w in self.add_value_frame.winfo_children():
            w.destroy()

        bp = {"highlightbackground": C["border"], "highlightthickness": 1, "bd": 0}
        atype = self.add_type_var.get()

        if atype == "key":
            self.add_key_var = tk.StringVar(value="space")
            tk.Entry(self.add_value_frame, textvariable=self.add_key_var,
                     bg=C["entry_bg"], fg=C["text"], insertbackground=C["text"],
                     relief="flat", font=("Courier New", 10), width=14, **bp).pack(side="left")
            tk.Label(self.add_value_frame, text="(e.g. space, f5, a)",
                     bg=C["surface2"], fg=C["subtext"],
                     font=("Courier New", 7)).pack(side="left", padx=4)

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
                     relief="flat", font=("Courier New", 9), width=8, **bp).pack(side="left", padx=2)
            tk.Label(self.add_value_frame, text="+", bg=C["surface2"],
                     fg=C["accent"], font=("Courier New", 10, "bold")).pack(side="left", padx=2)
            ttk.Combobox(self.add_value_frame, textvariable=self.add_mouse_var,
                         values=list(MOUSE_BUTTONS.keys()),
                         state="readonly", width=12).pack(side="left")

    def _add_type_changed(self, event=None):
        self._build_value_input()

    def _add_action(self):
        atype = self.add_type_var.get()

        # FIX 4: read from StringVars (set by _build_value_input), not a removed widget
        if atype == "key":
            val = getattr(self, "add_key_var", tk.StringVar(value="")).get().strip()
        elif atype == "mouse":
            val = getattr(self, "add_mouse_var", tk.StringVar(value="left click")).get().strip()
        else:  # hybrid
            key_p   = getattr(self, "add_key_var",   tk.StringVar(value="ctrl")).get().strip()
            mouse_p = getattr(self, "add_mouse_var",  tk.StringVar(value="left click")).get().strip()
            val = f"{key_p}|{mouse_p}"

        if not val:
            messagebox.showwarning("Invalid", "Please specify a value.")
            return

        action = Action(
            action_type=atype,
            value=val,
            interval_ms=self.add_interval_var.get(),
            looped=self.add_loop_var.get(),
            repeat=self.add_repeat_var.get(),
            parallel=self.add_parallel_var.get(),
            true_seq=self.add_true_seq_var.get(),
            spam_count=self.add_spam_count_var.get(),
            spam_delay=self.add_spam_delay_var.get(),
        )
        self.macro_actions.append(action)
        self._refresh_macro_list()

    def _refresh_macro_list(self):
        C = self.C
        for w in self.macro_list_inner.winfo_children():
            w.destroy()
        for i, action in enumerate(self.macro_actions):
            row_bg = C["surface"] if i % 2 == 0 else C["surface2"]
            if getattr(action, "parallel", False):
                row_bg = C["entry_bg"] if i % 2 == 0 else "#0f0f1a"
            row = tk.Frame(self.macro_list_inner, bg=row_bg)
            row.pack(fill="x")

            def mk_lbl(text, w=12, fg=None, bg=row_bg):
                return tk.Label(row, text=str(text), bg=bg,
                                fg=fg or C["text"], font=("Courier New", 9),
                                width=w, anchor="w")

            mk_lbl(i+1, 3).pack(side="left", padx=4, pady=3)
            color = {"key": C["accent"], "mouse": C["accent2"], "hybrid": C["yellow"]}.get(
                action.action_type, C["text"])
            mk_lbl(action.action_type.upper(), 8, color).pack(side="left", padx=4)
            mk_lbl(action.value, 18).pack(side="left", padx=4)
            mk_lbl(action.interval_ms, 11).pack(side="left", padx=4)
            mk_lbl("✓" if action.looped else "—", 5,
                   C["green"] if action.looped else C["subtext"]).pack(side="left", padx=4)
            mk_lbl(action.repeat if not action.looped else "∞", 7).pack(side="left", padx=4)

            is_par  = getattr(action, "parallel", False)
            is_bseq = getattr(action, "true_seq", False)
            mode_txt   = "PAR"   if is_par  else ("B-SEQ" if is_bseq else "SEQ")
            mode_color = C["yellow"] if is_par else (C["green"] if is_bseq else C["subtext"])
            mk_lbl(mode_txt, 8, mode_color).pack(side="left", padx=4)

            idx = i
            tk.Button(row, text="✕", bg=row_bg, fg=C["red"],
                      font=("Courier New", 9, "bold"), relief="flat", cursor="hand2",
                      command=lambda x=idx: self._delete_action(x)).pack(side="right", padx=8)
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

    # ── SETTINGS TAB ──
    def _build_settings_tab(self):
        C = self.C
        tab = self._tab_settings

        outer = tk.Frame(tab, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(outer, text="SETTINGS", bg=C["bg"], fg=C["accent"],
                 font=("Courier New", 12, "bold")).pack(anchor="w", pady=(0,12))

        kb_card = tk.LabelFrame(outer, text="\n  KEYBINDS  ", bg=C["surface"],
                                fg=C["accent"], font=("Courier New", 9, "bold"),
                                labelanchor="nw", highlightbackground=C["border"],
                                highlightthickness=1, bd=0, relief="flat", padx=14, pady=10)
        kb_card.pack(fill="x", pady=(0,10))
        self._build_keybind_row(kb_card, "Play Shortcut", "shortcut_play", row=0)
        self._build_keybind_row(kb_card, "Stop Shortcut", "shortcut_stop", row=1)

        gen_card = tk.LabelFrame(outer, text="\n  GENERAL  ", bg=C["surface"],
                                 fg=C["accent"], font=("Courier New", 9, "bold"),
                                 labelanchor="nw", highlightbackground=C["border"],
                                 highlightthickness=1, bd=0, relief="flat", padx=14, pady=10)
        gen_card.pack(fill="x", pady=(0,10))

        tk.Label(gen_card, text="Theme", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=0, column=0, sticky="w", pady=4)
        self.theme_var = tk.StringVar(value=self.config_data.get("theme", "dark"))
        ttk.Combobox(gen_card, textvariable=self.theme_var,
                     values=["dark", "light"], state="readonly", width=12).grid(
                         row=0, column=1, padx=12, sticky="w")

        tk.Label(gen_card, text="Default Interval (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=1, column=0, sticky="w", pady=4)
        self.def_interval_var = tk.IntVar(value=self.config_data["default_interval_ms"])
        tk.Spinbox(gen_card, from_=1, to=9999, textvariable=self.def_interval_var,
                   width=8, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9)).grid(row=1, column=1, padx=12, sticky="w")

        tk.Label(gen_card, text="Default Start Delay (ms)", bg=C["surface"], fg=C["subtext"],
                 font=("Courier New", 8)).grid(row=2, column=0, sticky="w", pady=4)
        self.def_delay_var = tk.IntVar(value=self.config_data["start_delay_ms"])
        tk.Spinbox(gen_card, from_=0, to=99999, textvariable=self.def_delay_var,
                   width=8, bg=C["entry_bg"], fg=C["text"],
                   buttonbackground=C["surface2"], relief="flat",
                   font=("Courier New", 9)).grid(row=2, column=1, padx=12, sticky="w")

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
                                font=("Courier New", 8), relief="flat", padx=8, cursor="hand2")
        capture_btn.grid(row=row, column=2, padx=4)
        capture_btn.configure(command=lambda e=entry, v=var, b=capture_btn, k=cfg_key:
                               self._start_capture(e, v, b, k))
        setattr(self, f"_kbvar_{cfg_key}", var)

    def _start_capture(self, entry, var, btn, cfg_key):
        C = self.C
        btn.config(text="Press any key...", bg=C["yellow"], fg=C["bg"])

        def on_key(event):
            key = event.keysym
            name = key.upper()
            var.set(name)
            self.config_data[cfg_key] = name
            btn.config(text="CAPTURE", bg=C["surface2"], fg=C["text"])
            self.unbind("<KeyPress>")
            self.focus_set()

        self.bind("<KeyPress>", on_key)
        self.focus_set()

    def _save_settings(self):
        for k in ["shortcut_play", "shortcut_stop"]:
            var = getattr(self, f"_kbvar_{k}", None)
            if var:
                self.config_data[k] = var.get()
        self.config_data["theme"]               = self.theme_var.get()
        self.config_data["default_interval_ms"] = self.def_interval_var.get()
        self.config_data["start_delay_ms"]      = self.def_delay_var.get()
        save_config(self.config_data)
        self._update_shortcut_label()
        self._setup_hotkeys()
        messagebox.showinfo("Saved", "Settings saved successfully!")

    def _update_shortcut_label(self):
        self._shortcut_info_lbl.config(
            text=f"[{self.config_data['shortcut_play']}] play  [{self.config_data['shortcut_stop']}] stop")

    def _setup_hotkeys(self):
        if hasattr(self, '_hotkey_listener') and self._hotkey_listener:
            self._hotkey_listener.stop()
        def get_keys():
            return (self.config_data["shortcut_play"], self.config_data["shortcut_stop"])
        self._hotkey_listener = HotkeyListener(
            play_cb=self._play, stop_cb=self._stop, get_keys=get_keys)
        self._hotkey_listener.start()

    def _play(self):
        if self.running:
            return
        tab = self.nb.index(self.nb.select())
        self.running = True
        self._set_ui_running(True)

        if tab == 0:
            btn_str  = self.ac_button_var.get().lower()
            interval = max(1, self.ac_interval_var.get())
            looped   = self.ac_loop_var.get()
            repeat   = self.ac_repeat_var.get()
            delay    = self.ac_delay_var.get()
            self.executor.run_autoclicker(btn_str, interval, looped, repeat, delay)

        elif tab == 1:
            if not self.macro_actions:
                messagebox.showwarning("Empty Macro", "Add at least one action to the macro.")
                self.running = False
                self._set_ui_running(False)
                return
            looped = self.macro_loop_var.get()
            repeat = self.macro_repeat_var.get()
            delay  = self.macro_delay_var.get()
            self.executor.run_macro(self.macro_actions, looped, repeat, delay)

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


if __name__ == "__main__":
    app = AutomatorApp()
    app.mainloop()
