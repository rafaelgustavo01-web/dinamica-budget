"""Robust Brazilian decimal parser.

Handles:
- 1.234,56  (BR thousand + decimal)
- 1234,56   (BR decimal)
- 1,234.56  (US thousand + decimal)
- 1234.56   (US decimal)
- 1234      (integer)
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def parse_decimal_br(value) -> Decimal | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # Remove common currency / whitespace noise
    s = re.sub(r"^[R$\s ]+", "", s)

    commas = s.count(",")
    dots = s.count(".")

    if commas == 0 and dots == 0:
        try:
            return Decimal(s)
        except InvalidOperation:
            return None

    if commas > 0 and dots > 0:
        # Mixed notation: the right-most separator is the decimal one
        last_comma = s.rfind(",")
        last_dot = s.rfind(".")
        if last_comma > last_dot:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif commas > 1 and dots == 0:
        # Commas used as thousand separators (e.g. 1,234,567)
        s = s.replace(",", "")
    elif dots > 1 and commas == 0:
        # Dots used as thousand separators (e.g. 1.234.567)
        s = s.replace(".", "")
    elif commas == 1 and dots == 0:
        # Single comma treated as decimal separator
        s = s.replace(",", ".")
    elif dots == 1 and commas == 0:
        # Single dot: if exactly 3 digits follow, treat as thousand separator (BR)
        # otherwise treat as decimal separator
        dot_idx = s.find(".")
        frac_len = len(s) - dot_idx - 1
        if frac_len == 3:
            s = s.replace(".", "")
        # else: pass (dot is decimal)

    try:
        return Decimal(s)
    except InvalidOperation:
        return None
