/*
 * Semana 4 · Actividad 2 · Gráfica web con p5.js
 * p5.js es la forma oficial de usar Processing en la web: mismo modelo setup()/draw(),
 * pero en JavaScript y dentro del navegador.
 *
 * Fuente de datos:
 *   - Simulada (por defecto)
 *   - Puerto serial con la Web Serial API (Chrome/Edge), mismo formato "valor,maximo"
 */

const MUESTRAS = 150;
const UMBRAL = 0.75;

let historial = new Array(MUESTRAS).fill(0);
let valorActual = 0;
let valorSuave = 0;
let simulado = true;
let lector = null;

function setup() {
  const c = createCanvas(Math.min(windowWidth - 48, 1000), 460);
  c.parent('lienzo');
  textFont('system-ui');

  select('#btnSerial').mousePressed(conectarSerial);
  select('#btnSimular').mousePressed(usarSimulado);
  if (!('serial' in navigator)) {
    select('#btnSerial').attribute('disabled', '');
    select('#estado').html('Modo: simulado (este navegador no soporta Web Serial)');
  }
}

function windowResized() {
  resizeCanvas(Math.min(windowWidth - 48, 1000), 460);
}

function draw() {
  background('#1E1E2F');
  if (simulado && frameCount % 2 === 0) {
    const t = frameCount * 0.015;
    agregarMuestra(constrain(0.45 + 0.3 * sin(t) + 0.25 * (noise(t * 3) - 0.5), 0, 1));
  }
  dibujarGrafica(0, 0, width - 230, height);
  dibujarIndicador(width - 110, height / 2 - 20, 85);
}

function agregarMuestra(v) {
  valorActual = v;
  historial.shift();
  historial.push(v);
}

function dibujarGrafica(x, y, w, h) {
  noStroke();
  fill('#2A2A42');
  rect(x, y, w, h, 14);
  const izq = x + 55, der = x + w - 20, arriba = y + 25, abajo = y + h - 35;

  textSize(12);
  for (let i = 0; i <= 4; i++) {
    const gy = lerp(arriba, abajo, i / 4);
    stroke('#3A3A5A');
    line(izq, gy, der, gy);
    noStroke();
    fill('#9AA0B4');
    textAlign(RIGHT, CENTER);
    text(`${100 - i * 25} %`, izq - 10, gy);
  }

  const uy = map(UMBRAL, 0, 1, abajo, arriba);
  stroke(255, 92, 92, 160);
  drawingContext.setLineDash([7, 7]);
  line(izq, uy, der, uy);
  drawingContext.setLineDash([]);

  noFill();
  stroke('#4DA3FF');
  strokeWeight(2.5);
  beginShape();
  historial.forEach((v, i) => vertex(map(i, 0, MUESTRAS - 1, izq, der), map(v, 0, 1, abajo, arriba)));
  endShape();
  strokeWeight(1);
}

function dibujarIndicador(cx, cy, r) {
  valorSuave = lerp(valorSuave, valorActual, 0.12);
  const inicio = PI * 0.75, recorrido = PI * 1.5;
  noFill();
  strokeCap(ROUND);
  strokeWeight(18);
  stroke('#3A3A5A');
  arc(cx, cy, r * 2, r * 2, inicio, inicio + recorrido);
  const c = valorSuave > UMBRAL
    ? color('#FF5C5C')
    : lerpColor(color('#3DDC97'), color('#F5A623'), valorSuave / UMBRAL);
  stroke(c);
  arc(cx, cy, r * 2, r * 2, inicio, inicio + recorrido * Math.max(valorSuave, 0.001));
  strokeWeight(1);
  noStroke();
  fill('#F2F4F8');
  textAlign(CENTER, CENTER);
  textSize(34);
  text(`${Math.round(valorSuave * 100)} %`, cx, cy);
  if (valorActual > UMBRAL && Math.floor(frameCount / 15) % 2 === 0) {
    fill('#FF5C5C');
    textSize(16);
    text('¡ALERTA!', cx, cy + r * 0.8);
  }
}

// ---------------- Web Serial ----------------

async function conectarSerial() {
  try {
    const puerto = await navigator.serial.requestPort();
    await puerto.open({ baudRate: 115200 });
    simulado = false;
    select('#estado').html('Modo: puerto serial');
    leerLineas(puerto);
  } catch (e) {
    select('#estado').html('No se conectó: ' + e.message);
  }
}

async function leerLineas(puerto) {
  const decodificador = new TextDecoderStream();
  puerto.readable.pipeTo(decodificador.writable);
  lector = decodificador.readable.getReader();
  let buffer = '';
  try {
    while (true) {
      const { value, done } = await lector.read();
      if (done) break;
      buffer += value;
      let i;
      while ((i = buffer.indexOf('\n')) >= 0) {
        const linea = buffer.slice(0, i).trim();
        buffer = buffer.slice(i + 1);
        const [crudo, max] = linea.split(',').map(Number);
        if (!simulado && max > 0 && Number.isFinite(crudo)) {
          agregarMuestra(constrain(crudo / max, 0, 1));
        }
      }
    }
  } catch (e) {
    select('#estado').html('Lectura interrumpida: ' + e.message);
  }
}

function usarSimulado() {
  simulado = true;
  select('#estado').html('Modo: simulado');
}
