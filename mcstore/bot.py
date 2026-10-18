import asyncio
import logging
from uuid import uuid4

import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from mcstore.config import get_settings

dispatcher = Dispatcher()


async def api_request(method: str, path: str, **kwargs):
    settings = get_settings()
    async with httpx.AsyncClient(base_url=settings.api_url, timeout=5) as client:
        response = await client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()


@dispatcher.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(
        "MC Store bot is online. Commands: /balance USER_ID, "
        "/transfer SOURCE_CARD TARGET_CARD AMOUNT"
    )


@dispatcher.message(Command("balance"))
async def balance(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /balance USER_ID")
        return
    try:
        cards = await api_request("GET", f"/users/{parts[1]}/cards")
    except httpx.HTTPError:
        await message.answer("Could not fetch cards from the API")
        return
    if not cards:
        await message.answer("This user has no cards")
        return
    await message.answer("\n".join(f"{card['name']}: {card['balance']}" for card in cards))


@dispatcher.message(Command("transfer"))
async def transfer_command(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) != 4 or not parts[3].isdigit():
        await message.answer("Usage: /transfer SOURCE_CARD TARGET_CARD AMOUNT")
        return
    payload = {
        "source_card_id": parts[1],
        "target_card_id": parts[2],
        "amount": int(parts[3]),
        "idempotency_key": uuid4().hex,
        "message": f"Telegram transfer by {message.from_user.id}",
    }
    try:
        transaction = await api_request("POST", "/transfers", json=payload)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("detail", "transfer rejected")
        await message.answer(detail)
        return
    except httpx.HTTPError:
        await message.answer("API is unavailable")
        return
    await message.answer(f"Transfer completed: {transaction['id']}")


async def main() -> None:
    settings = get_settings()
    if settings.bot_token is None:
        raise RuntimeError("MCSTORE_BOT_TOKEN is required")
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.bot_token.get_secret_value())
    await dispatcher.start_polling(bot)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
