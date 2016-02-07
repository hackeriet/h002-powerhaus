/* PowerHaus - comotion@hackeriet.no - 2015-02-13
 *  Added LLDP 2016-01-19
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
#undef VERBOSE
#undef LLDP
#define VERSION "2016-01-19"
#define NAME "powerhaus0"
#define HOST NAME".hackeriet.no"
#define DESCRIPTION "POWERHAUS kakesmurf zool, Pulse counting and CT power monitor, v"VERSION;
#ifdef VERBOSE
#define VLOG(x) Serial.println(x)
#else
#define VLOG(x)
#endif

#define BUF_SIZE 512
#define HEADER HOST" pulses/min:"
#define AUX_HEAD " CTpower: "
#define SAMPLE_DELAY 5 // total sample time = 2s

byte mymac[] = { 
  0x90, 0x13, 0x37, 0x04, 0x20, 0xcc };

byte Ethernet::buffer[BUF_SIZE];

#define CS_PIN 8
#define ERR_PIN 13

int res = 0;

void error_blink(int times)
{
  int period = 3000;
  for(int i = 0; i < times; i ++) { 
      digitalWrite(ERR_PIN, HIGH);
      delay(period/times/2);
      digitalWrite(ERR_PIN, LOW);
      delay(period/times/2);
  }
}
void initialize_ethernet(void){  
  for(;;){ // keep trying until you succeed 
    //Reinitialize ethernet module
    VLOG("Resetting Ethernet");
    pinMode(CS_PIN, OUTPUT);
    error_blink(2);

    if (ether.begin(sizeof Ethernet::buffer, mymac, CS_PIN) == 0){ 
      VLOG( "Failed to access Ethernet controller");
      error_blink(3);
      continue;
    }

    if (!ether.dhcpSetup(NAME, true)){
      VLOG("DHCP failed");
      error_blink(6);
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


#ifdef LLDP
void sendLLDP(void)
{
  Serial.println("sending LLDP");
  byte *p = ether.buffer;
  char lldpmac[] = { 0x01, 0x80, 0xc2, 0x00, 0x00, 0x00 };
  int16_t ethertype = 0x88cc;    // TLs are 7 bit type, 9 bit len
  int16_t chassisTL = 0x0207;    // type 1, len 7
  int16_t portTL = 0x0407;       // type 2, len 7
  int32_t  ttlTLV = 0x06020078;  // type 3, len 2, 120s
  int16_t portdescTL = 0x0809;   // type 4, len 9
  char portdesc[] = NAME;
  int16_t sysnameTL = 0x0a13;    // type 10, len 19
  char sysname[] = HOST;
  char sysdesc[] = DESCRIPTION;
  // multicast ends with 0e ? bcast 03?
  memcpy(p, lldpmac, sizeof(lldpmac));
  p += sizeof(lldpmac);
  memcpy(p, mymac, sizeof(mymac));
  p += sizeof(mymac);
  memcpy(p, &ethertype, sizeof(ethertype));
  p += sizeof(ethertype);
  memcpy(p, &chassisTL, sizeof(chassisTL));
  p += sizeof(chassisTL);
  *p++ = 0x05; //chassis id subtype networkAddress
  memcpy(p, EtherCard::myip, 4);
  p += 4;
  memcpy(p, &portTL, sizeof(portTL));
  *p++ = 0x03; //port id subtype MAC address
  memcpy(p, mymac, sizeof(mymac));
  p += sizeof(mymac);
  memcpy(p, &ttlTLV, sizeof(ttlTLV));
  p += sizeof(ttlTLV);
  memcpy(p, &portdescTL, sizeof(portdescTL));
  p += sizeof(portdescTL);
  memcpy(p, portdesc, sizeof(portdesc));
  p += sizeof(portdesc);
  memcpy(p, &sysnameTL, sizeof(sysnameTL));
  p += sizeof(sysnameTL);
  memcpy(p, sysname, sizeof(sysname));
  p += sizeof(sysname);
  memcpy(p, sysdesc, sizeof(sysdesc));
  p += sizeof(sysdesc);
  *p++ = 0x00; *p++ = 0x00; // end of LLDPDU
  EtherCard::packetSend(p - ether.buffer);
}

#endif
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

  // ICMP, DHCP renew, etc.
  rc = ether.packetLoop(ether.packetReceive());
  #ifdef LLDP
  sendLLDP();
#endif
  return;
}

