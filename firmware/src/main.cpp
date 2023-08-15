#ifdef ARDUINO_ARCH_ESP8266
    #include <ESP8266mDNS.h>        // Include the mDNS library
    #include <ESP8266WiFi.h>
#endif
#ifdef ARDUINO_ARCH_ESP32
    #include <WiFi.h>
    #include <ESPmDNS.h>
    #include <WiFiClient.h>
#endif
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCData.h>

#define INTERNAL_LED LED_BUILTIN // indicates if connected with server (low active)
#define OSC_IN_PORT 8888    // local osc receive port
#define VRC_UDP_PORT 9001   // reusing the vrc osc receiver so we need that port
#define USE_STATIC_IP 0     // Set to 0 to use dhcp, otherwise set to 1 and define your static ip below

WiFiUDP Udp;
OSCErrorCode error;
unsigned int ledState = LOW;
byte numMotors = 0;
unsigned long lastPacketRecv = millis();
unsigned long lastHeartbeatSend = 0;

// Only needed if you want to use a static ip
#if USE_STATIC_IP
    IPAddress staticIP(10,3,1,5);
    IPAddress gateway(10,1,1,1);
    IPAddress subnet(255,0,0,0);
#endif

#ifdef ARDUINO_ARCH_ESP8266
    // The only setting that should need adjustment aside from wifi stuff
    byte motorPins[] = {D1, D2};
#endif
#ifdef ARDUINO_ARCH_ESP32
    // The only setting that should need adjustment aside from wifi stuff
    byte motorPins[] = {2, 3};
#endif

#ifdef ARDUINO_ARCH_ESP8266
    // Set adc mode to read the internal voltage
    ADC_MODE(ADC_VCC);
#endif

void setup() {
    // Initialize outputs, we assume they are all valid and can drive pwm
    numMotors = sizeof(motorPins) / sizeof(motorPins[0]);
    for (byte i=0; i<numMotors; i++) {
        pinMode(motorPins[i], OUTPUT);
    }
    pinMode(INTERNAL_LED, OUTPUT);

    // Startup Serial
    Serial.begin(115200);

    WiFi.mode(WIFI_STA);
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
        digitalWrite(INTERNAL_LED, LOW);
        Serial.print(".");
        delay(100);
        digitalWrite(INTERNAL_LED, HIGH);
    }

    Serial.print(F("\nIP address: "));
    Serial.println(WiFi.localIP());  

    // Start the mDNS responder for patpatpat.local
    if (!MDNS.begin("patpatpat")) {
        Serial.println(F("Error setting up MDNS responder!"));
    }
    MDNS.addService("osc", "udp", OSC_IN_PORT);
    Serial.println(F("mDNS responder started"));
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

void loop() {
    #ifdef ARDUINO_ARCH_ESP8266
        MDNS.update();
    #endif
    
    int size = Udp.parsePacket();

    if (size > 0) {
        OSCMessage msg;
        while (size--) {
            msg.fill(Udp.read());
        }
        if (!msg.hasError()) {
            // drive motors
            msg.dispatch("/m", osc_motors);

            // handle heartbeat sending
            lastPacketRecv = millis();
            if (millis() - lastHeartbeatSend >= 1000) {
                digitalWrite(INTERNAL_LED, LOW);
                OSCMessage txmsg("/patpatpat/heartbeat");
                txmsg.add(WiFi.macAddress().c_str());
                txmsg.add((int)millis()/1000);
                // This will be replaced with reading the external battery voltage later
                #ifdef ARDUINO_ARCH_ESP8266
                    txmsg.add(ESP.getVcc());
                #else
                    txmsg.add(0);
                #endif
                txmsg.add(WiFi.RSSI());
                Udp.beginPacket(Udp.remoteIP(), VRC_UDP_PORT);
                txmsg.send(Udp);
                Udp.endPacket();
                txmsg.empty();
                lastHeartbeatSend = millis();
            }
        } else {
            error = msg.getError();
            Serial.print(F("error: "));
            Serial.println(error);
        }
    }

    // Disable led when we got no packets in the last 1.5s
    if (millis()-lastPacketRecv > 600) {
        digitalWrite(INTERNAL_LED, HIGH);
        // Make sure the motors don't keep running on connection loss
        for (byte i=0; i<numMotors; i++) {
            analogWrite(motorPins[i], 0);
        }
    }
}