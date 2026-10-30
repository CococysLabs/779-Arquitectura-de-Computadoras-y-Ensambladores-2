/*
 * Semana 4 · Monitor en tiempo real con Processing
 * Arquitectura de Computadoras y Ensambladores 2 · Laboratorio
 *
 * Recibe por el puerto serial líneas "valor,maximo" (ver sensor_serial.ino)
 * y las muestra con:
 *   - una gráfica de línea que se desplaza (historial)
 *   - un indicador circular animado con alerta por umbral
 *
 * Si no hay puerto disponible (o MODO_SIMULADO = true) genera datos simulados.
 *
 * Teclas:  S = guardar captura   P = pausar/reanudar
 */

import processing.serial.*;

// ---------------- Configuración ----------------
final boolean MODO_SIMULADO = false;  // true = trabajar sin hardware
final int INDICE_PUERTO = 0;          // índice del puerto en Serial.list()
final int BAUDIOS = 115200;           // igual que en el Arduino/ESP32
final int MUESTRAS = 200;             // puntos visibles en la gráfica
final float UMBRAL = 0.75;            // alerta al superar el 75 % del rango

// ---------------- Colores ----------------
final color FONDO = #1E1E2F;
final color PANEL = #2A2A42;
final color REJILLA = #3A3A5A;
final color TEXTO = #F2F4F8;
final color TENUE = #9AA0B4;
final color AZUL = #4DA3FF;
final color VERDE = #3DDC97;
final color NARANJA = #F5A623;
final color ROJO = #FF5C5C;

// ---------------- Estado ----------------
Serial puerto;
float[] historial = new float[MUESTRAS];  // lecturas normalizadas 0..1
float valorActual = 0;     // última lectura normalizada
float valorSuave = 0;      // valor animado del indicador
int valorCrudo = 0;
int valorMax = 4095;
long recibidos = 0;
boolean pausado = false;
String origen = "";

void setup() {
  size(1100, 600);
  surface.setTitle("Semana 4 · Monitor en tiempo real");
  textFont(createFont("SansSerif", 14));
  smooth(4);

  if (!MODO_SIMULADO) {
    println("Puertos disponibles:");
    printArray(Serial.list());
    if (Serial.list().length > INDICE_PUERTO) {
      try {
        puerto = new Serial(this, Serial.list()[INDICE_PUERTO], BAUDIOS);
        puerto.bufferUntil('\n');
        origen = "Serial · " + Serial.list()[INDICE_PUERTO] + " · " + BAUDIOS + " baudios";
      }
      catch (Exception e) {
        println("No se pudo abrir el puerto: " + e.getMessage());
        puerto = null;
      }
    }
  }
  if (puerto == null) {
    origen = "Datos simulados";
  }
}

void draw() {
  background(FONDO);

  if (puerto == null && !pausado && frameCount % 2 == 0) {
    simularLectura();
  }

  // Encabezado
  fill(TEXTO);
  textAlign(LEFT, BASELINE);
  textSize(26);
  text("Temperatura del laboratorio", 40, 52);
  fill(TENUE);
  textSize(14);
  text(origen + (pausado ? "  ·  PAUSADO" : ""), 40, 76);

  dibujarGrafica(40, 100, 680, 440);
  dibujarIndicador(910, 300, 130);
  dibujarEstadisticas(790, 470);
}

// ---------------- Entrada de datos ----------------

// Processing llama a esta función cada vez que llega un '\n' por el puerto
void serialEvent(Serial p) {
  String linea = p.readStringUntil('\n');
  if (linea == null || pausado) return;
  String[] partes = split(trim(linea), ',');
  if (partes.length == 0 || partes[0].length() == 0) return;

  int crudo = int(partes[0]);
  int max = (partes.length > 1) ? int(partes[1]) : valorMax;
  if (max > 0) {
    agregarMuestra(crudo, max);
  }
}

void simularLectura() {
  float t = frameCount * 0.015;
  float v = 0.45 + 0.3 * sin(t) + 0.25 * (noise(t * 3) - 0.5);
  agregarMuestra(int(constrain(v, 0, 1) * 4095), 4095);
}

void agregarMuestra(int crudo, int max) {
  valorCrudo = crudo;
  valorMax = max;
  valorActual = constrain(crudo / (float) max, 0, 1);
  // Corre el historial un lugar a la izquierda y agrega la nueva lectura al final
  arrayCopy(historial, 1, historial, 0, MUESTRAS - 1);
  historial[MUESTRAS - 1] = valorActual;
  recibidos++;
}

// ---------------- Visualización ----------------

void dibujarGrafica(float x, float y, float w, float h) {
  noStroke();
  fill(PANEL);
  rect(x, y, w, h, 14);

  float izq = x + 60, der = x + w - 20, arriba = y + 25, abajo = y + h - 35;

  // Rejilla horizontal con etiquetas en porcentaje
  textSize(12);
  for (int i = 0; i <= 4; i++) {
    float gy = lerp(arriba, abajo, i / 4.0);
    stroke(REJILLA);
    strokeWeight(1);
    line(izq, gy, der, gy);
    noStroke();
    fill(TENUE);
    textAlign(RIGHT, CENTER);
    text((100 - i * 25) + " %", izq - 10, gy);
  }

  // Línea de umbral
  float uy = map(UMBRAL, 0, 1, abajo, arriba);
  stroke(ROJO, 160);
  strokeWeight(1.5);
  for (float dx = izq; dx < der; dx += 14) {
    line(dx, uy, min(dx + 7, der), uy);
  }
  fill(ROJO);
  noStroke();
  textAlign(RIGHT, BOTTOM);
  text("umbral " + int(UMBRAL * 100) + " %", der, uy - 4);

  // Área bajo la curva
  noStroke();
  fill(AZUL, 40);
  beginShape();
  vertex(izq, abajo);
  for (int i = 0; i < MUESTRAS; i++) {
    vertex(map(i, 0, MUESTRAS - 1, izq, der), map(historial[i], 0, 1, abajo, arriba));
  }
  vertex(der, abajo);
  endShape(CLOSE);

  // Curva
  noFill();
  stroke(AZUL);
  strokeWeight(2.5);
  beginShape();
  for (int i = 0; i < MUESTRAS; i++) {
    vertex(map(i, 0, MUESTRAS - 1, izq, der), map(historial[i], 0, 1, abajo, arriba));
  }
  endShape();

  // Punto de la lectura más reciente
  float py = map(historial[MUESTRAS - 1], 0, 1, abajo, arriba);
  noStroke();
  fill(NARANJA);
  ellipse(der, py, 10, 10);

  fill(TENUE);
  textAlign(CENTER, TOP);
  text("últimas " + MUESTRAS + " lecturas  →  tiempo", (izq + der) / 2, abajo + 10);
}

void dibujarIndicador(float cx, float cy, float r) {
  // lerp() suaviza el movimiento: el indicador "persigue" al valor real
  valorSuave = lerp(valorSuave, valorActual, 0.12);

  float inicio = PI * 0.75;   // arco de 270°
  float recorrido = PI * 1.5;

  noFill();
  strokeCap(ROUND);
  strokeWeight(24);
  stroke(REJILLA);
  arc(cx, cy, r * 2, r * 2, inicio, inicio + recorrido);

  color c;
  if (valorSuave > UMBRAL) {
    c = ROJO;
  } else {
    c = lerpColor(VERDE, NARANJA, valorSuave / UMBRAL);
  }
  stroke(c);
  arc(cx, cy, r * 2, r * 2, inicio, inicio + recorrido * max(valorSuave, 0.001));

  // Valor central
  noStroke();
  fill(TEXTO);
  textAlign(CENTER, CENTER);
  textSize(48);
  text(round(valorSuave * 100) + " %", cx, cy - 8);
  fill(TENUE);
  textSize(15);
  text(valorCrudo + " / " + valorMax, cx, cy + 34);

  // Alerta parpadeante
  if (valorActual > UMBRAL && (frameCount / 15) % 2 == 0) {
    fill(ROJO);
    textSize(20);
    text("¡ALERTA!", cx, cy + r * 0.85);
  }
}

void dibujarEstadisticas(float x, float y) {
  float minimo = 1, maximo = 0, suma = 0;
  for (float v : historial) {
    minimo = min(minimo, v);
    maximo = max(maximo, v);
    suma += v;
  }
  float promedio = suma / MUESTRAS;

  textAlign(LEFT, BASELINE);
  textSize(14);
  String[] etiquetas = { "Mínimo", "Promedio", "Máximo", "Recibidas" };
  String[] valores = { round(minimo * 100) + " %", round(promedio * 100) + " %", round(maximo * 100) + " %", str(recibidos) };
  for (int i = 0; i < 4; i++) {
    float bx = x + i * 72;
    fill(TENUE);
    text(etiquetas[i], bx, y);
    fill(TEXTO);
    textSize(18);
    text(valores[i], bx, y + 26);
    textSize(14);
  }
}

// ---------------- Teclado ----------------
void keyPressed() {
  if (key == 's' || key == 'S') {
    saveFrame("captura-####.png");
    println("Captura guardada");
  } else if (key == 'p' || key == 'P') {
    pausado = !pausado;
  }
}
