#include <ESP8266mDNS.h>        // Include the mDNS library
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCBundle.h>
#include <OSCData.h>

#define INTERNAL_LED 2 // indicates if connected with server (low active)

#define OSC_IN_PORT 8888    // local osc receive port
#define OSC_SEND_TARGET_PORT 8888   // port of patstrap server

WiFiUDP Udp;
OSCErrorCode error;
unsigned int ledState = LOW;              // LOW means led is *on*

static unsigned int keep_alive = 0;

void setup() {
    pinMode(INTERNAL_LED, OUTPUT);

    Serial.begin(115200);


    WiFi.mode(WIFI_STA);
    #if defined(WIFI_CREDS_SSID) && defined(WIFI_CREDS_PASSWD)
        WiFi.begin(WIFI_CREDS_SSID, WIFI_CREDS_PASSWD); //Connect to wifi
    #else
        #error "Missing defines WIFI_CREDS_SSID and WIFI_CREDS_PASSWD"
    #endif
    
    // Wait for connection  
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

void led(OSCMessage &msg) {
    ledState = msg.getInt(0);
    digitalWrite(INTERNAL_LED, ledState);
    Serial.print("/led: ");
    Serial.println(ledState);
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
            msg.dispatch("/led", led);
        } else {
            error = msg.getError();
            Serial.print("error: ");
            Serial.println(error);
        }
    }
}