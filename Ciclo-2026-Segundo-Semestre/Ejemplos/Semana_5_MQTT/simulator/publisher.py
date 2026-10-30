"""
Semana 5 · Publicador MQTT simulado (reemplaza al ESP32 si no tienes hardware)

Publica lecturas de temperatura en un tópico con el QoS que elijas.

Uso:
    python publisher.py --qos 0
    python publisher.py --qos 1 --interval 1 --count 10
    python publisher.py --host 192.168.1.10 --topic usac/arqui2/grupo1/temperatura
"""
import argparse
import json
import math
import random
import time

import paho.mqtt.client as mqtt


def main():
    p = argparse.ArgumentParser(description="Publicador MQTT simulado")
    p.add_argument("--host", default="localhost", help="IP o nombre del broker")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="usac/arqui2/demo/temperatura")
    p.add_argument("--qos", type=int, choices=[0, 1, 2], default=0)
    p.add_argument("--interval", type=float, default=2.0, help="segundos entre mensajes")
    p.add_argument("--count", type=int, default=0, help="cantidad de mensajes (0 = infinito)")
    args = p.parse_args()

    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sim-pub-{random.randint(1000, 9999)}")

    def al_conectar(client, userdata, flags, reason_code, properties):
        print(f"Conectado a {args.host}:{args.port} ({reason_code})")

    def al_confirmar(client, userdata, mid, reason_code, properties):
        # QoS 0: se llama en cuanto el paquete sale (no hay confirmación del broker)
        # QoS 1: se llama al recibir PUBACK del broker
        # QoS 2: se llama al recibir PUBCOMP (fin del saludo de 4 pasos)
        evento = {0: "enviado (sin confirmación)", 1: "PUBACK recibido", 2: "PUBCOMP recibido"}[args.qos]
        print(f"  ← mid={mid}: {evento}")

    cliente.on_connect = al_conectar
    cliente.on_publish = al_confirmar
    cliente.connect(args.host, args.port, keepalive=30)
    cliente.loop_start()

    n = 0
    try:
        while args.count == 0 or n < args.count:
            temp = round(24 + 3 * math.sin(n / 5) + random.uniform(-0.3, 0.3), 2)
            payload = json.dumps({"n": n, "temp": temp, "qos": args.qos, "ts": int(time.time())})
            info = cliente.publish(args.topic, payload, qos=args.qos)
            print(f"→ PUBLISH mid={info.mid} qos={args.qos} {args.topic} {payload}")
            n += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(0.5)  # da tiempo a recibir las últimas confirmaciones
        cliente.disconnect()
        cliente.loop_stop()
        print(f"Fin: {n} mensajes publicados")


if __name__ == "__main__":
    main()
