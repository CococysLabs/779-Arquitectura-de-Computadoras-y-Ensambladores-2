#!/usr/bin/env python3
"""Simulacion didactica del mismo sistema LED-LDR sin hardware.

Modelo: un sistema de primer orden, con luz ambiente, contribucion de LED,
perturbacion de sombra y dinamica del sensor. NO sustituye mediciones reales.
Genera CSV compatible con el del sketch Arduino.

Uso: python simulacion/simular_pid.py --salida resultados/simulacion.csv
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DT = 0.1
REFERENCIA = 380.0
PWM_ABIERTO = 120


def limitar(x: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(maximo, x))


@dataclass
class PID:
    kp: float = 0.90
    ki: float = 0.35
    kd: float = 0.025
    integral: float = 0.0
    derivada_filtrada: float = 0.0
    ultima_medida: float = 180.0

    def actualizar(self, referencia: float, medida: float, dt: float) -> tuple[int, float, float, float]:
        error = referencia - medida
        p = self.kp * error
        derivada_medida = (medida - self.ultima_medida) / dt
        self.derivada_filtrada = 0.7 * self.derivada_filtrada + 0.3 * derivada_medida
        d = -self.kd * self.derivada_filtrada
        candidata = limitar(self.integral + self.ki * error * dt, -255, 255)
        salida_candidata = p + candidata + d
        saturado_arriba = salida_candidata > 255 and error > 0
        saturado_abajo = salida_candidata < 0 and error < 0
        if not saturado_arriba and not saturado_abajo:
            self.integral = candidata
        i = self.integral
        pwm = round(limitar(p + i + d, 0, 255))
        self.ultima_medida = medida
        return pwm, p, i, d


@dataclass
class PlantaIluminacion:
    luz: float = 180.0
    luz_ambiente: float = 180.0
    ganancia_led: float = 1.5
    constante_tiempo: float = 0.6

    def avanzar(self, pwm: int, sombra: float, dt: float) -> float:
        # El LED se representa como una fuente de luz controlable (0 a 255).
        equilibrio = self.luz_ambiente + self.ganancia_led * pwm + sombra
        alpha = limitar(dt / self.constante_tiempo, 0.0, 1.0)
        self.luz += alpha * (equilibrio - self.luz)
        return self.luz


def ejecutar_simulacion(duracion: float = 60.0, dt: float = DT) -> list[dict[str, float | int]]:
    """Simula ambos modos con la MISMA perturbacion entre 30 y 45 s."""
    if duracion <= 0 or dt <= 0:
        raise ValueError("duracion y dt deben ser positivos")
    plantas = {0: PlantaIluminacion(), 1: PlantaIluminacion()}
    pid = PID(ultima_medida=plantas[1].luz)
    datos = []
    pasos = int(round(duracion / dt))
    for paso in range(pasos + 1):
        t = paso * dt
        sombra = -85.0 if 30.0 <= t < 45.0 else 0.0
        for modo in (0, 1):
            planta = plantas[modo]
            medida = planta.luz  # lectura ANTES de actuar: realimentacion causal
            error = REFERENCIA - medida
            if modo == 0:
                pwm, p, i, d = PWM_ABIERTO, 0.0, 0.0, 0.0
            else:
                pwm, p, i, d = pid.actualizar(REFERENCIA, medida, dt)
            planta.avanzar(pwm, sombra, dt)
            datos.append({
                "tiempo_ms": round(t * 1000), "modo": modo,
                "referencia": round(REFERENCIA, 2),
                "luz": round(medida, 2), "pwm": pwm,
                "error": round(error, 2),
                "p": round(p, 2), "i": round(i, 2), "d": round(d, 2),
            })
    return datos


def guardar_csv(registros: list[dict[str, float | int]], salida: Path) -> None:
    salida.parent.mkdir(parents=True, exist_ok=True)
    campos = ["tiempo_ms", "modo", "referencia", "luz", "pwm", "error", "p", "i", "d"]
    with salida.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(registros)


def resumen(registros: list[dict[str, float | int]], inicio: float, fin: float) -> dict[int, float]:
    salida = {}
    for modo in (0, 1):
        errores = [abs(float(x["error"])) for x in registros
                   if x["modo"] == modo and inicio <= float(x["tiempo_ms"]) / 1000 < fin]
        salida[modo] = sum(errores) / len(errores) if errores else float("nan")
    return salida


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path("resultados/simulacion.csv"))
    args = parser.parse_args()
    registros = ejecutar_simulacion()
    guardar_csv(registros, args.salida)
    errores = resumen(registros, 40.0, 45.0)  # tras asentarse la perturbacion
    print(f"CSV generado: {args.salida}")
    print("Error absoluto medio (40-45 s, bajo sombra):")
    print(f"  Abierto: {errores[0]:.1f} unidades ADC")
    print(f"  Cerrado: {errores[1]:.1f} unidades ADC")
    print("Los resultados corresponden a un modelo didactico, no a medidas fisicas.")


if __name__ == "__main__":
    main()
