/*
  Author: Reece Wayt

  Note On Classes: 
    - Serial (USB CDC): This stands for Communication Device Class which is a USB class for serial communication. 
       The panda's core processor speaks to the Arduino Leonardo via a internal USB port "dev/ttyACM0".
    - Serial1 (TTL Serial): Transistor-Transistor Logic Serial, which describe the physical pins 0 (RX) and 1 (TX) on the Arduino 
       Leonardo 

  Prerequisites: 
    - run this in a terminal to allow user level permission of the device driver: 
        sudo chmod 666 /dev/ttyACM0

*/

const int rx = 0; 
const int tx = 1;

unsigned long timeoutDuration = 30000; // Timeout duration in milliseconds (30 seconds)
unsigned long lastActivityTime;
const int ledPin = 2; // LED connected to digital pin 2

void setup() {
  pinMode(ledPin, OUTPUT); // Initialize the digital pin as an output
  Serial.begin(115200); // Set to 115200 bps
  while (!Serial) {
    ; // Wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("UART echo test with timeout and LED blink");
  lastActivityTime = millis(); // Initialize the last activity time
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    Serial.print("You wrote: ");
    Serial.print(c); // Echo received characters
    if (c == '\r') { // Carriage return detected
      Serial.println(); // Add newline character
      blinkLed(); // Blink the LED
    }
    lastActivityTime = millis(); // Update the last activity time
  }
  
  // Check for timeout
  if (millis() - lastActivityTime > timeoutDuration) {
    Serial.println("Timeout reached. Stopping echo.");
    while (true) {
      // Stop execution
    }
  }
}

void blinkLed() {
  digitalWrite(ledPin, HIGH); // Turn the LED on
  delay(100); // Wait for 100 milliseconds
  digitalWrite(ledPin, LOW); // Turn the LED off
  delay(100); // Wait for 100 milliseconds
}