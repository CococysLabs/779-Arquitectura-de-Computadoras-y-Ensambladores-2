"""Contrato de mensajes MQTT y validación de datos no confiables."""
import json
import math
from datetime import datetime, timezone
from config import DEVICE_ID


class MensajeInvalido(ValueError):
    pass


def cargar_json(payload):
    try:
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        dato = json.loads(payload)
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        raise MensajeInvalido("JSON no interpretable") from exc
    if not isinstance(dato, dict):
        raise MensajeInvalido("Se esperaba un objeto JSON")
    return dato


def _timestamp(t):
    if not isinstance(t, str):
        raise MensajeInvalido("timestamp ausente")
    try:
        fecha = datetime.fromisoformat(t.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MensajeInvalido("timestamp sin formato ISO 8601") from exc
    if fecha.tzinfo is None:
        raise MensajeInvalido("timestamp debe incluir zona horaria")
    return fecha.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validar_lectura(data):
    if data.get("device_id") != DEVICE_ID:
        raise MensajeInvalido("identificador de dispositivo desconocido")
    if data.get("variable") != "temperatura" or data.get("unidad") != "C":
        raise MensajeInvalido("variable o unidad inesperada")
    if data.get("estado") != "valido":
        raise MensajeInvalido("estado de lectura no válido")
    v = data.get("valor")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not -20 <= v <= 80:
        raise MensajeInvalido("temperatura fuera del rango de -20 a 80 C")
    identificador = data.get("message_id")
    if not isinstance(identificador, str) or not (8 <= len(identificador) <= 64):
        raise MensajeInvalido("message_id ausente o inválido")
    return {
        "message_id": identificador,
        "device_id": DEVICE_ID,
        "timestamp": _timestamp(data.get("timestamp")),
        "variable": "temperatura",
        "valor": round(float(v), 2),
        "unidad": "C",
        "estado": "valido",
    }


def validar_estado(data):
    if data.get("device_id") != DEVICE_ID or not isinstance(data.get("fan"), bool):
        raise MensajeInvalido("estado del actuador inválido")
    if data.get("modo") not in ("automatico", "manual"):
        raise MensajeInvalido("modo desconocido")
    return {"device_id": DEVICE_ID, "fan": data["fan"], "modo": data["modo"], "timestamp": _timestamp(data.get("timestamp"))}


def validar_ack(data):
    if data.get("device_id") != DEVICE_ID or not isinstance(data.get("aplicado"), bool):
        raise MensajeInvalido("confirmación inválida")
    if not isinstance(data.get("command_id"), str) or not data["command_id"]:
        raise MensajeInvalido("command_id ausente")
    return {"command_id": data["command_id"], "aplicado": data["aplicado"], "timestamp": _timestamp(data.get("timestamp"))}


def validar_comando(data):
    if not isinstance(data, dict) or data.get("modo") not in ("automatico", "manual"):
        raise MensajeInvalido("modo debe ser 'automatico' o 'manual'")
    if data["modo"] == "manual" and not isinstance(data.get("fan"), bool):
        raise MensajeInvalido("en modo manual, fan debe ser true o false")
    return {"modo": data["modo"], "fan": data.get("fan") if data["modo"] == "manual" else None}
