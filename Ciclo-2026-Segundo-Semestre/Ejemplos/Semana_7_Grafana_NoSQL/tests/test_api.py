from datetime import datetime, timezone
import mongomock
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def entorno():
    coleccion = mongomock.MongoClient(tz_aware=True).temperaturas.lecturas
    with TestClient(create_app(coleccion, sembrar_datos=False)) as cliente:
        yield cliente, coleccion


def test_guardar_y_consultar_documento(entorno):
    cliente, coleccion = entorno
    respuesta = cliente.post('/lecturas', json={'valor':35, 'atributos':{'humedad':68}})
    assert respuesta.status_code == 201
    doc = respuesta.json()
    assert doc['estado'] == 'REVISAR'
    assert doc['unidad'] == '°C'
    guardado = coleccion.find_one({})
    assert isinstance(guardado['fecha'], datetime)
    assert guardado['atributos'] == {'humedad':68}
    assert str(guardado['_id']) == doc['_id']
    assert cliente.get('/lecturas').json() == [doc]


@pytest.mark.parametrize('valor', [-41, 126, 'no-es-un-numero'])
def test_rechaza_temperaturas_invalidas(entorno, valor):
    cliente, coleccion = entorno
    assert cliente.post('/lecturas', json={'valor':valor}).status_code == 422
    assert coleccion.count_documents({}) == 0


def test_fechas_y_limite_seleccionan_las_mas_recientes(entorno):
    cliente, _ = entorno
    for minuto in [3, 1, 4, 2]:
        cliente.post('/lecturas', json={'valor':20+minuto,
                     'fecha':f'2026-10-31T12:0{minuto}:00Z'})
    docs = cliente.get('/lecturas', params={'limite':2}).json()
    assert [x['valor'] for x in docs] == [23,24]
    docs = cliente.get('/lecturas', params={
        'desde':'2026-10-31T12:02:00Z', 'hasta':'2026-10-31T12:03:00Z'}).json()
    assert [x['valor'] for x in docs] == [22,23]


def test_zona_horaria_y_rango_invalido(entorno):
    cliente, _ = entorno
    assert cliente.post('/lecturas', json={'valor':24,'fecha':'2026-10-31T06:00:00'}).status_code == 422
    respuesta = cliente.post('/lecturas', json={'valor':24,'fecha':'2026-10-31T06:00:00-06:00'})
    assert respuesta.json()['fecha'] == '2026-10-31T12:00:00Z'
    assert cliente.get('/lecturas', params={'desde':'2026-10-31T12:00:00'}).status_code == 422
    assert cliente.get('/lecturas', params={'desde':'2026-10-31T13:00:00Z',
                                          'hasta':'2026-10-31T12:00:00Z'}).status_code == 422


def test_aislamiento_por_dispositivo_y_umbral(entorno):
    cliente, _ = entorno
    for sensor, valor in [('sensor-01',29.9),('sensor-01',30),('sensor-02',35)]:
        cliente.post('/lecturas', json={'valor':valor,'dispositivo':sensor})
    docs = cliente.get('/lecturas').json()
    assert [x['estado'] for x in docs] == ['NORMAL','REVISAR']
    assert len(cliente.get('/lecturas',params={'dispositivo':'sensor-02'}).json()) == 1


def test_historial_no_se_duplica():
    coleccion = mongomock.MongoClient(tz_aware=True).temperaturas.lecturas
    for _ in range(2):
        with TestClient(create_app(coleccion)) as cliente:
            assert cliente.get('/health').status_code == 200
            assert len(cliente.get('/lecturas').json()) == 30
    assert coleccion.count_documents({}) == 30
