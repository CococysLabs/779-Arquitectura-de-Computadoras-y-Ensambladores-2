# 📊 Interpretación de Datos Analógicos en Arduino mediante Rangos

**Curso:** Arquitectura de Computadoras y Ensambladores 2  
**Tema:** Conversión Analógico-Digital (ADC), Dato vs. Información, Umbrales.  
**Tiempo estimado:** 25 min

## 🎯 Objetivo

Comprender la diferencia entre un **dato** (valor numérico crudo del ADC) y **información** (interpretación del dato en un contexto). Demostrar cómo clasificar lecturas de sensores en rangos (Bajo, Medio, Alto) para la toma de decisiones.

## 🛠️ Recursos Necesarios

* **Placa:** Arduino Uno.
* **Componentes:**
  * 1x Potenciómetro (10kΩ) o Sensor analógico (ej. LDR, TMP36).
  * Cables de conexión (jumpers).
* **Software:** Arduino IDE o Tinkercad Circuits.

## 🔌 Diagrama de Conexión (Usando Potenciómetro)

1. **Terminal 1 del Potenciómetro:** A **5V** (o 3.3V).
2. **Terminal 2 del Potenciómetro:** A **GND**.
3. **Terminal Central (Wiper):** Al **Pin Analógico A0**.

## 💻 Código Fuente (Arduino)

```cpp
// Pin de entrada analógica
const int PIN_SENSOR = A0;

// Umbrales para clasificación (Rango ADC: 0 a 1023)
const int UMBRAL_BAJO = 341;
const int UMBRAL_MEDIO = 682;

void setup() {
  Serial.begin(9600);
  Serial.println("--- Inicio de Lectura Analógica ---");
  Serial.println("Gire el potenciometro para cambiar el valor.");
}

void loop() {
  // 1. Obtener el DATO (Lectura cruda del ADC)
  int lecturaCruda = analogRead(PIN_SENSOR);
  
  // 2. Interpretar el DATO para generar INFORMACIÓN
  String nivel = "";
  
  if (lecturaCruda < UMBRAL_BAJO) {
    nivel = "BAJO";
  } 
  else if (lecturaCruda < UMBRAL_MEDIO) {
    nivel = "MEDIO";
  } 
  else {
    nivel = "ALTO";
  }
  
  // 3. Representar el resultado (Salida)
  Serial.print("Dato (ADC): ");
  Serial.print(lecturaCruda);
  Serial.print("  |  Informacion: Nivel ");
  Serial.println(nivel);
  
  delay(500); // Pausa breve para facilitar la lectura en el monitor serie
}
