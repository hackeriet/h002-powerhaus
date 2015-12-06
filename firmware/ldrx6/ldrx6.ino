void setup(){
  Serial.begin(57600);
}

void loop(){
  int ldr;
  delay(10);
  ldr = analogRead(A0);
  Serial.print(ldr * 25 );
  Serial.print(" ");
  delay(10);
  ldr = analogRead(A1);
  Serial.print(ldr);
  Serial.print(" ");
  delay(10);
  ldr = analogRead(A2);
  Serial.print(ldr);
  Serial.print(" ");
  delay(10);
  ldr = analogRead(A3);
  Serial.print(ldr);
  Serial.print(" ");
  delay(10);
  ldr = analogRead(A4);
  Serial.print(ldr);
  Serial.print(" ");
  delay(10);
  ldr = analogRead(A5);
  Serial.print(ldr);
  Serial.println("");

}
