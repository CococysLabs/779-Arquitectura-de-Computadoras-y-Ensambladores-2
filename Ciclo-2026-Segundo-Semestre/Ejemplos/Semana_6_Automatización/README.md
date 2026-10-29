# Semana 6 · Automatización y capa de software en IoT

Actividad grupal de análisis: un proceso donde la automatización sustituyó total o parcialmente la intervención humana. Incluye además dos demos de los temas de la sesión (FreeRTOS y MicroPython).

**Competencia:** relaciona las actividades de proyectos con las capas del stack IoT mediante esquemas, prácticas guiadas y documentación técnica en contextos de diseño modular y conectividad escalable.

## Contenido

| Archivo | Qué contiene |
| --- | --- |
| [`templates/analysis-template.md`](templates/analysis-template.md) | **Actividad 1:** plantilla que llena cada grupo |
| [`examples/worked-example.md`](examples/worked-example.md) | Ejemplo resuelto (riego automatizado) para mostrar el nivel esperado |
| [`demos/freertos_two_tasks`](demos/freertos_two_tasks/freertos_two_tasks.ino) | Demo: dos tareas con FreeRTOS en el ESP32 |
| [`demos/micropython_mqtt`](demos/micropython_mqtt/main.py) | Demo: ESP32 con MicroPython publicando al broker de la Semana 5 |

## Actividad 1 · Análisis de un proceso automatizado (40 min, en grupos)

1. Elijan un proceso automatizado de **industria, agricultura, logística u hogar**. Ejemplos: cajas de autocobro, bandas clasificadoras de paquetes, ordeño automático, termostatos inteligentes, semáforos adaptativos, robots de limpieza.
2. Copien la plantilla en su carpeta de grupo y llénenla:

   ```text
   week-06-automation/submissions/grupo-XX/analysis.md
   ```

3. El análisis debe responder:
   - ¿Qué **tecnologías** lo hacen posible (sistemas embebidos, RTOS, Raspberry Pi, MicroPython)?
   - ¿Qué **tareas** siguen dependiendo de las personas?
   - ¿Qué **beneficios y riesgos** genera el cambio?
4. Preparen una conclusión de 1 minuto para compartir en el cierre: ¿la automatización **reemplazó** o **apoyó** a las personas?

## Criterios de revisión

| Criterio | Qué se espera |
| --- | --- |
| Proceso | Descrito con claridad, antes y después de automatizarse |
| Entrada → proceso → salida | Sensores, controlador y actuadores identificados, con diagrama |
| Tecnologías | Al menos dos tecnologías de la sesión, explicando para qué se usan |
| Factor humano | Tareas humanas concretas y por qué siguen siéndolo |
| Beneficios y riesgos | Al menos dos de cada uno, específicos del proceso |
| Conclusión | Postura clara (reemplazo o apoyo) justificada con el análisis |

## Demos de la sesión (opcionales)

### FreeRTOS: dos tareas en paralelo

Abre `demos/freertos_two_tasks/freertos_two_tasks.ino` en el Arduino IDE con una placa ESP32. El LED parpadea cada 500 ms mientras el sensor se lee cada segundo, sin que una tarea bloquee a la otra.

| Tiempo | tareaLED | tareaSensor |
| --- | --- | --- |
| 0 ms | enciende | lee el sensor |
| 500 ms | apaga | (esperando) |
| 1000 ms | enciende | lee el sensor |
| 1500 ms | apaga | (esperando) |

Mientras una tarea espera en `vTaskDelay()`, el planificador le da la CPU a la otra.

### MicroPython publicando por MQTT

1. Instala el firmware de [MicroPython para ESP32](https://micropython.org/download/ESP32_GENERIC/).
2. En [Thonny](https://thonny.org/), selecciona el intérprete MicroPython (ESP32).
3. Cambia la red Wi-Fi y la IP del broker en `main.py` y guárdalo en la placa.
4. Con el broker de la Semana 5 encendido, verás los mensajes en MQTT Explorer bajo `usac/arqui2/grupo1/micropython`.

## Para la próxima sesión

Buses de comunicación: **UART, I²C y SPI**.
