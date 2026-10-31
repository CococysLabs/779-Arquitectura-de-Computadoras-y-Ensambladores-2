"""Prueba del recorrido real MongoDB → API → Infinity → Grafana.
Ejecutar desde la raíz del proyecto, con Docker Compose ya iniciado.
Responsable del material: Wendy Mazariegos.
"""
import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.error
import urllib.request


def pedir(url, datos=None, usuario=None, clave=None):
    headers = {'Content-Type':'application/json'}
    if usuario:
        token = base64.b64encode(f'{usuario}:{clave}'.encode()).decode()
        headers['Authorization'] = 'Basic '+token
    req = urllib.request.Request(url, headers=headers,
           data=None if datos is None else json.dumps(datos).encode())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def main():
    env = {}
    ruta = Path(__file__).resolve().parents[1]/'.env'
    for linea in ruta.read_text().splitlines():
        if linea.strip() and not linea.lstrip().startswith('#') and '=' in linea:
            clave, valor = linea.split('=',1)
            env[clave.strip()] = valor.strip()
    assert pedir('http://localhost:8000/health')['estado'] == 'ok'
    creado = pedir('http://localhost:8000/lecturas',
                   {'valor':35,'origen':'verificacion','atributos':{'prueba':True}})
    guardados = pedir('http://localhost:8000/lecturas')
    assert any(x['_id'] == creado['_id'] for x in guardados), 'Lectura no recuperada'
    assert pedir('http://localhost:3000/api/health')['database'] == 'ok'
    ahora = datetime.now(timezone.utc)
    url = 'http://api:8000/lecturas?dispositivo=sensor-01'
    consulta = {'queries':[{'refId':'A',
        'datasource':{'uid':'temperaturas-json','type':'yesoreyeram-infinity-datasource'},
        'type':'json','source':'url','parser':'backend','format':'table',
        'url':url,'url_options':{'method':'GET'},'root_selector':'',
        'columns':[{'selector':'_id','text':'ID','type':'string'},
                   {'selector':'valor','text':'Temperatura','type':'number'}]}],
        'from':str(int((ahora-timedelta(minutes=15)).timestamp()*1000)),
        'to':str(int(ahora.timestamp()*1000))}
    respuesta = pedir('http://localhost:3000/api/ds/query', consulta,
                      env['GRAFANA_USER'], env['GRAFANA_PASSWORD'])
    resultado = respuesta.get('results',{}).get('A',{})
    assert not resultado.get('error'), resultado.get('error')
    marcos = resultado.get('frames',[])
    encontrado = False
    for marco in marcos:
        campos = marco.get('schema',{}).get('fields',[])
        valores = marco.get('data',{}).get('values',[])
        for i,campo in enumerate(campos):
            if campo.get('name') == 'ID' and creado['_id'] in valores[i]:
                encontrado = True
    assert encontrado, 'Grafana no devolvió la lectura: revisa Infinity y sus logs'
    print('OK: lectura de 35 °C guardada y recuperada a través de Grafana.')
    print('ID MongoDB:', creado['_id'])
    print('Abre http://localhost:3000/d/temperatura-demo y busca el punto de 35 °C.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, urllib.error.URLError, AssertionError, KeyError, ValueError) as error:
        raise SystemExit(f'No se completó la verificación: {error}\n'
                         'Revisa docker compose ps y docker compose logs grafana api.')
