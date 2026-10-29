"""
Semana 6 · Demo: ESP32 con MicroPython publicando por MQTT
Arquitectura de Computadoras y Ensambladores 2 · Laboratorio

1. Instala el firmware de MicroPython en el ESP32 (https://micropython.org/download/ESP32_GENERIC/).
2. Abre Thonny, selecciona el intérprete "MicroPython (ESP32)" y guarda este archivo en la placa como main.py.
3. Usa como broker el Mosquitto de la Semana 5.
"""
import network
import time
from machine import Pin, ADC

try:
    from umqtt.simple import MQTTClient
except ImportError:
    # Si el firmware no trae umqtt, instálalo una vez con la placa conectada a Wi-Fi:
    #   import mip; mip.install("umqtt.simple")
    raise

WIFI_SSID = "TU_RED"
WIFI_CLAVE = "TU_CLAVE"
BROKER_IP = "192.168.1.10"
TOPICO = b"usac/arqui2/grupo1/micropython"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_CLAVE)
while not wlan.isconnected():
    time.sleep(0.5)
print("Conectado, IP:", wlan.ifconfig()[0])

sensor = ADC(Pin(34))
sensor.atten(ADC.ATTN_11DB)   # rango completo de 0 a ~3.3 V

cliente = MQTTClient("esp32-micropython", BROKER_IP)
cliente.connect()
print("Conectado al broker", BROKER_IP)

led = Pin(2, Pin.OUT)
n = 0
while True:
    valor = sensor.read()                 # 0..4095
    cliente.publish(TOPICO, str(valor).encode())
    led.value(not led.value())
    print("PUBLISH", n, valor)
    n += 1
    time.sleep(2)
