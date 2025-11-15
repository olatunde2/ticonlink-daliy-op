import pandas as pd
import logging
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use your Render server URL
try:
    from config import RENDER_SERVER_URL
except ImportError:
    RENDER_SERVER_URL = "https://test-cfrs.onrender.com"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class IBClient:
    """
    A client for fetching market data from Render server.
    """

    def __init__(self, server_url=None):
        self.server_url = server_url or RENDER_SERVER_URL
        self.timeout = 30

    def get_tickers(self):
        """Get available instruments from the server"""
        try:
            logging.info(f"Fetching tickers from {self.server_url}")

            # Get server status to see available instruments
            response = requests.get(f"{self.server_url}/", timeout=self.timeout)
            data = response.json()

            if "data_status" in data and data["data_status"].get("instrument"):
                # Return the current instrument
                return [data["data_status"]["instrument"]]
            else:
                logging.warning("No instrument data available on server")
                return []

        except Exception as e:
            logging.error(f"Error fetching tickers: {e}")
            return []

    def get_available_tickers(self):
        """Alias for get_tickers"""
        return self.get_tickers()

    def get_historical_data(
        self, ticker=None, duration="1 Y", bar_size="1 day", what_to_show="TRADES"
    ):
        """
        Fetch historical data from Render server.
        Note: Parameters are kept for compatibility but not used for Render server.
        """
        try:
            logging.info(f"Fetching data from {self.server_url}/data/full")

            # Fetch complete data from Render server
            response = requests.get(
                f"{self.server_url}/data/full", timeout=self.timeout
            )
            data = response.json()

            if data.get("status") == "success" and "data" in data:
                # Convert the received data to DataFrame
                bars_data = data["data"]
                df = self._convert_to_dataframe(bars_data)

                logging.info(
                    f"Received {len(df)} bars for {data['summary']['instrument']}"
                )
                return df
            else:
                logging.warning(
                    f"No data returned: {data.get('message', 'Unknown error')}"
                )
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP request error: {e}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            return pd.DataFrame()

    def _convert_to_dataframe(self, bars_data):
        """Convert the bars data from Render server to pandas DataFrame"""
        bars_list = []

        for date_str, bar_data in bars_data.items():
            # Create flat bar structure
            flat_bar = {
                "time": date_str,
                "open": bar_data.get("Open"),
                "high": bar_data.get("High"),
                "low": bar_data.get("Low"),
                "close": bar_data.get("Close"),
                "volume": bar_data.get("Volume"),
                "mean": bar_data.get("Mean"),
                "instrument": bar_data.get("Instrument"),
                "bar_index": bar_data.get("BarIndex"),
            }

            # Flatten panel data with proper formatting
            panels = bar_data.get("Panels", {})
            for panel_name, panel_data in panels.items():
                for indicator, value in panel_data.items():
                    # Create unique column names
                    col_name = f"{panel_name}_{indicator}".replace(" ", "_").replace(
                        "?", "Unknown"
                    )

                    # Format numeric values to 3 decimal places
                    if isinstance(value, (int, float)):
                        flat_bar[col_name] = round(float(value), 3)
                    else:
                        flat_bar[col_name] = value

            bars_list.append(flat_bar)

        # Create DataFrame
        df = pd.DataFrame(bars_list)

        # Convert time to datetime and set as index
        if not df.empty and "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)

        return df

    def get_data_summary(self):
        """Get summary of available data"""
        try:
            response = requests.get(
                f"{self.server_url}/data/summary", timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching summary: {e}")
            return {}

    def get_sample_data(self, count=10):
        """Get sample data (first N bars)"""
        try:
            response = requests.get(
                f"{self.server_url}/data/sample", timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching sample: {e}")
            return {}

    def download_complete_data(self, filename=None):
        """Download complete data as JSON file"""
        try:
            if not filename:
                # Get instrument info for filename
                summary = self.get_data_summary()
                instrument = summary.get("instrument", "data")
                filename = f"{instrument}_complete_data.json"

            response = requests.get(
                f"{self.server_url}/data/full?download=true", timeout=self.timeout
            )

            with open(filename, "w") as f:
                f.write(response.text)

            logging.info(f"Data downloaded to {filename}")
            return True

        except Exception as e:
            logging.error(f"Error downloading data: {e}")
            return False

    def get_formatted_sample(self, count=5):
        """Get formatted sample data for display"""
        try:
            response = requests.get(
                f"{self.server_url}/data/sample", timeout=self.timeout
            )
            data = response.json()

            if data.get("status") == "success":
                formatted_data = []
                for date_str, bar_data in data.get("data", {}).items():
                    formatted_bar = {
                        "date": date_str,
                        "price_data": {
                            "Open": f"{bar_data.get('Open', 0):.2f}",
                            "High": f"{bar_data.get('High', 0):.2f}",
                            "Low": f"{bar_data.get('Low', 0):.2f}",
                            "Close": f"{bar_data.get('Close', 0):.2f}",
                            "Volume": f"{bar_data.get('Volume', 0):,.0f}",
                            "Mean": f"{bar_data.get('Mean', 0):,.2f}",
                        },
                    }

                    # Format panel data with 3 decimal places
                    panels = bar_data.get("Panels", {})
                    formatted_panels = {}
                    for panel_name, panel_data in panels.items():
                        formatted_panel = {}
                        for indicator, value in panel_data.items():
                            if isinstance(value, (int, float)):
                                formatted_panel[indicator] = f"{value:.3f}"
                            else:
                                formatted_panel[indicator] = value
                        formatted_panels[panel_name] = formatted_panel

                    formatted_bar["panels"] = formatted_panels
                    formatted_data.append(formatted_bar)

                return formatted_data
            return []

        except Exception as e:
            logging.error(f"Error getting formatted sample: {e}")
            return []
