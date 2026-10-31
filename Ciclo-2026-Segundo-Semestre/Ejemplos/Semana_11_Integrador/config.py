"""Configuración del ejemplo local de IoT. No requiere servicios externos."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BROKER = os.getenv("MQTT_HOST", "127.0.0.1")
PUERTO = int(os.getenv("MQTT_PORT", "1883"))
DEVICE_ID = "nodo-01"
TOPIC_BASE = f"laboratorio/iot/{DEVICE_ID}"
TOPIC_LECTURA = f"{TOPIC_BASE}/lectura"
TOPIC_ESTADO = f"{TOPIC_BASE}/estado"
TOPIC_COMANDO = f"{TOPIC_BASE}/comando"
TOPIC_ACK = f"{TOPIC_BASE}/confirmacion"
TOPIC_CONEXION = f"{TOPIC_BASE}/conexion"
TOPIC_PERTURBACION = f"{TOPIC_BASE}/perturbacion"
DB_PATH = BASE_DIR / "datos" / "iot.sqlite3"
INTERVALO = 2.0
UMBRAL_ON = 28.0
UMBRAL_OFF = 26.0


def utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
