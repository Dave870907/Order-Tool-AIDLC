import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional

from bot.models import AggregationResult, MenuItem, Order, Session
from bot.scheduler import DeadlineScheduler
from bot.storage import FileStore

logger = logging.getLogger(__name__)
_STORE_KEY = "session"


class SessionService:
    def __init__(self, store: FileStore, scheduler: DeadlineScheduler):
        self._store = store
        self._scheduler = scheduler

    def get_active(self) -> Optional[Session]:
        data = self._store.get(_STORE_KEY)
        if data is None or data.get("status") != "active":
            return None
        return _from_dict(data)

    def create(
        self,
        channel_id: str,
        thread_ts: str,
        restaurant: str,
        menu: List[MenuItem],
        deadline: datetime,
        on_deadline: Callable,
    ) -> Session:
        session = Session(
            session_id=str(uuid.uuid4()),
            channel_id=channel_id,
            thread_ts=thread_ts,
            restaurant=restaurant,
            menu=menu,
            deadline=deadline.isoformat(),
            orders=[],
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        _save(self._store, session)
        self._scheduler.schedule(session.session_id, deadline, on_deadline)
        return session

    def add_order(self, session: Session, order: Order) -> Session:
        session.orders.append(order)
        _save(self._store, session)
        return session

    def aggregate(self, session: Session) -> AggregationResult:
        totals: dict = {}
        for order in session.orders:
            item = session.find_menu_item(order.item_name)
            if item is None:
                continue
            if order.item_name not in totals:
                totals[order.item_name] = {"quantity": 0, "unit_price": item.price}
            totals[order.item_name]["quantity"] += order.quantity

        items = [
            {
                "name": name,
                "quantity": info["quantity"],
                "unit_price": info["unit_price"],
                "subtotal": round(info["quantity"] * info["unit_price"], 2),
            }
            for name, info in totals.items()
        ]
        grand_total = round(sum(i["subtotal"] for i in items), 2)

        return AggregationResult(
            restaurant=session.restaurant,
            session_id=session.session_id,
            items=items,
            grand_total=grand_total,
            order_count=len(session.orders),
        )

    def complete(self, session: Session) -> None:
        session.status = "completed"
        _save(self._store, session)
        self._scheduler.cancel(session.session_id)


def _save(store: FileStore, session: Session) -> None:
    store.set(
        _STORE_KEY,
        {
            "session_id": session.session_id,
            "channel_id": session.channel_id,
            "thread_ts": session.thread_ts,
            "restaurant": session.restaurant,
            "menu": [{"name": i.name, "price": i.price} for i in session.menu],
            "deadline": session.deadline,
            "orders": [
                {
                    "user_id": o.user_id,
                    "user_name": o.user_name,
                    "item_name": o.item_name,
                    "quantity": o.quantity,
                    "timestamp": o.timestamp,
                }
                for o in session.orders
            ],
            "status": session.status,
            "created_at": session.created_at,
        },
    )


def _from_dict(data: dict) -> Session:
    return Session(
        session_id=data["session_id"],
        channel_id=data["channel_id"],
        thread_ts=data["thread_ts"],
        restaurant=data["restaurant"],
        menu=[MenuItem(name=m["name"], price=m["price"]) for m in data["menu"]],
        deadline=data["deadline"],
        orders=[
            Order(
                user_id=o["user_id"],
                user_name=o["user_name"],
                item_name=o["item_name"],
                quantity=o["quantity"],
                timestamp=o["timestamp"],
            )
            for o in data.get("orders", [])
        ],
        status=data["status"],
        created_at=data["created_at"],
    )
