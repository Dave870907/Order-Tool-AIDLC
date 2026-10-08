import pytest

from bot.models import MenuItem
from bot.services.restaurant_service import RestaurantService
from bot.storage import FileStore


@pytest.fixture
def service(tmp_path):
    return RestaurantService(FileStore(str(tmp_path)))


def test_list_all_empty_by_default(service):
    assert service.list_all() == []


def test_save_and_list(service):
    service.save("師大便當", [MenuItem("炸雞便當", 80), MenuItem("排骨便當", 85)])
    restaurants = service.list_all()
    assert len(restaurants) == 1
    assert restaurants[0].name == "師大便當"
    assert len(restaurants[0].menu) == 2


def test_get_existing_restaurant(service):
    service.save("師大便當", [MenuItem("炸雞便當", 80)])
    result = service.get("師大便當")
    assert result is not None
    assert result.name == "師大便當"
    assert result.menu[0].price == 80


def test_get_nonexistent_returns_none(service):
    assert service.get("不存在") is None


def test_save_updates_existing_entry(service):
    service.save("師大便當", [MenuItem("炸雞便當", 80)])
    service.save("師大便當", [MenuItem("炸雞便當", 80), MenuItem("素食便當", 75)])
    restaurants = service.list_all()
    assert len(restaurants) == 1
    assert len(restaurants[0].menu) == 2


def test_save_multiple_restaurants(service):
    service.save("師大便當", [MenuItem("炸雞便當", 80)])
    service.save("老王便當", [MenuItem("紅燒便當", 90)])
    assert len(service.list_all()) == 2


def test_menu_prices_are_preserved(service):
    service.save("師大便當", [MenuItem("炸雞便當", 80.5)])
    result = service.get("師大便當")
    assert result.menu[0].price == 80.5


def test_persistence_across_instances(tmp_path):
    store = FileStore(str(tmp_path))
    svc1 = RestaurantService(store)
    svc1.save("師大便當", [MenuItem("炸雞便當", 80)])

    svc2 = RestaurantService(FileStore(str(tmp_path)))
    assert svc2.get("師大便當") is not None
