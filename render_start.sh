#!/bin/bash

python data_server.py &
 
python ninjatrader_receiver.py &

exec gunicorn main:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
