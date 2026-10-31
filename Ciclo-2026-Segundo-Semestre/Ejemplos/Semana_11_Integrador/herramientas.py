"""Pequeñas herramientas manuales para las pruebas P04 y P05.

Uso:
    python herramientas.py invalido
    python herramientas.py historico
"""
import json
import sys
import time
import uuid


def invalido():
    import paho.mqtt.client as mqtt
    from config import BROKER, PUERTO, TOPIC_LECTURA, DEVICE_ID, utc_now
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"prueba-{uuid.uuid4().hex[:8]}")
    try:
        client.connect(BROKER, PUERTO, keepalive=15)
    except OSError as exc:
        sys.exit(f"No se pudo conectar al broker en {BROKER}:{PUERTO} ({exc}). ¿Está iniciado Mosquitto?")
    client.loop_start()
    paquete = {"message_id": str(uuid.uuid4()), "device_id": DEVICE_ID,
               "timestamp": utc_now(), "variable": "temperatura",
               "valor": 999, "unidad": "C", "estado": "valido"}
    info = client.publish(TOPIC_LECTURA, json.dumps(paquete), qos=1)
    info.wait_for_publish(timeout=5)
    client.disconnect()
    client.loop_stop()
    print("P04: se publicó 999 C. Debe aparecer evento 'dato_rechazado', NO una nueva lectura válida.")


def historico():
    import datos
    datos.inicializar()
    for r in datos.filas("SELECT timestamp, device_id, valor, unidad FROM lecturas ORDER BY id DESC LIMIT 10"):
        print(f"{r['timestamp']} | {r['device_id']} | {r['valor']:.2f} {r['unidad']}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("invalido", "historico"):
        sys.exit("Uso: python herramientas.py [invalido|historico]")
    globals()[sys.argv[1]]()
