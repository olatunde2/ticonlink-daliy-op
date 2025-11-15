from dash import html

import pandas as pd


def styled_row(label, value, label_color="#cccccc", value_color="#ffffff"):
    """Create a two-cell row with specific colors"""
    row_style = {
        "display": "grid",
        "gridTemplateColumns": "1fr 1fr",
        "borderBottom": "1px solid #555",
        "fontSize": "12px",
        "lineHeight": "1.6",
    }

    label_style = {
        "backgroundColor": label_color,
        "color": "#000000",
        "padding": "4px 8px",
        "fontWeight": "bold",
        "borderRight": "1px solid #555",
    }

    value_style = {
        "backgroundColor": "#ffffff",
        "color": "#000000",
        "padding": "4px 8px",
        "textAlign": "right",
        "fontWeight": "normal",
    }

    return html.Div(
        [html.Div(label, style=label_style), html.Div(value, style=value_style)],
        style=row_style,
    )


def format_volume_full(v):
    """Format volume with commas for Panel 1 (45,891,110)"""
    try:
        volume_int = int(v)
        return f"{volume_int:,}"
    except (ValueError, TypeError):
        return str(v)


def format_volume_abbreviated(v):
    """Format volume abbreviated for Panel 4 (45M) - FIXED"""
    try:
        volume_int = int(v)
        if volume_int >= 1_000_000_000:
            return f"{volume_int // 1_000_000_000}B"  # ✅ Uses floor division
        elif volume_int >= 1_000_000:
            return (
                f"{volume_int // 1_000_000}M"  # ✅ Uses floor division - this gives 45M
            )
        elif volume_int >= 1_000:
            return f"{volume_int // 1_000}K"  # ✅ Uses floor division
        return str(volume_int)
    except (ValueError, TypeError):
        return str(v)


def create_data_panels(df, symbol, bar_index=-1):
    """Create NT8-style data panels matching the screenshot"""
    if df is None or df.empty:
        return "No data", "No data", "No data", "No data", "No data"

    latest = df.iloc[bar_index]
    latest_date = latest.name
    instrument = latest.get("Instrument", symbol)

    week_num = latest_date.isocalendar()[1]
    year = latest_date.year

    # FIXED: Use correct Mean value and volume formatting
    mean_value = latest.get("Mean", 0)
    if pd.isna(mean_value):
        mean_value = 0

    # FIXED: Different volume formatting for Panel 1 and Panel 4
    volume_panel1 = format_volume_full(latest["Volume"])  # "45,891,110"
    volume_panel4 = format_volume_abbreviated(latest["Volume"])  # "45M"

    data_box = html.Div(
        [
            html.Div(
                "Data Box",
                style={
                    "backgroundColor": "#FF6600",
                    "color": "#ffffff",
                    "padding": "4px 8px",
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "borderBottom": "1px solid #555",
                },
            ),
            html.Div(
                [
                    html.Div(
                        "Week",
                        style={
                            "flex": 1,
                            "backgroundColor": "#333",
                            "color": "#fff",
                            "padding": "4px 8px",
                            "fontWeight": "bold",
                        },
                    ),
                    html.Div(
                        f"{week_num}/{year}",
                        style={
                            "flex": 1,
                            "backgroundColor": "#fff",
                            "color": "#000",
                            "padding": "4px 8px",
                            "textAlign": "right",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "borderBottom": "1px solid #555",
                    "fontSize": "12px",
                },
            ),
            html.Div(
                "Panel 1",
                style={
                    "backgroundColor": "#ccc",
                    "color": "#000",
                    "padding": "4px 8px",
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "borderBottom": "1px solid #555",
                },
            ),
            html.Div(
                f"{instrument} (Daily)",
                style={
                    "backgroundColor": "#fff",
                    "color": "#000",
                    "padding": "4px 8px",
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "borderBottom": "1px solid #555",
                },
            ),
            styled_row("Date", latest_date.strftime("%m/%d/%Y")),
            styled_row("Price", f"{latest['Close']:.2f}"),
            styled_row("Open", f"{latest['Open']:.2f}"),
            styled_row("High", f"{latest['High']:.2f}"),
            styled_row("Low", f"{latest['Low']:.2f}"),
            styled_row("Close", f"{latest['Close']:.2f}"),
            # FIXED: Use full volume format for Panel 1
            styled_row("Volume", volume_panel1),
            # FIXED: Use correct Mean value
            styled_row("Mean", f"{mean_value:.2f}", label_color="#FF8C00"),
            styled_row(
                "SMA",
                f"{latest.get('SMA_20', 0):.2f}",
                label_color="#0000FF",
                value_color="#ffffff",
            ),
            styled_row(
                "Trigger", f"{latest.get('BB_middle', 0):.2f}", label_color="#FF00FF"
            ),
            styled_row(
                "Trigger Ave...",
                f"{latest.get('BB_middle_avg', 0):.2f}",
                label_color="#00FFFF",
            ),
            styled_row(
                "Upper band", f"{latest.get('BB_upper', 0):.2f}", label_color="#8B0000"
            ),
            styled_row(
                "Lower band", f"{latest.get('BB_lower', 0):.2f}", label_color="#8B0000"
            ),
        ],
        style={
            "backgroundColor": "#fff",
            "border": "2px solid #333",
            "marginBottom": "10px",
        },
    )

    panel_2 = html.Div(
        [
            html.Div(
                "Panel 2",
                style={
                    "backgroundColor": "#ccc",
                    "color": "#000",
                    "padding": "4px 8px",
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "borderBottom": "1px solid #555",
                },
            ),
            styled_row(
                "Momentum...",
                f"{latest.get('Momentum_Histogram', 0):.3f}",
                label_color="#008000",
            ),
            styled_row(
                "SqueezeDots",
                f"{latest.get('Squeeze_Dots', 0):.0f}",
                label_color="#0000FF",
                value_color="#ffffff",
            ),
        ],
        style={
            "backgroundColor": "#fff",
            "border": "2px solid #333",
            "marginBottom": "10px",
        },
    )

    panel_3 = html.Div(
        [
            html.Div(
                "Panel 3",
                style={
                    "backgroundColor": "#ccc",
                    "color": "#000",
                    "padding": "4px 8px",
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "borderBottom": "1px solid #555",
                },
            ),
            styled_row(
                "Squeeze",
                f"{latest.get('Squeeze', 0):.0f}",
                label_color="#0000FF",
                value_color="#ffffff",
            ),
            styled_row(
                "Momentum", f"{latest.get('Momentum', 0):.2f}", label_color="#FF0000"
            ),
        ],
        style={
            "backgroundColor": "#fff",
            "border": "2px solid #333",
            "marginBottom": "10px",
        },
    )

    panel_4 = html.Div(
        [
            html.Div(
                "Panel 4",
                style={
                    "backgroundColor": "#ccc",
                    "color": "#000",
                    "padding": "4px 8px",
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "borderBottom": "1px solid #555",
                },
            ),
            # FIXED: Use abbreviated volume format for Panel 4
            styled_row("Volume", volume_panel4, label_color="#8B0000"),
        ],
        style={
            "backgroundColor": "#fff",
            "border": "2px solid #333",
            "marginBottom": "10px",
        },
    )

    panel_5 = html.Div(
        [
            html.Div(
                "Panel 5",
                style={
                    "backgroundColor": "#ccc",
                    "color": "#000",
                    "padding": "4px 8px",
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "borderBottom": "1px solid #555",
                },
            ),
            styled_row(
                "Range value", f"{latest.get('Range', 0):.2f}", label_color="#008B8B"
            ),
            styled_row("ATR", f"{latest.get('ATR', 0):.1f}", label_color="#008B8B"),
        ],
        style={
            "backgroundColor": "#fff",
            "border": "2px solid #333",
            "marginBottom": "10px",
        },
    )

    return data_box, panel_2, panel_3, panel_4, panel_5
