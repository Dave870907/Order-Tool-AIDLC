import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from bot.models import MenuItem, Order
from bot.scheduler import DeadlineScheduler
from bot.services.session_service import SessionService
from bot.storage import FileStore


@pytest.fixture
def store(tmp_path):
    return FileStore(str(tmp_path))


@pytest.fixture
def scheduler():
    return MagicMock(spec=DeadlineScheduler)


@pytest.fixture
def service(store, scheduler):
    return SessionService(store, scheduler)


def _deadline():
    return datetime.now(timezone.utc) + timedelta(hours=1)


def test_get_active_returns_none_when_empty(service):
    assert service.get_active() is None


def test_create_returns_active_session(service, scheduler):
    menu = [MenuItem("炸雞便當", 80)]
    session = service.create("C123", "123.456", "師大便當", menu, _deadline(), lambda: None)
    assert session.status == "active"
    assert session.restaurant == "師大便當"
    assert len(session.menu) == 1


def test_create_schedules_deadline(service, scheduler):
    service.create("C123", "123.456", "師大便當", [MenuItem("炸雞便當", 80)], _deadline(), lambda: None)
    scheduler.schedule.assert_called_once()


def test_get_active_after_create(service, scheduler):
    service.create("C123", "123.456", "師大便當", [MenuItem("炸雞便當", 80)], _deadline(), lambda: None)
    active = service.get_active()
    assert active is not None
    assert active.restaurant == "師大便當"


def test_add_order_persists(service, scheduler):
    session = service.create("C123", "123.456", "師大便當", [MenuItem("炸雞便當", 80)], _deadline(), lambda: None)
    order = Order("U1", "Alice", "炸雞便當", 1, "2026-10-08T10:00:00Z")
    service.add_order(session, order)
    reloaded = service.get_active()
    assert len(reloaded.orders) == 1
    assert reloaded.orders[0].user_id == "U1"


def test_complete_removes_active_session(service, scheduler):
    session = service.create("C123", "123.456", "師大便當", [MenuItem("炸雞便當", 80)], _deadline(), lambda: None)
    service.complete(session)
    assert service.get_active() is None


def test_complete_cancels_scheduler(service, scheduler):
    session = service.create("C123", "123.456", "師大便當", [MenuItem("炸雞便當", 80)], _deadline(), lambda: None)
    service.complete(session)
    scheduler.cancel.assert_called_once_with(session.session_id)


def test_aggregate_single_order(service, scheduler):
    menu = [MenuItem("炸雞便當", 80)]
    session = service.create("C123", "123.456", "師大便當", menu, _deadline(), lambda: None)
    session.orders = [Order("U1", "Alice", "炸雞便當", 1, "t")]
    result = service.aggregate(session)
    assert result.grand_total == 80
    assert result.items[0]["quantity"] == 1
    assert result.order_count == 1


def test_aggregate_combines_same_item(service, scheduler):
    menu = [MenuItem("炸雞便當", 80)]
    session = service.create("C123", "123.456", "師大便當", menu, _deadline(), lambda: None)
    session.orders = [
        Order("U1", "Alice", "炸雞便當", 2, "t1"),
        Order("U2", "Bob", "炸雞便當", 3, "t2"),
    ]
    result = service.aggregate(session)
    assert result.items[0]["quantity"] == 5
    assert result.items[0]["subtotal"] == 400


def test_aggregate_grand_total(service, scheduler):
    menu = [MenuItem("炸雞便當", 80), MenuItem("排骨便當", 85)]
    session = service.create("C123", "123.456", "師大便當", menu, _deadline(), lambda: None)
    session.orders = [
        Order("U1", "Alice", "炸雞便當", 1, "t1"),  # 80
        Order("U2", "Bob", "排骨便當", 2, "t2"),    # 170
    ]
    result = service.aggregate(session)
    assert result.grand_total == 250


def test_aggregate_empty_orders(service, scheduler):
    session = service.create("C123", "123.456", "師大便當", [MenuItem("炸雞便當", 80)], _deadline(), lambda: None)
    result = service.aggregate(session)
    assert result.grand_total == 0
    assert result.items == []
    assert result.order_count == 0
