#!/bin/sh
# Runs everything on a PC with emulated hardware: http://localhost:8080
# Press the "button" with: touch /tmp/entrega5_btn   (release: rm /tmp/entrega5_btn)
set -e
cd "$(dirname "$0")/.."
make -C hwctl hwctl-host
./hwctl/hwctl-host --mock &
HW=$!
trap 'kill $HW' EXIT INT TERM
sleep 0.5
PORT=${PORT:-8080} python3 buildroot/overlay/opt/entrega5/server.py
