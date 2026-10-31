#!/usr/bin/env python3
"""Grafica una captura CSV del Arduino o los resultados del simulador.

Uso: python simulacion/graficar_csv.py resultados/simulacion.csv --salida resultados/grafica.png
"""
import argparse
import csv
from pathlib import Path


def cargar_registros(archivo: Path) -> list[dict[str, float]]:
    datos = []
    with archivo.open(encoding="utf-8-sig") as handle:
        # Permite pegar directamente la salida del Serial Monitor:
        # ignora mensajes de estado que comienzan con '#'.
        lineas = (linea for linea in handle if linea.strip() and not linea.lstrip().startswith("#"))
        lector = csv.DictReader(lineas)
        columnas = {"tiempo_ms", "modo", "referencia", "luz", "pwm"}
        if not columnas.issubset(set(lector.fieldnames or [])):
            raise ValueError("El archivo debe incluir: " + ",".join(sorted(columnas)))
        for fila in lector:
            try:
                datos.append({clave: float(fila[clave]) for clave in columnas})
            except (ValueError, TypeError, KeyError):
                continue
    if not datos:
        raise ValueError("No se encontraron registros CSV validos")
    return datos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="CSV del Arduino o simulador")
    parser.add_argument("--salida", type=Path, default=Path("resultados/grafica.png"))
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise SystemExit("Instale dependencias: pip install -r simulacion/requirements.txt") from error

    datos = cargar_registros(args.csv)
    figura, (eje_luz, eje_pwm) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    nombres = {0: "Lazo abierto", 1: "Lazo cerrado (PID)"}
    for modo in (0, 1):
        serie = [r for r in datos if round(r["modo"]) == modo]
        if not serie:
            continue
        inicio_modo = serie[0]["tiempo_ms"]
        tiempos = [(r["tiempo_ms"] - inicio_modo) / 1000.0 for r in serie]
        eje_luz.plot(tiempos, [r["luz"] for r in serie], label=nombres[modo])
        eje_pwm.plot(tiempos, [r["pwm"] for r in serie], label=nombres[modo])
    # Referencia constante o variable, usa el orden de la captura.
    referencia = [r for r in datos if round(r["modo"]) == 1] or datos
    inicio_referencia = referencia[0]["tiempo_ms"]
    eje_luz.plot([(r["tiempo_ms"] - inicio_referencia) / 1000.0 for r in referencia],
                 [r["referencia"] for r in referencia], "--", label="Referencia")
    eje_luz.set_ylabel("Luz (ADC 0-1023)")
    eje_luz.set_title("Respuesta de control: iluminacion")
    eje_luz.grid(alpha=0.25)
    eje_luz.legend()
    eje_pwm.set_xlabel("Tiempo (s, desde el inicio de cada modo)")
    eje_pwm.set_ylabel("PWM (0-255)")
    eje_pwm.set_ylim(-5, 260)
    eje_pwm.grid(alpha=0.25)
    eje_pwm.legend()
    figura.tight_layout()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(args.salida, dpi=160)
    plt.close(figura)
    print(f"Grafica guardada: {args.salida}")


if __name__ == "__main__":
    main()
