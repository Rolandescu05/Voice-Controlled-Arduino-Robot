import tkinter as tk
import serial
import speech_recognition as sr
import threading

# --- 1. BLUETOOTH SETTINGS ---
BLUETOOTH_PORT = 'COM5'  # <--- SET YOUR COM PORT
BAUD_RATE = 9600

try:
    robot = serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=1)
    connection_status = f"Connected to {BLUETOOTH_PORT} ✅"
except Exception as e:
    robot = None
    connection_status = f"Disconnected ❌"

# --- 2. COMMUNICATION FUNCTIONS ---
def send_command(command_char):
    if robot:
        robot.write(command_char.encode())
        
        # Visual feedback on screen
        if command_char == 'A':
            label_status.config(text="Free Roam ACTIVE")
            window.config(bg="#1abc9c") # Change the background color to green
        elif command_char == 'S':
            label_status.config(text="Command sent: STOP")
            window.config(bg="#2c3e50") # Return to standard gray
        else:
            label_status.config(text=f"Command sent manually: {command_char}")
            window.config(bg="#2c3e50")
    else:
        label_status.config(text="Error: Robot is not connected!")

# --- 3. CONTINUOUS VOICE FUNCTION ---
active_listening = False

def listening_loop():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        label_status.config(text="Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        while active_listening:
            label_status.config(text="🎙️ Listening... (say: auto, forward, stop)")
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                # Changed language to English to match the new voice commands
                command = recognizer.recognize_google(audio, language="en-US").lower()
                
                if "auto" in command or "explore" in command or "autonomous" in command:
                    send_command('A')
                elif "forward" in command or "front" in command:
                    send_command('F')
                elif "backward" in command or "back" in command:
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
                
    label_status.config(text="Waiting for manual commands...")

def toggle_voice():
    global active_listening
    if not active_listening:
        active_listening = True
        btn_voice.config(text="🔴 Stop Listening", bg="#e74c3c")
        threading.Thread(target=listening_loop, daemon=True).start()
    else:
        active_listening = False
        btn_voice.config(text="🎙️ Start Listening", bg="#3498db")
        send_command('S') 

# --- 4. KEYBOARD (WASD with HOLD + Q/Space with Tap) ---
stop_timer = None
current_key = None

def key_press(event):
    global active_listening, stop_timer, current_key
    key = event.char.lower()
    
    # 1. Cancel the "brake" if Windows is just auto-repeating the held key
    if stop_timer is not None:
        window.after_cancel(stop_timer)
        stop_timer = None
        
    # 2. Execute the command only if it's a new key
    if key != current_key:
        # Remember the key only for WASD, because for the rest we don't care about auto-repeat
        if key in ['w', 'a', 's', 'd']:
            current_key = key 
            
        if key == 'w': 
            send_command('F')
            btn_forward.config(relief=tk.SUNKEN)
        elif key == 's': 
            send_command('B')
            btn_backward.config(relief=tk.SUNKEN)
        elif key == 'a': 
            send_command('L')
            btn_left.config(relief=tk.SUNKEN)
        elif key == 'd': 
            send_command('R')
            btn_right.config(relief=tk.SUNKEN)
            
        elif key == 'q': 
            send_command('A')
            btn_auto.config(relief=tk.SUNKEN)
            current_key = None # Don't block Q
            
        elif key == ' ': 
            send_command('S') 
            btn_stop.config(relief=tk.SUNKEN)
            current_key = None # Don't block Space
            
            # KILL SWITCH: Also stops voice if it was active
            if active_listening:
                toggle_voice()

def execute_stop():
    # Send STOP only when releasing a WASD key
    global current_key
    send_command('S')
    current_key = None
    
    # Reset direction buttons to normal state
    btn_forward.config(relief=tk.RAISED)
    btn_backward.config(relief=tk.RAISED)
    btn_left.config(relief=tk.RAISED)
    btn_right.config(relief=tk.RAISED)

def key_release(event):
    global stop_timer
    key = event.char.lower()
    
    # Visually raise the special buttons instantly (they continue their action on the robot)
    if key == 'q':
        btn_auto.config(relief=tk.RAISED)
    elif key == ' ':
        btn_stop.config(relief=tk.RAISED)
        
    # If you release a WASD key, wait 50ms and apply the brake
    if key in ['w', 'a', 's', 'd']:
        stop_timer = window.after(50, execute_stop)

# --- 5. GRAPHICAL USER INTERFACE (TKINTER) ---
window = tk.Tk()
window.title("AI Robot Command Center")
window.geometry("400x520")
window.config(bg="#2c3e50")

tk.Label(window, text=connection_status, font=("Arial", 12), bg="#2c3e50", fg="#2ecc71" if robot else "#e74c3c").pack(pady=5)
label_status = tk.Label(window, text="Use WASD or Q for Auto...", font=("Arial", 11, "italic"), bg="#2c3e50", fg="#f1c40f")
label_status.pack(pady=10)

# NEW Button for Auto Mode
btn_auto = tk.Button(window, text="🤖 AUTO MODE (Q)", font=("Arial", 14, "bold"), bg="#9b59b6", fg="white", width=20, command=lambda: send_command('A'))
btn_auto.pack(pady=5)

button_frame = tk.Frame(window, bg="#2c3e50")
button_frame.pack(pady=10)

btn_forward = tk.Button(button_frame, text="⬆️ W", font=("Arial", 16), width=5, command=lambda: send_command('F'))
btn_left = tk.Button(button_frame, text="⬅️ A", font=("Arial", 16), width=5, command=lambda: send_command('L'))
btn_right = tk.Button(button_frame, text="➡️ D", font=("Arial", 16), width=5, command=lambda: send_command('R'))
btn_backward = tk.Button(button_frame, text="⬇️ S", font=("Arial", 16), width=5, command=lambda: send_command('B'))
btn_stop = tk.Button(button_frame, text="🛑 SPC", font=("Arial", 16), width=5, bg="#e74c3c", fg="white", command=lambda: send_command('S'))

btn_forward.grid(row=0, column=1, pady=5)
btn_left.grid(row=1, column=0, padx=5)
btn_stop.grid(row=1, column=1, padx=5)
btn_right.grid(row=1, column=2, padx=5)
btn_backward.grid(row=2, column=1, pady=5)

btn_voice = tk.Button(window, text="🎙️ Start Listening", font=("Arial", 16, "bold"), bg="#3498db", fg="white", command=toggle_voice)
btn_voice.pack(pady=10)

window.bind("<KeyPress>", key_press)
window.bind("<KeyRelease>", key_release)

window.mainloop()