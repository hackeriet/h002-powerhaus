short a0, a1, a2, a3, a4, a5;

void setup()
{
  Serial.begin(19200);
  while(!Serial) {
    delay(25);
  }
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH); // Indicate on status
  
  while (Serial.available() <= 0) {
    Serial.print('A');   // send a capital A
    delay(300);
  }
}

void loop()
{
  char inbyte;
  // if we get a valid byte, read analog ins:
  if (Serial.available() > 0) {
    // get incoming byte:
    inbyte = Serial.read();
    
    delay(10);    
    a0 = map(analogRead(A0), 0, 1024, 0, 255);
    delay(10);
    a1 = map(analogRead(A1), 0, 1024, 0, 255);
    delay(10);
    a2 = map(analogRead(A2), 0, 1024, 0, 255);
    delay(10);
    a3 = map(analogRead(A3), 0, 1024, 0, 255);
    delay(10);
    a4 = map(analogRead(A4), 0, 1024, 0, 255);
    delay(10);
    a5 = map(analogRead(A5), 0, 1024, 0, 255);


    Serial.print(a0);
    Serial.print(" ");
    Serial.print(a1);
    Serial.print(" ");
    Serial.print(a2);
    Serial.print(" ");
    Serial.print(a3);
    Serial.print(" ");
    Serial.print(a4);
    Serial.print(" ");
    Serial.println(a5);
/*
    Serial.write(A0);
    Serial.write(A1);
    Serial.write(A2);
    Serial.write(A3);
    Serial.write(A4);
    Serial.write(A5);
    */
  }
}
