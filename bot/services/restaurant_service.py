from datetime import datetime, timezone
from typing import List, Optional

from bot.models import MenuItem, Restaurant
from bot.storage import FileStore

_STORE_KEY = "restaurants"


class RestaurantService:
    def __init__(self, store: FileStore):
        self._store = store

    def save(self, name: str, menu: List[MenuItem]) -> None:
        restaurants = self._load_all()
        entry = {
            "name": name,
            "menu": [{"name": item.name, "price": item.price} for item in menu],
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        idx = next((i for i, r in enumerate(restaurants) if r["name"] == name), None)
        if idx is not None:
            restaurants[idx] = entry
        else:
            restaurants.append(entry)
        self._store.set(_STORE_KEY, restaurants)

    def list_all(self) -> List[Restaurant]:
        return [_from_dict(r) for r in self._load_all()]

    def get(self, name: str) -> Optional[Restaurant]:
        match = next((r for r in self._load_all() if r["name"] == name), None)
        return _from_dict(match) if match else None

    def _load_all(self) -> list:
        data = self._store.get(_STORE_KEY)
        return data if data is not None else []


def _from_dict(data: dict) -> Restaurant:
    return Restaurant(
        name=data["name"],
        menu=[MenuItem(name=m["name"], price=m["price"]) for m in data["menu"]],
        saved_at=data["saved_at"],
    )
