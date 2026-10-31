/*
  Control de iluminacion: lazo abierto vs. lazo cerrado (PID)
  Laboratorio de Arquitectura de Computadoras y Ensambladores 2

  Hardware (Arduino Uno):
    D9 --- R 220 ohm --- anodo LED | catodo LED --- GND
    5V --- LDR ---+--- A0
                  |
                  R 10k ohm
                  |
                 GND

  Nota: con este divisor, mas luz significa una lectura mayor.
  En Wokwi, el modulo de LDR tiene polaridad inversa; si se desea
  leer el modulo real de Wokwi, cambiar LDR_INVERTIDA a true.
  Wokwi NO acopla opticamente el LED y la LDR; para un lazo de
  realimentacion reproducible usar el modo de planta virtual: sim on.

  Monitor serie: 115200 baudios, fin de linea 'Nueva linea'.
  Comandos: ayuda, abierto, cerrado, pwm 120, ref 450, calibrar,
            sim on, sim off, sombra, normal, estado.
  Salida CSV: tiempo_ms,modo,referencia,luz,pwm,error,p,i,d
  modo: 0 = abierto; 1 = cerrado
*/

#include <Arduino.h>
#include <stdio.h>
#include <string.h>

constexpr uint8_t PIN_LED = 9;
constexpr uint8_t PIN_LDR = A0;
constexpr unsigned long PERIODO_MS = 100;   // dt nominal = 0.1 s
constexpr bool LDR_INVERTIDA = false;        // true para modulo LDR de Wokwi

// Ganancias iniciales orientativas. Reajustar segun el circuito real.
float kp = 0.90f;
float ki = 0.35f;
float kd = 0.025f;

int referencia = 500;           // Se reemplaza con calibracion al iniciar
int pwmAbierto = 120;
int pwmActual = 120;
bool lazoCerrado = false;

// Modelo optico sencillo para Wokwi y pruebas sin LDR fisica.
// El regulador PID es exactamente el mismo en ambos casos.
bool plantaVirtual = false;
float luzVirtual = 360.0f;
float sombraVirtual = 0.0f;
constexpr float LUZ_AMBIENTE_VIRTUAL = 180.0f;
constexpr float GANANCIA_LED_VIRTUAL = 1.5f;
constexpr float CONSTANTE_TIEMPO_VIRTUAL = 0.6f;

float integral = 0.0f;
float derivadaFiltrada = 0.0f;
float ultimaLectura = 0.0f;
unsigned long ultimaMuestraMs = 0;

char bufferComando[48];
uint8_t longitudComando = 0;

int leerLuz() {
  if (plantaVirtual) return constrain((int)(luzVirtual + 0.5f), 0, 1023);
  int lectura = analogRead(PIN_LDR);
  return LDR_INVERTIDA ? 1023 - lectura : lectura;
}

float limitar(float valor, float minValor, float maxValor) {
  if (valor < minValor) return minValor;
  if (valor > maxValor) return maxValor;
  return valor;
}

void aplicarPwm(int salida) {
  pwmActual = constrain(salida, 0, 255);
  analogWrite(PIN_LED, pwmActual);
}

void reiniciarPID() {
  integral = 0.0f;
  derivadaFiltrada = 0.0f;
  ultimaLectura = (float)leerLuz();
}

void entrarEnLazoCerrado() {
  reiniciarPID();
  // Transferencia suave: conserva aproximadamente el PWM actual al
  // cambiar de lazo abierto a PID, evitando un salto innecesario.
  integral = limitar((float)pwmActual -
      kp * ((float)referencia - ultimaLectura), -255.0f, 255.0f);
  lazoCerrado = true;
}

float lecturaPromedio() {
  float suma = 0.0f;
  for (uint8_t n = 0; n < 10; ++n) {
    suma += leerLuz();
    delay(15);
  }
  return suma / 10.0f;
}

void calibrarSensor() {
  if (plantaVirtual) {
    // Los limites del modelo son conocidos: no se usan datos medidos.
    referencia = (int)(LUZ_AMBIENTE_VIRTUAL +
        0.60f * GANANCIA_LED_VIRTUAL * 255.0f + 0.5f);
    lazoCerrado = false;
    aplicarPwm(pwmAbierto);
    reiniciarPID();
    ultimaMuestraMs = millis();
    Serial.print(F("# Referencia de planta simulada="));
    Serial.println(referencia);
    return;
  }
  // Calibracion manual de limites medidos: esta es una accion puntual,
  // no se ejecuta dentro del ciclo periodico de control.
  Serial.println(F("# Calibrando: LED apagado y LED al maximo..."));
  aplicarPwm(0);
  delay(450);
  const float minLuz = lecturaPromedio();

  aplicarPwm(255);
  delay(450);
  const float maxLuz = lecturaPromedio();

  const float amplitud = maxLuz - minLuz;
  if (amplitud >= 25.0f) {
    referencia = (int)(minLuz + 0.60f * amplitud + 0.5f);
    Serial.println(F("# Calibracion correcta. Referencia: 60% del intervalo medido."));
  } else {
    referencia = (int)(minLuz + 0.5f);
    Serial.println(F("# AVISO: poca respuesta de la LDR al LED. Acerque el sensor al LED,"));
    Serial.println(F("# reduzca luz ambiente o compruebe el conexionado. En Wokwi es normal."));
  }

  Serial.print(F("# LED apagado=")); Serial.print(minLuz, 0);
  Serial.print(F("; LED maximo=")); Serial.print(maxLuz, 0);
  Serial.print(F("; referencia=")); Serial.println(referencia);

  lazoCerrado = false;
  aplicarPwm(pwmAbierto);
  reiniciarPID();
  ultimaMuestraMs = millis();
}

void imprimirAyuda() {
  Serial.println(F("# Comandos disponibles:"));
  Serial.println(F("#   abierto    : PWM fijo (lazo abierto)"));
  Serial.println(F("#   cerrado    : PID con retroalimentacion (lazo cerrado)"));
  Serial.println(F("#   pwm 120    : fija PWM del modo abierto [0..255]"));
  Serial.println(F("#   ref 450    : fija referencia de luz [0..1023]"));
  Serial.println(F("#   calibrar   : mide luz minima/maxima y crea referencia"));
  Serial.println(F("#   sim on     : modelo virtual para Wokwi (sin LDR fisica)"));
  Serial.println(F("#   sim off    : leer la LDR fisica nuevamente"));
  Serial.println(F("#   sombra     : oscurece el modelo virtual"));
  Serial.println(F("#   normal     : quita la sombra virtual"));
  Serial.println(F("#   estado     : muestra configuracion"));
  Serial.println(F("#   ayuda      : muestra comandos"));
}

void imprimirEstado() {
  Serial.print(F("# modo=")); Serial.print(lazoCerrado ? F("cerrado") : F("abierto"));
  Serial.print(F("; ref=")); Serial.print(referencia);
  Serial.print(F("; pwm_abierto=")); Serial.print(pwmAbierto);
  Serial.print(F("; planta_virtual=")); Serial.print(plantaVirtual ? 1 : 0);
  Serial.print(F("; kp=")); Serial.print(kp, 3);
  Serial.print(F("; ki=")); Serial.print(ki, 3);
  Serial.print(F("; kd=")); Serial.println(kd, 3);
}

void procesarComando(const char* comando) {
  int valor = 0;

  if (strcmp(comando, "abierto") == 0) {
    lazoCerrado = false;
    aplicarPwm(pwmAbierto);
    reiniciarPID();
    Serial.println(F("# Modo abierto: PWM fijo"));
  } else if (strcmp(comando, "cerrado") == 0) {
    entrarEnLazoCerrado();
    Serial.println(F("# Modo cerrado: control PID activo"));
  } else if (strcmp(comando, "calibrar") == 0) {
    calibrarSensor();
  } else if (strcmp(comando, "sim on") == 0) {
    plantaVirtual = true;
    sombraVirtual = 0.0f;
    luzVirtual = LUZ_AMBIENTE_VIRTUAL + GANANCIA_LED_VIRTUAL * pwmActual;
    calibrarSensor();
    Serial.println(F("# Modo virtual activo: pruebe sombra y normal"));
  } else if (strcmp(comando, "sim off") == 0) {
    plantaVirtual = false;
    sombraVirtual = 0.0f;
    lazoCerrado = false;
    aplicarPwm(pwmAbierto);
    reiniciarPID();
    Serial.println(F("# Leyendo LDR fisica. Ejecute calibrar."));
  } else if (strcmp(comando, "sombra") == 0 && plantaVirtual) {
    sombraVirtual = -85.0f;
    Serial.println(F("# Sombra virtual aplicada (-85 ADC en equilibrio)"));
  } else if (strcmp(comando, "normal") == 0 && plantaVirtual) {
    sombraVirtual = 0.0f;
    Serial.println(F("# Iluminacion virtual normal restaurada"));
  } else if (strcmp(comando, "sombra") == 0 || strcmp(comando, "normal") == 0) {
    // Sin planta virtual la sombra es fisica: tapar la LDR con la mano.
    Serial.println(F("# sombra/normal solo aplican con 'sim on'. En hardware tape la LDR."));
  } else if (strcmp(comando, "estado") == 0) {
    imprimirEstado();
  } else if (strcmp(comando, "ayuda") == 0) {
    imprimirAyuda();
  } else if (sscanf(comando, "pwm %d", &valor) == 1 && valor >= 0 && valor <= 255) {
    pwmAbierto = valor;
    if (!lazoCerrado) aplicarPwm(pwmAbierto);
    Serial.println(F("# PWM abierto actualizado"));
  } else if (sscanf(comando, "ref %d", &valor) == 1 && valor >= 0 && valor <= 1023) {
    // No se reinicia la integral: en lazo cerrado eso haria caer el PWM
    // de golpe. El PID se adapta solo a la nueva referencia.
    referencia = valor;
    Serial.println(F("# Referencia actualizada"));
  } else if (comando[0] != '\0') {
    Serial.println(F("# Comando no reconocido. Escriba: ayuda"));
  }
}

void leerComandosSerial() {
  // Buffer de tamano fijo para evitar reservas dinamicas en Arduino Uno.
  while (Serial.available() > 0) {
    const char caracter = (char)Serial.read();
    if (caracter == '\n' || caracter == '\r') {
      if (longitudComando > 0) {
        bufferComando[longitudComando] = '\0';
        procesarComando(bufferComando);
        longitudComando = 0;
      }
    } else if (longitudComando < sizeof(bufferComando) - 1) {
      bufferComando[longitudComando++] = caracter;
    } else {
      longitudComando = 0;
      Serial.println(F("# Comando demasiado largo"));
    }
  }
}

void cicloControl(float dt, unsigned long tiempoMs) {
  if (plantaVirtual) {
    // Dinamica de primer orden: salida anterior -> nueva medicion.
    const float equilibrio = LUZ_AMBIENTE_VIRTUAL +
        GANANCIA_LED_VIRTUAL * pwmActual + sombraVirtual;
    const float alfa = limitar(dt / CONSTANTE_TIEMPO_VIRTUAL, 0.0f, 1.0f);
    luzVirtual += alfa * (equilibrio - luzVirtual);
  }
  const int luz = leerLuz();
  const float error = (float)referencia - (float)luz;
  float p = 0.0f, i = 0.0f, d = 0.0f;

  if (lazoCerrado) {
    // P: depende del error presente.
    p = kp * error;

    // D: derivada de la medicion para evitar golpe por cambiar la referencia.
    const float derivadaMedida = ((float)luz - ultimaLectura) / dt;
    derivadaFiltrada = 0.70f * derivadaFiltrada + 0.30f * derivadaMedida;
    d = -kd * derivadaFiltrada;

    // I: integra el error. Anti-windup por integracion condicional.
    const float integralCandidata = limitar(integral + ki * error * dt, -255.0f, 255.0f);
    const float salidaCandidata = p + integralCandidata + d;
    const bool saturadoArriba = salidaCandidata > 255.0f && error > 0.0f;
    const bool saturadoAbajo  = salidaCandidata <   0.0f && error < 0.0f;
    if (!saturadoArriba && !saturadoAbajo) {
      integral = integralCandidata;
    }

    i = integral;
    aplicarPwm((int)(limitar(p + i + d, 0.0f, 255.0f) + 0.5f));
  } else {
    aplicarPwm(pwmAbierto);
  }

  ultimaLectura = (float)luz;

  // Solo son datos CSV las lineas sin el prefijo '#'.
  Serial.print(tiempoMs); Serial.print(',');
  Serial.print(lazoCerrado ? 1 : 0); Serial.print(',');
  Serial.print(referencia); Serial.print(',');
  Serial.print(luz); Serial.print(',');
  Serial.print(pwmActual); Serial.print(',');
  Serial.print(error, 1); Serial.print(',');
  Serial.print(p, 2); Serial.print(',');
  Serial.print(i, 2); Serial.print(',');
  Serial.println(d, 2);
}

void setup() {
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_LDR, INPUT);
  Serial.begin(115200);
  Serial.println(F("# Practica S10: lazo abierto y PID de iluminacion"));
  calibrarSensor();
  imprimirAyuda();
  Serial.println(F("tiempo_ms,modo,referencia,luz,pwm,error,p,i,d"));
}

void loop() {
  leerComandosSerial();
  const unsigned long ahora = millis();
  if (ahora - ultimaMuestraMs >= PERIODO_MS) {
    const float dt = (ahora - ultimaMuestraMs) / 1000.0f;
    ultimaMuestraMs = ahora;
    cicloControl(dt, ahora);
  }
}
