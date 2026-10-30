/*
 * Semana 6 · Demo: dos tareas independientes con FreeRTOS en el ESP32
 * Arquitectura de Computadoras y Ensambladores 2 · Laboratorio
 *
 * El ESP32 ya trae FreeRTOS: el loop() de Arduino corre dentro de una tarea.
 * Aquí se crean dos tareas más que funcionan "en paralelo" sin bloquearse:
 *   - tareaLED: parpadea el LED integrado cada 500 ms
 *   - tareaSensor: lee el pin 34 cada 1000 ms
 */

const int PIN_LED = 2;      // LED integrado en la mayoría de placas ESP32
const int PIN_SENSOR = 34;

void tareaLED(void *param) {
  pinMode(PIN_LED, OUTPUT);
  bool estado = false;
  for (;;) {                          // cada tarea es un ciclo infinito
    estado = !estado;
    digitalWrite(PIN_LED, estado);
    vTaskDelay(pdMS_TO_TICKS(500));   // cede la CPU a otras tareas mientras espera
  }
}

void tareaSensor(void *param) {
  for (;;) {
    Serial.printf("[%lu ms] sensor = %d\n", millis(), analogRead(PIN_SENSOR));
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void setup() {
  Serial.begin(115200);
  //          función      nombre    pila   parámetro prioridad handle
  xTaskCreate(tareaLED,    "LED",    2048,  NULL,     1,        NULL);
  xTaskCreate(tareaSensor, "Sensor", 2048,  NULL,     1,        NULL);
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));    // loop() no hace nada: el trabajo está en las tareas
}
