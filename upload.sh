#!/usr/bin/env bash

ampy -p /dev/ttyUSB0 -b 115200 put ./main.py ./main.py
ampy -p /dev/ttyUSB0 -b 115200 put ./boot.py ./boot.py
ampy -p /dev/ttyUSB0 -b 115200 put ./env.json ./env.json
ampy -p /dev/ttyUSB0 -b 115200 put ./schema.json ./schema.json
ampy -p /dev/ttyUSB0 -b 115200 ls