# Alcance de validación

**Responsable del material: Wendy Mazariegos**

## Comprobado al preparar esta entrega

- 8 pruebas automatizadas de la API aprobadas, con FastAPI TestClient y mongomock.
- Registro y recuperación del mismo documento; fecha BSON simulada y atributo opcional.
- Rechazo de temperaturas fuera de rango, de textos y de fechas sin zona horaria.
- Normalización de fechas a UTC, selección por intervalo y orden de las últimas lecturas.
- Separación de dispositivos, umbral de 30 °C e historial inicial sin duplicación.
- Lectura estructural de los archivos YAML/JSON y sintaxis de los archivos Python.

## Pendiente de verificar en un equipo con Docker

Este entorno no dispone de Docker. No se ejecutaron los contenedores de MongoDB
ni Grafana, ni se inspeccionó el dashboard en un navegador. Las pruebas usan una
base simulada; no confirman el funcionamiento real del plugin Infinity.

Para comprobar la integración, inicia el proyecto según el README y ejecuta:

```bash
python scripts/verificar_demo.py
```

Este comando verifica almacenamiento, consulta y recuperación del identificador
por medio de Grafana. Después comprueba visualmente la gráfica y el cambio a rojo.
La descarga inicial de imágenes y del plugin requiere conexión a Internet.

Versiones declaradas: MongoDB 8.0 (etiqueta de rama, recibe actualizaciones de parche),
Grafana OSS 12.2.5 e Infinity 4.1.5. Las versiones principales de las dependencias
Python están fijadas en los archivos de requisitos; las dependencias transitivas
se resuelven al instalar.
