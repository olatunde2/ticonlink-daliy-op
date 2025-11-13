from dash import html, dcc
import dash_bootstrap_components as dbc


def create_calculator_panel():
    """Create the trade calculator UI panel"""

    input_style = {
        "width": "100%",
        "backgroundColor": "#404040",
        "color": "#ffffff",
        "border": "1px solid #606060",
        "padding": "4px 8px",
        "borderRadius": "3px",
        "fontSize": "12px",
        "marginBottom": "8px",
    }

    label_style = {
        "color": "#ffffff",
        "fontSize": "12px",
        "marginBottom": "4px",
        "fontWeight": "bold",
    }

    result_row_style = {
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "6px 8px",
        "borderBottom": "1px solid #404040",
        "fontSize": "12px",
    }

    return html.Div(
        [
            html.Div(
                "Trade Calculator",
                style={
                    "backgroundColor": "#0066cc",
                    "color": "#ffffff",
                    "padding": "8px",
                    "fontWeight": "bold",
                    "fontSize": "14px",
                    "marginBottom": "10px",
                    "textAlign": "center",
                },
            ),
            # Input Section
            html.Div(
                [
                    html.Div("Market Cycle", style=label_style),
                    dcc.Input(
                        id="calc-market-cycle",
                        type="text",
                        placeholder="e.g., 1st Market Cycle - 11/21/2025",
                        style=input_style,
                    ),
                    html.Div("Ticker", style=label_style),
                    dcc.Input(
                        id="calc-ticker",
                        type="text",
                        value="QQQ",
                        placeholder="e.g., IWM",
                        style=input_style,
                    ),
                    html.Div("Description (Optional)", style=label_style),
                    dcc.Input(
                        id="calc-description",
                        type="text",
                        placeholder="e.g., ETF Squeeze Sell",
                        style=input_style,
                    ),
                    html.Div("Trade Direction", style=label_style),
                    dcc.Dropdown(
                        id="calc-direction",
                        options=[
                            {"label": "Long (Call)", "value": "long"},
                            {"label": "Short (Put)", "value": "short"},
                        ],
                        value="long",
                        style={"marginBottom": "8px", "fontSize": "12px"},
                        clearable=False,
                    ),
                    html.Div("Open Price", style=label_style),
                    dcc.Input(
                        id="calc-open-price",
                        type="number",
                        value=600.00,
                        style=input_style,
                    ),
                    html.Div("Current Price", style=label_style),
                    dcc.Input(
                        id="calc-current-price",
                        type="number",
                        value=605.00,
                        style=input_style,
                    ),
                    html.Div("Strike Price", style=label_style),
                    dcc.Input(
                        id="calc-strike-price",
                        type="number",
                        value=600.00,
                        style=input_style,
                    ),
                    html.Div("ATR", style=label_style),
                    dcc.Input(
                        id="calc-atr", type="number", value=10.00, style=input_style
                    ),
                    html.Div("Bid Price", style=label_style),
                    dcc.Input(
                        id="calc-bid-price",
                        type="number",
                        value=8.50,
                        style=input_style,
                    ),
                    html.Div("Ask Price", style=label_style),
                    dcc.Input(
                        id="calc-ask-price",
                        type="number",
                        value=9.00,
                        style=input_style,
                    ),
                    html.Div("IV Override (Optional)", style=label_style),
                    dcc.Input(
                        id="calc-iv-override",
                        type="number",
                        placeholder="Leave blank for auto",
                        style=input_style,
                    ),
                    html.Button(
                        "Calculate",
                        id="calc-button",
                        style={
                            "width": "100%",
                            "backgroundColor": "#00cc66",
                            "color": "#ffffff",
                            "border": "none",
                            "padding": "8px",
                            "borderRadius": "3px",
                            "cursor": "pointer",
                            "fontSize": "12px",
                            "fontWeight": "bold",
                            "marginTop": "10px",
                        },
                    ),
                ],
                style={"padding": "10px"},
            ),
            # Results Section
            html.Div(
                [
                    html.Div(
                        "Results",
                        style={
                            "backgroundColor": "#2d2d2d",
                            "color": "#ffffff",
                            "padding": "6px 8px",
                            "fontWeight": "bold",
                            "fontSize": "12px",
                            "marginTop": "15px",
                            "marginBottom": "5px",
                        },
                    ),
                    html.Div(
                        id="calc-results",
                        children=[
                            html.Div(
                                [
                                    html.Span(
                                        "Target Price:", style={"color": "#aaaaaa"}
                                    ),
                                    html.Span(
                                        "--",
                                        style={
                                            "color": "#ffffff",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ],
                                style=result_row_style,
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        "Option Price:", style={"color": "#aaaaaa"}
                                    ),
                                    html.Span(
                                        "--",
                                        style={
                                            "color": "#ffffff",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ],
                                style=result_row_style,
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        "Intrinsic Value:", style={"color": "#aaaaaa"}
                                    ),
                                    html.Span(
                                        "--",
                                        style={
                                            "color": "#ffffff",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ],
                                style=result_row_style,
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        "Extrinsic Value:", style={"color": "#aaaaaa"}
                                    ),
                                    html.Span(
                                        "--",
                                        style={
                                            "color": "#ffffff",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ],
                                style=result_row_style,
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        "Target Size:", style={"color": "#aaaaaa"}
                                    ),
                                    html.Span(
                                        "--",
                                        style={
                                            "color": "#ffffff",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ],
                                style=result_row_style,
                            ),
                            html.Div(
                                [
                                    html.Span("Tradable:", style={"color": "#aaaaaa"}),
                                    html.Span(
                                        "--",
                                        style={
                                            "color": "#ffffff",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ],
                                style=result_row_style,
                            ),
                        ],
                    ),
                ],
                style={"padding": "0 10px"},
            ),
        ],
        style={
            "backgroundColor": "#2d2d2d",
            "height": "100%",
            "overflowY": "auto",
            "borderLeft": "1px solid #404040",
        },
    )
