import pandas as pd
import logging
import json
import websocket
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import config, fallback to hard-coded URL for Windows compatibility
try:
    from config import WEBSOCKET_DATA_URL
except ImportError:
    WEBSOCKET_DATA_URL = "ws://localhost:8000/data"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class IBClient:
    """
    A client for fetching market data via WebSocket connection.
    """

    def __init__(self, ws_url=None):
        # Default to port 8000 (Data Server), not 9000 (NinjaTrader Receiver)
        self.ws_url = ws_url or WEBSOCKET_DATA_URL or "ws://localhost:8000/data"
        self.timeout = 30

    def get_tickers(self):
        """Alias for get_available_tickers"""
        return self.get_available_tickers()

    def get_available_tickers(self):
        """
        Fetch available tickers from the WebSocket server.
        """
        ws = None
        try:
            logging.info(f"Connecting to WebSocket at {self.ws_url} for tickers")

            ws = websocket.create_connection(self.ws_url, timeout=self.timeout)

            request_data = {"action": "get_tickers"}

            ws.send(json.dumps(request_data))
            logging.info(f"Sent request for tickers")

            response = ws.recv()
            data = json.loads(response)

            if data.get("status") == "error":
                logging.error(f"Error from server: {data.get('message')}")
                return []

            tickers = data.get("tickers", [])
            logging.info(f"Received {len(tickers)} tickers")
            return tickers

        except Exception as e:
            logging.error(f"Error fetching tickers: {e}")
            return []
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    def get_historical_data(
        self, ticker, duration="1 Y", bar_size="1 day", what_to_show="TRADES"
    ):
        """
        Fetch historical data for a given ticker via WebSocket.
        """
        ws = None
        try:
            logging.info(f"Connecting to WebSocket at {self.ws_url} for {ticker}")

            ws = websocket.create_connection(self.ws_url, timeout=self.timeout)

            request_data = {
                "action": "get_historical_data",
                "ticker": ticker,
                "duration": duration,
                "bar_size": bar_size,
                "what_to_show": what_to_show,
            }

            ws.send(json.dumps(request_data))
            logging.info(f"Sent request for {ticker}: {request_data}")

            response = ws.recv()

            data = json.loads(response)

            if data.get("status") == "error":
                logging.error(f"Error from server: {data.get('message')}")
                return pd.DataFrame()

            if "data" in data and len(data["data"]) > 0:
                df = pd.DataFrame(data["data"])

                if "time" in df.columns:
                    df["time"] = pd.to_datetime(df["time"])
                    df.set_index("time", inplace=True)
                elif "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    df.rename(columns={"date": "time"}, inplace=True)
                    df.set_index("time", inplace=True)

                logging.info(f"Received {len(df)} bars for {ticker}")
                return df
            else:
                logging.warning(f"No historical data returned for {ticker}")
                return pd.DataFrame()

        except websocket.WebSocketTimeoutException:
            logging.error(f"WebSocket connection timeout for {ticker}")
            return pd.DataFrame()
        except websocket.WebSocketException as e:
            logging.error(f"WebSocket error for {ticker}: {e}")
            return pd.DataFrame()
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for {ticker}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass
