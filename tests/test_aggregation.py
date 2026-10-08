"""Aggregation calculation tests — exercises the math directly via SessionService.aggregate()."""
from unittest.mock import MagicMock

import pytest

from bot.models import MenuItem, Order, Session
from bot.services.session_service import SessionService


def _make_service():
    store = MagicMock()
    store.get.return_value = None
    return SessionService(store, MagicMock())


def _session(orders, menu=None):
    if menu is None:
        menu = [
            MenuItem("炸雞便當", 80),
            MenuItem("排骨便當", 85),
            MenuItem("素食便當", 75),
        ]
    return Session(
        session_id="t",
        channel_id="C",
        thread_ts="1.0",
        restaurant="師大便當",
        menu=menu,
        deadline="2026-10-08T12:30:00+00:00",
        orders=orders,
        status="active",
        created_at="2026-10-08T10:00:00+00:00",
    )


def test_empty_orders_zero_total():
    svc = _make_service()
    result = svc.aggregate(_session([]))
    assert result.grand_total == 0
    assert result.items == []
    assert result.order_count == 0


def test_single_order_single_qty():
    svc = _make_service()
    result = svc.aggregate(_session([Order("U1", "A", "炸雞便當", 1, "t")]))
    assert result.grand_total == 80
    assert result.items[0]["subtotal"] == 80


def test_single_order_multiple_qty():
    svc = _make_service()
    result = svc.aggregate(_session([Order("U1", "A", "炸雞便當", 3, "t")]))
    assert result.items[0]["quantity"] == 3
    assert result.items[0]["subtotal"] == 240


def test_same_item_multiple_orders_aggregated():
    svc = _make_service()
    orders = [
        Order("U1", "A", "炸雞便當", 2, "t1"),
        Order("U2", "B", "炸雞便當", 1, "t2"),
    ]
    result = svc.aggregate(_session(orders))
    assert len(result.items) == 1
    assert result.items[0]["quantity"] == 3
    assert result.items[0]["subtotal"] == 240


def test_multiple_items_correct_grand_total():
    svc = _make_service()
    orders = [
        Order("U1", "A", "炸雞便當", 1, "t1"),   # 80
        Order("U2", "B", "排骨便當", 1, "t2"),    # 85
        Order("U3", "C", "素食便當", 2, "t3"),    # 150
    ]
    result = svc.aggregate(_session(orders))
    assert result.grand_total == 315


def test_order_count_matches_orders_list():
    svc = _make_service()
    orders = [
        Order("U1", "A", "炸雞便當", 2, "t1"),
        Order("U2", "B", "排骨便當", 1, "t2"),
    ]
    result = svc.aggregate(_session(orders))
    assert result.order_count == 2


def test_restaurant_name_in_result():
    svc = _make_service()
    result = svc.aggregate(_session([]))
    assert result.restaurant == "師大便當"
