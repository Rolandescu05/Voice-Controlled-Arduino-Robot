# 🤖 Voice & Keyboard Controlled Autonomous Robot

An advanced robotics project featuring a custom Python Desktop Application that communicates with an Arduino-based smart robot over Bluetooth (HC-05). The system integrates cloud-based speech recognition, precise keyboard gameplay controls, and automated collision avoidance.

---

## 🚀 Features

- **🎮 Game-Style Keyboard Controls:** Fluid manual navigation using **WASD** (Hold to move, release to stop) and **Spacebar** as an emergency Kill Switch.
- **🎙️ Cloud-Based Voice Control:** Continuous hands-free steering powered by Google Web Speech API, with full support for Romanian language commands (*"înainte"*, *"stânga"*, *"stop"*, etc.).
- **🤖 Autonomous Navigation (Free Roam):** Activated via the **Q key**, forcing the robot to use its Ultrasonic sensor to map paths, measure safety thresholds, and autonomously dodge walls.
- **🛡️ ADAS (Driver Assistance):** Real-time sensor overriding that automatically triggers emergency braking and avoidance maneuvers even while under manual/voice operation.

---

## 🛠️ Architecture & System Design

The project bridges high-level cloud AI processing with low-level hardware execution by distributing tasks between the PC and the Microcontroller.

+---------------------------------------------------------+
|                  PC / LAPTOP CONTROL                    |
|                                                         |
|  [Tkinter GUI] <---> [WASD / Q / Space Inputs]          |
|         |                                               |
|         v                                               |
|  [SpeechRecognition] ---> (Google Web Speech Cloud API) |
+---------------------------------------------------------+
|
(Bluetooth Link)
|
v
+---------------------------------------------------------+
|                    ARDUINO ROBOT                        |
|                                                         |
|    [HC-05 Module] ---> [Arduino Uno (UART)]             |
|                               |                         |
|                               v                         |
|    [Ultrasonic Sensor] <---> [L298N Driver]             |
+---------------------------------------------------------+

### 1. Wireless Communication (Serial Emulation)
The **HC-05 Bluetooth module** operates using the **SPP (Serial Port Profile)**, emulating a standard hardware serial connection over a 2.4 GHz radio link. The PC app flushes commands into a virtual COM port at **9600 Baud**. To minimize latency, the payload is optimized to a single **1-Byte ASCII character** (`'F'`, `'B'`, `'L'`, `'R'`, `'S'`, `'A'`). On the robot side, an Arduino decodes the stream via protocol **UART** using the `SoftwareSerial` library.

### 2. Speech Recognition Logic
Voice acquisition uses `PyAudio` to digitize acoustic pressure waves from the microphone. The software performs dynamic ambient noise calibration to establish a baseline threshold. When a phrase is captured, it is packaged and routed via a cloud API call. The neural network computes the phonetic matrix, yields a lowercase string token back to Python, and matches it against our command registry.

---

## 📂 Project Structure
├── desktop_app.py      # Python Tkinter source code (GUI, Voice, WASD thread)
├── robot_firmware.ino  # Arduino source code (Motor control, Ultrasonic logic, UART)
└── README.md           # Project documentation

🔧 Installation & Setup
Prerequisites

Make sure you have Python 3.x installed on your PC, alongside the Arduino IDE.
1. Python Dependencies

Open your terminal or Command Prompt and install the required modules:

pip install pyserial
pip install SpeechRecognition
pip install PyAudio

2. Arduino Configuration

    Wire the HC-05 Module to Arduino (TX to A0, RX to A1 via a voltage divider if needed).

    Wire the Ultrasonic Sensor (Trig to Pin 2, Echo to Pin 3).

    Upload robot_firmware.ino to your board while the USB cable is the only serial stream connected.

    Disconnect USB, power the robot via batteries, and pair it with Windows (PIN: 1234).

3. Running the Host App

Find your Outgoing COM Port in Windows Bluetooth settings, update PORT_BLUETOOTH inside desktop_app.py, and run: 
python desktop_app.py


