import asyncio
import gui
from time import time

loop = asyncio.get_event_loop()

messages_queue = asyncio.Queue()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()


async def generate_msgs(queue):
    while True:
        timestamp = int(time())
        message = f'Ping {timestamp}'
        queue.put_nowait(message)
        await asyncio.sleep(1)


async def main():
    tasks = await asyncio.gather(
        generate_msgs(messages_queue),
        gui.draw(
            messages_queue,
            sending_queue,
            status_updates_queue
        ),
    )


loop.run_until_complete(main())
