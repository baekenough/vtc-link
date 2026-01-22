import pytest

from app.core.errors import ParseError
from app.utils.parsing import (
    coerce_int,
    format_screened_date,
    parse_birthdate,
    parse_float,
    parse_int,
    parse_timestamp,
)


def test_parse_int_valid():
    assert parse_int("123", "SBP") == 123


def test_parse_int_invalid():
    with pytest.raises(ParseError):
        parse_int("abc", "SBP")


def test_parse_float_valid():
    assert parse_float("36.5", "BT") == 36.5


def test_parse_birthdate():
    assert parse_birthdate("19900101", ["%Y%m%d"]) == "19900101"


def test_parse_timestamp():
    result = parse_timestamp("2024-01-01 10:00:00", ["%Y-%m-%d %H:%M:%S"])
    assert result.endswith("Z")


def test_coerce_int():
    assert coerce_int("10") == 10
    assert coerce_int("10.2") == 10
    assert coerce_int("invalid") == 0


def test_format_screened_date():
    value = "2024-01-01 10:00:00"
    result = format_screened_date(value, ["%Y-%m-%d %H:%M:%S"])
    assert result == "20240101 10:00:00"
