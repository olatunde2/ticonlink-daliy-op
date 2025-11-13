"""
NinjaTrader Webhook Receiver
Accepts HTTP POST requests from NinjaTrader and saves to live_market_data.json
"""
import json
import logging
from pathlib import Path
from flask import request, jsonify

logger = logging.getLogger(__name__)

def register_webhook_routes(server):
    """Register webhook endpoints with Flask server"""
    
    @server.route('/ninjatrader/webhook', methods=['POST'])
    def ninjatrader_webhook():
        """
        Receives market data from NinjaTrader via HTTP POST
        
        Expected JSON format:
        {
            "instrument": "QQQ",
            "bars": [
                {
                    "time": "2025-11-13T09:30:00",
                    "open": 500.25,
                    "high": 502.50,
                    "low": 499.75,
                    "close": 501.00,
                    "volume": 1500000,
                    "sma_20": 498.50,
                    "donchian_upper": 505.00,
                    "donchian_mean": 500.00,
                    "donchian_lower": 495.00,
                    "bollinger_upper": 503.00,
                    "bollinger_mean": 500.00,
                    "bollinger_lower": 497.00,
                    "bollinger_trigger": 1,
                    "momentum": 2.5,
                    "momentum_histogram": -1.2,
                    "squeeze": 1,
                    "squeeze_dots": 1,
                    "atr": 3.45,
                    "range": 2.75
                }
            ]
        }
        """
        try:
            # Get JSON data from POST request
            data = request.get_json()
            
            if not data:
                logger.error("No JSON data received")
                return jsonify({
                    "status": "error",
                    "message": "No JSON data received"
                }), 400
            
            # Validate required fields
            if 'instrument' not in data or 'bars' not in data:
                logger.error("Missing required fields: instrument or bars")
                return jsonify({
                    "status": "error",
                    "message": "Missing required fields: instrument and bars"
                }), 400
            
            instrument = data['instrument']
            bars = data['bars']
            
            if not isinstance(bars, list) or len(bars) == 0:
                logger.error("bars must be a non-empty list")
                return jsonify({
                    "status": "error",
                    "message": "bars must be a non-empty list"
                }), 400
            
            # Save to live_market_data.json
            output_file = Path('live_market_data.json')
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✓ Received {len(bars)} bars for {instrument} from NinjaTrader")
            logger.info(f"✓ Saved to {output_file}")
            
            return jsonify({
                "status": "success",
                "message": f"Received {len(bars)} bars for {instrument}",
                "bars_received": len(bars)
            }), 200
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return jsonify({
                "status": "error",
                "message": f"Invalid JSON: {str(e)}"
            }), 400
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return jsonify({
                "status": "error",
                "message": f"Internal error: {str(e)}"
            }), 500
    
    @server.route('/ninjatrader/health', methods=['GET'])
    def webhook_health():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "message": "NinjaTrader webhook receiver is running"
        }), 200
    
    logger.info("✓ NinjaTrader webhook endpoints registered:")
    logger.info("  POST /ninjatrader/webhook - Receive market data")
    logger.info("  GET  /ninjatrader/health  - Health check")
