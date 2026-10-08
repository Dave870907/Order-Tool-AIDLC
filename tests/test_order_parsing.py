import pytest

from bot.handlers.events import _parse_order


def test_simple_item_name():
    item, qty = _parse_order("炸雞便當")
    assert item == "炸雞便當"
    assert qty == 1


def test_item_with_x2():
    item, qty = _parse_order("炸雞便當 x2")
    assert item == "炸雞便當"
    assert qty == 2


def test_item_with_x_no_space():
    item, qty = _parse_order("炸雞便當x2")
    assert item == "炸雞便當"
    assert qty == 2


def test_item_with_number_only():
    item, qty = _parse_order("炸雞便當 3")
    assert item == "炸雞便當"
    assert qty == 3


def test_item_with_fen_suffix():
    item, qty = _parse_order("炸雞便當 2份")
    assert item == "炸雞便當"
    assert qty == 2


def test_item_with_ge_suffix():
    item, qty = _parse_order("炸雞便當 2個")
    assert item == "炸雞便當"
    assert qty == 2


def test_item_with_he_suffix():
    item, qty = _parse_order("炸雞便當 2盒")
    assert item == "炸雞便當"
    assert qty == 2


def test_quantity_minimum_one():
    # zero is coerced to 1
    item, qty = _parse_order("炸雞便當 0")
    assert qty >= 1


def test_uppercase_x():
    item, qty = _parse_order("炸雞便當 X3")
    assert item == "炸雞便當"
    assert qty == 3


def test_fullwidth_x():
    item, qty = _parse_order("炸雞便當 ×2")
    assert item == "炸雞便當"
    assert qty == 2


def test_item_name_with_spaces_preserved():
    item, qty = _parse_order("炸雞 便當 x2")
    assert qty == 2
    assert "炸雞" in item
