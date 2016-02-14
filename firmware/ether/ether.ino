#include <EtherCard.h>

#define BUF_SIZE 512

byte mymac[] = { 0x90, 0x13, 0x37, 0x04, 0x20, 0xcc };

byte Ethernet::buffer[BUF_SIZE];

#define CS_PIN 8

int res = 0;
void initialize_ethernet(void){  
  for(;;){ // keep trying until you succeed 
    //Reinitialize ethernet module
    pinMode(CS_PIN, OUTPUT);
    Serial.println("Resetting Ethernet...");
    digitalWrite(CS_PIN, LOW);
    delay(1000);
    digitalWrite(CS_PIN, HIGH);
    delay(500);

    if (ether.begin(sizeof Ethernet::buffer, mymac, CS_PIN) == 0){ 
      Serial.println( "Failed to access Ethernet controller");
      continue;
    }
    
    Serial.println("DHCP");
    if (!ether.dhcpSetup("powerhaus0", true)){
      Serial.println("DHCP failed");
      continue;
    }

    ether.printIp("IP:   ", ether.myip);
    ether.printIp("GW:   ", ether.gwip);  
    ether.printIp("DNS:  ", ether.dnsip);  
    ether.printIp("Bcast:", ether.broadcastip);

    //reset init value
    res = 0;
    break;
  }
}

void setup(void)
{
    Serial.begin(57600);
    delay(2000);
    
    initialize_ethernet();
}

static void udpbcast(byte *buf, int pos, short srcport, short dstport )
{
  ether.sendUdp((char*) buf, pos, srcport, ether.broadcastip, dstport);
}
void loop(void)
{
    word rc;
    char *data = "powerhaus0.kakesmurf.zool: ";
    /* These function calls are required if ICMP packets are to be accepted */
 //   rc = ether.packetLoop(ether.packetReceive());
    udpbcast((byte*)data, strlen(data), 12345, 54321);
    Serial.print("ether.packetLoop() returned ");
    Serial.println(rc, DEC);

    // For debugging
    delay(5000);

    return;
}
