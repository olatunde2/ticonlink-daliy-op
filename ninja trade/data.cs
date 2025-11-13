#region Using declarations
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.IO;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui;
using NinjaTrader.NinjaScript;
using NinjaTrader.Data;
#endregion

namespace NinjaTrader.NinjaScript.AddOns
{
    public class DataBoxStreamer : AddOnBase
    {
        private readonly string snapshotsRoot = @"C:\NinjaTrader\DailySnapshots";
        private readonly Uri wsUri = new Uri("ws://localhost:9000/data"); // Python receiver endpoint
        private bool didFullExport = false;

        // WebSocket fields
        private ClientWebSocket wsClient;
        private bool wsConnected = false;

        protected override void OnWindowCreated(Window window)
        {
            if (!(window is Chart chart))
                return;

            chart.Dispatcher.InvokeAsync(async () =>
            {
                await Task.Delay(1500); // wait for chart load

                var cc = GetChartControl(chart);
                if (cc == null) return;

                TryAddOverlay(cc);

                if (!didFullExport)
                {
                    didFullExport = true;
                    await Task.Delay(2000); // ensure indicators loaded
                    await ConnectWebSocketAsync();
                    string json = ExportAllBarsToSingleFile(chart);
                    await SendWebSocketAsync(json);

                    NinjaTrader.Code.Output.Process("Full historical export + WebSocket send completed.", PrintTo.OutputTab1);
                }
            });
        }

        // ------------------------------------------------------------------
        // Main Export Logic
        // ------------------------------------------------------------------
        private string ExportAllBarsToSingleFile(Chart chart)
        {
            string jsonOutput = string.Empty;
            try
            {
                var cc = GetChartControl(chart);
                var chartBars = cc?.BarsArray?.FirstOrDefault();
                var primaryBars = chartBars?.Bars;
                if (primaryBars == null || primaryBars.Count == 0)
                    return "{}";

                string instrument = cc.Instrument?.FullName ?? "Unknown";
                string instrumentKey = (cc.Instrument?.MasterInstrument?.Name ?? "Unknown").Replace(':', '_');

                string outDir = Path.Combine(snapshotsRoot);
                Directory.CreateDirectory(outDir);
                string outFile = Path.Combine(outDir, $"{instrumentKey}_AllBars.json");

                var sb = new StringBuilder();
                sb.Append("{\n");
                bool firstDate = true;

                int totalBars = primaryBars.Count;
                for (int i = 0; i < totalBars; i++)
                {
                    DateTime t = primaryBars.GetTime(i);
                    int isoWeek = CultureInfo.InvariantCulture.Calendar.GetWeekOfYear(
                        t, CalendarWeekRule.FirstFourDayWeek, DayOfWeek.Monday);

                    var data = new Dictionary<string, object>
                    {
                        ["Week"] = $"{isoWeek}/{t.Year}",
                        ["Date"] = t.ToString("yyyy-MM-dd"),
                        ["Open"] = primaryBars.GetOpen(i),
                        ["High"] = primaryBars.GetHigh(i),
                        ["Low"] = primaryBars.GetLow(i),
                        ["Close"] = primaryBars.GetClose(i),
                        ["Volume"] = primaryBars.GetVolume(i),
                        ["Instrument"] = instrument,
                        ["BarIndex"] = i
                    };

                    var panels = new Dictionary<string, object>();
                    data["Panels"] = panels;

                    // Panel 1 base data
                    var p1 = GetOrCreatePanel(panels, "Panel 1");
                    p1["Price"] = primaryBars.GetClose(i);
                    p1["Open"] = primaryBars.GetOpen(i);
                    p1["High"] = primaryBars.GetHigh(i);
                    p1["Low"] = primaryBars.GetLow(i);
                    p1["Close"] = primaryBars.GetClose(i);
                    p1["Volume"] = primaryBars.GetVolume(i);

                    // Indicators
                    foreach (var indi in cc.Indicators)
                    {
                        int panelIndex = GetIndicatorPanelIndex(indi, cc);
                        string panelKey = panelIndex > 0 ? $"Panel {panelIndex}" : "Panel ?";
                        var panel = GetOrCreatePanel(panels, panelKey);

                        for (int pidx = 0; pidx < indi.Plots.Count(); pidx++)
                        {
                            string label = indi.Plots[pidx].Name;
                            double v = double.NaN;
                            try
                            {
                                var series = indi.Values[pidx];
                                int count = series.Count;

                                // Map to correct offset index
                                int offset = primaryBars.Count - count;
                                int idx = i - offset;

                                if (idx >= 0 && idx < count)
                                    v = series.GetValueAt(idx);
                            }
                            catch { }

                            if (double.IsNaN(v) || double.IsInfinity(v))
                                panel[label] = null;
                            else
                                panel[label] = v;
                        }
                    }

                    if (!firstDate) sb.Append(",\n");
                    firstDate = false;
                    sb.Append($"  \"{t:yyyy-MM-dd}\": {BuildJson(data)}");
                }

                sb.Append("\n}");
                jsonOutput = sb.ToString();

                File.WriteAllText(outFile, jsonOutput, Encoding.UTF8);
                NinjaTrader.Code.Output.Process($"Exported {totalBars} bars → {outFile}", PrintTo.OutputTab1);
            }
            catch (Exception ex)
            {
                NinjaTrader.Code.Output.Process($"Export error: {ex.Message}", PrintTo.OutputTab1);
            }

            return jsonOutput;
        }

        // ------------------------------------------------------------------
        // Helpers
        // ------------------------------------------------------------------
        private static Dictionary<string, object> GetOrCreatePanel(Dictionary<string, object> panels, string key)
        {
            if (!panels.TryGetValue(key, out var obj) || !(obj is Dictionary<string, object> dict))
            {
                dict = new Dictionary<string, object>();
                panels[key] = dict;
            }
            return (Dictionary<string, object>)panels[key];
        }

        private int GetIndicatorPanelIndex(NinjaTrader.Gui.NinjaScript.IndicatorRenderBase indi, ChartControl cc)
        {
            try
            {
                var prop = indi.GetType().GetProperty("Panel");
                if (prop != null)
                {
                    var val = prop.GetValue(indi);
                    if (val is int n)
                        return n + 1;
                }

                var chartPanelProp = indi.GetType().GetProperty("ChartPanel");
                if (chartPanelProp != null)
                {
                    var chartPanel = chartPanelProp.GetValue(indi);
                    if (chartPanel != null)
                    {
                        int idx = cc.ChartPanels.IndexOf(chartPanel as ChartPanel);
                        if (idx >= 0) return idx + 1;
                    }
                }
            }
            catch { }
            return 1;
        }

        private ChartControl GetChartControl(Chart chart)
        {
            try
            {
                var propActive = chart.GetType().GetProperty("ActiveChartControl");
                if (propActive != null)
                {
                    var cc = propActive.GetValue(chart) as ChartControl;
                    if (cc != null) return cc;
                }

                var propLegacy = chart.GetType().GetProperty("ChartControl");
                if (propLegacy != null)
                {
                    var cc = propLegacy.GetValue(chart) as ChartControl;
                    if (cc != null) return cc;
                }

                var field = chart.GetType().GetField("chartControl",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                return field?.GetValue(chart) as ChartControl;
            }
            catch { return null; }
        }

        private void TryAddOverlay(ChartControl cc)
        {
            try
            {
                var panel = cc.ChartPanels.FirstOrDefault();
                if (panel == null) return;

                var gridField = panel.GetType().GetField("panelGrid",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                var grid = gridField?.GetValue(panel) as System.Windows.Controls.Grid;
                if (grid == null) return;

                var label = new System.Windows.Controls.TextBlock
                {
                    Text = "DataBox Full Export (WebSocket) Active",
                    Foreground = System.Windows.Media.Brushes.LimeGreen,
                    Margin = new Thickness(10, 10, 0, 0)
                };
                grid.Children.Add(label);
            }
            catch { }
        }

        // ------------------------------------------------------------------
        // JSON Builder
        // ------------------------------------------------------------------
        private string BuildJson(Dictionary<string, object> data)
        {
            var sb = new StringBuilder();
            WriteObject(sb, data);
            return sb.ToString();
        }

        private void WriteObject(StringBuilder sb, Dictionary<string, object> obj)
        {
            sb.Append("{");
            bool first = true;
            foreach (var kv in obj)
            {
                if (!first) sb.Append(",");
                first = false;
                sb.Append($"\"{kv.Key}\": ");
                WriteValue(sb, kv.Value);
            }
            sb.Append("}");
        }

        private void WriteValue(StringBuilder sb, object val)
        {
            if (val == null)
            {
                sb.Append("null");
                return;
            }

            if (val is Dictionary<string, object> nested)
            {
                WriteObject(sb, nested);
                return;
            }

            if (val is string s)
            {
                sb.Append($"\"{s.Replace("\"", "\\\"")}\"");
                return;
            }

            if (val is double d)
            {
                if (double.IsNaN(d) || double.IsInfinity(d))
                    sb.Append("null");
                else
                    sb.Append(d.ToString(CultureInfo.InvariantCulture));
                return;
            }

            if (val is int || val is long || val is short)
            {
                sb.Append(Convert.ToString(val, CultureInfo.InvariantCulture));
                return;
            }

            sb.Append($"\"{val}\"");
        }

        // ------------------------------------------------------------------
        // WebSocket Integration
        // ------------------------------------------------------------------
        private async Task ConnectWebSocketAsync()
        {
            try
            {
                wsClient = new ClientWebSocket();
                await wsClient.ConnectAsync(wsUri, CancellationToken.None);
                wsConnected = true;
                NinjaTrader.Code.Output.Process("WebSocket connected.", PrintTo.OutputTab1);
            }
            catch (Exception ex)
            {
                wsConnected = false;
                NinjaTrader.Code.Output.Process($"WebSocket connect failed: {ex.Message}", PrintTo.OutputTab1);
            }
        }

        private async Task SendWebSocketAsync(string json)
        {
            if (string.IsNullOrWhiteSpace(json)) return;

            if (wsClient == null || wsClient.State != WebSocketState.Open)
            {
                await ConnectWebSocketAsync();
                if (!wsConnected) return;
            }

            try
            {
                var bytes = Encoding.UTF8.GetBytes(json);
                await wsClient.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
                NinjaTrader.Code.Output.Process($"JSON sent ({bytes.Length} bytes)", PrintTo.OutputTab1);
            }
            catch (Exception ex)
            {
                wsConnected = false;
                NinjaTrader.Code.Output.Process($" WebSocket send failed: {ex.Message}", PrintTo.OutputTab1);
            }
        }
    }
}
