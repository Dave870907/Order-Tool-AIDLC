from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class MenuItem:
    name: str
    price: float


@dataclass
class Order:
    user_id: str
    user_name: str
    item_name: str
    quantity: int
    timestamp: str


@dataclass
class Session:
    session_id: str
    channel_id: str
    thread_ts: str
    restaurant: str
    menu: List[MenuItem]
    deadline: str  # ISO 8601
    orders: List[Order]
    status: str    # "active" | "completed"
    created_at: str

    def get_deadline_dt(self) -> datetime:
        return datetime.fromisoformat(self.deadline)

    def is_active(self) -> bool:
        return self.status == "active"

    def find_menu_item(self, name: str) -> Optional[MenuItem]:
        name_lower = name.lower().strip()
        for item in self.menu:
            if item.name.lower() == name_lower:
                return item
        return None

    def get_menu_names(self) -> List[str]:
        return [item.name for item in self.menu]


@dataclass
class Restaurant:
    name: str
    menu: List[MenuItem]
    saved_at: str


@dataclass
class AggregationResult:
    restaurant: str
    session_id: str
    items: List[dict]  # [{name, quantity, unit_price, subtotal}]
    grand_total: float
    order_count: int
