import asyncio
import logging
import uvloop
import os
import requests
import json
import random

from pyrogram import Client, enums
from pyrogram.errors import FloodWait


from pathlib import Path
from typing import List, Dict
from requests.exceptions import ReadTimeout

from itertools import cycle
from dotenv import load_dotenv


SESSIONS_PATH = Path(os.environ.get("SESSIONS_PATH"))

load_dotenv()

TOKEN = os.environ.get("TOKEN")
BUY_TO = os.environ.get("BUY_TO")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
EXCLUDE = os.environ.get("EXCLUDE", "")
DROP_PERCENT = int(os.environ.get("DROP_PERCENT", "40"))
percent = (100 - DROP_PERCENT) / 100

if EXCLUDE:
    EXCLUDE_LIST = [i.strip() for i in EXCLUDE]
else:
    EXCLUDE_LIST = []

PROCESS = 0

clients: List[Client] = []
gifts: Dict[int, int] = {}
checked: List[str] = []

logging.getLogger("pyrogram").setLevel(logging.ERROR)

with open(SESSIONS_PATH, "r", encoding="utf-8") as f:
    sessions = f.readlines()


def notifaction(text: str):
    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML",
                "link_preview_options": json.dumps({"is_disabled": True}),
            },
            timeout=2,
        )
    except ReadTimeout:
        pass


async def start_client(session_string: str):
    client = Client(
        "name",
        session_string=session_string.strip(),
        no_updates=True,
    )
    try:
        await asyncio.sleep(random.randint(1, 5) / 10)
        await client.connect()
        client.me = await client.get_me()
        clients.append(client)
    except Exception as e:
        print(f"Error while connecting with session: {e.__class__.__name__}: {e}")


async def check(gift_id: int, client: Client):
    global PROCESS
    try:
        async for gift in client.search_gifts_for_resale(
            gift_id=gift_id, order=enums.GiftForResaleOrder.PRICE, limit=1
        ):
            PROCESS += 1
            if gift_id not in gifts or gifts[gift_id] is None:
                gifts.update({gift_id: gift.last_resale_price})
            elif gift.last_resale_price <= gifts[gift_id] * percent:
                old_price = gifts[gift_id]
                drop_percent = round(
                    ((gifts[gift_id] - gift.last_resale_price) / gifts[gift_id]) * 100,
                    2,
                )
                respose: dict = requests.get(
                    "http://127.0.0.1:8000/hint",
                    params={"link": gift.link, "username": BUY_TO},
                ).json()
                if respose.get("already"):
                    continue
                elif respose["status"] is True:
                    status = f"✅ Gift has been purchased and sent to @{BUY_TO}."
                else:
                    status = f"❗ Error while buying gift <code>{gift_id}</code>:\n{respose['error']}"

                notifaction(
                    (
                        f"🎁 Gift ({gift.title}) price dropped by {drop_percent}%!\n"
                        f"💰 Previous price: {old_price}\n"
                        f"💸 Current price: {gift.last_resale_price}\n\n{gift.link}\n\n"
                        f"👤 OWNER: {f'@{gift.owner.username}' if gift.owner.username else 'No Username'} | {gift.owner.full_name}\n"
                        f"{status}"
                    )
                )
    except (FloodWait, TypeError, TimeoutError):
        pass
    except Exception as e:
        notifaction(
            f"❗ Error while checking gift <code>{gift_id}</code> with account: <strong>+{client.me.phone_number}</strong>\n\n<code>{e.__class__.__name__}: {e}</code>",
        )


async def check_gifts(
    client: Client,
    semaphore: asyncio.Semaphore,
    ids: List[int],
):
    async with semaphore:
        await asyncio.gather(*[check(i, client) for i in ids], return_exceptions=True)


def distribute_gifts(gift_ids: List[int]) -> List[List[int]]:
    n_sessions = len(clients)
    n_gifts = len(gift_ids)

    if n_gifts >= n_sessions:
        return [gift_ids[i::n_sessions] for i in range(n_sessions)]

    result = [[] for _ in range(n_sessions)]
    gift_cycle = cycle(gift_ids)

    for i in range(n_sessions):
        result[i].append(next(gift_cycle))

    return result


async def main():
    global PROCESS

    await asyncio.gather(*[start_client(s) for s in sessions])

    notifaction(
        f"✅ <strong>{len(clients)}</strong> accounts started out of <strong>{len(sessions)}</strong> total accounts.",
    )

    ids = [
        gift.id
        for gift in await clients[0].get_available_gifts()
        if gift.available_resale_amount and gift.title not in EXCLUDE_LIST
    ]

    notifaction(
        f"🎁 <strong>{len(ids)}</strong> upgradable gifts detected, starting to check all of them now...",
    )

    for i in ids:
        gifts.update({i: None})

    chunks = distribute_gifts(ids)
    count = min(50, len(clients) * 3)
    while True:
        semaphore = asyncio.Semaphore(count)

        await asyncio.gather(
            *[
                check_gifts(client, semaphore, chunk)
                for client, chunk in zip(clients, chunks)
            ]
        )

        print(
            f"✅ Checked {PROCESS} times in this round | 🎯 {len(checked)} tried to claim"
        )
        PROCESS = 0


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())
