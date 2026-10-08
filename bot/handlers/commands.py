import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from slack_bolt import App

from bot.formatting import format_aggregation_message, format_menu_message
from bot.models import MenuItem
from bot.services.restaurant_service import RestaurantService
from bot.services.session_service import SessionService

logger = logging.getLogger(__name__)


def register_commands(
    app: App,
    session_service: SessionService,
    restaurant_service: RestaurantService,
) -> None:

    @app.command("/lunch-start")
    def handle_start(ack, body, client, command):
        ack()
        user_id = body["user_id"]
        channel_id = body["channel_id"]

        if session_service.get_active():
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="⚠️ 目前已有進行中的訂餐活動，請等候完成後再開始新的活動。",
            )
            return

        text = command.get("text", "").strip()
        parts = [p.strip() for p in text.split("|")]

        if len(parts) == 3:
            restaurant = parts[0]
            menu = _parse_menu(parts[1])
            deadline = _parse_deadline(parts[2])
            if not menu:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="❌ 菜單格式錯誤。格式：餐廳名稱 | 品項1:價格1, 品項2:價格2 | 12:30",
                )
                return
            if deadline is None:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="❌ 截止時間格式錯誤。請使用 HH:MM（例如 12:30）或相對時間（例如 30m、1h）。",
                )
                return
            _start_session(client, channel_id, user_id, restaurant, menu, deadline, session_service)
        else:
            client.views_open(
                trigger_id=body["trigger_id"],
                view=_build_start_modal(channel_id),
            )

    @app.view("lunch_start_modal")
    def handle_start_modal_submit(ack, body, client, view):
        ack()
        user_id = body["user"]["id"]
        channel_id = view["private_metadata"]
        values = view["state"]["values"]

        if session_service.get_active():
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="⚠️ 目前已有進行中的訂餐活動，請等候完成後再開始新的活動。",
            )
            return

        restaurant = values["restaurant_block"]["restaurant_input"]["value"]
        menu_text = values["menu_block"]["menu_input"]["value"]
        deadline_text = values["deadline_block"]["deadline_input"]["value"]

        menu = _parse_menu(menu_text)
        if not menu:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="❌ 菜單格式錯誤。格式：品項1:價格1, 品項2:價格2",
            )
            return

        deadline = _parse_deadline(deadline_text)
        if deadline is None:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="❌ 截止時間格式錯誤。請使用 HH:MM（例如 12:30）或相對時間（例如 30m、1h）。",
            )
            return

        _start_session(client, channel_id, user_id, restaurant, menu, deadline, session_service)

    @app.command("/lunch-close")
    def handle_close(ack, body, client, command):
        ack()
        user_id = body["user_id"]
        channel_id = body["channel_id"]

        session = session_service.get_active()
        if not session:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="⚠️ 目前沒有進行中的訂餐活動。",
            )
            return

        result = session_service.aggregate(session)
        session_service.complete(session)
        client.chat_postMessage(
            channel=session.channel_id,
            thread_ts=session.thread_ts,
            text=format_aggregation_message(result),
        )

    @app.command("/lunch-restaurants")
    def handle_list_restaurants(ack, body, client, command):
        ack()
        user_id = body["user_id"]
        channel_id = body["channel_id"]

        restaurants = restaurant_service.list_all()
        if not restaurants:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="📋 目前沒有儲存的餐廳。開始一輪訂餐後，使用 `/lunch-save` 儲存。",
            )
            return

        lines = ["📋 *已儲存的餐廳*\n"]
        for r in restaurants:
            items_str = "、".join(f"{item.name} ${item.price:.0f}" for item in r.menu)
            lines.append(f"*{r.name}*：{items_str}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="\n".join(lines),
        )

    @app.command("/lunch-save")
    def handle_save(ack, body, client, command):
        ack()
        user_id = body["user_id"]
        channel_id = body["channel_id"]

        session = session_service.get_active()
        if not session:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="⚠️ 目前沒有進行中的訂餐活動，無法儲存餐廳。",
            )
            return

        restaurant_service.save(session.restaurant, session.menu)
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"✅ 已儲存餐廳 *{session.restaurant}* 及其菜單，下次可用 `/lunch-load {session.restaurant}` 快速載入。",
        )

    @app.command("/lunch-load")
    def handle_load(ack, body, client, command):
        ack()
        user_id = body["user_id"]
        channel_id = body["channel_id"]
        name = command.get("text", "").strip()

        if session_service.get_active():
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="⚠️ 目前已有進行中的訂餐活動，請等候完成後再開始新的活動。",
            )
            return

        if not name:
            restaurants = restaurant_service.list_all()
            if not restaurants:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="📋 目前沒有儲存的餐廳。使用 `/lunch-restaurants` 查看。",
                )
                return
            names_list = "\n".join(f"• {r.name}" for r in restaurants)
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"請指定餐廳名稱：`/lunch-load 餐廳名稱`\n\n已儲存的餐廳：\n{names_list}",
            )
            return

        restaurant = restaurant_service.get(name)
        if not restaurant:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"❌ 找不到餐廳 *{name}*。使用 `/lunch-restaurants` 查看已儲存餐廳。",
            )
            return

        menu_text = ", ".join(f"{item.name}:{item.price:.0f}" for item in restaurant.menu)
        client.views_open(
            trigger_id=body["trigger_id"],
            view=_build_start_modal(channel_id, restaurant_name=restaurant.name, menu_text=menu_text),
        )


def _start_session(
    client,
    channel_id: str,
    user_id: str,
    restaurant: str,
    menu: List[MenuItem],
    deadline: datetime,
    session_service: SessionService,
) -> None:
    response = client.chat_postMessage(
        channel=channel_id,
        text=format_menu_message(restaurant, menu, deadline),
    )
    thread_ts = response["ts"]

    def on_deadline():
        try:
            session = session_service.get_active()
            if session and session.thread_ts == thread_ts:
                result = session_service.aggregate(session)
                session_service.complete(session)
                client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=format_aggregation_message(result),
                )
        except Exception:
            logger.exception("Error in deadline callback for thread %s", thread_ts)

    session_service.create(
        channel_id=channel_id,
        thread_ts=thread_ts,
        restaurant=restaurant,
        menu=menu,
        deadline=deadline,
        on_deadline=on_deadline,
    )


def _parse_menu(text: str) -> List[MenuItem]:
    items = []
    for part in text.split(","):
        part = part.strip()
        if ":" not in part:
            return []
        name, _, price_str = part.rpartition(":")
        name = name.strip()
        price_str = price_str.strip()
        try:
            price = float(price_str)
            if not name:
                return []
            items.append(MenuItem(name=name, price=price))
        except ValueError:
            return []
    return items


def _parse_deadline(text: str) -> Optional[datetime]:
    text = text.strip()
    if not text:
        return None
    try:
        now = datetime.now(timezone.utc)
        # Relative offset: 30m or 1h
        match = re.fullmatch(r"(\d+)(m|h)", text.lower())
        if match:
            value, unit = int(match.group(1)), match.group(2)
            delta = timedelta(minutes=value) if unit == "m" else timedelta(hours=value)
            return now + delta
        # Absolute HH:MM (treated as UTC)
        hhmm = datetime.strptime(text, "%H:%M")
        deadline = now.replace(hour=hhmm.hour, minute=hhmm.minute, second=0, microsecond=0)
        if deadline <= now:
            deadline += timedelta(days=1)
        return deadline
    except ValueError:
        return None


def _build_start_modal(
    channel_id: str,
    restaurant_name: str = "",
    menu_text: str = "",
) -> dict:
    return {
        "type": "modal",
        "callback_id": "lunch_start_modal",
        "private_metadata": channel_id,
        "title": {"type": "plain_text", "text": "開始訂餐"},
        "submit": {"type": "plain_text", "text": "開始"},
        "close": {"type": "plain_text", "text": "取消"},
        "blocks": [
            {
                "type": "input",
                "block_id": "restaurant_block",
                "label": {"type": "plain_text", "text": "餐廳名稱"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "restaurant_input",
                    "initial_value": restaurant_name,
                    "placeholder": {"type": "plain_text", "text": "例如：師大便當"},
                },
            },
            {
                "type": "input",
                "block_id": "menu_block",
                "label": {"type": "plain_text", "text": "菜單（品項:價格，逗號分隔）"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "menu_input",
                    "initial_value": menu_text,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "炸雞便當:80, 排骨便當:85, 素食便當:75",
                    },
                    "multiline": False,
                },
            },
            {
                "type": "input",
                "block_id": "deadline_block",
                "label": {"type": "plain_text", "text": "截止時間（HH:MM 或 30m / 1h）"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "deadline_input",
                    "placeholder": {"type": "plain_text", "text": "例如：12:30 或 30m"},
                },
            },
        ],
    }
