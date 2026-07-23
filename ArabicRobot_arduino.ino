#include <cvzone.h>
#include <Servo.h>


Servo LServo; 
Servo RServo; 
Servo HServo; 


const int LS_pin = 8;
const int RS_pin = 9;
const int HS_pin = 10;
const int IR_pin = 2; 


SerialData serialData(3, 3); 
int valsRec[3]; 


int irCounter = 0;        
bool lastIrState = HIGH;  
bool wavingActive = false; 

void setup() {
  serialData.begin(); 
  
  pinMode(IR_pin, INPUT);

  LServo.attach(LS_pin);
  RServo.attach(RS_pin);
  HServo.attach(HS_pin);
}

void loop() {

  serialData.Get(valsRec);

  if (!wavingActive) {
    LServo.write(valsRec[0]);
    RServo.write(valsRec[1]);
    HServo.write(valsRec[2]);
  }


  bool currentIrState = digitalRead(IR_pin);

  if (currentIrState == LOW && lastIrState == HIGH) {
    irCounter++;
    delay(200); 
  }
  lastIrState = currentIrState;


  if (irCounter >= 4) {
    wavingActive = true;
    performWave();    
    irCounter = 0;    
    wavingActive = false; 
  }
}


void performWave() {
  for (int i = 0; i < 3; i++) {
    RServo.write(150);
    delay(300);
    RServo.write(30); 
    delay(300);
  }
}
