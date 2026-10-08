import logging
import re
from datetime import datetime, timezone
from typing import Tuple

from slack_bolt import App

from bot.models import Order
from bot.services.session_service import SessionService

logger = logging.getLogger(__name__)


def register_events(app: App, session_service: SessionService) -> None:

    @app.event("message")
    def handle_message(event, client, say):
        # Only process thread replies; ignore top-level messages and bot messages
        if not event.get("thread_ts") or event.get("subtype") or event.get("bot_id"):
            return

        session = session_service.get_active()
        if session is None:
            return

        if event["thread_ts"] != session.thread_ts:
            return

        user_id = event.get("user")
        if not user_id:
            return

        text = event.get("text", "").strip()
        if not text:
            return

        item_name, quantity = _parse_order(text)
        matched_item = session.find_menu_item(item_name)

        if matched_item is None:
            valid_items = "、".join(session.get_menu_names())
            say(
                text=f"<@{user_id}> ❌ 找不到品項 *{item_name}*。\n可選品項：{valid_items}",
                thread_ts=event["thread_ts"],
            )
            return

        try:
            user_info = client.users_info(user=user_id)
            user_name = (
                user_info["user"].get("real_name")
                or user_info["user"].get("name")
                or user_id
            )
        except Exception:
            user_name = user_id

        order = Order(
            user_id=user_id,
            user_name=user_name,
            item_name=matched_item.name,
            quantity=quantity,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        session_service.add_order(session, order)

        qty_text = f" x{quantity}" if quantity > 1 else ""
        total = matched_item.price * quantity
        say(
            text=f"<@{user_id}> ✅ 已記錄：*{matched_item.name}*{qty_text}（${total:.0f}）",
            thread_ts=event["thread_ts"],
        )


def _parse_order(text: str) -> Tuple[str, int]:
    """Parse item name and quantity from a thread reply.

    Supported formats:
      炸雞便當          → ("炸雞便當", 1)
      炸雞便當 x2       → ("炸雞便當", 2)
      炸雞便當x2        → ("炸雞便當", 2)
      炸雞便當 2        → ("炸雞便當", 2)
      炸雞便當 2份      → ("炸雞便當", 2)
      炸雞便當 2個      → ("炸雞便當", 2)
    """
    match = re.search(r"[xX×]?\s*(\d+)\s*(?:份|個|盒)?$", text)
    if match:
        quantity = max(1, int(match.group(1)))
        item_name = text[: match.start()].strip()
        item_name = re.sub(r"\s*[xX×]\s*$", "", item_name).strip()
    else:
        quantity = 1
        item_name = text

    return item_name, quantity
