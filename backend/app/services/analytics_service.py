from __future__ import annotations


def calculate_strategy_performance(
    sent: int = 0,
    opened: int = 0,
    replied: int = 0,
) -> dict:
    open_rate = opened / sent if sent else 0
    reply_rate = replied / sent if sent else 0

    return {
        "sent": sent,
        "opened": opened,
        "replied": replied,
        "open_rate": round(open_rate, 4),
        "reply_rate": round(reply_rate, 4),
    }