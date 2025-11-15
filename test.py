import json
from core.data_processing import fetch_and_process_data, format_volume


def test_data_processing():
    """Test function to check if data processing is working"""
    print("=== TESTING DATA PROCESSING ===")

    # Test format_volume function
    test_volume = 45891110
    formatted, abbreviated = format_volume(test_volume)
    print(
        f"Volume formatting test: {test_volume} -> {formatted} (full), {abbreviated} (abbreviated)"
    )

    # Test fetching data
    df, chart_json = fetch_and_process_data()

    if df is not None:
        print("✓ Data fetching successful")

        # Check if Mean column exists and has values
        if "Mean" in df.columns:
            mean_value = df["Mean"].iloc[-1]
            print(f"✓ Mean column exists, latest value: {mean_value}")
        else:
            print("✗ Mean column missing")
            print("Available columns:", df.columns.tolist())

        # Check if volume columns exist
        if "Panel_1_Volume" in df.columns:
            print(f"✓ Panel_1_Volume exists")
        if "Panel_4_Volume" in df.columns:
            print(f"✓ Panel_4_Volume exists")

    if chart_json:
        chart_data = json.loads(chart_json)
        print("✓ Chart data generated")

        # Check what's in the chart data
        if chart_data["candlestick"]:
            latest_candle = chart_data["candlestick"][-1]
            print(
                f"Latest candle volume_formatted: {latest_candle.get('volume_formatted', 'MISSING')}"
            )

        if chart_data["mean"]:
            latest_mean = chart_data["mean"][-1]
            print(f"Latest mean value: {latest_mean.get('value', 'MISSING')}")

        if chart_data["volume"]:
            latest_volume = chart_data["volume"][-1]
            print(
                f"Latest volume formatted: {latest_volume.get('formatted', 'MISSING')}"
            )

    print("=== TEST COMPLETE ===")


# Add this at the bottom to run the test when the file is executed directly
if __name__ == "__main__":
    test_data_processing()
