# GUI application in Python for remote control of an autonomous robot via Bluetooth.
# Integrates asynchronous voice recognition (Google Cloud API) and video-game-style manual control (Hold-to-Move).

import tkinter as tk
import tkinter.font as tkfont
import serial
import speech_recognition as sr
import threading

# --- 0. DESIGN TOKENS ---
C = {
    "bg":        "#0e1116",   # window background
    "panel":     "#161b22",   # panels / cards
    "panel_hi":  "#1f2630",   # button hover
    "line":      "#2a3340",   # subtle borders
    "text":      "#e6edf3",   # primary text
    "muted":     "#8b97a5",   # secondary text
    "accent":    "#2dd4bf",   # teal — active / action
    "accent_dk": "#0d9488",   # teal pressed
    "auto":      "#a78bfa",   # violet — autonomous mode
    "auto_dk":   "#7c5cf0",
    "danger":    "#f43f5e",   # red — STOP
    "danger_dk": "#be123c",
    "ok":        "#34d399",   # connection LED
    "warn":      "#fbbf24",   # waiting statuses
}

# --- 1. BLUETOOTH SETTINGS ---
BT_PORT = 'COM5'   # <--- SET YOUR COM PORT HERE
BAUD_RATE = 9600

try:
    robot = serial.Serial(BT_PORT, BAUD_RATE, timeout=1)
    connected = True
except Exception:
    robot = None
    connected = False

# --- 2. FLAT BUTTON WIDGET ---
class FlatButton(tk.Label):
    """Flat button with hover and active-state colour feedback."""
    def __init__(self, master, text, command=None, kind="normal",
                 font=None, width=None, pady=10, padx=12):
        self.kind = kind
        self.command = command
        self.active = False
        super().__init__(master, text=text, font=font, width=width,
                         pady=pady, padx=padx, cursor="hand2",
                         bg=self._bg_normal(), fg=self._fg_normal(),
                         bd=0, highlightthickness=1,
                         highlightbackground=C["line"])
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _bg_normal(self):
        return {"normal": C["panel"], "accent": C["panel"],
                "auto": C["panel"], "danger": C["danger"]}[self.kind]

    def _fg_normal(self):
        return {"normal": C["text"], "accent": C["accent"],
                "auto": C["auto"], "danger": "#ffffff"}[self.kind]

    def _bg_active(self):
        return {"normal": C["accent_dk"], "accent": C["accent_dk"],
                "auto": C["auto_dk"], "danger": C["danger_dk"]}[self.kind]

    def _on_enter(self, _):
        if not self.active:
            self.config(bg=C["panel_hi"] if self.kind != "danger" else C["danger_dk"])

    def _on_leave(self, _):
        if not self.active:
            self.config(bg=self._bg_normal())

    def _on_click(self, _):
        if self.command:
            self.command()

    def set_active(self, state: bool):
        """Light up / dim the button (replaces relief=SUNKEN)."""
        self.active = state
        if state:
            self.config(bg=self._bg_active(), fg="#ffffff",
                        highlightbackground=self._bg_active())
        else:
            self.config(bg=self._bg_normal(), fg=self._fg_normal(),
                        highlightbackground=C["line"])

# --- 3. COMMUNICATION FUNCTIONS ---
def set_status(text, color=None):
    lbl_status.config(text=text, fg=color or C["muted"])

def set_mode(text, color):
    """Update the large mode pill + top accent bar."""
    lbl_mode.config(text=text, fg=color)
    accent_bar.config(bg=color)

def send_command(letter):
    if robot:
        robot.write(letter.encode())
        if letter == 'A':
            set_mode("AUTONOMOUS MODE", C["auto"])
            set_status("Free Roam active — robot is exploring on its own", C["auto"])
            btn_auto.set_active(True)
        elif letter == 'S':
            set_mode("STATIONARY", C["muted"])
            set_status("Command sent: STOP", C["text"])
            btn_auto.set_active(False)
        else:
            name = {"F": "FORWARD", "B": "BACKWARD", "L": "LEFT", "R": "RIGHT"}.get(letter, letter)
            set_mode("MANUAL CONTROL", C["accent"])
            set_status(f"Command sent: {name}", C["accent"])
            btn_auto.set_active(False)
    else:
        set_status("Error: robot is not connected", C["danger"])

# --- 4. CONTINUOUS VOICE LISTENING ---
listening_active = False

def listening_loop():
    recognizer = sr.Recognizer()
    recognizer.non_speaking_duration = 0.3
    recognizer.pause_threshold = 0.5
    with sr.Microphone() as source:
        set_status("Calibrating microphone…", C["warn"])
        recognizer.adjust_for_ambient_noise(source, duration=1)

        while listening_active:
            set_status("🎙 Listening…  say: auto · forward · stop", C["warn"])
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                command = recognizer.recognize_google(audio, language="en-US").lower()

                if "auto" in command or "explore" in command or "autonomous" in command:
                    send_command('A')
                elif "forward" in command or "ahead" in command:
                    send_command('F')
                elif "back" in command or "backward" in command or "reverse" in command:
                    send_command('B')
                elif "left" in command:
                    send_command('L')
                elif "right" in command:
                    send_command('R')
                elif "stop" in command or "halt" in command:
                    send_command('S')

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                break

    set_status("Waiting for manual commands…")

def toggle_voice():
    global listening_active
    if not listening_active:
        listening_active = True
        btn_voice.config(text="●  STOP LISTENING")
        btn_voice.set_active(True)
        threading.Thread(target=listening_loop, daemon=True).start()
    else:
        listening_active = False
        btn_voice.config(text="🎙  VOICE CONTROL")
        btn_voice.set_active(False)
        send_command('S')

# --- 5. KEYBOARD (WASD hold + Q/Space tap) ---
stop_timer = None
current_key = None

def on_key_press(event):
    global listening_active, stop_timer, current_key
    key = event.char.lower() if event.char else ""

    # Cancel the pending brake if Windows is auto-repeating a held key
    if stop_timer is not None:
        window.after_cancel(stop_timer)
        stop_timer = None

    if key != current_key:
        if key in ['w', 'a', 's', 'd']:
            current_key = key

        if key == 'w':
            send_command('F'); btn_forward.set_active(True)
        elif key == 's':
            send_command('B'); btn_backward.set_active(True)
        elif key == 'a':
            send_command('L'); btn_left.set_active(True)
        elif key == 'd':
            send_command('R'); btn_right.set_active(True)
        elif key == 'q':
            send_command('A')
            current_key = None
        elif key == ' ':
            send_command('S')
            btn_stop.set_active(True)
            current_key = None
            # KILL SWITCH: also stop voice if active
            if listening_active:
                toggle_voice()

def execute_brake():
    global current_key
    send_command('S')
    current_key = None
    for b in (btn_forward, btn_backward, btn_left, btn_right):
        b.set_active(False)

def on_key_release(event):
    global stop_timer
    key = event.char.lower() if event.char else ""

    if key == ' ':
        btn_stop.set_active(False)

    if key in ['w', 'a', 's', 'd']:
        stop_timer = window.after(50, execute_brake)

# --- 6. GUI LAYOUT ---
window = tk.Tk()
window.title("Robot Command")
window.geometry("420x640")
window.config(bg=C["bg"])
window.resizable(False, False)

F_TITLE  = tkfont.Font(family="Segoe UI", size=17, weight="bold")
F_MODE   = tkfont.Font(family="Consolas", size=13, weight="bold")
F_STATUS = tkfont.Font(family="Consolas", size=10)
F_BTN    = tkfont.Font(family="Segoe UI", size=14, weight="bold")
F_DPAD   = tkfont.Font(family="Segoe UI", size=16, weight="bold")
F_SMALL  = tkfont.Font(family="Consolas", size=9)

# Top accent bar — changes colour with current mode
accent_bar = tk.Frame(window, bg=C["muted"], height=3)
accent_bar.pack(fill="x")

# Header: title + connection LED
header = tk.Frame(window, bg=C["bg"])
header.pack(fill="x", padx=24, pady=(18, 4))

tk.Label(header, text="ROBOT COMMAND", font=F_TITLE,
         bg=C["bg"], fg=C["text"]).pack(side="left")

tk.Label(header, text="●", font=("Segoe UI", 14),
         bg=C["bg"], fg=C["ok"] if connected else C["danger"]).pack(side="right")
tk.Label(header, text=BT_PORT if connected else "OFFLINE",
         font=F_SMALL, bg=C["bg"],
         fg=C["muted"]).pack(side="right", padx=(0, 4), pady=(4, 0))

# Telemetry panel: current mode + last status
panel = tk.Frame(window, bg=C["panel"], highlightthickness=1,
                 highlightbackground=C["line"])
panel.pack(fill="x", padx=24, pady=(14, 18))

lbl_mode = tk.Label(panel, text="STATIONARY", font=F_MODE,
                    bg=C["panel"], fg=C["muted"], anchor="w")
lbl_mode.pack(fill="x", padx=16, pady=(12, 2))

lbl_status = tk.Label(panel, text="Use WASD · Q = autonomous · Space = stop",
                      font=F_STATUS, bg=C["panel"], fg=C["muted"],
                      anchor="w", wraplength=340, justify="left")
lbl_status.pack(fill="x", padx=16, pady=(0, 12))

# Autonomous mode button
btn_auto = FlatButton(window, text="🤖  AUTONOMOUS MODE  (Q)", kind="auto",
                      font=F_BTN, command=lambda: send_command('A'), pady=12)
btn_auto.pack(fill="x", padx=24)

# D-Pad
dpad_frame = tk.Frame(window, bg=C["bg"])
dpad_frame.pack(pady=22)

btn_forward  = FlatButton(dpad_frame, text="▲", kind="accent", font=F_DPAD,
                          width=4, pady=14, command=lambda: send_command('F'))
btn_left     = FlatButton(dpad_frame, text="◀", kind="accent", font=F_DPAD,
                          width=4, pady=14, command=lambda: send_command('L'))
btn_stop     = FlatButton(dpad_frame, text="STOP", kind="danger", font=F_DPAD,
                          width=4, pady=14, command=lambda: send_command('S'))
btn_right    = FlatButton(dpad_frame, text="▶", kind="accent", font=F_DPAD,
                          width=4, pady=14, command=lambda: send_command('R'))
btn_backward = FlatButton(dpad_frame, text="▼", kind="accent", font=F_DPAD,
                          width=4, pady=14, command=lambda: send_command('B'))

btn_forward.grid(row=0, column=1, padx=6, pady=6)
btn_left.grid(row=1, column=0, padx=6, pady=6)
btn_stop.grid(row=1, column=1, padx=6, pady=6)
btn_right.grid(row=1, column=2, padx=6, pady=6)
btn_backward.grid(row=2, column=1, padx=6, pady=6)

tk.Label(window, text="W / A / S / D — hold to drive",
         font=F_SMALL, bg=C["bg"], fg=C["muted"]).pack()

# Voice control button
btn_voice = FlatButton(window, text="🎙  VOICE CONTROL", kind="accent",
                       font=F_BTN, command=toggle_voice, pady=12)
btn_voice.pack(fill="x", padx=24, pady=(20, 6))

tk.Label(window, text="commands: auto · forward · back · left · right · stop",
         font=F_SMALL, bg=C["bg"], fg=C["muted"]).pack()

window.bind("<KeyPress>", on_key_press)
window.bind("<KeyRelease>", on_key_release)

window.mainloop()