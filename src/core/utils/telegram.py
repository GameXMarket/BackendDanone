import json

import httpx

from core.logging.helpers import create_logger


tg_logger = create_logger("telegram")


async def send_telegram_message(bot_token, chat_id, text, parse_mode="MarkdownV2", need_log: bool = False):
    target_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    headers = {"Content-Type": "application/json"}
    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Нажми меня",
                    "url": "https://example.com"
                }
            ]
        ]
    }

    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
        "disable_notification": False,
        "reply_markup": json.dumps(inline_keyboard),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(target_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200 and need_log:
            tg_logger.info(f"Telegram message sendet to {chat_id}")
        else:
            tg_logger.error(
                f"Telegram message not sendet?\n status: {response.status_code}\n response_text: {response.text}"
            )
