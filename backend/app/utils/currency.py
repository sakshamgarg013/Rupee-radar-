def format_inr(amount: float, include_decimals: bool = False) -> str:
    """
    Format a number into Indian currency notation with ₹ symbol.
    Example:
        125000 -> ₹1,25,000
        1234567.89 -> ₹12,34,567.89
        -500 -> -₹500
    """
    is_negative = amount < 0
    abs_amount = abs(amount)

    if include_decimals:
        formatted_base = f"{abs_amount:.2f}"
        integer_part, decimal_part = formatted_base.split(".")
    else:
        integer_part = str(int(round(abs_amount)))
        decimal_part = ""

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        # Last 3 digits
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        # Group remaining digits in pairs from right to left
        groups = []
        while remaining:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        groups.reverse()
        formatted_int = ",".join(groups) + "," + last_three

    result = f"₹{formatted_int}"
    if include_decimals and decimal_part:
        result += f".{decimal_part}"

    if is_negative:
        result = f"-{result}"

    return result
