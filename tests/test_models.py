from bot.models import MenuItem, Session


def _make_session(**kwargs):
    defaults = dict(
        session_id="sess-1",
        channel_id="C123",
        thread_ts="1234567890.123456",
        restaurant="師大便當",
        menu=[MenuItem(name="炸雞便當", price=80), MenuItem(name="排骨便當", price=85)],
        deadline="2026-10-08T12:30:00+00:00",
        orders=[],
        status="active",
        created_at="2026-10-08T10:00:00+00:00",
    )
    defaults.update(kwargs)
    return Session(**defaults)


def test_find_menu_item_exact_match():
    session = _make_session()
    item = session.find_menu_item("炸雞便當")
    assert item is not None
    assert item.name == "炸雞便當"
    assert item.price == 80


def test_find_menu_item_case_insensitive():
    session = _make_session(menu=[MenuItem(name="Chicken", price=80)])
    item = session.find_menu_item("chicken")
    assert item is not None
    assert item.name == "Chicken"


def test_find_menu_item_strips_whitespace():
    session = _make_session()
    item = session.find_menu_item("  炸雞便當  ")
    assert item is not None


def test_find_menu_item_not_found():
    session = _make_session()
    assert session.find_menu_item("素食便當") is None


def test_get_menu_names_returns_all():
    session = _make_session()
    names = session.get_menu_names()
    assert "炸雞便當" in names
    assert "排骨便當" in names
    assert len(names) == 2


def test_is_active_true_when_active():
    session = _make_session(status="active")
    assert session.is_active() is True


def test_is_active_false_when_completed():
    session = _make_session(status="completed")
    assert session.is_active() is False


def test_get_deadline_dt_parses_isoformat():
    session = _make_session(deadline="2026-10-08T12:30:00+00:00")
    dt = session.get_deadline_dt()
    assert dt.hour == 12
    assert dt.minute == 30
