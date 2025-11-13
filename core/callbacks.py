import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import json
import pandas as pd
import numpy as np
import logging
from core.data_processing import fetch_and_process_data
from core.ui_components import create_data_panels
from core.calculators import calculate_trade_analysis
from core.db import insert_trade_result
import math
from datetime import datetime

# Global app variable to store the app instance
_app = None


def set_app(app):
    """Set the app instance for callback registration"""
    global _app
    _app = app


def validate_numeric_input(value, field_name):
    """
    Validate and convert numeric input, rejecting None, empty, NaN strings
    """
    # Check for None or empty
    if value is None:
        raise ValueError(f"{field_name} is required")

    # Handle string inputs
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() == "nan" or value.lower() == "none":
            raise ValueError(f"{field_name} is required")

    # Convert to float
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number")

    # Check if result is NaN or infinite
    if math.isnan(num_value) or math.isinf(num_value):
        raise ValueError(f"{field_name} must be a valid finite number")

    return num_value


def register_python_callbacks(app):
    """Register all Python callbacks with the app"""

    @app.callback(
        [
            Output("chart-data", "data"),
            Output("dataframe-store", "data"),
            Output("data-box", "children"),
            Output("panel-2", "children"),
            Output("panel-3", "children"),
            Output("panel-4", "children"),
            Output("panel-5", "children"),
            Output("symbol-input", "value"),
            Output("last-symbol-store", "data"),
        ],
        [
            Input("update-btn", "n_clicks"),
            Input("auto-update", "n_intervals"),
            Input("interval-dropdown", "value"),
        ],
        [State("symbol-input", "value"), State("last-symbol-store", "data")],
        prevent_initial_call=False,
    )
    def update_chart(n_clicks, n_intervals, interval, symbol, last_symbol):
        period = "10y"
        ctx = dash.callback_context

        # Use default symbol if not set
        if not symbol:
            symbol = "QQQ"

        df, chart_data_json = fetch_and_process_data(symbol, period, interval)
        if df is None:
            return (
                no_update,
                no_update,
                "No data",
                "No data",
                "No data",
                "No data",
                "No data",
                no_update,
                no_update,
            )

        chart_data = json.loads(chart_data_json)

        # Extract instrument from the data
        instrument = (
            df["Instrument"].iloc[0]
            if "Instrument" in df.columns and not df.empty
            else symbol
        )

        # Check if this is an auto-update and if symbol hasn't changed
        if ctx.triggered and len(ctx.triggered) > 0:
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if trigger_id == "auto-update" and last_symbol == instrument:
                # Symbol hasn't changed, don't update
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )

        df_json = df.to_json(date_format="iso", orient="split")

        data_box, panel_2, panel_3, panel_4, panel_5 = create_data_panels(
            df, instrument
        )
        return (
            chart_data,
            df_json,
            data_box,
            panel_2,
            panel_3,
            panel_4,
            panel_5,
            instrument,
            instrument,
        )

    @app.callback(
        [
            Output("data-box", "children", allow_duplicate=True),
            Output("panel-2", "children", allow_duplicate=True),
            Output("panel-3", "children", allow_duplicate=True),
            Output("panel-4", "children", allow_duplicate=True),
            Output("panel-5", "children", allow_duplicate=True),
        ],
        [Input("clicked-bar-index", "data")],
        [State("dataframe-store", "data"), State("symbol-input", "value")],
        prevent_initial_call=True,
    )
    def update_panels_on_click(bar_index, df_json, symbol):
        if bar_index is None or df_json is None:
            return no_update, no_update, no_update, no_update, no_update

        try:
            bar_index = int(bar_index)
        except (ValueError, TypeError):
            return no_update, no_update, no_update, no_update, no_update

        df = pd.read_json(df_json, orient="split")
        df.index = pd.to_datetime(df.index)

        if bar_index < 0 or bar_index >= len(df):
            return no_update, no_update, no_update, no_update, no_update

        # Show the clicked candle's data
        data_box, panel_2, panel_3, panel_4, panel_5 = create_data_panels(
            df, symbol, bar_index
        )
        return data_box, panel_2, panel_3, panel_4, panel_5

    @app.callback(
        [
            Output("calc-ticker", "value"),
            Output("calc-open-price", "value"),
            Output("calc-atr", "value"),
        ],
        [Input("clicked-bar-index", "data")],
        [State("dataframe-store", "data")],
        prevent_initial_call=True,
    )
    def update_calculator_from_click(bar_index, df_json):
        print(
            f"Calculator callback triggered! bar_index={bar_index}, has_data={df_json is not None}"
        )

        if bar_index is None or df_json is None:
            print("Calculator callback: No bar index or data, returning no_update")
            return no_update, no_update, no_update

        try:
            bar_index = int(bar_index)
        except (ValueError, TypeError) as e:
            print(f"Calculator callback: Error converting bar_index: {e}")
            return no_update, no_update, no_update

        df = pd.read_json(df_json, orient="split")
        df.index = pd.to_datetime(df.index)

        if bar_index < 0 or bar_index >= len(df):
            print(
                f"Calculator callback: Invalid bar_index {bar_index} for df length {len(df)}"
            )
            return no_update, no_update, no_update

        # Show the clicked candle's data
        row = df.iloc[bar_index]

        # Get ticker from instrument column in data
        ticker = row.get("Instrument", "QQQ")
        open_price = round(row["Open"], 2) if "Open" in row else no_update
        atr = round(row["ATR"], 2) if "ATR" in row else no_update

        print(f"Calculator auto-fill: Ticker={ticker}, Open={open_price}, ATR={atr}")

        return ticker, open_price, atr

    @app.callback(
        Output("calc-results", "children"),
        [Input("calc-button", "n_clicks")],
        [
            State("calc-market-cycle", "value"),
            State("calc-ticker", "value"),
            State("calc-description", "value"),
            State("calc-direction", "value"),
            State("calc-open-price", "value"),
            State("calc-current-price", "value"),
            State("calc-strike-price", "value"),
            State("calc-atr", "value"),
            State("calc-bid-price", "value"),
            State("calc-ask-price", "value"),
            State("calc-iv-override", "value"),
        ],
        prevent_initial_call=True,
    )
    def calculate_trade(
        n_clicks,
        market_cycle,
        ticker,
        description,
        direction,
        open_price,
        current_price,
        strike_price,
        atr,
        bid_price,
        ask_price,
        iv_override,
    ):
        if n_clicks is None:
            return no_update

        result_row_style = {
            "display": "flex",
            "justifyContent": "space-between",
            "padding": "6px 8px",
            "borderBottom": "1px solid #404040",
            "fontSize": "12px",
        }

        try:
            if not direction or direction not in ["long", "short"]:
                raise ValueError("Please select a valid trade direction")

            validated_open_price = validate_numeric_input(open_price, "Open Price")
            validated_current_price = validate_numeric_input(
                current_price, "Current Price"
            )
            validated_strike_price = validate_numeric_input(
                strike_price, "Strike Price"
            )
            validated_atr = validate_numeric_input(atr, "ATR")
            validated_bid_price = validate_numeric_input(bid_price, "Bid Price")
            validated_ask_price = validate_numeric_input(ask_price, "Ask Price")

            trade_data = {
                "open_price": validated_open_price,
                "current_price": validated_current_price,
                "strike_price": validated_strike_price,
                "atr_value": validated_atr,
                "bid_price": validated_bid_price,
                "ask_price": validated_ask_price,
                "trade_direction": direction,
                "scenario": "standard",
            }

            if iv_override is not None and iv_override != "":
                try:
                    validated_iv = float(iv_override)
                    if validated_iv < 0:
                        raise ValueError("IV Override must be non-negative")
                    trade_data["custom_intrinsic_value"] = validated_iv
                except (ValueError, TypeError):
                    pass

            results = calculate_trade_analysis(trade_data)

            try:
                if not ticker or ticker.strip() == "":
                    ticker = "UNKNOWN"

                insert_trade_result(
                    trade_date=datetime.now().strftime("%m/%d/%Y"),
                    ticker=ticker.upper(),
                    direction=direction,
                    scenario="standard",
                    target_price_value=results["target_price"],
                    option_bid=validated_bid_price,
                    option_ask=validated_ask_price,
                    intrinsic_value=results["intrinsic_value"],
                    extrinsic_value=results["extrinsic_value"],
                    target_size=results["target_size"],
                    tradable_flag=results["is_tradable"],
                    inputs_dict=trade_data,
                    market_cycle_date=None,
                    description=description
                    if description and description.strip()
                    else None,
                )
            except Exception as db_error:
                logging.warning(f"Failed to save to database: {db_error}")

            dir_label = "Long" if direction == "long" else "Short"
            market_cycle_text = (
                market_cycle
                if market_cycle and market_cycle.strip()
                else "Market Cycle"
            )

            header_text = f"{market_cycle_text} [{ticker.upper()} {dir_label}]"

            option_total = validated_bid_price + validated_ask_price
            option_mid = option_total / 2

            ev_value = validated_bid_price - results["intrinsic_value"]

            tradable_color = "#00ff88" if results["is_tradable"] else "#ff4444"
            tradable_text = (
                "Tradeable ✅" if results["is_tradable"] else "Not Tradeable ✗"
            )

            output = [
                html.Div(
                    header_text,
                    style={
                        "color": "#ffffff",
                        "fontWeight": "bold",
                        "fontSize": "12px",
                        "padding": "4px 8px",
                        "marginBottom": "8px",
                    },
                ),
            ]

            if description and description.strip():
                output.append(
                    html.Div(
                        description,
                        style={
                            "color": "#ffffff",
                            "fontSize": "12px",
                            "padding": "4px 8px",
                            "marginBottom": "8px",
                        },
                    )
                )

            output.append(html.Div(style={"marginBottom": "8px"}))

            if direction == "long":
                target_formula = f"Target Price: {validated_open_price:.2f} + {validated_atr:.1f} = {results['target_price']:.2f}"
            else:
                target_formula = f"Target Price: {validated_open_price:.2f} - {validated_atr:.1f} = {results['target_price']:.2f}"

            output.extend(
                [
                    html.Div(
                        [
                            html.Div(
                                target_formula,
                                style={"color": "#ffffff", "fontSize": "12px"},
                            )
                        ],
                        style={"padding": "4px 8px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                f"Price of the Option: {validated_bid_price:.2f} + {validated_ask_price:.2f} = {option_total:.2f}",
                                style={"color": "#ffffff", "fontSize": "12px"},
                            ),
                            html.Div(
                                f"{option_total:.2f}/2 = {option_mid:.3f}",
                                style={
                                    "color": "#ffffff",
                                    "fontSize": "12px",
                                    "marginLeft": "20px",
                                },
                            ),
                        ],
                        style={"padding": "4px 8px", "marginBottom": "8px"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                f"IV = {results['intrinsic_value']:.2f}",
                                style={"color": "#ffffff", "fontSize": "12px"},
                            ),
                            html.Div(
                                f"EV = {validated_bid_price:.2f} - {results['intrinsic_value']:.2f} = {ev_value:.2f}",
                                style={"color": "#ffffff", "fontSize": "12px"},
                            ),
                        ],
                        style={"padding": "4px 8px", "marginBottom": "12px"},
                    ),
                    html.Div(
                        tradable_text,
                        style={
                            "color": tradable_color,
                            "fontSize": "12px",
                            "fontWeight": "bold",
                            "padding": "8px",
                            "textAlign": "center",
                            "borderTop": "1px solid #404040",
                        },
                    ),
                ]
            )

            return output

        except (ValueError, TypeError, KeyError) as e:
            return [
                html.Div(
                    f"Error: {str(e)}",
                    style={"color": "#ff4444", "padding": "10px", "fontSize": "12px"},
                )
            ]


def register_clientside_callbacks(app):
    app.clientside_callback(
        """
        function renderChart(chartData, currentIndex) {
  if (!chartData || !chartData.candlestick || !window.LightweightCharts) {
    return [window.dash_clientside.no_update, ""];
  }

  ["main-chart", "momentum-chart", "squeeze-chart", "volume-chart"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  });

  const container = document.getElementById("main-chart");
  const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth || 800,
    height: container.clientHeight || 500,
    layout: { backgroundColor: "#1e1e1e", textColor: "#ffffff" },
    rightPriceScale: { borderColor: "#555" },
    timeScale: { borderColor: "#555" },
    grid: { vertLines: { color: "#2b2b2b" }, horzLines: { color: "#2b2b2b" } },
  });

  const candleSeries = chart.addCandlestickSeries({
    upColor: "#00ff88",
    downColor: "#ff4444",
    borderDownColor: "#ff4444",
    borderUpColor: "#00ff88",
    wickDownColor: "#ff4444",
    wickUpColor: "#00ff88",
  });
  candleSeries.setData(chartData.candlestick);
  
  let clickedIndex = currentIndex;
  chart.subscribeClick((param) => {
    if (param.time) {
      const barIndex = chartData.candlestick.findIndex(bar => bar.time === param.time);
      if (barIndex >= 0) {
        clickedIndex = barIndex;
        window.dash_clientside.set_props("clicked-bar-index", {data: barIndex});
      }
    }
  });

  function addLineSeries(key, color, options = {}) {
    if (chartData[key]) {
      const series = chart.addLineSeries({ color, lineWidth: 2, ...options });
      series.setData(chartData[key]);
    }
  }

  addLineSeries("sma20", "#0000FF");
  addLineSeries("bb_upper", "#FF00FF", { lineStyle: LightweightCharts.LineStyle.Dotted });
  addLineSeries("bb_middle", "#FF00FF");
  addLineSeries("bb_lower", "#FF00FF", { lineStyle: LightweightCharts.LineStyle.Dotted });
  addLineSeries("dc_upper", "#8B0000", { lineStyle: LightweightCharts.LineStyle.Dotted });
  addLineSeries("dc_middle", "#FF8C00");
  addLineSeries("dc_lower", "#8B0000", { lineStyle: LightweightCharts.LineStyle.Dotted });

  if (chartData.momentum) {
    const momentumEl = document.getElementById("momentum-chart");
    if (momentumEl) {
      const momentumChart = LightweightCharts.createChart(momentumEl, {
        width: momentumEl.clientWidth,
        height: momentumEl.clientHeight,
        layout: { backgroundColor: "#1e1e1e", textColor: "#fff" },
        grid: { vertLines: { color: "#2b2b2b" }, horzLines: { color: "#2b2b2b" } },
        timeScale: { visible: false },
      });
      momentumChart.addHistogramSeries({ color: "#008000" }).setData(chartData.momentum);
    }
  }

  if (chartData.squeeze) {
    const squeezeEl = document.getElementById("squeeze-chart");
    if (squeezeEl) {
      const squeezeChart = LightweightCharts.createChart(squeezeEl, {
        width: squeezeEl.clientWidth,
        height: squeezeEl.clientHeight,
        layout: { backgroundColor: "#1e1e1e", textColor: "#fff" },
        grid: { vertLines: { color: "#2b2b2b" }, horzLines: { color: "#2b2b2b" } },
        timeScale: { visible: false },
      });
      squeezeChart.addHistogramSeries({ color: "#0000FF" }).setData(chartData.squeeze);
    }
  }

  if (chartData.volume) {
    const volumeEl = document.getElementById("volume-chart");
    if (volumeEl) {
      const volumeChart = LightweightCharts.createChart(volumeEl, {
        width: volumeEl.clientWidth,
        height: volumeEl.clientHeight,
        layout: { backgroundColor: "#1e1e1e", textColor: "#fff" },
        grid: { vertLines: { color: "#2b2b2b" }, horzLines: { color: "#2b2b2b" } },
        timeScale: { visible: true },
      });
      volumeChart.addHistogramSeries({ color: "#26a69a" }).setData(chartData.volume);
    }
  }

  return ["", clickedIndex];
}
        """,
        [Output("main-chart", "children"), Output("clicked-bar-index", "data")],
        [Input("chart-data", "data"), Input("clicked-bar-index", "data")],
    )
