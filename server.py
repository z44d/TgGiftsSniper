import uvicorn
import os

from fastapi import FastAPI
from pyrogram import Client
from contextlib import asynccontextmanager

from dotenv import load_dotenv

client: Client = None
done = {}

load_dotenv()

BUYER = os.environ.get("BUYER")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = Client(
        "name",
        session_string=BUYER,
    )
    await client.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/hint")
async def hint(link: str, username: str):
    if link in done:
        return {"already": True, "payload": done[link]}
    done[link] = {}
    payload = {}
    try:
        await client.send_resold_gift(link, username)
        status = True
    except Exception as e:
        payload["error"] = f"<code>{e.__class__.__name__}:  {e}</code>"
        status = False
    payload["status"] = status
    done[link] = payload

    return payload


@app.get("/")
async def index():
    return {
        "me": (await client.get_me()).username,
    }


uvicorn.run(app, host="0.0.0.0", port=8000)
