from datetime import datetime
from typing import List

from bot.models import AggregationResult, MenuItem


def format_menu_message(restaurant: str, menu: List[MenuItem], deadline: datetime) -> str:
    deadline_str = deadline.strftime("%H:%M")
    lines = [
        f"🍱 *{restaurant} 訂餐開始！*",
        "",
        "*菜單：*",
    ]
    for item in menu:
        lines.append(f"• {item.name} — ${item.price:.0f}")
    lines += [
        "",
        f"⏰ 截止時間：*{deadline_str}*",
        "",
        "請在此訊息的 *thread* 中回覆品項名稱（例如：`炸雞便當` 或 `炸雞便當 x2`）",
    ]
    return "\n".join(lines)


def format_aggregation_message(result: AggregationResult) -> str:
    if not result.items:
        return f"📊 *{result.restaurant}* 訂單彙整\n\n本次沒有收到任何訂單。"

    lines = [
        f"📊 *{result.restaurant}* 訂單彙整",
        "",
        "*品項* | *數量* | *小計*",
        "─" * 28,
    ]
    for item in result.items:
        lines.append(f"• {item['name']} | {item['quantity']} 份 | ${item['subtotal']:.0f}")
    lines += [
        "─" * 28,
        f"*總計：${result.grand_total:.0f}*（共 {result.order_count} 筆訂單）",
    ]
    return "\n".join(lines)
