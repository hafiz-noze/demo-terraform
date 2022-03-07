#!/bin/bash

exec python /cmd/send/send.py &
exec python /cmd/receive/receive.py