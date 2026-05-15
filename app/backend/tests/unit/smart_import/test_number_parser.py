from decimal import Decimal

import pytest

from backend.services.smart_import.number_parser import parse_decimal_br


@pytest.mark.parametrize(
    "input_val,expected",
    [
        ("1.234,56", Decimal("1234.56")),
        ("1234,56", Decimal("1234.56")),
        ("1,234.56", Decimal("1234.56")),
        ("1234.56", Decimal("1234.56")),
        ("1234", Decimal("1234")),
        ("0", Decimal("0")),
        ("  42  ", Decimal("42")),
        ("R$ 1.234,56", Decimal("1234.56")),
        ("1.234", Decimal("1234")),
        ("1,234", Decimal("1.234")),
        (None, None),
        ("", None),
        ("abc", None),
    ],
)
def test_parse_decimal_br(input_val, expected):
    assert parse_decimal_br(input_val) == expected
