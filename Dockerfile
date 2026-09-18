FROM python:3.13-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    --prefix=/install \
    board \
    adafruit-circuitpython-bmp280 \
    prometheus_client \
    paho-mqtt \
    RPi.GPIO \
    gpiozero

FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /install /usr/local
COPY sensor.py .

EXPOSE 8000

CMD ["python", "-u", "sensor.py"]
