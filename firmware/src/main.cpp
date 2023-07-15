#include <ESP8266mDNS.h>        // Include the mDNS library
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCData.h>

#define INTERNAL_LED 2 // indicates if connected with server (low active)
#define OSC_IN_PORT 8888    // local osc receive port
#define VRC_UDP_PORT 9001   // reusing the vrc osc receiver so we need that port

WiFiUDP Udp;
OSCErrorCode error;
unsigned int ledState = LOW;
byte numMotors = 0;
unsigned long lastPacketRecv = millis();
unsigned long lastHeartbeatSend = 0;

// The only setting that should need adjustment aside from wifi stuff
byte motorPins[] = {INTERNAL_LED, 3};

void setup() {
    // Initialize outputs, we assume they are all valid and can drive pwm
    numMotors = sizeof(motorPins) / sizeof(motorPins[0]);
    for (byte i=0; i<numMotors; i++) {
        pinMode(motorPins[i], OUTPUT);
    }

    // Startup Serial
    Serial.begin(115200);

    WiFi.mode(WIFI_STA);
    #if defined(WIFI_CREDS_SSID) && defined(WIFI_CREDS_PASSWD)
        WiFi.begin(WIFI_CREDS_SSID, WIFI_CREDS_PASSWD); //Connect to wifi
    #else
        #error "Missing defines WIFI_CREDS_SSID and WIFI_CREDS_PASSWD"
    #endif
    
    // Wait for wifi connection  
    Serial.println("Connecting to Wifi");
    while (WiFi.status() != WL_CONNECTED) {   
        delay(100);
        digitalWrite(INTERNAL_LED, LOW);
        Serial.print(".");
        delay(100);
        digitalWrite(INTERNAL_LED, HIGH);
    }

    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());  

    // Start the mDNS responder for patstrap.local
    if (!MDNS.begin("patstrap")) {
        Serial.println("Error setting up MDNS responder!");
    }
    MDNS.addService("osc", "udp", OSC_IN_PORT);
    Serial.println("mDNS responder started");
    Serial.println("Starting UDP");
    Udp.begin(OSC_IN_PORT);
}

void osc_motors(OSCMessage &msg) {
    // Get length of osc message and read values
    byte msize = msg.size();
    for (byte i=0; i<msize; i++) {
        byte val = msg.getInt(i);
        analogWrite(motorPins[i], val);
        Serial.print(val);
        Serial.print(",");
    }
    Serial.println();
}

void loop() {
    MDNS.update();
    
    OSCMessage msg;
    int size = Udp.parsePacket();

    if (size > 0) {
        while (size--) {
            msg.fill(Udp.read());
        }
        if (!msg.hasError()) {
            // drive motors
            msg.dispatch("/m", osc_motors);

            // handle heartbeat sending
            lastPacketRecv = millis();
            if (millis() - lastHeartbeatSend >= 1000) {
                lastHeartbeatSend = millis();
                OSCMessage txmsg("/patstrap/heartbeat");
                txmsg.add((double)millis());
                Udp.beginPacket(Udp.remoteIP(), VRC_UDP_PORT);
                txmsg.send(Udp);
                Udp.endPacket();
                txmsg.empty();
            }
        } else {
            error = msg.getError();
            Serial.print("error: ");
            Serial.println(error);
        }
    }
}