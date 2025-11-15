import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from core.calculator_ui import create_calculator_panel

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Import callbacks to register them with the app - MUST be after app initialization
from core.callbacks import register_clientside_callbacks, register_python_callbacks

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script src="https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .trading-container {
                display: flex;
                height: 100vh;
                background-color: #1e1e1e;
            }
            .left-panel {
                width: 250px;
                background-color: #2d2d2d;
                border-right: 1px solid #404040;
                overflow-y: auto;
                padding: 10px;
            }
            .right-panel {
                width: 300px;
                background-color: #2d2d2d;
                overflow-y: auto;
            }
            .main-chart-area {
                flex: 1;
                display: flex;
                flex-direction: column;
                background-color: #1e1e1e;
            }
            .chart-container {
                flex: 1;
                position: relative;
                margin: 5px;
            }
            .indicators-panel {
                height: 250px;
                display: flex;
                flex-direction: column;
                border-top: 1px solid #404040;
            }
            .indicator-chart {
                flex: 1;
                margin: 2px;
                border: 1px solid #404040;
            }
            .controls-bar {
                height: 40px;
                background-color: #2d2d2d;
                border-bottom: 1px solid #404040;
                display: flex;
                align-items: center;
                padding: 0 10px;
                gap: 10px;
            }
            .control-input {
                background-color: #404040;
                border: 1px solid #606060;
                color: #000000;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            .control-button {
                background-color: #0066cc;
                border: none;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
                cursor: pointer;
                font-size: 12px;
            }
            .control-button:hover {
                background-color: #0080ff;
            }
            #main-chart, #momentum-chart, #squeeze-chart, #volume-chart {
                height: 100%;
                width: 100%;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

app.layout = html.Div(
    [
        html.Div(
            [
                html.Label("Symbol:", style={"color": "#ffffff", "marginRight": "5px"}),
                dcc.Input(
                    id="symbol-input",
                    value="QQQ",
                    type="text",
                    className="control-input",
                    readOnly=True,
                    placeholder="Auto-filled from NinjaTrader",
                    style={
                        "width": "80px",
                        "marginRight": "10px",
                        "backgroundColor": "#2d2d2d",
                        "color": "#ffffff",
                        "cursor": "not-allowed",
                    },
                ),
                html.Label(
                    "Interval:",
                    style={
                        "color": "white",
                        "marginRight": "5px",
                    },
                ),
                dcc.Dropdown(
                    id="interval-dropdown",
                    options=[
                        {"label": "Daily", "value": "1d"},
                        {"label": "Weekly", "value": "1wk"},
                    ],
                    value="1d",
                    className="control-input",
                    style={
                        "width": "100px",
                        "marginRight": "10px",
                        "backgroundColor": "#ffffff",
                        "color": "#404040",
                    },
                ),
                html.Button("Update", id="update-btn", className="control-button"),
                dcc.Interval(
                    id="auto-update", interval=30000, n_intervals=0, max_intervals=-1
                ),
            ],
            className="controls-bar",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(id="data-box"),
                        html.Div(id="panel-2"),
                        html.Div(id="panel-3"),
                        html.Div(id="panel-4"),
                        html.Div(id="panel-5"),
                    ],
                    className="left-panel",
                    style={"overflowY": "auto"},
                ),
                html.Div(
                    [
                        html.Div(
                            [html.Div(id="main-chart")],
                            className="chart-container",
                            style={"flex": "2"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            id="momentum-chart",
                                            className="indicator-chart",
                                        ),
                                        html.Div(
                                            id="squeeze-chart",
                                            className="indicator-chart",
                                        ),
                                        html.Div(
                                            id="volume-chart",
                                            className="indicator-chart",
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "height": "100%",
                                    },
                                )
                            ],
                            className="indicators-panel",
                        ),
                    ],
                    className="main-chart-area",
                ),
                html.Div([create_calculator_panel()], className="right-panel"),
            ],
            className="trading-container",
        ),
        dcc.Store(id="chart-data"),
        dcc.Store(id="dataframe-store"),
        dcc.Store(id="clicked-bar-index"),
        dcc.Store(id="last-symbol-store"),
    ]
)

register_clientside_callbacks(app)
register_python_callbacks(app)

# Initialize database
from core.db import init_database

init_database()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
