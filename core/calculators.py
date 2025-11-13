def calculate_trade_analysis(data: dict) -> dict:
    """
    Calculate all trading metrics with scenario-based extrinsic values
    Enhanced with intrinsic_adjustment feature
    """
    open_price = data["open_price"]
    atr_value = data["atr_value"]
    bid_price = data["bid_price"]
    ask_price = data["ask_price"]
    strike_price = data["strike_price"]
    current_price = data["current_price"]
    trade_direction = data.get("trade_direction", "long")

    intrinsic_value = calculate_custom_intrinsic(data)

    scenario = data.get("scenario", "standard")

    if trade_direction == "short":
        target_price = open_price - atr_value
    else:
        target_price = open_price + atr_value

    option_price = (bid_price + ask_price) / 2

    auto_extrinsic = option_price - intrinsic_value
    extrinsic_value = auto_extrinsic
    calculation_method = "Standard (Auto)"

    target_size = option_price - intrinsic_value

    is_tradable = target_price <= target_size

    return {
        "target_price": round(target_price, 4),
        "option_price": round(option_price, 4),
        "intrinsic_value": round(intrinsic_value, 4),
        "extrinsic_value": round(extrinsic_value, 4),
        "target_size": round(target_size, 4),
        "is_tradable": is_tradable,
        "calculation_method": calculation_method,
        "scenario": scenario,
        "validation_rule": f"Target Price ({round(target_price, 4)}) <= Target Size ({round(target_size, 4)})",
        "intrinsic_calculation_method": data.get(
            "intrinsic_calculation_method", "auto"
        ),
        "intrinsic_adjustment_applied": data.get("intrinsic_adjustment", 1.0),
    }


def calculate_short_trade_analysis(data: dict) -> dict:
    """
    For short trades (subtract instead of add)
    Enhanced with intrinsic_adjustment feature
    """
    open_price = data["open_price"]
    atr_value = data["atr_value"]
    bid_price = data["bid_price"]
    ask_price = data["ask_price"]
    strike_price = data["strike_price"]
    current_price = data["current_price"]

    intrinsic_value = calculate_custom_intrinsic(data)

    target_price = open_price - atr_value

    option_price = (bid_price + ask_price) / 2
    extrinsic_value = option_price - intrinsic_value
    target_size = option_price - intrinsic_value

    is_tradable = target_price <= target_size

    return {
        "target_price": round(target_price, 4),
        "option_price": round(option_price, 4),
        "intrinsic_value": round(intrinsic_value, 4),
        "extrinsic_value": round(extrinsic_value, 4),
        "target_size": round(target_size, 4),
        "is_tradable": is_tradable,
        "validation_rule": f"Target Price ({round(target_price, 4)}) <= Target Size ({round(target_size, 4)})",
        "intrinsic_calculation_method": data.get(
            "intrinsic_calculation_method", "auto"
        ),
        "intrinsic_adjustment_applied": data.get("intrinsic_adjustment", 1.0),
    }


def calculate_custom_intrinsic(data: dict) -> float:
    """
    Calculate intrinsic value with multiple customization options

    Mathematical Formulas:
    For CALL Options (long trades): Base Intrinsic = max(0, Current Price - Strike Price)
    For PUT Options (short trades): Base Intrinsic = max(0, Strike Price - Current Price)
    Final Intrinsic = Base Intrinsic × Intrinsic Adjustment
    """
    strike_price = data["strike_price"]
    current_price = data["current_price"]
    trade_direction = data.get("trade_direction", "long")

    if "custom_intrinsic_value" in data and data["custom_intrinsic_value"] is not None:
        data["intrinsic_calculation_method"] = "manual_override"
        return float(data["custom_intrinsic_value"])

    if trade_direction == "short":
        base_intrinsic = max(0, strike_price - current_price)
    else:
        base_intrinsic = max(0, current_price - strike_price)

    adjustment = data.get("intrinsic_adjustment", 1.0)
    adjusted_intrinsic = base_intrinsic * adjustment

    if adjustment != 1.0:
        data["intrinsic_calculation_method"] = f"adjusted_auto_{adjustment}x"
    else:
        data["intrinsic_calculation_method"] = "auto"

    return adjusted_intrinsic
