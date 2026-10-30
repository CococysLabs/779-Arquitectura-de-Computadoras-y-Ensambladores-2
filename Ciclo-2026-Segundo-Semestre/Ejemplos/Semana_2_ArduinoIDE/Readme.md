# 🚦 Demostración de Interrupciones Externas en Arduino (Botón y LED)

**Curso:** Arquitectura de Computadoras y Ensambladores 2  
**Tema:** Interrupciones externas, ISR y uso de `millis()`.  
**Tiempo estimado:** 25 min

## 🎯 Objetivo

Demostrar cómo un sistema embebido puede responder a eventos externos en tiempo real utilizando interrupciones (`attachInterrupt`), evitando el bloqueo del ciclo principal (`loop`) y diferenciando este método de la lectura secuencial (`digitalRead`).

## 🛠️ Recursos Necesarios

* **Placa:** Arduino Uno.
* **Componentes:**
  * 1x LED.
  * 1x Resistencia para LED (220Ω o 330Ω).
  * 1x Botón (Pushbutton).
  * Cables de conexión (jumpers).
* **Software:** Arduino IDE o Tinkercad Circuits.

## 🔌 Diagrama de Conexión

1. **LED:** Conectar el ánodo (pata larga) al **Pin Digital 13** a través de la resistencia, y el cátodo a **GND**.
2. **Botón:** Conectar un terminal del botón al **Pin Digital 2** y el otro terminal a **GND**.
   *(Nota: Se usará `INPUT_PULLUP` para aprovechar la resistencia interna del Arduino, evitando resistencias externas para el botón).*

## 💻 Código Fuente (Arduino)

```cpp
// Definición de pines
const int PIN_BOTON = 2;  // Pin 2 soporta interrupciones externas en Arduino Uno
const int PIN_LED = 13;

// Variable volátil: cambia dentro de la ISR y se lee en el loop
volatile bool estadoLed = false; 

// Variables para millis()
unsigned long tiempoAnterior = 0;
const long intervalo = 1000; // Imprimir cada 1 segundo

void setup() {
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);
  
  Serial.begin(9600);
  Serial.println("Sistema iniciado. Presione el boton.");

  // Asociar la interrupción externa
  // FALLING: Porque con INPUT_PULLUP el pin está en HIGH, y al presionar pasa a LOW
  attachInterrupt(digitalPinToInterrupt(PIN_BOTON), cambiarEstadoLed, FALLING);
}

void loop() {
  // Reflejar el estado lógico en la salida física
  digitalWrite(PIN_LED, estadoLed);

  // Verificación con millis() (Temporización sin bloqueo)
  unsigned long tiempoActual = millis();
  if (tiempoActual - tiempoAnterior >= intervalo) {
    tiempoAnterior = tiempoActual;
    Serial.print("Tiempo: ");
    Serial.print(tiempoActual / 1000);
    Serial.print("s | Estado del LED: ");
    Serial.println(estadoLed ? "ENCENDIDO" : "APAGADO");
  }
}

// Rutina de Servicio de Interrupción (ISR)
void cambiarEstadoLed() {
  estadoLed = !estadoLed; // Invierte el estado
}
