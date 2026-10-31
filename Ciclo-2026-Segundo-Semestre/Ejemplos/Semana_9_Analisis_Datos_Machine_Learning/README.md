# Semana 9 · Análisis de Datos y Machine Learning

**Análisis de lecturas de un sensor y una predicción sencilla**  
**Responsable del material: Wendy Mazariegos**

Ejemplo corto con temperaturas **simuladas** de un único sensor. Muestra datos
originales, problemas de calidad, tendencia, evaluación y una predicción nueva.

## Ver el ejemplo sin instalar nada

Descomprime la carpeta y abre **`demo.html`** con doble clic. Mantén la carpeta
`resultados` junto a la página para que se muestre la gráfica. El reporte incluido
ya está calculado y funciona sin Internet. No es una medición en tiempo real.

## Qué demuestra

| Etapa | Acción |
|---|---|
| Datos originales | Leer `datos/lecturas.csv`: 25 registros con minuto y temperatura. |
| Calidad | Descartar un duplicado, un vacío, un texto, un minuto inválido y una temperatura fuera del rango del laboratorio. |
| Tendencia | Ordenar las 20 lecturas válidas y visualizar su evolución. |
| Entrenamiento | Aprender una recta con las primeras 16 lecturas. |
| Evaluación | Predecir las últimas cuatro y calcular su error absoluto medio (MAE). |
| Predicción futura | Reajustar con las 20 lecturas válidas y estimar el minuto 20. |

La **regresión lineal** aprende dos parámetros a partir de los datos:

`temperatura estimada = pendiente × minuto + intercepto`

Es un modelo supervisado sencillo: el minuto es la entrada y la temperatura
observada es el valor que se busca predecir. El ajuste por mínimos cuadrados está
implementado en Python para poder leer la operación completa.

## Resultados del CSV incluido

- 25 registros originales → 20 válidos y 5 descartados.
- MAE de la regresión en prueba: aproximadamente **0.084 °C**.
- MAE de repetir la última lectura de entrenamiento: **1.000 °C**.
- Predicción del modelo final para el minuto 20: aproximadamente **29.01 °C**.

El MAE es el promedio de las diferencias absolutas entre las predicciones y los
valores observados. La referencia simple permite comprobar si la regresión aporta
algo frente a repetir una lectura. Las métricas se calculan con datos de prueba
posteriores al entrenamiento, sin mezclarlos aleatoriamente.

El modelo final se ajusta después de evaluar y usa todo el historial válido. La
predicción futura no tiene un error medido todavía: falta observar ese minuto.
Los errores pequeños del ejemplo no aseguran precisión con un sensor real.

## Recalcular o modificar los datos

Requisito: **Python 3.10 o posterior**. Desde la carpeta de esta semana:

```bash
python -m pip install -r requirements.txt
python analisis.py
```

En algunos equipos el comando se llama `py` o `python3`.
La instalación inicial requiere Internet; la ejecución posterior es local.
El script encuentra el CSV a partir de su propia ubicación y regenera los resultados
y `demo.html`. No modifica el CSV original. Puedes usar un entorno virtual si lo prefieres.

## Demostración de cinco minutos

1. Abre `demo.html` y despliega las filas originales: localiza el vacío, el texto y los 85 °C.
2. Explica que el rango de **0 a 50 °C** es una regla fija de este laboratorio; un valor fuera de él no es universalmente imposible.
3. Señala en la gráfica los datos de entrenamiento, los de prueba y la tendencia.
4. Compara el MAE de la regresión con el de repetir la última lectura.
5. Muestra la predicción del minuto 20 y distingue una estimación de una medición.

Para experimentar, cambia una temperatura válida del CSV, ejecuta el script y
recarga la página. Compara la gráfica y las métricas antes y después. No se rellenan
lecturas faltantes; se mantienen los minutos originales para no comprimir el tiempo.
Ante minutos duplicados se conserva el primer registro válido en el orden del CSV.

## Archivos para el repositorio

| Archivo | Contenido |
|---|---|
| `analisis.py` | Limpieza, regresión, evaluación y generación del reporte. |
| `datos/lecturas.csv` | Datos sintéticos originales con cinco problemas introducidos. |
| `requirements.txt` | Dependencia para dibujar la gráfica. |
| `demo.html` | Reporte visual generado. |
| `resultados/lecturas_limpias.csv` | Datos que pasan las reglas de calidad. |
| `resultados/calidad.csv` | Diagnóstico de cada fila original. |
| `resultados/evaluacion.csv` | Valores observados, predichos y errores de prueba. |
| `resultados/resumen.json` | Parámetros del modelo y métricas calculadas. |
| `resultados/tendencia.png` | Gráfica del historial y la predicción. |

Sube **`Semana_9_Analisis_Datos_Machine_Learning`** completa junto a las semanas 7 y 8.
Los resultados se incluyen para visualizar el ejemplo sin ejecutar Python.

**Alcance:** se ejecutó el análisis con el CSV incluido y se contrastaron los
parámetros y errores con un cálculo independiente. Los datos son sintéticos y la
serie es breve; una única división temporal ofrece una evaluación limitada.
No hay un sensor físico conectado. El modelo supone una tendencia lineal y no debe
extrapolarse a períodos largos o condiciones distintas.

[Referencia: guardar figuras con Matplotlib](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)
