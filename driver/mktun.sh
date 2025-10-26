#!/usr/bin/env bash

set -exu

sudo openvpn --mktun --dev tun13
sudo ip link set tun13 up
sudo ip addr add 10.0.0.1/24 dev tun13
