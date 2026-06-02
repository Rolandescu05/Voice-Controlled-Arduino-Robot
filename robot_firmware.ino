#include <SoftwareSerial.h>

SoftwareSerial BT(A0, A1); 

// Motor Pins
const int ENA = 5; const int IN1 = 6; const int IN2 = 7;
const int IN3 = 8; const int IN4 = 9; const int ENB = 10;

// Ultrasonic Sensor Pins
const int trigPin = 2;
const int echoPin = 3;

int speed = 180; 
bool autoMode = false; 
char currentCommand = 'S'; // NEW: Remembers what the robot is currently doing

void setup() {
  BT.begin(9600);
  
  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT); pinMode(ENB, OUTPUT);
  pinMode(trigPin, OUTPUT); pinMode(echoPin, INPUT);
}

void loop() {
  // 1. WAITING FOR COMMANDS FROM LAPTOP (VOICE OR KEYBOARD)
  if (BT.available()) {
    char receivedCommand = BT.read(); 
    
    if (receivedCommand == 'A' || receivedCommand == 'a') {
      autoMode = true; 
    } 
    else if (receivedCommand == 'F' || receivedCommand == 'B' || receivedCommand == 'L' || receivedCommand == 'R' || receivedCommand == 'S') {
      autoMode = false; // Stops fully autonomous mode
      currentCommand = receivedCommand; // Save the command that was just given
      
      if (currentCommand == 'F') moveForward();
      if (currentCommand == 'B') moveBackward();
      if (currentCommand == 'L') turnLeft();
      if (currentCommand == 'R') turnRight();
      if (currentCommand == 'S') stopRobot();
    }
  }

  // 2. ROUTINE FOR FULLY AUTONOMOUS MODE (Key Q)
  if (autoMode) {
    freeRoamLogic();
  }

  // 3. NEW: DRIVING ASSISTANCE (For Voice and WASD)
  // If the robot is not on Auto, but is moving FORWARD
  if (!autoMode && currentCommand == 'F') {
    long distance = measureDistance();
    
    // If an obstacle appears at less than 30 cm
    if (distance > 0 && distance <= 30) {
      
      // Collision avoidance reflex
      stopRobot();
      delay(300);
      moveBackward();
      delay(300);
      turnRight();
      delay(800); 
      stopRobot();
      
      // After avoiding the obstacle, it stops and waits for your new voice/manual command!
      currentCommand = 'S'; 
    }
  }
}

// --- AUTONOMOUS INTELLIGENCE LOGIC (Free Roam) ---
void freeRoamLogic() {
  long distance = measureDistance();
  
  if (distance > 30 || distance == 0) { 
    moveForward();
  } 
  else {
    stopRobot(); delay(300); 
    moveBackward(); delay(300); stopRobot(); delay(200);
    
    turnRight(); delay(800); stopRobot(); delay(400); 
    
    long newDistance = measureDistance();
    if (newDistance <= 30 && newDistance > 0) {
      turnLeft(); delay(1200); stopRobot(); delay(300);
    }
  }
}

// --- SENSOR FUNCTION ---
long measureDistance() {
  digitalWrite(trigPin, LOW); delayMicroseconds(2);
  digitalWrite(trigPin, HIGH); delayMicroseconds(10); digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH, 30000); 
  if (duration == 0) return 0;
  return duration * 0.034 / 2;
}

// --- MOVEMENT FUNCTIONS ---
void moveForward() {
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH); 
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);  
  
  // Here you put your numbers found during calibration so it moves perfectly straight!
  analogWrite(ENA, 220); 
  analogWrite(ENB, 150); 
}
void moveBackward() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);  
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH); 
  analogWrite(ENA, speed); analogWrite(ENB, speed);
}
void turnLeft() {
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH); 
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH); 
  analogWrite(ENA, speed); analogWrite(ENB, speed);
}
void turnRight() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);  
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);  
  analogWrite(ENA, speed); analogWrite(ENB, speed);
}
void stopRobot() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
  analogWrite(ENA, 0); analogWrite(ENB, 0);
}