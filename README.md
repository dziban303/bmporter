# rpi-bme280-to-prom

This Python script within a docker container will get data from a Bosch BM**P**280 — that is, the temperature and pressure model, *not* the humidity model (BM**E**280), as well as the CPU temperature from the Pi. It then computes some other metrics (altimeter, density altitude, pressure tendency), and serves these data as a Prometheus endpoint (port 8000) as well as sending the data via MQTT.

Just clone the repo, adjust if docker-compose.yml if needed and run 'docker-compose up -d' and off you go. The metrics will be available at http://<ip/dns>:<port>/metrics. 