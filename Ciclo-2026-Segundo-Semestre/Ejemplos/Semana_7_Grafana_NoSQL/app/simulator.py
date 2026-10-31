"""Sensor simulado: no requiere hardware. Responsable: Wendy Mazariegos."""
import json
import os
import time
import urllib.error
import urllib.request

# Ciclo de dos minutos: sube, cruza el umbral de 30 °C y luego desciende.
VALORES = [24, 24.5, 25, 25.5, 26, 27, 28, 29, 30, 31, 32, 33,
           32, 31, 30, 29, 28, 27, 26, 25.5, 25, 24.5, 24, 23.5]


def main():
    api = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    intervalo = float(os.getenv("INTERVALO_SEGUNDOS", "5"))
    i = 0
    while True:
        valor = VALORES[i % len(VALORES)]
        cuerpo = {"dispositivo": "sensor-01", "valor": valor,
                  "origen": "sensor-simulado", "ubicacion": "Laboratorio"}
        req = urllib.request.Request(api+"/lecturas", data=json.dumps(cuerpo).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as respuesta:
                doc = json.load(respuesta)
            print(f'{doc["fecha"]} | {valor} °C | {doc["estado"]} | id={doc["_id"]}', flush=True)
            i += 1
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"API no disponible; se reintentará: {error}", flush=True)
        time.sleep(intervalo)


if __name__ == "__main__":
    main()
