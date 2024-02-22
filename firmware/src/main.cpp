// Define imports and definitions for different build targets

// D1 Mini
#ifdef TARGET_D1_MINI
    #include <ESP8266WiFi.h>

    #define LEDON LOW
    #define LEDOFF HIGH
#endif

// S2 Mini
#ifdef TARGET_S2_MINI
    #include <WiFi.h>
    #include <WiFiClient.h>

    #define LEDON HIGH
    #define LEDOFF LOW
    #define S2BATTERYPIN 1
#endif

// Universl imports
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCData.h>
#include <ArduinoOTA.h>

// User-configurable settings:
#define DEBUG 1                     // Enable or disable serial debugging output
#define USE_STATIC_IP 0             // Set to 0 to use dhcp, otherwise set to 1 and define your static ip below

// Default settings, classes and variables
#define INTERNAL_LED LED_BUILTIN            // Indicates if connected with server
#define OSC_IN_PORT 8888                    // Local osc receive port on the esp
unsigned int remotePort = 0;                // Once available saves the remote server port we reply to
unsigned long lastPacketRecv = millis();    // The time in millis when the last valid osc packet was received
unsigned long lastHeartbeatSent = 0;        // The last time in millis when a heartbeat message was sent
bool hasConnection = false;                 // Keep state if there is an active connection (data coming in)
bool enableOTA = true;                      // If ota should currently be enabled
byte mac[6];                                // The wifi mac adress of the devices (used for identification of the device)
char hostname[11];                          // A human-friendly hotname with the 2nd half of the hardware mac
byte numMotors = 0;                         // The total number of motors attached to this hardware

OSCErrorCode oscError;
WiFiUDP Udp;

#if USE_STATIC_IP
    IPAddress staticIP(10,3,1,5);
    IPAddress gateway(10,1,1,1);
    IPAddress subnet(255,0,0,0);
#endif

// Pin definitions for each build target
#ifdef TARGET_D1_MINI
    // TODO: find usable pins on d1 mini
    byte motorPins[] = {D1, D2};
#endif
#ifdef TARGET_S2_MINI
    // These are the pins used on the "official-dev" pcb
    byte motorPins[] = {2, 3, 4, 5, 6, 7, 8};
#endif


void setup() {
    // Wait for serial with timeout
    #ifdef TARGET_S2_MINI
        while (!Serial && millis()<5000) {}
    #endif

    // Initialize output pins, we assume they are all valid and can drive pwm
    numMotors = sizeof(motorPins) / sizeof(motorPins[0]);
    for (byte i=0; i<numMotors; i++) {
        pinMode(motorPins[i], OUTPUT);
    }
    // Set led output mode
    pinMode(INTERNAL_LED, OUTPUT);

    // Set adc mode for each build target
    #ifdef ARDUINO_ARCH_ESP8266
        ADC_MODE(ADC_VCC);
    #endif
    #ifdef TARGET_S2_MINI
        pinMode(S2BATTERYPIN, INPUT);
    #endif

    // Startup Serial
    Serial.begin(115200);

    // Configure wifi
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);

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

    // Once connected, print out some information and create mac and hostname

    WiFi.macAddress(mac);
    sprintf(hostname, "ppp-%02x%02x%02x", mac[3], mac[4], mac[5]);
    WiFi.setHostname(hostname);
    Serial.print(F("\nIP address: "));
    Serial.println(WiFi.localIP());
    Serial.print(F("Hostname "));
    Serial.println(hostname);
    Serial.println(F("Starting UDP OSC Receiver"));

    // Setup OTA
    ArduinoOTA.setPassword("taptaptap");
    ArduinoOTA
        .onStart([]() {
            String type;
            if (ArduinoOTA.getCommand() == U_FLASH)
                type = "sketch";
            else // U_SPIFFS
                type = "filesystem";

            Serial.println("Start OTA updating " + type);
        })
        .onEnd([]() {
            Serial.println("\nEnd");
        })
        .onProgress([](unsigned int progress, unsigned int total) {
            Serial.printf("OTA Progress: %u%%\r", (progress / (total / 100)));
        })
        .onError([](ota_error_t error) {
            Serial.printf("Error[%u]: ", error);
            if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
            else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
            else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
            else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
            else if (error == OTA_END_ERROR) Serial.println("End Failed");
        });
    ArduinoOTA.begin();

    // Start the udp socket
    Udp.begin(OSC_IN_PORT);
}

void handle_osc_motors(OSCMessage &msg) {
    // Get length of osc message
    byte msize = msg.size();
    for (byte i=0; i<msize; i++) {
        // Safeguard from overwriting into void
        if (i >= numMotors) break;
        // Get value for each pin and write to motors
        byte val = msg.getInt(i);
        analogWrite(motorPins[i], val);
        #if DEBUG
            Serial.print(val);
            Serial.print(",");
        #endif
    }
    // Enable the onbord led
    digitalWrite(INTERNAL_LED, LEDON);
    #if DEBUG
    Serial.println();
    #endif
}

void handle_osc_discover(OSCMessage &msg) {
    // If connection was established once, do not send reply
    if (remotePort > 0) return;

    Serial.println(F("Discovery request received while not connected"));

    // Save the remote port for use later
    remotePort = Udp.remotePort() + 1;

    // Create and send discovery response
    OSCMessage discoverReply("/patpatpat/noticeme/senpai");
    discoverReply.add(WiFi.macAddress().c_str());
    discoverReply.add(hostname);
    discoverReply.add(numMotors);
    Udp.beginPacket(Udp.remoteIP(), remotePort);
    discoverReply.send(Udp);
    Udp.endPacket();
    discoverReply.empty();

    #if DEBUG
    Serial.println("Sent discovery reply");
    #endif

    // Blink LED once
    digitalWrite(INTERNAL_LED, LEDON);
    delay(200);
    digitalWrite(INTERNAL_LED, LEDOFF);
}

void handleOTA() {
    if (enableOTA) {
        // Disable PTA after 5 minutes
        if (millis() > 360000) {
            enableOTA = false;
            Serial.println("OTA was disabled by timeout.");
        }
        ArduinoOTA.handle();
    }
}

void loop() {
    handleOTA();

    // Read data from udp socket
    unsigned int udpPacketSize = Udp.parsePacket();

    // Check if there is data to parse
    if (udpPacketSize > 0) {
        // Create new osc message from buffer
        OSCMessage msg;
        while (udpPacketSize--) {
            msg.fill(Udp.read());
        }

        // Check message state
        if (msg.hasError()) {
            oscError = msg.getError();
            Serial.print(F("osc message error: "));
            Serial.println(oscError);
        } else {
            // Save timestamp of last valid packet
            lastPacketRecv = millis();
            // Handle osc message
            msg.dispatch("/m", handle_osc_motors);
            msg.dispatch("/patpatpat/discover", handle_osc_discover);
            hasConnection = true;
        }

    }

    // Handle heartbeat sending if connection is active and 4 seconds since the last one have passed
    if (hasConnection && millis()-lastHeartbeatSent >= 3997) {
        // Create heartbeat message
        OSCMessage heartbeatMessage("/patpatpat/heartbeat");
        heartbeatMessage.add(WiFi.macAddress().c_str());
        heartbeatMessage.add((int)millis()/1000);

        // This will be replaced with reading the external battery voltage later
        #ifdef ARDUINO_ARCH_ESP8266
            heartbeatMessage.add(ESP.getVcc());
        #else
            heartbeatMessage.add(analogRead(S2BATTERYPIN));
        #endif

        heartbeatMessage.add(WiFi.RSSI());
        Udp.beginPacket(Udp.remoteIP(), remotePort);
        heartbeatMessage.send(Udp);
        Udp.endPacket();
        heartbeatMessage.empty();

        #if DEBUG
        Serial.print("Sent heartbeat. Delta @ ");
        Serial.println(millis() - lastHeartbeatSent);
        #endif

        lastHeartbeatSent = millis();
    }

    // Disable led and save state when we got no packets in the last 1000ms
    if (millis()-lastPacketRecv > 1000) {
        hasConnection = false;
        digitalWrite(INTERNAL_LED, LEDOFF);
        // Set all motors to stop
        for (byte i=0; i<numMotors; i++) {
            analogWrite(motorPins[i], 0);
        }
    }    
}