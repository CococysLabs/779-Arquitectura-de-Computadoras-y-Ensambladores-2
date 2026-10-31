# Semana 11 · Integrador IoT: temperatura y control de ventilación

**Ejemplo práctico de evaluación integradora · Arquitectura de Computadoras y Ensambladores 2**

Este ejemplo junta en un solo sistema lo visto en el curso: un **nodo embebido simulado** que mide temperatura, un **broker MQTT**, un **backend** que valida y guarda los datos en **SQLite**, y un **panel web** desde el que se controla un ventilador.

No necesita Arduino ni componentes: el sensor y el ventilador están simulados en Python y los datos son **sintéticos**. Lo importante es **seguir una lectura de extremo a extremo**, enviar una orden al actuador y comprobar su **confirmación**, provocar fallas controladas y documentar **evidencias**.

## Contenido

| Archivo | Qué contiene |
|---|---|
| [`dispositivo.py`](dispositivo.py) | Nodo IoT simulado: sensor de temperatura, control con histéresis y ventilador virtual |
| [`backend.py`](backend.py) | Suscriptor MQTT, validación, API REST y servidor del panel (Flask) |
| [`protocolo.py`](protocolo.py) | Formato de los mensajes JSON y sus validaciones |
| [`datos.py`](datos.py) | Tablas y consultas SQLite |
| [`config.py`](config.py) | Broker, tópicos, umbrales e intervalo de muestreo |
| [`herramientas.py`](herramientas.py) | Utilidades para las pruebas P04 (dato inválido) y P05 (histórico) |
| [`templates/index.html`](templates/index.html), [`static/`](static/) | Panel web (HTML, JavaScript y CSS sin librerías) |
| [`docker-compose.yml`](docker-compose.yml), [`mosquitto/mosquitto.conf`](mosquitto/mosquitto.conf) | Broker Mosquitto local |
| [`evidencias/MATRIZ_DE_PRUEBAS.md`](evidencias/MATRIZ_DE_PRUEBAS.md) | Plantilla que completa cada estudiante |
| [`requirements.txt`](requirements.txt) | Dependencias de Python: Flask y paho-mqtt |

## 1. Arquitectura

```text
  ┌──────────────────────┐   lectura (cada 2 s)    ┌──────────────┐
  │  dispositivo.py      │ ──────────────────────► │              │
  │  sensor simulado     │   estado / conexión     │    Broker    │
  │  ventilador virtual  │ ──────────────────────► │     MQTT     │
  │                      │ ◄────────────────────── │  (Mosquitto) │
  │                      │   comando / perturbación│              │
  │                      │ ──────────────────────► │              │
  └──────────────────────┘   confirmación          └──────┬───────┘
                                                          │ ▲
                                              suscribe    │ │ publica comandos
                                                          ▼ │
                                                   ┌────────────────┐
                                                   │  backend.py    │──► SQLite
                                                   │  valida y      │   (datos/iot.sqlite3)
                                                   │  sirve API     │
                                                   └───────┬────────┘
                                                           │ HTTP (cada 2 s)
                                                           ▼
                                                   ┌────────────────┐
                                                   │  Panel web     │
                                                   │  navegador     │
                                                   └────────────────┘
```

El navegador **no habla MQTT**: consulta la API REST del backend, y es el backend quien publica y recibe por MQTT.

### Recorrido de una lectura (nodo → panel)

| Paso | Dónde ocurre |
|---|---|
| 1. El nodo calcula la temperatura y publica un JSON en `.../lectura` | `dispositivo.py` → `_simular_paso()` |
| 2. Mosquitto entrega el mensaje a quien esté suscrito | broker |
| 3. El backend recibe, valida (rango −20 a 80 °C, unidad, `device_id`...) | `backend.py` → `_al_mensaje()` → `protocolo.validar_lectura()` |
| 4. Si es válida se guarda; si no, se registra un evento `dato_rechazado` | `datos.guardar_lectura()` / `datos.agregar_evento()` |
| 5. El panel pide `/api/estado` y `/api/lecturas` y redibuja | `backend.py` → `estado()`, `static/app.js` → `refresh()` |

### Recorrido de un comando (panel → ventilador → confirmación)

| Paso | Dónde ocurre |
|---|---|
| 1. Clic en un botón → `POST /api/comando` | `static/app.js` → `send()` |
| 2. El backend crea un `command_id`, lo guarda como **pendiente** y lo publica en `.../comando` | `backend.py` → `comando()` |
| 3. El nodo aplica la orden y publica su nuevo estado y una **confirmación** con el mismo `command_id` | `dispositivo.py` → `_al_mensaje()` |
| 4. El backend marca el comando como **confirmado** | `backend.py` → `_al_mensaje()` → `datos.confirmar_comando()` |

> **Publicar una orden no significa que se haya ejecutado.** Por eso existe la confirmación: si el nodo está apagado, el comando queda `pendiente` para siempre.

### Control automático con histéresis

En modo **automático** el nodo enciende el ventilador al llegar a **28 °C** y no lo apaga hasta bajar a **26 °C** (`UMBRAL_ON` y `UMBRAL_OFF` en `config.py`). Con un único umbral, el ventilador se encendería y apagaría continuamente cuando la temperatura ronda ese valor.

El modelo térmico es muy simple (`_simular_paso()`): sin ventilador la temperatura sube unos **0,12 °C por lectura** y con ventilador baja unos **0,36 °C**, más un pequeño ruido aleatorio. Parte de 25,4 °C, así que sin intervenir tarda cerca de **45 s** en llegar a 28 °C.

## 2. Requisitos

- **Python 3.10 o superior**.
- **Docker Desktop** (o Docker Engine con `docker compose`) para el broker.
- Un navegador web.

Las únicas dependencias de Python son `Flask` y `paho-mqtt`. SQLite viene incluido en Python. No se necesitan servicios en la nube, cuentas ni Internet una vez instalado todo.

## 3. Preparación

Abre una terminal **dentro de esta carpeta** (`Semana_11_Integrador/`). Todos los comandos se ejecutan desde aquí.

### 3.1 Iniciar el broker MQTT

```bash
docker compose up -d
docker compose ps
```

Debe aparecer el servicio `mosquitto` con el puerto `127.0.0.1:1883`.

> **Puerto 1883 ocupado:** si dejaste corriendo el broker de la Semana 5, detenlo primero (`docker compose down` dentro de `Semana_5_MQTT/broker`).
>
> **Sin Docker:** instala [Mosquitto](https://mosquitto.org/download/) y ejecuta `mosquitto -v` en una terminal aparte. Mosquitto 2 sin configuración escucha solo en el propio equipo y acepta clientes anónimos, que es lo que necesita este ejemplo. Para la prueba P03, detenlo con `Ctrl+C` y vuelve a iniciarlo.

### 3.2 Instalar las bibliotecas en un entorno virtual

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Linux / macOS:**

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

En el resto del documento, `python` significa el Python del entorno virtual: `.\.venv\Scripts\python.exe` en Windows o `./.venv/bin/python` en Linux/macOS. También puedes activarlo (`.\.venv\Scripts\Activate.ps1` o `source .venv/bin/activate`) y escribir `python` directamente.

## 4. Ejecución

Abre **dos terminales** en esta carpeta.

**Terminal A — Backend y panel:**

```bash
python backend.py
```

Debe mostrar `Panel disponible en http://127.0.0.1:5000` y luego `MQTT conectado, suscripciones activas`.

**Terminal B — Dispositivo simulado:**

```bash
python dispositivo.py
```

Cada 2 s imprime una línea como:

```text
... INFO Temperatura: 25.52 C | Ventilador: OFF | Modo: automatico
```

Abre **http://127.0.0.1:5000**. En unos segundos deben verse **Broker: conectado**, **Nodo: conectado**, la temperatura y la gráfica.

**Terminal C (opcional) — Ver los mensajes MQTT crudos:**

```bash
docker compose exec mosquitto mosquitto_sub -t "laboratorio/iot/#" -v
```

Muestra cada mensaje con su tópico. Es la mejor forma de ver qué viaja realmente por el broker al pulsar los botones del panel. También puedes usar MQTT Explorer como en la Semana 5.

### Secuencia recomendada para la demostración

1. Observa cómo llegan lecturas y aumenta **Lecturas guardadas**.
2. Pulsa **Simular calor +6 °C** para superar rápido los 28 °C.
3. En modo automático, comprueba que el ventilador se **enciende** y que la temperatura baja hasta 26 °C antes de apagarse.
4. Pulsa **Manual · Apagar**: el ventilador se apaga aunque haga calor. Es la diferencia entre decisión automática y orden explícita.
5. Pulsa **Manual · Encender** y comprueba en **Comandos recientes** que pasa de `pendiente` a `confirmado`.
6. Pulsa **Activar automático** y observa cómo el nodo vuelve a decidir solo.
7. Detén el dispositivo (`Ctrl+C` en la terminal B) y envía un comando: queda `pendiente` porque nadie lo confirma.

> El ventilador es una variable del programa, no un dispositivo físico, y el modelo térmico solo sirve para explicar el flujo de datos y las decisiones de control.

## 5. Mensajes MQTT

Todos los tópicos usan el identificador `nodo-01` (definidos en `config.py`):

| Tópico | Dirección | Contenido |
|---|---|---|
| `laboratorio/iot/nodo-01/lectura` | Nodo → Backend | Lectura de temperatura |
| `laboratorio/iot/nodo-01/estado` | Nodo → Backend | Estado del ventilador y modo (*retained*) |
| `laboratorio/iot/nodo-01/comando` | Backend → Nodo | Orden de funcionamiento |
| `laboratorio/iot/nodo-01/confirmacion` | Nodo → Backend | Resultado de la orden |
| `laboratorio/iot/nodo-01/conexion` | Nodo → Backend | `online` / `offline` (*retained* + último deseo) |
| `laboratorio/iot/nodo-01/perturbacion` | Backend → Nodo | Aumento simulado de temperatura |

### Ejemplo de lectura

```json
{
  "message_id": "a4d39f11-a117-4c62-bd85-d881cfa917c1",
  "device_id": "nodo-01",
  "timestamp": "2026-10-31T12:00:00Z",
  "variable": "temperatura",
  "valor": 25.4,
  "unidad": "C",
  "estado": "valido"
}
```

### Ejemplo de comando y su confirmación

```json
{ "modo": "manual", "fan": true,
  "command_id": "5d243aa1-b42b-4fd0-bebd-dcce5b6a8df4", "timestamp": "2026-10-31T12:00:00Z" }
```

```json
{ "command_id": "5d243aa1-b42b-4fd0-bebd-dcce5b6a8df4", "device_id": "nodo-01",
  "aplicado": true, "timestamp": "2026-10-31T12:00:01Z" }
```

En modo `automatico` el comando no lleva `fan`: lo decide el nodo con la histéresis.

### Conceptos MQTT que aparecen en el código

| Concepto | Dónde se usa | Por qué |
|---|---|---|
| **QoS 1** (al menos una vez) | Todas las publicaciones | El broker garantiza la entrega, pero un mensaje **puede llegar dos veces** |
| **Idempotencia** | `message_id` (UNIQUE en SQLite), `command_id` en el nodo | Si una lectura o un comando llega repetido, no se duplica ni se aplica dos veces |
| **Retained** | `estado` y `conexion` | El broker guarda el último valor y se lo entrega a quien se suscriba después |
| **Último deseo (LWT)** | `will_set(...)` en `dispositivo.py` | Si el nodo se cae sin despedirse, el broker publica `offline` en su nombre |
| **Reconexión automática** | `connect_async()` + `loop_start()` | paho reintenta solo cuando el broker vuelve |

Todas las fechas se guardan en **UTC**. En la tabla `lecturas`, `timestamp` es cuándo la generó el nodo y `recibido` cuándo la guardó el backend; la diferencia es la latencia.

## 6. Pruebas P01–P05

Para cada prueba documenta: **fecha y hora, procedimiento, resultado esperado, resultado observado, evidencia y estado** (aprobada / no aprobada).

| ID | Acción | Resultado esperado | Evidencia sugerida |
|---|---|---|---|
| **P01** | Ejecutar nodo + backend y observar 5 lecturas | El panel muestra datos en °C y aumenta el contador | Captura del panel y de la terminal |
| **P02** | Pulsar `Manual · Encender` y `Manual · Apagar` | El ventilador cambia y ambos comandos quedan `confirmado` | Tabla de comandos y estado del ventilador |
| **P03** | Detener y volver a iniciar Mosquitto | El backend detecta la desconexión y vuelve a recibir lecturas al restablecerse | Eventos del panel y consola del backend |
| **P04** | Publicar una lectura inválida (999 °C) | Evento `dato_rechazado`; la lectura **no** se guarda | Evento en el panel y consulta P05 |
| **P05** | Consultar el histórico | Se listan registros con fecha, dispositivo, valor y unidad | Salida de la terminal |

### P03: interrupción y reconexión

En otra terminal:

```bash
docker compose stop mosquitto
```

En unos segundos el panel muestra **Broker: desconectado**, los botones se deshabilitan y las terminales A y B registran la pérdida de conexión. Recupera el servicio:

```bash
docker compose start mosquitto
```

Los clientes se reconectan solos (pueden tardar hasta 10 s). Observa que, mientras no hay broker, el nodo **deja de generar lecturas** (no las acumula para enviarlas después). Habrá un hueco en el histórico: no afirmes que no se perdió nada sin comprobarlo.

### P04: inyectar un dato fuera de rango

Con el broker y el backend en ejecución:

```bash
python herramientas.py invalido
```

Publica una temperatura de **999 °C**. En **Eventos del sistema** debe aparecer `dato_rechazado · .../lectura: temperatura fuera del rango de -20 a 80 C`, y el contador de lecturas no debe aumentar por ese mensaje.

### P05: consultar el histórico en SQLite

```bash
python herramientas.py historico
```

Muestra las diez lecturas más recientes:

```text
2026-10-31T12:00:10Z | nodo-01 | 25.64 C
2026-10-31T12:00:08Z | nodo-01 | 25.52 C
...
```

La base se crea automáticamente en `datos/iot.sqlite3` al iniciar el backend. Para empezar desde cero, detén el backend y borra la carpeta `datos/`.

## 7. Matriz de evidencias

Usa la plantilla [`evidencias/MATRIZ_DE_PRUEBAS.md`](evidencias/MATRIZ_DE_PRUEBAS.md). **Los resultados observados se llenan durante la ejecución**, no antes. Es válido documentar una prueba no aprobada si explicas el problema y su posible causa.

Evidencias mínimas:

- Captura del panel con valores y gráfica (P01).
- Orden enviada, confirmación y estado del ventilador (P02).
- Consola o eventos al detener y recuperar el broker (P03).
- Evento `dato_rechazado` y prueba de que no se almacenó (P04).
- Salida del histórico SQLite (P05).

Cierra con una **falla observada**, su causa probable y una **mejora técnica concreta** para prevenirla o diagnosticarla.

## 8. Diagnóstico rápido

| Síntoma | Qué revisar |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` o `'paho'` | Estás usando el Python del sistema; usa el del entorno virtual (sección 3.2) |
| `Broker: desconectado` todo el tiempo | `docker compose ps`; ¿Docker Desktop está abierto? ¿El puerto 1883 lo usa otro broker? |
| `Nodo: desconectado` | ¿Está corriendo `dispositivo.py`? El nodo se considera activo si su última lectura tiene menos de 15 s |
| Comando siempre `pendiente` | El nodo no está conectado o no recibió la orden; revisa la terminal B |
| Error de puerto 5000 en uso (`Address already in use` / `WinError 10048`) | Ya hay otro backend abierto; ciérralo con `Ctrl+C` |
| `herramientas.py invalido` dice que no se pudo conectar | El broker no está iniciado |
| El panel no carga | Abre `http://127.0.0.1:5000` (no `https`) y revisa que la terminal A siga activa |

## 9. Límites y seguridad

- Ejemplo **local y académico**. Mosquitto acepta conexiones anónimas para simplificar, por eso Docker expone el puerto **solo en `127.0.0.1`**. No publiques este broker en Internet.
- El panel Flask también escucha solo en `127.0.0.1` y no tiene autenticación. No está listo para producción.
- El sensor, la temperatura y el ventilador son simulados; el modelo no representa una planta térmica real.
- Los mensajes que se intenten enviar mientras el broker está detenido se pierden. Reconectarse no equivale a almacenar y reenviar.

## 10. Finalizar

- `Ctrl+C` en las terminales del backend y del dispositivo.
- Detener y eliminar el contenedor del broker: `docker compose down`.

## 11. Recursos

- [MQTT: conceptos y especificación](https://mqtt.org/)
- [Eclipse Mosquitto](https://mosquitto.org/documentation/)
- [Cliente Paho MQTT para Python](https://pypi.org/project/paho-mqtt/)
- [Flask](https://flask.palletsprojects.com/en/stable/)
- [SQLite en Python](https://docs.python.org/3/library/sqlite3.html)
