"""Semana 9: calidad, tendencia y regresión lineal de un sensor.
Responsable del material: Wendy Mazariegos.
"""
import csv
import html
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
AUTORA = 'Wendy Mazariegos'


def limpiar(filas):
    """Reglas fijas del laboratorio, sin estimar valores a partir del futuro."""
    limpias, auditoria, vistos = [], [], set()
    for numero, fila in enumerate(filas, start=2):
        motivo = 'válida'
        try:
            minuto = float(fila['minuto'])
            temperatura = float(fila['temperatura_c'])
            if not (math.isfinite(minuto) and math.isfinite(temperatura)):
                motivo = 'valor no finito'
            elif minuto < 0:
                motivo = 'minuto negativo'
            elif not 0 <= temperatura <= 50:
                motivo = 'fuera del rango del laboratorio (0–50 °C)'
            elif minuto in vistos:
                motivo = 'minuto duplicado'
            else:
                vistos.add(minuto)
                limpias.append({'minuto': minuto, 'temperatura_c': temperatura})
        except (ValueError, TypeError):
            motivo = 'dato vacío o no numérico'
        auditoria.append({'fila_csv': numero, **fila, 'resultado': motivo})
    return sorted(limpias, key=lambda x: x['minuto']), auditoria


def entrenar(datos):
    """Mínimos cuadrados: aprende pendiente e intercepto de los ejemplos."""
    xs = [f['minuto'] for f in datos]
    ys = [f['temperatura_c'] for f in datos]
    xm, ym = mean(xs), mean(ys)
    denominador = sum((x-xm)**2 for x in xs)
    if denominador == 0:
        raise ValueError('Se necesitan al menos dos minutos distintos para entrenar.')
    pendiente = sum((x-xm)*(y-ym) for x, y in zip(xs, ys))/denominador
    return pendiente, ym-pendiente*xm


def predecir(modelo, minuto):
    pendiente, intercepto = modelo
    return pendiente*minuto+intercepto


def guardar_csv(nombre, filas, columnas):
    with (BASE/'resultados'/nombre).open('w', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def main():
    with (BASE/'datos/lecturas.csv').open(encoding='utf-8', newline='') as f:
        originales = list(csv.DictReader(f))
    datos, auditoria = limpiar(originales)
    if len(datos) < 10:
        raise ValueError('Se requieren al menos 10 lecturas válidas para esta demostración.')
    # División temporal: se entrena con el pasado y se evalúa con las últimas lecturas.
    corte = int(len(datos)*0.8)
    entrenamiento, prueba = datos[:corte], datos[corte:]
    modelo = entrenar(entrenamiento)
    evaluacion = [dict(f, prediccion_c=predecir(modelo, f['minuto']),
                       base_c=entrenamiento[-1]['temperatura_c']) for f in prueba]
    for f in evaluacion:
        f['error_absoluto_c'] = abs(f['temperatura_c']-f['prediccion_c'])
    mae = mean(f['error_absoluto_c'] for f in evaluacion)
    mae_base = mean(abs(f['temperatura_c']-f['base_c']) for f in evaluacion)
    # Después de evaluar, se ajusta otro modelo con todo el historial válido.
    modelo_final = entrenar(datos)
    siguiente = datos[-1]['minuto'] + 1
    futuro = predecir(modelo_final, siguiente)
    resumen = {
        'responsable': AUTORA, 'datos': 'simulados con errores introducidos',
        'filas_originales': len(originales), 'filas_validas': len(datos),
        'filas_descartadas': len(originales)-len(datos),
        'motivos_descarte': dict(Counter(f['resultado'] for f in auditoria if f['resultado'] != 'válida')),
        'entrenamiento': len(entrenamiento), 'prueba': len(prueba),
        'modelo_evaluado': {'pendiente': modelo[0], 'intercepto': modelo[1]},
        'mae_modelo_c': mae, 'mae_base_ultima_lectura_c': mae_base,
        'modelo_final': {'pendiente': modelo_final[0], 'intercepto': modelo_final[1]},
        'minuto_futuro': siguiente, 'prediccion_futura_c': futuro,
    }
    (BASE/'resultados').mkdir(exist_ok=True)
    guardar_csv('lecturas_limpias.csv', datos, ['minuto','temperatura_c'])
    guardar_csv('calidad.csv', auditoria, ['fila_csv','minuto','temperatura_c','resultado'])
    guardar_csv('evaluacion.csv', evaluacion,
                ['minuto','temperatura_c','prediccion_c','base_c','error_absoluto_c'])
    (BASE/'resultados/resumen.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10})
    fig, ax = plt.subplots(figsize=(10,4.6), layout='constrained')
    ax.set_facecolor('#f5f8fa')
    ax.scatter([f['minuto'] for f in entrenamiento], [f['temperatura_c'] for f in entrenamiento],
               label='Lecturas de entrenamiento', color='#147d82', s=38, zorder=3)
    ax.scatter([f['minuto'] for f in prueba], [f['temperatura_c'] for f in prueba],
               label='Lecturas de prueba', color='#d07819', s=46, zorder=3)
    xs = [datos[0]['minuto'], datos[-1]['minuto']]
    ax.plot(xs, [predecir(modelo,x) for x in xs], '--', color='#6a5acd',
            label='Modelo evaluado (entrenado solo con el pasado)')
    ax.scatter([siguiente],[futuro],marker='*',s=180,color='#be3e57',
               label='Predicción siguiente minuto (modelo final)', zorder=4)
    ax.axvline((entrenamiento[-1]['minuto']+prueba[0]['minuto'])/2,
               color='#8b979e',linewidth=1,linestyle=':')
    ax.set(xlabel='Tiempo desde el inicio (minutos)', ylabel='Temperatura (°C)',
           title='Sensor simulado · Datos, tendencia y predicción')
    ax.grid(alpha=.2)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper left',fontsize=8)
    fig.savefig(BASE/'resultados/tendencia.png',dpi=150,
                metadata={'Author':AUTORA,'Title':'Semana 9 · Análisis de un sensor'})
    plt.close(fig)

    filas_html = ''.join('<tr>'+''.join('<td>'+html.escape(str(f[c]))+'</td>' for c in
                        ['fila_csv','minuto','temperatura_c','resultado'])+'</tr>' for f in auditoria)
    pruebas_html = ''.join(f"<tr><td>{f['minuto']:g}</td><td>{f['temperatura_c']:.2f}</td>"
                           f"<td>{f['prediccion_c']:.2f}</td><td>{f['error_absoluto_c']:.2f}</td></tr>"
                           for f in evaluacion)
    pagina = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="author" content="{AUTORA}"><title>Semana 9 · Análisis y Machine Learning</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#eff4f6;color:#183742;font:16px/1.6 system-ui,Segoe UI,sans-serif}}main{{max-width:1040px;margin:auto;padding:30px 22px}}h1{{font-size:clamp(26px,4vw,39px);line-height:1.18;letter-spacing:-.03em}}h2{{font-size:21px}}.eyebrow{{color:#147d82;font-size:12px;font-weight:750;letter-spacing:.12em;text-transform:uppercase}}.lead{{max-width:760px;color:#516b76}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:25px 0}}.card,section{{background:white;border:1px solid #d9e4e8;border-radius:15px;padding:20px}}.card strong{{display:block;font-size:32px;color:#147d82}}.card small{{color:#526c76}}section{{margin:17px 0}}img{{width:100%;height:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:9px;text-align:left;border-bottom:1px solid #e2e9eb}}th{{color:#426774}}.scroll{{overflow-x:auto}}.note{{border-left:4px solid #147d82;padding-left:15px;color:#4a6570}}.prediction{{font-size:30px;color:#be3e57;font-weight:750}}code{{background:#eff4f6;padding:2px 5px;border-radius:4px}}summary{{cursor:pointer;font-weight:650}}footer{{font-size:13px;color:#5d7480;margin:20px 0}}@media(max-width:600px){{.grid{{grid-template-columns:1fr}}main{{padding:20px 14px}}section{{padding:15px}}}}
</style></head><body><main>
<div class="eyebrow">Semana 9 · Ejemplo práctico</div><h1>De lecturas imperfectas<br>a una predicción sencilla</h1>
<p>Responsable del material: <strong>{AUTORA}</strong></p>
<p class="lead">Un sensor simulado registra temperaturas. Primero revisamos la calidad, después aprendemos una tendencia del historial y finalmente comprobamos el modelo con datos posteriores.</p>
<div class="grid"><div class="card"><strong>{len(originales)}</strong><small>lecturas originales</small></div><div class="card"><strong>{len(datos)}</strong><small>lecturas válidas</small></div><div class="card"><strong>{len(originales)-len(datos)}</strong><small>registros descartados</small></div></div>
<section><h2>1. Datos originales y problemas de calidad</h2><p>Se descartan datos vacíos o no numéricos, minutos inválidos, temperaturas fuera del rango didáctico de 0 a 50 °C y minutos duplicados. No se inventan valores para rellenar los huecos.</p><details><summary>Ver las {len(originales)} filas y su diagnóstico</summary><div class="scroll"><table><thead><tr><th>Fila CSV</th><th>Minuto</th><th>Temperatura</th><th>Diagnóstico</th></tr></thead><tbody>{filas_html}</tbody></table></div></details></section>
<section><h2>2. Tendencia y separación temporal</h2><p>Las primeras <b>{len(entrenamiento)}</b> lecturas entrenan el modelo; las últimas <b>{len(prueba)}</b> lo ponen a prueba. La línea aprende una relación entre minuto y temperatura, sin utilizar las lecturas de prueba para ajustar sus parámetros.</p><img src="resultados/tendencia.png" alt="Temperaturas de entrenamiento y prueba, línea de regresión y predicción del siguiente minuto"><p class="note">Pendiente aprendida en entrenamiento: <b>{modelo[0]:.3f} °C por minuto</b>. Esta serie muestra una tendencia ascendente; no demuestra la causa del calentamiento.</p></section>
<section><h2>3. Resultado del modelo</h2><p>Error absoluto medio (MAE) de la regresión: <b>{mae:.3f} °C</b>.<br>MAE de repetir la última lectura de entrenamiento: <b>{mae_base:.3f} °C</b>. Un error menor indica un mejor ajuste en estas lecturas de prueba.</p><div class="scroll"><table><thead><tr><th>Minuto de prueba</th><th>Valor observado (°C)</th><th>Predicción (°C)</th><th>Error absoluto (°C)</th></tr></thead><tbody>{pruebas_html}</tbody></table></div></section>
<section><h2>4. Una predicción nueva</h2><p>Tras evaluar, ajustamos un modelo final con las {len(datos)} lecturas válidas para estimar el siguiente minuto.</p><div class="prediction">Minuto {siguiente:g}: {futuro:.2f} °C</div><p>Es una estimación, no una medición. Su error aún no puede calcularse porque no tenemos una lectura observada de ese minuto. El MAE anterior corresponde al modelo evaluado, no a esta predicción futura.</p></section>
<p class="note">Datos sintéticos para clase: el ejemplo no asegura precisión con sensores reales ni tendencias que cambien. Una sola división temporal ofrece evidencia limitada; no extrapoles esta recta a períodos largos.</p>
<footer>Para recalcular: edita <code>datos/lecturas.csv</code> y ejecuta <code>python analisis.py</code>. La página y los resultados se generan a partir de ese archivo; no requieren conexión para visualizarse.</footer>
</main></body></html>'''
    (BASE/'demo.html').write_text(pagina,encoding='utf-8')
    print(f'Calidad: {len(originales)} originales → {len(datos)} válidas.')
    print(f'MAE regresión: {mae:.3f} °C | MAE base: {mae_base:.3f} °C')
    print(f'Predicción minuto {siguiente:g}: {futuro:.2f} °C')
    print('Abre demo.html para visualizar los resultados.')


if __name__ == '__main__':
    main()
