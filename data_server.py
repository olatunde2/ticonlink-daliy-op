import asyncio
import websockets
import json
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MarketDataServer:
    def __init__(
        self, data_file="market_data.json", live_data_file="live_market_data.json"
    ):
        self.data_file = data_file
        self.live_data_file = live_data_file
        self.market_data = {}
        self.using_live_data = False
        self.last_mtime = None
        self.last_instrument = None
        self.load_data()

    def load_data(self):
        """Load data from live source first, fall back to static JSON"""
        # Try live data first
        try:
            if os.path.exists(self.live_data_file):
                with open(self.live_data_file, "r") as f:
                    self.market_data = json.load(f)
                self.using_live_data = True
                self.last_mtime = os.path.getmtime(self.live_data_file)

                # Get instrument from first bar
                first_bar = next(iter(self.market_data.values()), {})
                new_instrument = first_bar.get("Instrument", "UNKNOWN")

                if new_instrument != self.last_instrument:
                    logging.info(
                        f"✓ Loaded {len(self.market_data)} bars from LIVE NinjaTrader data - Instrument: {new_instrument}"
                    )
                    self.last_instrument = new_instrument
                return
        except Exception as e:
            logging.warning(f"Could not load live data: {e}")

        # Fall back to static JSON
        try:
            with open(self.data_file, "r") as f:
                self.market_data = json.load(f)
            self.using_live_data = False
            logging.info(
                f"⚠ Loaded {len(self.market_data)} bars from FALLBACK JSON file"
            )
        except Exception as e:
            logging.error(f"Error loading market data: {e}")
            self.market_data = {}

    async def watch_file_changes(self):
        """Background task to watch for file changes and reload data"""
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                if os.path.exists(self.live_data_file):
                    current_mtime = os.path.getmtime(self.live_data_file)

                    # If file has been modified, reload
                    if self.last_mtime is None or current_mtime > self.last_mtime:
                        old_instrument = self.last_instrument
                        self.load_data()

                        # Log only if instrument changed
                        if old_instrument and old_instrument != self.last_instrument:
                            logging.info(
                                f"🔄 Auto-reloaded: Symbol changed from {old_instrument} to {self.last_instrument}"
                            )
            except Exception as e:
                logging.error(f"Error watching file: {e}")
                await asyncio.sleep(5)

    def get_available_tickers(self):
        tickers = set()
        for date_str, bar_data in self.market_data.items():
            instrument = bar_data.get("Instrument")
            if instrument:
                tickers.add(instrument)
        return sorted(list(tickers))

    def convert_to_full_data(self, data_dict):
        bars = []
        for date_str, bar_data in data_dict.items():
            try:
                panels = bar_data.get("Panels", {})
                panel_1 = panels.get("Panel 1", {})
                panel_q = panels.get("Panel ?", {})
                panel_2 = panels.get("Panel 2", {})
                panel_3 = panels.get("Panel 3", {})
                panel_4 = panels.get("Panel 4", {})

                panel_5 = panels.get("Panel 5", {})

                full_bar = {
                    "time": bar_data.get("Date", date_str),
                    "open": float(bar_data.get("Open", 0)),
                    "high": float(bar_data.get("High", 0)),
                    "low": float(bar_data.get("Low", 0)),
                    "close": float(bar_data.get("Close", 0)),
                    "volume": int(bar_data.get("Volume", 0)),
                    "instrument": bar_data.get("Instrument", ""),
                    "sma20": panel_q.get("SMA"),
                    "bb_upper": panel_q.get("Upper band"),
                    "bb_middle": panel_q.get(
                        "Trigger"
                    ),  # From NinjaTrader's "Trigger" field
                    "bb_middle_avg": panel_q.get(
                        "Trigger Average"
                    ),  # From "Trigger Average"
                    "bb_lower": panel_q.get("Lower band"),
                    "dc_upper": panel_q.get("Upper"),
                    "dc_lower": panel_q.get("Lower"),
                    "dc_middle": panel_q.get("Mean"),
                    "uptrend": panel_q.get("UpTrend"),
                    "downtrend": panel_q.get("DownTrend"),
                    "momentum": panel_3.get("Momentum"),  # From Panel 3, not Panel 2
                    "momentum_histogram": panel_2.get("MomentumHistogram"),
                    "squeeze": panel_3.get("Squeeze"),  # From Panel 3
                    "squeeze_dots": panel_2.get("SqueezeDots"),
                    "rmo_bar": panel_3.get("RMOBar"),
                    "rmo_line": panel_3.get("RMOLine"),
                    "range": panel_5.get("Range value"),
                    "atr": panel_5.get("ATR"),
                }

                bars.append({k: v for k, v in full_bar.items() if v is not None})
            except (ValueError, TypeError) as e:
                logging.warning(f"Error converting bar for {date_str}: {e}")
                continue

        bars.sort(key=lambda x: x["time"])
        return bars

    async def handle_client(self, websocket):
        client_id = id(websocket)
        logging.info(f"Client {client_id} connected")

        try:
            async for message in websocket:
                try:
                    request = json.loads(message)
                    action = request.get("action")

                    if action == "get_historical_data":
                        ticker = request.get("ticker", "")
                        duration = request.get("duration", "1 Y")
                        bar_size = request.get("bar_size", "1 day")

                        logging.info(
                            f"Request from {client_id}: {ticker}, {duration}, {bar_size}"
                        )

                        bars = self.convert_to_full_data(self.market_data)

                        response = {"status": "success", "ticker": ticker, "data": bars}

                        await websocket.send(json.dumps(response))
                        logging.info(f"Sent {len(bars)} bars to client {client_id}")

                    elif action == "get_tickers":
                        tickers = self.get_available_tickers()

                        response = {"status": "success", "tickers": tickers}

                        await websocket.send(json.dumps(response))
                        logging.info(
                            f"Sent {len(tickers)} tickers to client {client_id}"
                        )

                    else:
                        error_response = {
                            "status": "error",
                            "message": f"Unknown action: {action}",
                        }
                        await websocket.send(json.dumps(error_response))

                except json.JSONDecodeError:
                    error_response = {"status": "error", "message": "Invalid JSON"}
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    logging.error(f"Error processing request: {e}")
                    error_response = {"status": "error", "message": str(e)}
                    await websocket.send(json.dumps(error_response))

        except websockets.exceptions.ConnectionClosed:
            logging.info(f"Client {client_id} disconnected")
        except Exception as e:
            logging.error(f"Error with client {client_id}: {e}")

    async def start(self, host="0.0.0.0", port=8000):
        server = await websockets.serve(self.handle_client, host, port)
        data_source = "LIVE NinjaTrader" if self.using_live_data else "FALLBACK JSON"
        logging.info(f"Market Data WebSocket server running on ws://{host}:{port}/data")
        logging.info(
            f"Server has {len(self.market_data)} bars loaded from {data_source}"
        )
        if self.using_live_data:
            logging.info("✓ Using LIVE data from NinjaTrader")
            logging.info("🔄 Auto-reload enabled: Watching for symbol changes...")
        else:
            logging.info(
                "⚠ Using FALLBACK JSON - start NinjaTrader receiver to get live data"
            )

        # Start file watching in background
        asyncio.create_task(self.watch_file_changes())

        await asyncio.Future()


async def main():
    server = MarketDataServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped")
