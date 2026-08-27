import os
from loader import parse_number

def test_parse_number():
    assert parse_number(123.45) == 123.45
    assert parse_number("123,45") == 123.45
    assert parse_number(":") is None
    assert parse_number("") is None
    assert parse_number(None) is None
