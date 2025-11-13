import pandas as pd
import json
from .ib_client import IBClient

def fetch_and_process_data(symbol, period, interval):
    """Fetch stock data from files or WebSocket and prepare it for charting"""
    print("Fetching and processing data")
    if not symbol:
        symbol = "QQQ"

    # Mappings for IBKR
    ib_period_map = {
        '5d': '5 D',
        '1mo': '1 M',
        '3mo': '3 M',
        '6mo': '6 M',
        '1y': '1 Y',
        '2y': '2 Y',
        '5y': '5 Y',
        '10y': '10 Y'
    }
    ib_interval_map = {
        '1m': '1 min',
        '5m': '5 mins',
        '15m': '15 mins',
        '30m': '30 mins',
        '1h': '1 hour',
        '4h': '4 hours',
        '1d': '1 day',
        '1wk': '1 week'
    }

    duration = ib_period_map.get(period)
    bar_size = ib_interval_map.get(interval)

    if not duration or not bar_size:
        return None, f"Invalid period/interval for IBKR: {period}/{interval}"
    print("Period: ", period)
    print("Interval: ", interval)

    try:
        # Try to load from files first (works on Render)
        import os
        from pathlib import Path
        
        # Check for live data from NinjaTrader
        live_file = Path('live_market_data.json')
        static_file = Path('market_data.json')
        
        df = None
        
        if live_file.exists():
            print("Loading from live_market_data.json")
            with open(live_file, 'r') as f:
                data = json.load(f)
                if 'bars' in data and len(data['bars']) > 0:
                    df = pd.DataFrame(data['bars'])
                    if 'time' in df.columns:
                        df['time'] = pd.to_datetime(df['time'])
                        df.set_index('time', inplace=True)
                    print(f"Loaded {len(df)} bars from live data")
        
        if df is None or df.empty:
            if static_file.exists():
                print("Loading from market_data.json (fallback)")
                with open(static_file, 'r') as f:
                    data = json.load(f)
                    if 'bars' in data and len(data['bars']) > 0:
                        df = pd.DataFrame(data['bars'])
                        if 'time' in df.columns:
                            df['time'] = pd.to_datetime(df['time'])
                            df.set_index('time', inplace=True)
                        print(f"Loaded {len(df)} bars from static data")
        
        # If file loading failed, try WebSocket as fallback
        if df is None or df.empty:
            print("Files not found, trying WebSocket")
            ib_client = IBClient()
            df = ib_client.get_historical_data(
                ticker=symbol,
                duration=duration,
                bar_size=bar_size
            )
            print(df)

        if df is None or df.empty:
            return None, "No data"

        # Rename columns to match existing convention
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'instrument': 'Instrument',
            'sma20': 'SMA_20',
            'bb_upper': 'BB_upper',
            'bb_middle': 'BB_middle',  # Trigger
            'bb_middle_avg': 'BB_middle_avg',  # Trigger Average
            'bb_lower': 'BB_lower',
            'dc_upper': 'DC_upper',
            'dc_middle': 'DC_middle',
            'dc_lower': 'DC_lower',
            'atr': 'ATR',
            'range': 'Range',
            'momentum': 'Momentum',  # Panel 3 Momentum
            'momentum_histogram': 'Momentum_Histogram',  # Panel 2
            'squeeze': 'Squeeze',  # Panel 3 Squeeze
            'squeeze_dots': 'Squeeze_Dots',  # Panel 2
            'uptrend': 'UpTrend',
            'downtrend': 'DownTrend'
        }, inplace=True)
        
        # Make sure index is datetime
        df.index = pd.to_datetime(df.index)

        # Initialize chart_data with all possible keys as empty lists
        chart_data = {
            'candlestick': [],
            'sma20': [],
            'ema14': [],
            'wma20': [],
            'hma20': [],
            'tma20': [],
            'tema20': [],
            'atr': [],
            'bb_upper': [],
            'bb_middle': [],
            'bb_lower': [],
            'bb_bandwidth': [],
            'bb_percent_b': [],
            'stddev': [],
            'dc_upper': [],
            'dc_middle': [],
            'dc_lower': [],
            'kc_upper': [],
            'kc_middle': [],
            'kc_lower': [],
            'rsi': [],
            'cci': [],
            'cmo': [],
            'stoch_k': [],
            'stoch_d': [],
            'macd': [],
            'macd_signal': [],
            'macd_histogram': [],
            'max_20': [],
            'min_20': [],
            'sum_volume': [],
            'daily_range': [],
            'avg_range': [],
            'linreg': [],
            'linreg_slope': [],
            'linreg_r2': [],
            'williams_r': [],
            'ultimate_osc': [],
            'roc': [],
            'obv': [],
            'volume_sma': [],
            'vwap': [],
            'ad_line': [],
            'chaikin_mf': [],
            'momentum': [],
            'squeeze': [],
            'volume': []
        }

        for timestamp, row in df.iterrows():
            time_value = int(timestamp.timestamp())

            # Candlestick data
            chart_data['candlestick'].append({
                'time': time_value,
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close'])
            })

            # Helper function to append if column exists and is not NaN
            def add_indicator(key, col_name):
                if col_name in df.columns and not pd.isna(row[col_name]):
                    chart_data[key].append({
                        'time': time_value,
                        'value': float(row[col_name])
                    })

            # Add all indicators from WebSocket
            add_indicator('sma20', 'SMA_20')
            add_indicator('atr', 'ATR')
            add_indicator('bb_upper', 'BB_upper')
            add_indicator('bb_middle', 'BB_middle')
            add_indicator('bb_lower', 'BB_lower')
            add_indicator('dc_upper', 'DC_upper')
            add_indicator('dc_middle', 'DC_middle')
            add_indicator('dc_lower', 'DC_lower')

            # Momentum with color (from websocket)
            if 'Momentum' in df.columns and not pd.isna(row['Momentum']):
                color = '#00ff88' if row['Momentum'] > 0 else '#ff4444'
                chart_data['momentum'].append({
                    'time': time_value,
                    'value': float(row['Momentum']),
                    'color': color
                })

            # Squeeze (from websocket - 0 = green, non-zero = red)
            if 'Squeeze' in df.columns and not pd.isna(row['Squeeze']):
                val = float(row['Momentum']) if 'Momentum' in df.columns and not pd.isna(row['Momentum']) else 0
                color = '#ff4444' if row['Squeeze'] != 0 else '#00ff88'
                chart_data['squeeze'].append({
                    'time': time_value,
                    'value': val,
                    'color': color
                })

            # Volume with color (up/down candles)
            chart_data['volume'].append({
                'time': time_value,
                'value': float(row['Volume']),
                'color': '#00ff88' if row['Close'] > row['Open'] else '#ff4444'
            })

        return df, json.dumps(chart_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error: {str(e)}"
