"""Nodo IoT simulado: sensor, controlador con histéresis y ventilador virtual.

Ejecutar: python dispositivo.py
"""
import json
import logging
import random
import threading
import time
import uuid

import paho.mqtt.client as mqtt

from config import (BROKER, PUERTO, DEVICE_ID, INTERVALO, UMBRAL_ON, UMBRAL_OFF,
                    TOPIC_LECTURA, TOPIC_COMANDO, TOPIC_ESTADO, TOPIC_ACK,
                    TOPIC_CONEXION, TOPIC_PERTURBACION, utc_now)
from protocolo import MensajeInvalido, cargar_json, validar_comando

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dispositivo")


class NodoSimulado:
    def __init__(self):
        self._lock = threading.Lock()
        self._online = threading.Event()
        self.temperatura = 25.4
        self.fan = False
        self.modo = "automatico"
        self._procesados = set()
        self._orden = []
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"iot-{DEVICE_ID}")
        self.client.will_set(TOPIC_CONEXION, payload="offline", qos=1, retain=True)
        self.client.on_connect = self._al_conectar
        self.client.on_disconnect = self._al_desconectar
        self.client.on_message = self._al_mensaje
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)

    def _al_conectar(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("Conexión rechazada: %s", reason_code)
            return
        client.subscribe([(TOPIC_COMANDO, 1), (TOPIC_PERTURBACION, 1)])
        client.publish(TOPIC_CONEXION, "online", qos=1, retain=True)
        self._online.set()
        self._publicar_estado()
        log.info("Nodo conectado a MQTT")

    def _al_desconectar(self, client, userdata, disconnect_flags, reason_code, properties):
        self._online.clear()
        log.warning("Conexión perdida: %s. Reconectando...", reason_code)

    def _publicar(self, topic, data, retain=False):
        if self._online.is_set():
            self.client.publish(topic, json.dumps(data, ensure_ascii=False), qos=1, retain=retain)

    def _publicar_estado(self):
        with self._lock:
            data = {"device_id": DEVICE_ID, "fan": self.fan, "modo": self.modo, "timestamp": utc_now()}
        self._publicar(TOPIC_ESTADO, data, retain=True)

    def _al_mensaje(self, client, userdata, msg):
        try:
            data = cargar_json(msg.payload)
            if msg.topic == TOPIC_PERTURBACION:
                delta = data.get("delta")
                if isinstance(delta, bool) or not isinstance(delta, (int, float)) or not 2 <= delta <= 15:
                    raise MensajeInvalido("perturbación fuera de rango")
                with self._lock:
                    self.temperatura = min(65, self.temperatura + delta)
                log.info("Perturbación aplicada: +%s C", delta)
                return
            if msg.topic == TOPIC_COMANDO:
                comando = validar_comando(data)
                command_id = data.get("command_id")
                if not isinstance(command_id, str) or not command_id:
                    raise MensajeInvalido("command_id inválido")
                with self._lock:
                    if command_id not in self._procesados:
                        self.modo = comando["modo"]
                        if self.modo == "manual":
                            self.fan = comando["fan"]
                        else:
                            self._control_automatico()
                        self._procesados.add(command_id)
                        self._orden.append(command_id)
                        if len(self._orden) > 100:
                            viejo = self._orden.pop(0)
                            self._procesados.discard(viejo)
                self._publicar_estado()
                self._publicar(TOPIC_ACK, {"command_id": command_id, "device_id": DEVICE_ID,
                                          "aplicado": True, "timestamp": utc_now()})
                log.info("Comando confirmado: %s", command_id[:8])
        except MensajeInvalido as exc:
            log.warning("Comando/perturbación ignorado: %s", exc)
        except Exception:
            log.exception("Error al recibir mensaje")

    def _control_automatico(self):
        """Llamar únicamente con self._lock adquirido."""
        if not self.fan and self.temperatura >= UMBRAL_ON:
            self.fan = True
        elif self.fan and self.temperatura <= UMBRAL_OFF:
            self.fan = False

    def _simular_paso(self):
        """Modelo didáctico, NO corresponde a mediciones de un sensor real."""
        with self._lock:
            self.temperatura += (-0.36 if self.fan else 0.12) + random.uniform(-0.06, 0.06)
            self.temperatura = min(65, max(21, self.temperatura))
            previo = self.fan
            if self.modo == "automatico":
                self._control_automatico()
            cambio = self.fan != previo
            temperatura = round(self.temperatura, 2)
            fan = self.fan
            modo = self.modo
        lectura = {"message_id": str(uuid.uuid4()), "device_id": DEVICE_ID,
                   "timestamp": utc_now(), "variable": "temperatura", "valor": temperatura,
                   "unidad": "C", "estado": "valido"}
        self._publicar(TOPIC_LECTURA, lectura)
        if cambio:
            self._publicar_estado()
        log.info("Temperatura: %.2f C | Ventilador: %s | Modo: %s", temperatura, "ON" if fan else "OFF", modo)

    def ejecutar(self):
        self.client.connect_async(BROKER, PUERTO, keepalive=15)
        self.client.loop_start()
        try:
            while True:
                if self._online.is_set():
                    self._simular_paso()
                time.sleep(INTERVALO)
        except KeyboardInterrupt:
            log.info("Deteniendo nodo")
        finally:
            if self._online.is_set():
                info = self.client.publish(TOPIC_CONEXION, "offline", qos=1, retain=True)
                info.wait_for_publish(timeout=2)
            self.client.disconnect()
            self.client.loop_stop()


if __name__ == "__main__":
    NodoSimulado().ejecutar()
