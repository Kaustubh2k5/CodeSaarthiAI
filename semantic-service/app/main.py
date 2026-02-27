import asyncio
from fastapi import FastAPI
from app.model.symbol import Symbol
from app.queue.queue import request_queue
from app.queue.worker import worker

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(worker())


@app.post("/describe")
async def describe(symbol: Symbol):

    loop = asyncio.get_event_loop()
    future = loop.create_future()

    await request_queue.put({
        "symbol": symbol,
        "future": future
    })

    result = await future
    return result