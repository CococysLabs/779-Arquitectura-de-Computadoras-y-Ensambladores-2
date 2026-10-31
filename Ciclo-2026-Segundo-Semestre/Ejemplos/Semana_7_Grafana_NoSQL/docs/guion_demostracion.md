# Guion práctico · Semana 7

**Responsable del material: Wendy Mazariegos**  
**Duración sugerida: 20 minutos**  
**Tema: registro y monitoreo de lecturas de temperatura con Grafana y NoSQL**

## Antes de la clase

Inicia el proyecto siguiendo el README, abre el dashboard y la API interactiva.
Comprueba que las lecturas llegan y que la gráfica se actualiza. Deja preparadas
una terminal para MongoDB y otra para los comandos Docker.

## Secuencia de demostración

| Tiempo | Acción de la docente | Qué deben observar los estudiantes |
|---|---|---|
| 0–3 min | Presentar el problema: “¿Cómo registraríamos la temperatura del laboratorio durante el día?” | Un valor aislado no muestra la evolución; necesitamos fecha, dispositivo y almacenamiento. |
| 3–6 min | Mostrar las lecturas en `/lecturas?limite=3` y ejecutar la consulta de los tres documentos más recientes en MongoDB. | Cada registro contiene un identificador, una fecha y un valor; los datos se conservan en una colección. |
| 6–10 min | Mostrar la gráfica y relacionar una fecha y temperatura de la tabla con su punto. | El eje horizontal representa tiempo y el vertical temperatura en °C; Grafana consulta datos ya guardados. |
| 10–14 min | Detener el sensor; ingresar 24 y después 35 °C desde POST /lecturas en `/docs`. | La lectura nueva aparece en MongoDB, la línea sube y el indicador cambia a rojo a partir de 30 °C. |
| 14–17 min | Registrar 27 °C con `atributos.humedad: 68`; mostrar ese documento y otro sin humedad. | Los documentos pueden contener campos adicionales, conservando los campos que permiten consultarlos y graficarlos. |
| 17–20 min | Ejecutar la consulta de promedio y reanudar el sensor. Pedir que expliquen el recorrido de una lectura. | Sensor → API → MongoDB; Grafana → API → MongoDB → gráfica. |

## Explicación breve para acompañar la práctica

“El sensor de este ejemplo es un programa. Cada cinco segundos envía una temperatura.
La API valida el dato y lo guarda como un documento en MongoDB. Cada documento tiene
su propia fecha e identificador. Grafana consulta esos documentos a través de la API
y usa la fecha y el valor para ubicar cada punto. Si ingresamos 35 grados, podremos
seguir el mismo dato desde su registro hasta su aparición en la gráfica.”

## Participación de los estudiantes

1. Registrar una lectura de 28 °C y anotar el identificador devuelto.
2. Buscarla en MongoDB y en la tabla de Grafana.
3. Registrar otra de 32 °C y describir qué cambia en el indicador.
4. Agregar un atributo opcional y comparar ambos documentos.
5. Explicar qué ocurre con el historial si se cierra Grafana pero MongoDB sigue activo.

**Resultado esperado:** los valores aparecen en la colección y en el dashboard;
el de 32 °C supera el umbral visual. Cerrar el navegador no borra los documentos.

## Cierre

Preguntar: “¿Qué componente almacena la lectura? ¿Cuál la representa? ¿Por qué
necesitamos una fecha? ¿NoSQL significa que los datos no necesitan reglas?”

La respuesta debe distinguir almacenamiento y visualización, y reconocer que la
flexibilidad de documentos convive con validaciones de fecha, dispositivo y valor.

## Evidencias sugeridas

- Captura del documento de 35 °C en MongoDB.
- Captura del mismo valor en el dashboard.
- Comparación de un documento con humedad y otro sin ese atributo.

Las capturas deben obtenerse al ejecutar la demostración; no se incluyen imágenes
que aparenten resultados de una ejecución real.
