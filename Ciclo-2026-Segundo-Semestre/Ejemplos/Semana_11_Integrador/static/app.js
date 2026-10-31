// Panel web: cada 2 s consulta la API REST del backend y redibuja la página.
// El navegador NO habla MQTT; todo pasa por backend.py.

const $ = (id) => document.getElementById(id);
const fmtHour = (iso) => (iso ? iso.substring(11, 19) : '—'); // "2026-10-31T12:00:00Z" -> "12:00:00"

function status(id, label, healthy) {
  const el = $(id);
  el.textContent = `${label}: ${healthy ? 'conectado' : 'desconectado'}`;
  el.className = `pill ${healthy ? 'ok' : 'bad'}`;
}

async function getJson(url) {
  const r = await fetch(url, { cache: 'no-store' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

// ---------- Gráfica SVG de temperatura (sin librerías externas) ----------
function drawChart(data) {
  const svg = $('chart');
  svg.replaceChildren();
  const ns = 'http://www.w3.org/2000/svg';
  const create = (name, attrs) => {
    const el = document.createElementNS(ns, name);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    svg.appendChild(el);
    return el;
  };

  const W = 640, H = 250, left = 45, right = 12, top = 15, bottom = 27;
  const values = data.map((d) => Number(d.valor)).filter(Number.isFinite);
  if (!values.length) {
    const t = create('text', { x: 320, y: 132, 'text-anchor': 'middle', fill: '#8090a3', 'font-size': 14 });
    t.textContent = 'Esperando lecturas MQTT…';
    return;
  }

  // Escala vertical: siempre incluye 24–30 °C para que se vean los umbrales.
  const minV = Math.floor(Math.min(...values, 24) - 1);
  const maxV = Math.ceil(Math.max(...values, 30) + 1);
  const x = (i) => left + (i * (W - left - right)) / Math.max(1, values.length - 1);
  const y = (v) => H - bottom - ((v - minV) * (H - top - bottom)) / (maxV - minV);

  // Líneas guía horizontales con su etiqueta en °C.
  for (let i = 0; i < 5; i++) {
    const val = minV + ((maxV - minV) * i) / 4;
    create('line', { x1: left, y1: y(val), x2: W - right, y2: y(val), stroke: '#e8edf5', 'stroke-width': 1 });
    const t = create('text', { x: left - 8, y: y(val) + 4, 'text-anchor': 'end', fill: '#8899ac', 'font-size': 11 });
    t.textContent = `${val.toFixed(0)}°`;
  }

  // Umbral de encendido (28 °C) punteado.
  create('line', { x1: left, y1: y(28), x2: W - right, y2: y(28), stroke: '#e8a451', 'stroke-dasharray': '5 4', 'stroke-width': 1.5 });

  // Serie de temperatura y punto de la última lectura.
  const path = values.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(2)} ${y(v).toFixed(2)}`).join(' ');
  create('path', { d: path, fill: 'none', stroke: '#1c72b5', 'stroke-width': 3, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' });
  const last = values.length - 1;
  create('circle', { cx: x(last), cy: y(values[last]), r: 4.5, fill: '#1c72b5', stroke: 'white', 'stroke-width': 2 });

  // Hora de la primera y la última lectura en el eje X.
  for (const [pos, idx] of [[left, 0], [W - right, last]]) {
    const t = create('text', { x: pos, y: H - 6, 'text-anchor': pos === left ? 'start' : 'end', fill: '#8a9baa', 'font-size': 11 });
    t.textContent = fmtHour(data[idx]?.timestamp);
  }
}

// ---------- Tabla de comandos: pendiente vs. confirmado ----------
function renderTable(rows) {
  const body = $('comandos');
  body.replaceChildren();
  if (!rows.length) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 4;
    td.textContent = 'Sin comandos';
    tr.append(td);
    body.append(tr);
    return;
  }
  for (const r of rows) {
    const tr = document.createElement('tr');
    const orden = r.fan === null ? 'AUTO' : r.fan ? 'ON' : 'OFF';
    for (const value of [fmtHour(r.solicitado), r.modo, orden]) {
      const td = document.createElement('td');
      td.textContent = value;
      tr.append(td);
    }
    const resultado = document.createElement('td');
    resultado.textContent = r.estado;
    resultado.className = 'tag ' + (r.estado === 'confirmado' ? 'ok' : r.estado === 'pendiente' ? 'pending' : '');
    tr.append(resultado);
    body.append(tr);
  }
}

// ---------- Lista de eventos del backend ----------
function renderEvents(rows) {
  const body = $('eventos');
  body.replaceChildren();
  if (!rows.length) {
    const li = document.createElement('li');
    li.textContent = 'Sin eventos';
    body.append(li);
    return;
  }
  for (const e of rows) {
    const li = document.createElement('li');
    const time = document.createElement('time');
    time.textContent = fmtHour(e.timestamp);
    const tipo = document.createElement('b');
    tipo.textContent = `${e.tipo} · `;
    // textContent / createTextNode evitan interpretar como HTML datos que vienen de MQTT.
    li.append(time, tipo, document.createTextNode(String(e.detalle)));
    body.append(li);
  }
}

// ---------- Ciclo de actualización ----------
let refreshing = false;
async function refresh() {
  if (refreshing) return; // evita solapar consultas si el backend tarda
  refreshing = true;
  try {
    const [estado, lecturas, comandos, eventos] = await Promise.all([
      getJson('/api/estado'),
      getJson('/api/lecturas?limit=50'),
      getJson('/api/comandos'),
      getJson('/api/eventos'),
    ]);
    status('broker-status', 'Broker', estado.broker_conectado);
    status('device-status', 'Nodo', estado.dispositivo_conectado);
    $('temperatura').textContent = estado.ultima_lectura ? `${Number(estado.ultima_lectura.valor).toFixed(1)} °C` : '—';
    $('ventilador').textContent = estado.actuador ? (estado.actuador.fan ? 'Encendido' : 'Apagado') : '—';
    $('modo').textContent = `Modo: ${estado.actuador?.modo ?? '—'}`;
    $('total').textContent = estado.cantidad_lecturas;
    $('fecha').textContent = fmtHour(estado.ultima_lectura?.timestamp);
    // Sin broker no tiene sentido enviar órdenes.
    for (const id of ['auto', 'on', 'off', 'heat']) $(id).disabled = !estado.broker_conectado;
    drawChart(lecturas);
    renderTable(comandos);
    renderEvents(eventos);
  } catch (err) {
    $('feedback').textContent = `No se puede consultar el backend: ${err.message}`;
    $('feedback').className = 'feedback error';
  } finally {
    refreshing = false;
  }
}

// ---------- Botones: POST a la API; el backend publica por MQTT ----------
async function send(path, payload, label) {
  $('feedback').textContent = `Enviando ${label}…`;
  $('feedback').className = 'feedback';
  try {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const body = await r.json();
    if (!r.ok) throw new Error(body.error || `HTTP ${r.status}`);
    $('feedback').textContent = `${label} enviado. Confirma su ejecución en la tabla de comandos y el estado del ventilador.`;
  } catch (err) {
    $('feedback').textContent = err.message;
    $('feedback').className = 'feedback error';
  }
  await refresh();
}

$('auto').onclick = () => send('/api/comando', { modo: 'automatico' }, 'Modo automático');
$('on').onclick = () => send('/api/comando', { modo: 'manual', fan: true }, 'Encender ventilador');
$('off').onclick = () => send('/api/comando', { modo: 'manual', fan: false }, 'Apagar ventilador');
$('heat').onclick = () => send('/api/perturbacion', {}, 'Perturbación de +6 °C');

refresh();
setInterval(refresh, 2000);
