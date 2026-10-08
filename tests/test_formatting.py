from datetime import datetime, timezone

from bot.formatting import format_aggregation_message, format_menu_message
from bot.models import AggregationResult, MenuItem


def _deadline():
    return datetime(2026, 10, 8, 12, 30, tzinfo=timezone.utc)


def test_menu_message_contains_restaurant_name():
    msg = format_menu_message("師大便當", [MenuItem("炸雞便當", 80)], _deadline())
    assert "師大便當" in msg


def test_menu_message_contains_item_name():
    msg = format_menu_message("師大便當", [MenuItem("炸雞便當", 80)], _deadline())
    assert "炸雞便當" in msg


def test_menu_message_contains_item_price():
    msg = format_menu_message("師大便當", [MenuItem("炸雞便當", 80)], _deadline())
    assert "80" in msg


def test_menu_message_contains_deadline_time():
    msg = format_menu_message("師大便當", [MenuItem("炸雞便當", 80)], _deadline())
    assert "12:30" in msg


def test_menu_message_lists_all_items():
    menu = [MenuItem("炸雞便當", 80), MenuItem("排骨便當", 85), MenuItem("素食便當", 75)]
    msg = format_menu_message("師大便當", menu, _deadline())
    assert "炸雞便當" in msg
    assert "排骨便當" in msg
    assert "素食便當" in msg


def test_aggregation_message_contains_restaurant():
    result = AggregationResult(
        restaurant="師大便當",
        session_id="s1",
        items=[{"name": "炸雞便當", "quantity": 2, "unit_price": 80, "subtotal": 160}],
        grand_total=160,
        order_count=2,
    )
    msg = format_aggregation_message(result)
    assert "師大便當" in msg


def test_aggregation_message_contains_subtotal():
    result = AggregationResult(
        restaurant="師大便當",
        session_id="s1",
        items=[{"name": "炸雞便當", "quantity": 2, "unit_price": 80, "subtotal": 160}],
        grand_total=160,
        order_count=2,
    )
    msg = format_aggregation_message(result)
    assert "160" in msg


def test_aggregation_message_contains_grand_total():
    result = AggregationResult(
        restaurant="師大便當",
        session_id="s1",
        items=[
            {"name": "炸雞便當", "quantity": 1, "unit_price": 80, "subtotal": 80},
            {"name": "排骨便當", "quantity": 1, "unit_price": 85, "subtotal": 85},
        ],
        grand_total=165,
        order_count=2,
    )
    msg = format_aggregation_message(result)
    assert "165" in msg


def test_aggregation_empty_orders_message():
    result = AggregationResult(
        restaurant="師大便當",
        session_id="s1",
        items=[],
        grand_total=0,
        order_count=0,
    )
    msg = format_aggregation_message(result)
    assert "沒有" in msg
    assert "師大便當" in msg
