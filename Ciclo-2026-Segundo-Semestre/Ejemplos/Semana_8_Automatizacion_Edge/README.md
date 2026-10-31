# Semana 8 · Automatización y Edge

**Control automático de un ventilador según la temperatura**  
**Responsable del material: Wendy Mazariegos**

Ejemplo pequeño para observar cómo un dispositivo lee un dato, toma una decisión
local y activa una salida. Incluye una simulación visual y el código equivalente
para Arduino Uno R3.

## Abrir la demostración (sin instalaciones)

1. Descomprime la carpeta `Semana_8_Automatizacion_Edge`.
2. Abre **`demo.html`** con doble clic en Chrome, Edge o Firefox.
3. Pulsa **Reproducir ejemplo** o mueve el control de temperatura.
4. Observa el ventilador, el estado de la salida D8 y el registro de decisiones.

Funciona sin conexión a Internet y sin instalar Docker, Python ni bibliotecas.
El navegador simula el sensor y la salida; no controla un ventilador físico.

## Regla de control

| Temperatura | Decisión local |
|---|---|
| 30 °C o más | Encender el ventilador: D8 = HIGH. |
| 28 °C o menos | Apagar el ventilador: D8 = LOW. |
| Mayor que 28 °C y menor que 30 °C | Conservar el estado anterior. |

El ventilador inicia apagado. Los dos umbrales crean **histéresis**: evitan que
pequeñas variaciones alrededor de una sola temperatura lo enciendan y apaguen
continuamente. Los valores son didácticos y pueden ajustarse en el código.

## Demostración de cinco minutos

Sigue esta secuencia en la página o en el Monitor serie de Arduino:

| Paso | Lectura | Resultado esperado | Explicación |
|---|---:|---|---|
| 1 | 24 °C | Apagado | La temperatura está por debajo del umbral inferior. |
| 2 | 29 °C | Apagado | Conserva el estado apagado. |
| 3 | 30 °C | Encendido | Alcanza el umbral superior. |
| 4 | 32 °C | Encendido | Continúa por encima del umbral. |
| 5 | 29 °C | Encendido | Conserva el estado encendido. |
| 6 | 28 °C | Apagado | Alcanza el umbral inferior. |

**Pregunta para la clase:** ¿Por qué a 29 °C puede estar encendido o apagado?
Porque la decisión depende también del estado anterior.

**¿Dónde aparece Edge?** En la placa, la lectura, la comparación y la activación
ocurren en el propio Arduino, cerca del sensor. No se envía la temperatura a un
servidor para recibir una orden. La página permite visualizar esa misma lógica
local, pero representa el dispositivo mediante una simulación.

## Probar en Arduino sin sensor ni ventilador

Se necesita un Arduino Uno R3, cable USB y Arduino IDE.

1. Abre `arduino/ventilador_edge/ventilador_edge.ino`.
2. Mantén `USAR_TMP36 = false` (configuración inicial).
3. Selecciona la placa **Arduino Uno** y su puerto, y carga el programa.
4. Abre el Monitor serie a **9600 baudios** y selecciona **Nueva línea**.
5. Envía `24`, `29`, `30`, `32`, `29` y `28`, uno por uno. Usa punto para decimales.
6. Observa los mensajes y el LED integrado: encendido representa ventilador activo.

El pin D8 cambia al mismo tiempo que el LED. Es una señal de control: **no conectes
un ventilador directamente al pin**. Esta modalidad permite demostrar una salida
física utilizando solamente el LED de la placa.

## Extensión opcional: sensor y ventilador reales

El código admite un sensor **TMP36** y un módulo de relé de 5 V con entrada
**activa en HIGH**, compatible con la señal del Uno R3. Utiliza un ventilador DC
de baja tensión y una fuente adecuada a su voltaje y corriente.

| Componente | Conexión |
|---|---|
| TMP36: alimentación +VS | 5 V del Arduino. |
| TMP36: GND | GND del Arduino. |
| TMP36: VOUT | A0 del Arduino. |
| Módulo de relé: VCC / GND | Alimentación de 5 V según las especificaciones del módulo; referencia de señal común cuando corresponda. |
| Módulo de relé: IN | D8; el ejemplo requiere activación en HIGH. |
| Positivo de la fuente del ventilador | COM del relé. |
| NO del relé | Positivo del ventilador. |
| Negativo del ventilador | Negativo de su fuente. |

Verifica el pinout del encapsulado TMP36 y las especificaciones de tu módulo antes
de conectar. El ventilador se alimenta desde su propia fuente a través de los
contactos del relé. Trabaja únicamente con baja tensión DC para esta práctica.

Cambia `USAR_TMP36` a `true` y vuelve a cargar el programa. El Arduino tomará una
lectura aproximadamente cada segundo. La conversión del TMP36 es
`temperatura = (voltaje - 0.5) * 100`, usando una referencia ADC nominal de 5 V.
La resolución y la tolerancia del sensor pueden producir diferencias respecto de
un termómetro de referencia; esta extensión no es un controlador industrial.

## Estructura para el repositorio

| Archivo | Función |
|---|---|
| `README.md` | Instrucciones y guion breve de demostración. |
| `demo.html` | Simulación visual completa, sin dependencias externas. |
| `arduino/ventilador_edge/ventilador_edge.ino` | Programa de decisión local y activación de salida. |

Coloca **`Semana_8_Automatizacion_Edge`** junto a `Semana_7_Grafana_NoSQL` y las demás
carpetas de tu repositorio. Sube la carpeta completa; no necesitas crear un
repositorio independiente dentro de ella.

## Validación

Se verificaron los controles HTML y JavaScript mediante un DOM simulado: secuencia
de temperaturas, histéresis, estado de la salida, reproducción, pausa y reinicio.
No se comprobó visualmente el diseño en un navegador. El programa Arduino se
compiló y ejecutó con señales simuladas en C++; esta comprobación no sustituye
la compilación para Uno R3 en Arduino IDE. No se cargó en una placa física ni se
probó un circuito real; esa comprobación se realiza al disponer del equipo.

## Referencias técnicas

- [Arduino: lectura analógica](https://docs.arduino.cc/built-in-examples/analog/AnalogInput/)
- [Analog Devices: hoja de datos TMP35/TMP36/TMP37](https://www.analog.com/media/en/technical-documentation/data-sheets/tmp35_36_37.pdf)
