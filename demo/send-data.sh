#!/usr/bin/env bash

set -exu

echo -n "hello, hacknotts!!" | nc -u -s 10.0.0.1 10.0.1.0 4000
