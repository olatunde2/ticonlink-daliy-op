# data_processing.py with FIXED mean and volume

import pandas as pd
import json
from .ib_client import IBClient


def format_value(value, decimals=3):
    """Format numeric values to specified decimal places"""
    if isinstance(value, (int, float)):
        return round(float(value), decimals)
    return value


def format_volume(volume_value):
    """Format volume with commas for display and abbreviated format"""
    try:
        volume_int = int(volume_value)

        # Format with commas (45,891,110)
        formatted_with_commas = f"{volume_int:,}"

        # Format abbreviated (45M) - FIXED: floor division for no rounding
        if volume_int >= 1_000_000_000:
            formatted_abbreviated = f"{volume_int // 1_000_000_000}B"
        elif volume_int >= 1_000_000:
            formatted_abbreviated = f"{volume_int // 1_000_000}M"  # This will give 45M
        elif volume_int >= 1_000:
            formatted_abbreviated = f"{volume_int // 1_000}K"
        else:
            formatted_abbreviated = str(volume_int)

        return formatted_with_commas, formatted_abbreviated
    except (ValueError, TypeError):
        return str(volume_value), str(volume_value)


def fetch_and_process_data(symbol=None, period=None, interval=None):
    """Fetch stock data from Render server and prepare it for charting"""
    print("Fetching and processing data from Render server")

    try:
        print("Start fetching data from Render server")
        # Fetch data from Render server
        ib_client = IBClient()
        df = ib_client.get_historical_data()
        print(f"Retrieved {len(df)} bars")

        if df.empty:
            return None, "No data available from server"

        # FIXED: Correct column mapping
        column_mapping = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "instrument": "Instrument",
            # FIXED: Map Panel_1_Mean to Mean
            "Panel_1_Mean": "Mean",
            # Map the panel indicators to standard names
            "Panel_Unknown_SMA": "SMA_20",
            "Panel_Unknown_Upper_band": "BB_upper",
            "Panel_Unknown_Middle_band": "BB_middle",
            "Panel_Unknown_Trigger": "BB_middle_avg",
            "Panel_Unknown_Lower_band": "BB_lower",
            "Panel_1_Upper": "DC_upper",
            "Panel_1_Lower": "DC_lower",
            "Panel_5_ATR": "ATR",
            "Panel_5_Range_value": "Range",
            "Panel_3_Momentum": "Momentum",
            "Panel_2_MomentumHistogram": "Momentum_Histogram",
            "Panel_3_Squeeze": "Squeeze",
            "Panel_2_SqueezeDots": "Squeeze_Dots",
            "Panel_Unknown_UpTrend": "UpTrend",
            "Panel_Unknown_DownTrend": "DownTrend",
        }

        # Apply column mapping
        df.rename(columns=column_mapping, inplace=True)

        # Format numeric columns
        numeric_columns = [
            "SMA_20",
            "BB_upper",
            "BB_middle",
            "BB_middle_avg",
            "BB_lower",
            "Mean",
            "DC_upper",
            "DC_lower",
            "ATR",
            "Range",
            "Momentum",
            "Momentum_Histogram",
            "Squeeze",
            "Squeeze_Dots",
            "UpTrend",
            "DownTrend",
        ]

        for col in numeric_columns:
            if col in df.columns:
                # Use 2 decimals for prices, 3 for indicators
                decimals = 2 if col in ["Mean"] else 3
                df[col] = df[col].apply(lambda x: format_value(x, decimals))

        # Make sure index is datetime
        df.index = pd.to_datetime(df.index)

        # Initialize chart_data
        chart_data = {
            "candlestick": [],
            "sma20": [],
            "bb_upper": [],
            "bb_middle": [],
            "bb_lower": [],
            "atr": [],
            "momentum": [],
            "squeeze": [],
            "volume": [],
            "mean": [],
        }

        for timestamp, row in df.iterrows():
            time_value = int(timestamp.timestamp())  # type: ignore

            # FIXED: Separate volume formatting for Panel 1 and Panel 4
            volume_panel1 = row.get("Panel_1_Volume", row.get("Volume", 0))
            volume_panel1_formatted, _ = format_volume(volume_panel1)  # "45,891,110"

            volume_panel4 = row.get("Panel_4_Volume", row.get("Volume", 0))
            _, volume_panel4_abbreviated = format_volume(volume_panel4)  # "45M"

            # Candlestick data with Panel 1 volume format
            chart_data["candlestick"].append(
                {
                    "time": time_value,
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    # FIXED: Use Panel 1 formatted volume
                    "volume_formatted": volume_panel1_formatted,  # "45,891,110"
                }
            )

            # Helper function to append indicators
            def add_indicator(key, col_name, decimals=3):
                if col_name in df.columns and not pd.isna(row[col_name]):  # type: ignore
                    chart_data[key].append(
                        {
                            "time": time_value,
                            "value": round(float(row[col_name]), decimals),  # type: ignore
                        }
                    )

            # Add indicators
            add_indicator("sma20", "SMA_20", 3)
            add_indicator("atr", "ATR", 3)
            add_indicator("bb_upper", "BB_upper", 3)
            add_indicator("bb_middle", "BB_middle", 3)
            add_indicator("bb_lower", "BB_lower", 3)

            # FIXED: Mean should now work with correct column mapping
            if "Mean" in df.columns and not pd.isna(row["Mean"]):
                chart_data["mean"].append(
                    {"time": time_value, "value": round(float(row["Mean"]), 2)}
                )

            # Momentum with color
            if "Momentum" in df.columns and not pd.isna(row["Momentum"]):
                momentum_value = round(float(row["Momentum"]), 3)
                color = "#00ff88" if momentum_value > 0 else "#ff4444"
                chart_data["momentum"].append(
                    {
                        "time": time_value,
                        "value": momentum_value,
                        "color": color,
                    }
                )

            # Squeeze
            if "Squeeze" in df.columns and not pd.isna(row["Squeeze"]):
                squeeze_value = round(float(row["Squeeze"]), 3)
                val = (
                    round(float(row["Momentum"]), 3)
                    if "Momentum" in df.columns and not pd.isna(row["Momentum"])
                    else 0
                )
                color = "#ff4444" if squeeze_value != 0 else "#00ff88"
                chart_data["squeeze"].append(
                    {"time": time_value, "value": val, "color": color}
                )

            # Volume for Panel 4 with abbreviated format
            if "Volume" in df.columns and not pd.isna(row["Volume"]):
                color = "#00ff88" if row["Close"] > row["Open"] else "#ff4444"
                chart_data["volume"].append(
                    {
                        "time": time_value,
                        "value": int(row["Volume"]),
                        "color": color,
                        # FIXED: Use Panel 4 abbreviated volume
                        "formatted": volume_panel4_abbreviated,  # "45M"
                    }
                )

        return df, json.dumps(chart_data)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return None, f"Error: {str(e)}"
