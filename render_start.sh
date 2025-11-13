#!/bin/bash
# Render startup script - runs Data Server and Dash App

# Start Data Server in background
python data_server.py &

# Start Dash App on Render's PORT (foreground)
# Note: Webhook is built into the Dash app, no separate receiver needed
exec gunicorn main:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
