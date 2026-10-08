from datetime import datetime, timezone, timedelta

import pytest

from bot.handlers.commands import _parse_deadline, _parse_menu


# --- _parse_deadline ---

def test_relative_minutes():
    before = datetime.now(timezone.utc)
    result = _parse_deadline("30m")
    after = datetime.now(timezone.utc)
    assert result is not None
    assert before + timedelta(minutes=29) < result < after + timedelta(minutes=31)


def test_relative_hours():
    before = datetime.now(timezone.utc)
    result = _parse_deadline("2h")
    assert result is not None
    assert result > before + timedelta(hours=1, minutes=59)


def test_hhmm_format_returns_datetime():
    result = _parse_deadline("12:30")
    assert result is not None
    assert result.hour == 12
    assert result.minute == 30


def test_hhmm_in_future():
    result = _parse_deadline("12:30")
    assert result > datetime.now(timezone.utc)


def test_empty_string_returns_none():
    assert _parse_deadline("") is None


def test_invalid_text_returns_none():
    assert _parse_deadline("invalid") is None
    assert _parse_deadline("abc") is None
    assert _parse_deadline("99:99") is None


def test_single_digit_minutes_not_valid():
    # "5" alone is not a valid format
    assert _parse_deadline("5") is None


# --- _parse_menu ---

def test_parse_menu_single_item():
    items = _parse_menu("炸雞便當:80")
    assert len(items) == 1
    assert items[0].name == "炸雞便當"
    assert items[0].price == 80


def test_parse_menu_multiple_items():
    items = _parse_menu("炸雞便當:80, 排骨便當:85")
    assert len(items) == 2
    names = [i.name for i in items]
    assert "炸雞便當" in names
    assert "排骨便當" in names


def test_parse_menu_decimal_price():
    items = _parse_menu("炸雞便當:79.5")
    assert items[0].price == 79.5


def test_parse_menu_no_colon_returns_empty():
    assert _parse_menu("炸雞便當 80") == []


def test_parse_menu_empty_string_returns_empty():
    assert _parse_menu("") == []


def test_parse_menu_invalid_price_returns_empty():
    assert _parse_menu("炸雞便當:abc") == []
