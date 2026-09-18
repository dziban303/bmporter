FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install \
    board \
    adafruit-circuitpython-bmp280 \
    prometheus_client \
    paho-mqtt \
    RPi.GPIO \
    gpiozero

COPY sensor.py .

EXPOSE 8000

CMD ["python", "-u", "sensor.py"]
