"""Backend: MQTT -> validación -> SQLite -> API/Panel Flask.

Ejecutar: python backend.py
"""
import json
import logging
import threading
import uuid
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request

import datos
from config import (BROKER, PUERTO, DEVICE_ID, TOPIC_LECTURA, TOPIC_ESTADO,
                    TOPIC_COMANDO, TOPIC_ACK, TOPIC_CONEXION, TOPIC_PERTURBACION, utc_now)
from protocolo import (MensajeInvalido, cargar_json, validar_lectura, validar_estado,
                       validar_ack, validar_comando)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backend")
# El panel consulta la API cada 2 s; sin esto, la consola se llena de líneas
# "GET /api/..." y no se ven los mensajes de MQTT (útiles para la prueba P03).
logging.getLogger("werkzeug").setLevel(logging.WARNING)
app = Flask(__name__)


class ServicioMQTT:
    def __init__(self):
        self._lock = threading.Lock()
        self._conectado = False
        self._dispositivo_online = False
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iot-backend-lab")
        self.client.on_connect = self._al_conectar
        self.client.on_disconnect = self._al_desconectar
        self.client.on_message = self._al_mensaje
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)

    @property
    def conectado(self):
        with self._lock:
            return self._conectado

    @property
    def dispositivo_online(self):
        with self._lock:
            return self._dispositivo_online

    def iniciar(self):
        self.client.connect_async(BROKER, PUERTO, keepalive=15)
        self.client.loop_start()

    def _al_conectar(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("Broker rechazó conexión: %s", reason_code)
            return
        with self._lock:
            self._conectado = True
        client.subscribe([(TOPIC_LECTURA, 1), (TOPIC_ESTADO, 1),
                          (TOPIC_ACK, 1), (TOPIC_CONEXION, 1)])
        datos.agregar_evento("conexion", "Backend conectado a MQTT")
        log.info("MQTT conectado, suscripciones activas")

    def _al_desconectar(self, client, userdata, disconnect_flags, reason_code, properties):
        with self._lock:
            self._conectado = False
            self._dispositivo_online = False
        datos.agregar_evento("desconexion", f"Se perdió la conexión con MQTT: {reason_code}")
        log.warning("MQTT desconectado: %s. Reconexión automática en curso", reason_code)

    def _al_mensaje(self, client, userdata, msg):
        try:
            if msg.topic == TOPIC_CONEXION:
                texto = msg.payload.decode("utf-8")
                if texto not in ("online", "offline"):
                    raise MensajeInvalido("estado de conexión desconocido")
                with self._lock:
                    self._dispositivo_online = texto == "online"
                datos.agregar_evento("dispositivo", f"Dispositivo: {texto}")
                return
            paquete = cargar_json(msg.payload)
            if msg.topic == TOPIC_LECTURA:
                dato = validar_lectura(paquete)
                if not datos.guardar_lectura(dato):
                    datos.agregar_evento("duplicado", f"Lectura repetida: {dato['message_id']}")
            elif msg.topic == TOPIC_ESTADO:
                estado = validar_estado(paquete)
                datos.guardar_estado(estado)
                datos.agregar_evento("actuador", f"Ventilador {'ON' if estado['fan'] else 'OFF'} / {estado['modo']}")
            elif msg.topic == TOPIC_ACK:
                ack = validar_ack(paquete)
                if datos.confirmar_comando(ack["command_id"], ack["aplicado"]):
                    datos.agregar_evento("confirmacion", f"{ack['command_id'][:8]}: {'OK' if ack['aplicado'] else 'ERROR'}")
                else:
                    datos.agregar_evento("confirmacion", "Confirmación sin comando asociado")
        except (MensajeInvalido, ValueError) as exc:
            datos.agregar_evento("dato_rechazado", f"{msg.topic}: {exc}")
            log.warning("Mensaje rechazado: %s", exc)
        except Exception:
            log.exception("Error al procesar mensaje MQTT")
            datos.agregar_evento("error", "Fallo interno al procesar mensaje")

    def publicar(self, topic, contenido):
        if not self.conectado:
            return False
        info = self.client.publish(topic, json.dumps(contenido, ensure_ascii=False), qos=1)
        return info.rc == mqtt.MQTT_ERR_SUCCESS


servicio = ServicioMQTT()


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/estado")
def estado():
    lecturas = datos.ultimas_lecturas(1)
    ultima = lecturas[0] if lecturas else None
    # Solo se considera activo al nodo si la última lectura no está obsoleta.
    actual = False
    if ultima:
        try:
            fecha = datetime.fromisoformat(ultima["recibido"].replace("Z", "+00:00"))
            actual = (datetime.now(timezone.utc) - fecha).total_seconds() < 15
        except ValueError:
            pass
    return jsonify({"broker_conectado": servicio.conectado,
                    "dispositivo_conectado": servicio.dispositivo_online and servicio.conectado and actual,
                    "ultima_lectura": ultima,
                    "actuador": datos.ultimo_estado(),
                    "cantidad_lecturas": datos.filas("SELECT COUNT(*) AS cantidad FROM lecturas")[0]["cantidad"]})


@app.get("/api/lecturas")
def lecturas():
    try:
        limite = max(1, min(100, int(request.args.get("limit", 50))))
    except (ValueError, TypeError):
        return jsonify({"error": "limit debe ser un entero"}), 400
    return jsonify(datos.ultimas_lecturas(limite))


@app.get("/api/eventos")
def eventos():
    return jsonify(datos.eventos())


@app.get("/api/comandos")
def comandos():
    return jsonify(datos.comandos())


@app.post("/api/comando")
def comando():
    try:
        contenido = validar_comando(request.get_json(silent=True))
    except MensajeInvalido as exc:
        return jsonify({"error": str(exc)}), 400
    if not servicio.conectado:
        return jsonify({"error": "Broker MQTT no conectado"}), 503
    command_id = str(uuid.uuid4())
    mensaje = {**contenido, "command_id": command_id, "timestamp": utc_now()}
    datos.guardar_comando(command_id, contenido["modo"], contenido["fan"])
    if not servicio.publicar(TOPIC_COMANDO, mensaje):
        datos.confirmar_comando(command_id, False)
        return jsonify({"error": "No se pudo publicar el comando"}), 503
    datos.agregar_evento("comando", f"Solicitud {contenido['modo']} / {contenido['fan']}")
    return jsonify({"command_id": command_id, "estado": "pendiente"}), 202


@app.post("/api/perturbacion")
def perturbacion():
    if not servicio.conectado:
        return jsonify({"error": "Broker MQTT no conectado"}), 503
    if not servicio.publicar(TOPIC_PERTURBACION, {"delta": 6}):
        return jsonify({"error": "No se pudo publicar la perturbación"}), 503
    return jsonify({"resultado": "Se solicitó aumento de temperatura de 6 C"}), 202


if __name__ == "__main__":
    datos.inicializar()
    servicio.iniciar()
    print("Panel disponible en http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)
