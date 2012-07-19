#!/bin/bash
tools/server.py --log=DEBUG --address=tcp:localhost:2718 & pid=$!
sleep 0.2
tools/client.py tcp:localhost:2718
kill $pid
