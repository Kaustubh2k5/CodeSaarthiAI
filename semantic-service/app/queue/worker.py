from app.queue.queue import request_queue
from app.services.describer import describe_symbol

async def worker():

    print("Worker started")

    while True:
        job = await request_queue.get()

        symbol = job["symbol"]
        future = job["future"]

        try:
            result = await describe_symbol(symbol)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

        request_queue.task_done()