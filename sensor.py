import board
import adafruit_bmp280
import paho.mqtt.publish as publish
import time
import json
import socket
from collections import deque

# Imports for CPU temperature on the PI
from gpiozero import CPUTemperature

# Imports for proemtheus
from prometheus_client import Gauge, start_http_server, REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR

# Create Prometheus gauges
# gh = Gauge('humidity', 'Humidity percentage measured by the sensor')
gt = Gauge('temperature', 'Temperature measured by the sensor in celsius')
gp = Gauge('pressure', 'Pressure measured by the sensor in hPa')
ct = Gauge('cpu_temp', 'RPI CPU Temp')
ga = Gauge('altitude', 'Altitude measured by the sensor in meters')
gd = Gauge('density_altitude', 'Density altitude calculated from pressure and temperature in feet')

i2c = board.I2C()
sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c,0x76)   # i2c address on this one is 0x76

sensor.sea_level_pressure = 1013.25  # standard atmospheric pressure at sea level, zero relevance to real life
sensor.iir_filter = adafruit_bmp280.IIR_FILTER_X16 # IIR filter at max to reject bogus readings. default is 16x
sensor.overscan_pressure = adafruit_bmp280.OVERSCAN_X16 # scans 16 times longer than shortest interval for more accurate reading. default is 16x
sensor.overscan_temperature = adafruit_bmp280.OVERSCAN_X4 # scans 4 times longer than shortest interval. default is 2x for temp

history = deque(maxlen=360)  # 3 hrs of readings at 30s interval

MQTT_BROKER = "192.168.0.175"
TOPIC = "dzicave/pimedia/sensors"
METRICS_PORT = 8000


def density_altitude(pressure_hpa, temp_c, station_elevation_m=0):
  # pressure altitude: how high the current pressure "looks like" vs standard atmosphere
  pressure_altitude_ft = (1013.25 - pressure_hpa) * 27  # ~27 ft per hPa, rough but standard approximation

  # ISA standard temp at this pressure altitude (lapse rate 1.98°C/1000ft)
  isa_temp_c = 15 - (1.98 * pressure_altitude_ft / 1000)

  da_ft = pressure_altitude_ft + 120 * (temp_c - isa_temp_c)
  return round(da_ft, 1)


def classify_tendency(pressure_history):
  if len(pressure_history) < 2:
    return "insufficient data"
  delta = pressure_history[-1] - pressure_history[0]  # change over the window
  if delta <= -1.6:
    return "falling rapidly"
  elif delta <= -0.6:
    return "falling"
  elif delta >= 1.6:
    return "rising rapidly"
  elif delta >= 0.6:
    return "rising"
  return "steady"


start_http_server(METRICS_PORT)
print("Serving sensor metrics on :{}".format(METRICS_PORT))

while True:
  try:
    cpu_temp = round(CPUTemperature().temperature, 1)
    temperature = round(sensor.temperature, 2)
    pressure_hpa = sensor.pressure
    pressure_cal = round(pressure_hpa - 1.86, 2) # compared with sixel reading, which i'm taking as ground truth
    alt = round(sensor.altitude, 2)
    history.append(pressure_cal)

    # gh.set(humidity)
    gt.set(temperature)
    gp.set(pressure_cal)
    ct.set(cpu_temp)
    ga.set(alt)
    gd.set(density_altitude(pressure_hpa, temperature))

    data = {"CPU_temp": cpu_temp, "temperature": temperature, "pressure": pressure_cal, "altitude": alt, "density_altitude": density_altitude(pressure_hpa, temperature), "tendency": classify_tendency(history)}

    payload = json.dumps(data)  # Serialize data to JSON format
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    print(f"{timestamp} - {payload}")

    publish.single(TOPIC, payload=payload, hostname=MQTT_BROKER)

  except socket.timeout as e:
      # Handle the socket timeout exception
      print(f"Error: {e}. Retrying in 30 seconds...")
      time.sleep(30)  # Adjust as needed

  except Exception as e:
      # Handle other exceptions
      print(f"An error occurred: {e}")

  time.sleep(30)  # Adjust as needed
