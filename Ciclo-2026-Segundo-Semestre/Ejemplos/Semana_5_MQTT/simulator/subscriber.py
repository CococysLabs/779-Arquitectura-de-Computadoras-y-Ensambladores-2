"""
Semana 5 · Suscriptor MQTT para observar QoS

Muestra cada mensaje recibido con su QoS efectivo y la bandera DUP.

Uso:
    python subscriber.py --qos 1
    python subscriber.py --topic "usac/arqui2/+/temperatura"
    python subscriber.py --qos 1 --persist     # sesión persistente (experimento de cola)
"""
import argparse
import json

import paho.mqtt.client as mqtt


def main():
    p = argparse.ArgumentParser(description="Suscriptor MQTT")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="usac/arqui2/#", help="admite comodines + y #")
    p.add_argument("--qos", type=int, choices=[0, 1, 2], default=0, help="QoS de la suscripción")
    p.add_argument("--persist", action="store_true",
                   help="sesión persistente: el broker guarda los mensajes QoS 1/2 mientras estás desconectado")
    args = p.parse_args()

    # Con sesión persistente el broker identifica al cliente por su client_id, así que debe ser fijo
    client_id = "suscriptor-persistente" if args.persist else ""
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id,
                          clean_session=not args.persist)

    def al_conectar(client, userdata, flags, reason_code, properties):
        print(f"Conectado ({reason_code}) · sesión previa encontrada: {flags.session_present}")
        client.subscribe(args.topic, qos=args.qos)

    def al_suscribir(client, userdata, mid, reason_code_list, properties):
        print(f"Suscrito a '{args.topic}' · QoS otorgado por el broker: {reason_code_list[0]}")

    def al_recibir(client, userdata, msg):
        try:
            datos = json.loads(msg.payload)
            texto = f"n={datos.get('n')} temp={datos.get('temp')} (publicado con QoS {datos.get('qos')})"
        except (ValueError, AttributeError):
            texto = msg.payload.decode(errors="replace")
        dup = "  DUP" if msg.dup else ""
        print(f"← {msg.topic} · recibido con QoS {msg.qos}{dup} · {texto}")

    cliente.on_connect = al_conectar
    cliente.on_subscribe = al_suscribir
    cliente.on_message = al_recibir
    cliente.connect(args.host, args.port, keepalive=30)
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("\nDesconectado")


if __name__ == "__main__":
    main()
