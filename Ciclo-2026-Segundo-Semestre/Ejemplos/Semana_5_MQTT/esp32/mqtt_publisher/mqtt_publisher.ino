/*
 * Semana 5 · ESP32 publicando lecturas por MQTT
 * Arquitectura de Computadoras y Ensambladores 2 · Laboratorio
 *
 * Librería: "MQTT" de Joel Gaehwiler (arduino-mqtt). Instálala desde el
 * Administrador de librerías del Arduino IDE. Se usa en lugar de PubSubClient
 * porque permite PUBLICAR con QoS 1 (PubSubClient solo publica con QoS 0).
 *
 * Desde el Monitor Serie (115200) escribe:
 *   0  → publicar con QoS 0
 *   1  → publicar con QoS 1
 */

#include <WiFi.h>
#include <MQTT.h>

// ---------------- Configuración ----------------
const char* WIFI_SSID   = "TU_RED";
const char* WIFI_CLAVE  = "TU_CLAVE";
const char* BROKER_IP   = "192.168.1.10";   // IP de la computadora donde corre Docker
const int   BROKER_PUERTO = 1883;
const char* TOPICO      = "usac/arqui2/grupo1/temperatura";   // cambia grupo1 por tu grupo

const int PIN_SENSOR = 34;            // sensor analógico (o déjalo al aire para valores variados)
const bool MODO_SIMULADO = true;      // false = leer el pin analógico
const unsigned long INTERVALO_MS = 2000;

// ---------------- Estado ----------------
WiFiClient red;
MQTTClient cliente(256);   // tamaño del buffer en bytes
int qos = 0;
unsigned long ultimoEnvio = 0;
unsigned long contador = 0;

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("Conectando a WiFi");
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nIP del ESP32: ");
  Serial.println(WiFi.localIP());
}

void conectarBroker() {
  // Identificador único por placa, basado en su dirección MAC
  String id = "esp32-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  Serial.print("Conectando al broker " + String(BROKER_IP));
  while (!cliente.connect(id.c_str())) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConectado como " + id);
}

float leerTemperatura() {
  if (MODO_SIMULADO) {
    return 24.0 + 3.0 * sin(contador / 5.0) + random(-30, 31) / 100.0;
  }
  // Escala la lectura 0..4095 a un rango de 15 °C a 35 °C (ajústalo a tu sensor)
  return 15.0 + analogRead(PIN_SENSOR) / 4095.0 * 20.0;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  conectarWiFi();
  cliente.begin(BROKER_IP, BROKER_PUERTO, red);
  conectarBroker();
  Serial.println("Escribe 0 o 1 en el Monitor Serie para cambiar el QoS");
}

void loop() {
  cliente.loop();   // mantiene viva la conexión y procesa confirmaciones
  delay(10);

  if (WiFi.status() != WL_CONNECTED) conectarWiFi();
  if (!cliente.connected()) conectarBroker();

  // Cambiar QoS desde el Monitor Serie
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '0' || c == '1') {
      qos = c - '0';
      Serial.printf(">> Ahora se publica con QoS %d\n", qos);
    }
  }

  if (millis() - ultimoEnvio >= INTERVALO_MS) {
    ultimoEnvio = millis();
    float temp = leerTemperatura();

    char payload[96];
    snprintf(payload, sizeof(payload), "{\"n\":%lu,\"temp\":%.2f,\"qos\":%d}", contador, temp, qos);

    // Con QoS 1, publish() espera el PUBACK del broker antes de devolver true
    unsigned long t0 = millis();
    bool ok = cliente.publish(TOPICO, payload, false, qos);
    unsigned long ms = millis() - t0;

    Serial.printf("PUBLISH n=%lu qos=%d -> %s (%lu ms)  %s\n", contador, qos,
                  ok ? (qos == 1 ? "PUBACK recibido" : "enviado") : "FALLO", ms, payload);
    contador++;
  }
}
