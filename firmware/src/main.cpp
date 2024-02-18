#ifdef TARGET_D1_MINI
    #include <ESP8266WiFi.h>
    #define LEDON LOW
    #define LEDOFF HIGH
#endif
#ifdef TARGET_S2_MINI
    #include <WiFi.h>
    #include <WiFiClient.h>
    #define LEDON HIGH
    #define LEDOFF LOW
    #define s2batteryPin 1
#endif
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCData.h>

#define INTERNAL_LED LED_BUILTIN    // indicates if connected with server
#define OSC_IN_PORT 8888            // local osc receive port
#define VRC_UDP_PORT 9001           // reusing the vrc osc receiver so we need that port
#define USE_STATIC_IP 0             // Set to 0 to use dhcp, otherwise set to 1 and define your static ip below

WiFiUDP Udp;
OSCErrorCode error;
unsigned int ledState = LOW;
byte numMotors = 7;
unsigned long lastPacketRecv = millis();
unsigned long lastHeartbeatSend = 0;
unsigned int remotePort = 0;
bool hasConnection = false;

// Only needed if you want to use a static ip
#if USE_STATIC_IP
    IPAddress staticIP(10,3,1,5);
    IPAddress gateway(10,1,1,1);
    IPAddress subnet(255,0,0,0);
#endif

#ifdef TARGET_D1_MINI
    // TODO: find usable pins on d1 mini
    byte motorPins[] = {D1, D2};
#endif
#ifdef TARGET_S2_MINI
    // These are the pins used on the "official" pcb
    byte motorPins[] = {2, 3, 4, 5, 6, 7, 8};
#endif

#ifdef ARDUINO_ARCH_ESP8266
    // Set adc mode to read the internal voltage (esp8266 only)
    ADC_MODE(ADC_VCC);
#endif

void setup() {
    #ifdef TARGET_S2_MINI
        while (!Serial && millis()<5000) {}
    #endif
    // Initialize outputs, we assume they are all valid and can drive pwm
    numMotors = sizeof(motorPins) / sizeof(motorPins[0]);
    for (byte i=0; i<numMotors; i++) {
        pinMode(motorPins[i], OUTPUT);
    }
    pinMode(INTERNAL_LED, OUTPUT);

    #ifdef TARGET_S2_MINI
        pinMode(s2batteryPin, INPUT);
    #endif

    // Startup Serial
    Serial.begin(115200);

    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false); // Not sure if this is needed, testing because mdns discovery issues on esp32
    #if USE_STATIC_IP
        WiFi.config(staticIP, gateway, subnet);
    #endif
    #if defined(WIFI_CREDS_SSID) && defined(WIFI_CREDS_PASSWD)
        WiFi.begin(WIFI_CREDS_SSID, WIFI_CREDS_PASSWD); //Connect to wifi
    #else
        #error "Missing defines WIFI_CREDS_SSID and WIFI_CREDS_PASSWD"
    #endif
    
    // Wait for wifi connection  
    Serial.print(F("\n\nConnecting to Wifi "));
    while (WiFi.status() != WL_CONNECTED) {   
        delay(100);
        digitalWrite(INTERNAL_LED, LEDON);
        Serial.print(".");
        delay(100);
        digitalWrite(INTERNAL_LED, LEDOFF);
    }

    Serial.print(F("\nIP address: "));
    Serial.println(WiFi.localIP());

    byte mac [6];
    char hostname[11];
    WiFi.macAddress(mac);
    sprintf(hostname, "ppp-%02x%02x%02x", mac[3], mac[4], mac[5]);
    WiFi.setHostname(hostname);
    Serial.print(F("Hostname "));
    Serial.println(hostname);
    Serial.println(F("Starting UDP OSC Receiver"));
    Udp.begin(OSC_IN_PORT);
}

void osc_motors(OSCMessage &msg) {
    // Get length of osc message
    byte msize = msg.size();
    for (byte i=0; i<msize; i++) {
        // Get value for each pin and write to motors
        byte val = msg.getInt(i);
        analogWrite(motorPins[i], val);
        Serial.print(val);
        Serial.print(",");
    }
    Serial.println();
}

void handle_discover(OSCMessage &msg) {
    if (hasConnection) return;
    Serial.println("Discovery request received");

    // Send discovery response
    OSCMessage discoverReply("/patpatpat/noticeme/senpai");
    discoverReply.add(WiFi.macAddress().c_str());
    discoverReply.add(numMotors);
    Udp.beginPacket(Udp.remoteIP(), remotePort);
    discoverReply.send(Udp);
    Udp.endPacket();
    discoverReply.empty();
    Serial.println("Sent discovery reply");

    digitalWrite(INTERNAL_LED, LEDON);
}

void loop() {
    #ifdef ARDUINO_ARCH_ESP8266
        MDNS.update();
    #endif

    unsigned int size = Udp.parsePacket();

    if (size > 0) {
        OSCMessage msg;
        while (size--) {
            msg.fill(Udp.read());
        }
        
        if (!msg.hasError()) {
            remotePort = Udp.remotePort() + 1;
            // Serial.println("osc message is valid");
            lastPacketRecv = millis();
            // drive motors
            msg.dispatch("/m", osc_motors);
            msg.dispatch("/patpatpat/discover", handle_discover);
            hasConnection = true;
        } else {
            error = msg.getError();
            Serial.print(F("osc message error: "));
            Serial.println(error);
        }

    }

    // handle heartbeat sending
    if (hasConnection && millis() - lastHeartbeatSend >= 5000) {
        // Send Heartbeat
        OSCMessage txmsg("/patpatpat/heartbeat");
        txmsg.add(WiFi.macAddress().c_str());
        txmsg.add((int)millis()/1000);
        // This will be replaced with reading the external battery voltage later
        #ifdef ARDUINO_ARCH_ESP8266
            txmsg.add(ESP.getVcc());
        #else
            txmsg.add(analogRead(s2batteryPin));
        #endif
        // Serial.println(Udp.remoteIP());
        // Serial.println(remotePort);
        txmsg.add(WiFi.RSSI());
        Udp.beginPacket(Udp.remoteIP(), remotePort);
        txmsg.send(Udp);
        Udp.endPacket();
        txmsg.empty();
        Serial.println("Sent heartbeat");
        lastHeartbeatSend = millis();
    }

    // Disable led when we got no packets in the last 600ms
    if (millis()-lastPacketRecv > 600) {
        digitalWrite(INTERNAL_LED, LEDOFF);
        // Make sure the motors don't keep running on connection loss
        for (byte i=0; i<numMotors; i++) {
            analogWrite(motorPins[i], 0);
        }
    }
}