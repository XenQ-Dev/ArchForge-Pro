"""String formatting helpers for Indian currency and dates."""
from __future__ import annotations


def fmt_inr(amount: float) -> str:
    """Format a number as Indian Rupees with ₹ symbol and Indian comma grouping."""
    if amount is None:
        return "₹0.00"
    is_negative = amount < 0
    amount = abs(amount)

    # Indian grouping: last 3 digits, then 2 digits each
    integer_part = int(amount)
    decimal_part = round((amount - integer_part) * 100)

    s = str(integer_part)
    if len(s) <= 3:
        grouped = s
    else:
        grouped = s[-3:]
        s = s[:-3]
        while s:
            grouped = s[-2:] + "," + grouped
            s = s[:-2]

    result = f"₹{grouped}.{decimal_part:02d}"
    return f"-{result}" if is_negative else result


def fmt_date(date_str: str | None) -> str:
    """Convert yyyy-mm-dd to dd-MM-yyyy."""
    if not date_str:
        return "—"
    try:
        parts = date_str.split("T")[0].split("-")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
    except Exception:
        pass
    return date_str or "—"
