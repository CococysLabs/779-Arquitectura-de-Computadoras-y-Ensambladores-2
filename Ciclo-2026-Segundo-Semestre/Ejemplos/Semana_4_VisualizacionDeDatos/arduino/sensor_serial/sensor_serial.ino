/*
 * Semana 4 · Envío de lecturas por puerto serial
 * Arquitectura de Computadoras y Ensambladores 2 · Laboratorio
 *
 * Envía una línea por lectura con el formato:  valor,maximo
 *   ej. "2048,4095"  (ESP32, ADC de 12 bits)
 *       "512,1023"   (Arduino UNO R4, ADC de 10 bits por defecto)
 *
 * Enviar el máximo permite que Processing normalice la lectura
 * sin importar la placa que uses.
 *
 * Sin sensor: cambia MODO_SIMULADO a true.
 */

#if defined(ESP32)
const int PIN_SENSOR = 34;     // entrada analógica del ESP32 (solo entrada)
const int VALOR_MAX = 4095;
#else
const int PIN_SENSOR = A0;     // Arduino UNO R4 / UNO
const int VALOR_MAX = 1023;
#endif

const bool MODO_SIMULADO = false;
const unsigned long INTERVALO_MS = 50;   // 20 lecturas por segundo
const long BAUDIOS = 115200;              // debe coincidir con Processing

unsigned long ultimoEnvio = 0;

int leerSimulado() {
  // Onda suave + un poco de ruido para que se vea como un sensor real
  float t = millis() / 1000.0;
  float v = 0.5 + 0.35 * sin(t * 0.8) + random(-40, 41) / 1000.0;
  return constrain((int)(v * VALOR_MAX), 0, VALOR_MAX);
}

void setup() {
  Serial.begin(BAUDIOS);
#if !defined(ESP32)
  randomSeed(analogRead(A1));
#endif
}

void loop() {
  // Temporización con millis(): no bloquea el programa (repaso de semana 2)
  if (millis() - ultimoEnvio >= INTERVALO_MS) {
    ultimoEnvio = millis();

    int valor = MODO_SIMULADO ? leerSimulado() : analogRead(PIN_SENSOR);

    Serial.print(valor);
    Serial.print(',');
    Serial.println(VALOR_MAX);
  }
}
