import asyncio
import websockets
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class NinjaTraderReceiver:
    """WebSocket server that receives live data from NinjaTrader"""

    def __init__(self, host="0.0.0.0", port=9000):
        self.host = host
        self.port = port
        self.live_data = None
        self.last_update = None
        self.data_file = Path("live_market_data.json")

    async def handle_client(self, websocket):
        """Handle incoming WebSocket connection from NinjaTrader"""
        client_id = id(websocket)
        logging.info(
            f"NinjaTrader client {client_id} connected from {websocket.remote_address}"
        )

        try:
            async for message in websocket:
                try:
                    message_size = len(message)
                    logging.info(
                        f"Received {message_size:,} bytes from NinjaTrader client {client_id}"
                    )

                    # Receive JSON data from NinjaTrader
                    data = json.loads(message)

                    # Store in memory
                    self.live_data = data
                    self.last_update = datetime.now()

                    # Also save to file for persistence
                    with open(self.data_file, "w") as f:
                        json.dump(data, f)

                    bar_count = len(data) if isinstance(data, dict) else 0
                    logging.info(
                        f"✓ Successfully received {bar_count} bars from NinjaTrader"
                    )
                    logging.info(f"✓ Data saved to {self.data_file}")

                    # Send acknowledgment
                    response = {
                        "status": "success",
                        "bars_received": bar_count,
                        "timestamp": self.last_update.isoformat(),
                    }
                    await websocket.send(json.dumps(response))
                    logging.info(f"✓ Sent acknowledgment to NinjaTrader")

                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON from client {client_id}: {e}")
                    try:
                        await websocket.send(
                            json.dumps({"status": "error", "message": "Invalid JSON"})
                        )
                    except:
                        pass
                except Exception as e:
                    logging.error(f"Error processing message from {client_id}: {e}")
                    import traceback

                    logging.error(traceback.format_exc())
                    try:
                        await websocket.send(
                            json.dumps({"status": "error", "message": str(e)})
                        )
                    except:
                        pass

        except websockets.exceptions.ConnectionClosed:
            logging.info(f"NinjaTrader client {client_id} disconnected")
        except Exception as e:
            logging.error(f"Error handling client {client_id}: {e}")
            import traceback

            logging.error(traceback.format_exc())

    def get_live_data(self):
        """Return live data if available and recent"""
        if self.live_data is None:
            # Try loading from file
            if self.data_file.exists():
                try:
                    with open(self.data_file, "r") as f:
                        self.live_data = json.load(f)
                    logging.info(f"Loaded live data from {self.data_file}")
                except Exception as e:
                    logging.error(f"Error loading live data file: {e}")
                    return None
            else:
                return None

        return self.live_data

    async def start(self):
        """Start the WebSocket receiver server"""
        logging.info(
            f"Starting NinjaTrader receiver on ws://{self.host}:{self.port}/data"
        )

        # Increase message size limit to handle large data (default is 1MB, we need more)
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            ping_interval=None,  # Disable ping for large transfers
        ):
            logging.info(
                f"NinjaTrader receiver listening on ws://{self.host}:{self.port}/data"
            )
            logging.info(f"Max message size: 10MB")
            logging.info("Waiting for NinjaTrader to send data...")
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    receiver = NinjaTraderReceiver(host="0.0.0.0", port=9000)
    asyncio.run(receiver.start())
