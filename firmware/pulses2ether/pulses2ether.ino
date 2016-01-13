/* PowerHaus - comotion@hackeriet.no - 2015-02-13
 *
 * Code reads power consumption through pulse counting each of 6 LDRs
 * as well as communicating serially with auxillary chip, and sends the
 * data over UDP to the broadcast address.
 *
 * aux chip is configured to write A's when it boots at 19200 baud,
 * and respond to a single byte by responding with a line of output
 * The entirety of the response goes into the packet.
 *
 * The process is not interrupt driven, and only reads one input at
 * a time. Therefore you get a snapshit of the pulse values in each time period.
 * This can miss pulse spikes, but should be representative.
 */

#include <EtherCard.h>

#ifdef VERBOSE
#define VLOG(x) Serial.println(x)
#else
#define VLOG(x)
#endif

#define BUF_SIZE 512
#define HEADER "powerhaus0.kakesmurf.zool pulses/min:"
#define AUX_HEAD " CTpower: "
#define SAMPLE_DELAY 5 // total sample time = 2s

byte mymac[] = { 
  0x90, 0x13, 0x37, 0x04, 0x20, 0xcc };

byte Ethernet::buffer[BUF_SIZE];

#define CS_PIN 8
#define ERR_PIN 13

int res = 0;
void initialize_ethernet(void){  
  for(;;){ // keep trying until you succeed 
    //Reinitialize ethernet module
    VLOG("Resetting Ethernet");
    pinMode(CS_PIN, OUTPUT);
    digitalWrite(CS_PIN, LOW);
    delay(1000);
    digitalWrite(CS_PIN, HIGH);
    delay(500);

    if (ether.begin(sizeof Ethernet::buffer, mymac, CS_PIN) == 0){ 
      VLOG( "Failed to access Ethernet controller");
      digitalWrite(ERR_PIN, HIGH);
      delay(1000);
      digitalWrite(ERR_PIN, LOW);
      delay(300);
      digitalWrite(ERR_PIN, HIGH);
      delay(1000);
      digitalWrite(ERR_PIN, LOW);

      continue;
    }

    if (!ether.dhcpSetup("powerhaus0", true)){
      VLOG("DHCP failed");
      digitalWrite(ERR_PIN, HIGH);
      delay(300);
      digitalWrite(ERR_PIN, LOW);
      delay(300);
      digitalWrite(ERR_PIN, HIGH);
      delay(300);
      digitalWrite(ERR_PIN, LOW);
      continue;
    }
#ifdef VERBOSE
    ether.printIp("IP:   ", ether.myip);
    ether.printIp("GW:   ", ether.gwip);  
    ether.printIp("DNS:  ", ether.dnsip);  
    ether.printIp("Bcast:", ether.broadcastip);
#endif
    //reset init value
    res = 0;
    break;
  }
}

void setup(void)
{
  // serial is used to speak to auxillary atmega88, which sets its pin
  // when data is available.
  pinMode(ERR_PIN, OUTPUT);
  digitalWrite(ERR_PIN, HIGH);
  Serial.begin(19200);
  Serial.setTimeout(500);
  delay(1000);
  initialize_ethernet();
  digitalWrite(ERR_PIN, LOW);
}

static float count_pulses(int pin, int secs)
{
  int i;
  int samples = secs * 1000 / SAMPLE_DELAY;
  int pcount = 0;
  int ldr[3] = { 
    0, 0, 0  };
  byte pulse = 2; // 2 means dunno
  for(i = 0; i < samples; i++){
    delay(SAMPLE_DELAY); // let the ADC settle
    // shuffle the old ones;
    ldr[0] = ldr[1];
    ldr[1] = ldr[2];
    ldr[2] = analogRead(pin);
    // define a pulse as change bigger than twice the size of two last values
    // measure on falling edge, to detect "in-the-middle-of-pulse" 1st sample
    // if not first input & prev/2 > now then pulse
    if (pulse && i > 1 && (ldr[0] / 1.5 ) > ldr[2]) {
      pcount++;
      pulse = 0;
    }
    // if new val is larger than 50% more than previous, got a pulse
    // yep this will miss shit if you suddenly turn on the light
    if(i > 1 && (ldr[0] * 1.5 ) < ldr[2]) {
      pulse = 1;
    }
  }
  return (float) pcount / secs;
}

static void udpbcast(byte *buf, int pos, short srcport, short dstport )
{
  ether.sendUdp((char*) buf, pos, srcport, ether.broadcastip, dstport);
}

int count_all_analog(char *buf, int maxlen, int secs)
{
  int t = 0;
  float pulses = count_pulses(A0, secs);
  t += sprintf((char *)buf+t, " %d", int(pulses * 60));
  pulses = count_pulses(A1, secs);
  t += sprintf((char *)buf+t, " %d", int(pulses * 60));
  pulses = count_pulses(A2, secs);
  t += sprintf((char *)buf+t, " %d", int(pulses * 60));
  pulses = count_pulses(A3, secs);
  t += sprintf((char *)buf+t, " %d", int(pulses * 60));
  pulses = count_pulses(A4, secs);
  t += sprintf((char *)buf+t, " %d", int(pulses * 60));
  pulses = count_pulses(A5, secs);
  t += sprintf((char *)buf+t, " %d", int(pulses * 60));
  
  return t;

}

/* send a byte to aux, then consume a line from aux */
int interrogate_aux(char *buf, int maxlen)
{
  int len = 0;
  Serial.print('y');
  if(Serial.available()){  
    if(Serial.peek() == 'A'){
      Serial.find("\n");
      Serial.print('S'); // aux just booted, needs one more byte to get started.
    }
    len = Serial.readBytesUntil('\n', buf, maxlen);
  }
  return len;
}

void loop(void)
{
  word rc;
  char buf[BUF_SIZE];
  int secs = 2;
  int len = strlen(HEADER);
  // composit the data
  memcpy(buf, HEADER, len);
  
  len += count_all_analog(buf + len, BUF_SIZE - len, secs);
  strcat(buf, AUX_HEAD);
  len += strlen(AUX_HEAD);
  len += interrogate_aux(buf + len, BUF_SIZE - len);
  udpbcast((byte*)buf, len, 12345, 54321);

  /* These function calls are required if ICMP packets are to be accepted */
  //rc = ether.packetLoop(ether.packetReceive()); // today we do not accept nuthin

  return;
}

