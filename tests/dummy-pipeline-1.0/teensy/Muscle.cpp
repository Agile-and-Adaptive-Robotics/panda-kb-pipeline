#include "../include/Muscle.h"

Muscle::Muscle(String Name, int valve_pin, int pressure_pin) {
  this->Name = Name;
  this->valve_pin = valve_pin;
  this->pressure_pin = pressure_pin;
}

void Muscle::begin() {
  //set the pinModes 
  pinMode(valve_pin, OUTPUT);
  pinMode(pressure_pin, OUTPUT);  

  //Assign starting values to class variables, which defines them. 
  PRESSURE_NOW = 0;
  PRESSURE_PREVIOUS = 0;
  PRESSURE_GRADIENT = 0;
  
  DT_ON = 8;
  IS_PULSING_ENABLED = false;
  IS_A_PULSE_ACTIVE = false;
  
  WHEN_THIS_PULSE_STARTED = millis();
  WHEN_LAST_PULSE_ENDED = millis();
  PULSE_FREQUENCY = 30;
  SetPulseFrequency(PULSE_FREQUENCY);
  
  //Get current pressure values     
  updatePressure();
  
}

void Muscle::updatePressure() {
  /*This method fetches the average pressure (n=30) and uses it to 
   * calculate the pressure gradient, resetting pressure_prev, pressure_now, 
   * and pressure_gradient.
   */
  float temp = 0;
  for (int n = 0; n < 30; n++) {
    temp += analogRead(pressure_pin); 
  }
  PRESSURE_PREVIOUS = PRESSURE_NOW;
  PRESSURE_NOW = temp / 30;
  PRESSURE_GRADIENT = PRESSURE_NOW - PRESSURE_PREVIOUS;  
}

bool Muscle::ShouldPulseEnd() {
  //yes if dt_target<dt_actual
  if ((millis() - WHEN_THIS_PULSE_STARTED) > DT_ON) {
    if (IS_A_PULSE_ACTIVE) {
      thisPulseEnd();
      return true;
    }
    return false;
  } else {
    return false;
  }
}

bool Muscle::ShouldPulseStart() {
  //yes, if dt_since_last_pulse_ended >= dt_off
  if ((millis() - WHEN_LAST_PULSE_ENDED) >= DT_OFF) {
    if (!IS_A_PULSE_ACTIVE) {
      thisPulseStart();
      return true;
    }
    return false;
  } else {
    return false;
  }
}

void Muscle::Pulse_Nanny() {
  ShouldPulseStart();
  ShouldPulseEnd();
}

void Muscle::SetPulseFrequency(float freq) {
  //assign incoming value
  PULSE_FREQUENCY = freq;

  //calculate DT_Off from new frequency
  DT_OFF = 1000 / PULSE_FREQUENCY - DT_ON;
}

void Muscle::thisPulseStart() {
  //open the valve
  Open();

  //record the time
  WHEN_THIS_PULSE_STARTED = millis();
  
  //flip the pulse control boolean
  IS_A_PULSE_ACTIVE = true;
  
  return;
}

void Muscle::thisPulseEnd() {
  //flip pulse control boolean
  IS_A_PULSE_ACTIVE = false;
  
  //close the muscle's valve
  Close();
  
  //record the time
  WHEN_LAST_PULSE_ENDED = millis();
  
  return; 
}

float Muscle::getPressure() {
  return PRESSURE_NOW;
}

float Muscle::getNewPressure() {
  updatePressure();
  return PRESSURE_NOW;
}

float Muscle::getPressureGradient() {
  return PRESSURE_GRADIENT;
}

float Muscle::getNewPressureGradient() {
  updatePressure();
  return PRESSURE_GRADIENT;
}

void Muscle::Open() {
  digitalWrite(valve_pin, HIGH);
  return;
}

void Muscle::Close() {
  digitalWrite(valve_pin, LOW);
  return;
}

void Muscle::handleCommand(char command, Muscle &otherMuscle) {
  switch (command) {
    case 'O':  // Open the valve
      Open();
      Serial.println("Valve opened.");
      break;
    case 'C':  // Close the valve
      Close();
      Serial.println("Valve closed.");
      break;
    case 'P':  // Toggle pulsing on/off
      if (IS_PULSING_ENABLED) {
        IS_PULSING_ENABLED = false;
        Close();
        Serial.println("Pulsing stopped and valve closed.");
      } else {
        IS_PULSING_ENABLED = true;
        Serial.println("Pulsing started.");
      }
      break;
    case 'F':  // Start pulsing at the current set frequency
      IS_PULSING_ENABLED = true;
      SetPulseFrequency(PULSE_FREQUENCY); // Use the currently set frequency
      Serial.print("Pulsing at ");
      Serial.print(PULSE_FREQUENCY);
      Serial.println(" Hz.");
      break;
    case 'G':  // Set pulse frequency from serial input
      if (Serial.available() > 0) {
        newFrequency = Serial.parseInt();
        if (newFrequency > 0) {  // Check if a valid frequency was entered
          SetPulseFrequency(newFrequency);
          otherMuscle.SetPulseFrequency(newFrequency); // Update the other muscle
          Serial.print("Pulse frequency set to ");
          Serial.print(newFrequency);
          Serial.println(" Hz.");
        }
      }
      break;
  }
}

