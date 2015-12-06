#include <EmonLib.h>

double in0, in1, in2, in3, in4, in5;

EnergyMonitor e0, e1, e2, e3, e4, e5;

void setup()
{
  Serial.begin(19200);
  while(!Serial) {
    delay(25);
  }
  // Indicator light
  pinMode(2, OUTPUT);
  
  while (Serial.available() <= 0) {
    digitalWrite(2, HIGH);
    Serial.print('A');   // send a capital A
    delay(150);
    digitalWrite(2, LOW);
    delay(150);
  }
  // safe values
  in0 = in1 = in2 = in3 = in4 = in5 = 0;  
  // setup emon
  e0.current(A0, 111.1);
  e1.current(A1, 111.1);
  e2.current(A2, 111.1);
  e3.current(A3, 111.1);
  e4.current(A4, 111.1);
  e5.current(A5, 111.1);
  
  // Indicate on & booted
  digitalWrite(2, HIGH);

}

void loop()
{
  char inbyte;
  // read the energy
  in0 = 230 * e0.calcIrms(1480);
  in1 = 230 * e1.calcIrms(1480);
  in2 = 230 * e2.calcIrms(1480);
  in3 = 230 * e3.calcIrms(1480);
  in4 = 230 * e4.calcIrms(1480);
  in5 = 230 * e5.calcIrms(1480);
  
  // if we get a valid byte, read analog ins
  if (Serial.available() > 0) {
    digitalWrite(2, LOW);
    // consume incoming byte:
    inbyte = Serial.read();
    // print off the values
    
    Serial.print(in0);
    Serial.print(" ");
    Serial.print(in1);
    Serial.print(" ");
    Serial.print(in2);
    Serial.print(" ");
    Serial.print(in3);
    Serial.print(" ");
    Serial.print(in4);
    Serial.print(" ");
    Serial.print(in5);
    Serial.println("");
    digitalWrite(2, HIGH);
  }
}
