#!/bin/bash
# Render startup script - runs Dash App only

# Note: On Render, data is loaded directly from files (market_data.json / live_market_data.json)
# Data Server and NinjaTrader Receiver are not needed for cloud deployment
# Webhook is built into the Dash app at /ninjatrader/webhook

# Start Dash App on Render's PORT (foreground)
exec gunicorn main:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
