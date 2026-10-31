/*
  Semana 8: Automatización y Edge
  Responsable del material: Wendy Mazariegos
  Placa: Arduino Uno R3 (5 V).
  Por defecto recibe temperaturas simuladas por el Monitor serie.
  Para leer un TMP36 conectado a A0, cambia USAR_TMP36 a true.
  No requiere red, nube ni librerías adicionales.
*/
#include <Arduino.h>
#include <stdlib.h>
#include <math.h>

const bool USAR_TMP36 = false;
const byte PIN_SENSOR = A0;
const byte PIN_SALIDA = 8;  // HIGH activa un módulo de salida compatible.
const float TEMPERATURA_ENCENDIDO = 30.0;
const float TEMPERATURA_APAGADO = 28.0;
const float REFERENCIA_ADC = 5.0; // Valor nominal del Uno R3; ajustar si se calibra.
bool ventiladorEncendido = false;
char entrada[24];
byte longitud = 0;
bool entradaDemasiadoLarga = false;
unsigned long ultimaLectura = 0;

void procesarTemperatura(float temperatura) {
  if (temperatura >= TEMPERATURA_ENCENDIDO) {
    ventiladorEncendido = true;
  } else if (temperatura <= TEMPERATURA_APAGADO) {
    ventiladorEncendido = false;
  }
  // En el intervalo abierto (28, 30) se conserva el estado anterior.
  digitalWrite(PIN_SALIDA, ventiladorEncendido ? HIGH : LOW);
  digitalWrite(LED_BUILTIN, ventiladorEncendido ? HIGH : LOW);
  Serial.print(temperatura, 1);
  Serial.print(F(" C | D8="));
  Serial.print(ventiladorEncendido ? F("HIGH") : F("LOW"));
  Serial.println(ventiladorEncendido ? F(" | Ventilador ENCENDIDO") : F(" | Ventilador APAGADO"));
}

void leerMonitorSerie() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      entrada[longitud] = '\0';
      char *fin;
      float temperatura = strtod(entrada, &fin);
      if (!entradaDemasiadoLarga && fin != entrada && *fin == '\0' &&
          isfinite(temperatura) && temperatura >= -40 && temperatura <= 125) {
        procesarTemperatura(temperatura);
      } else {
        Serial.println(F("Entrada invalida: envia un numero entre -40 y 125, con punto decimal."));
      }
      longitud = 0;
      entradaDemasiadoLarga = false;
    } else if (longitud < sizeof(entrada) - 1) {
      entrada[longitud++] = c;
    } else {
      entradaDemasiadoLarga = true;
    }
  }
}

void setup() {
  digitalWrite(PIN_SALIDA, LOW);
  pinMode(PIN_SALIDA, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
  Serial.println(F("Semana 8 - Wendy Mazariegos"));
  Serial.println(USAR_TMP36 ? F("Modo sensor TMP36 en A0") : F("Modo simulado: envia 24, 29, 30, 32, 29, 28, una lectura por linea."));
}

void loop() {
  if (USAR_TMP36) {
    unsigned long ahora = millis();
    if (ahora - ultimaLectura >= 1000) {
      ultimaLectura = ahora;
      float voltaje = analogRead(PIN_SENSOR) * REFERENCIA_ADC / 1024.0;
      float temperatura = (voltaje - 0.5) * 100.0;
      procesarTemperatura(temperatura);
    }
  } else {
    leerMonitorSerie();
  }
}
