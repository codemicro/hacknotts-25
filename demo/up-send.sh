#!/usr/bin/env bash

set -exu

sudo ip tuntap add mode tun dev tun13
sudo ip addr add local 10.0.0.1/24 remote 10.0.1.0 dev tun13
sudo ip link set tun13 up
