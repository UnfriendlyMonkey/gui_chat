import asyncio
import aiofiles
import datetime
import logging

from utils import get_asyncio_connection


logger = logging.getLogger('client')


def formatted_time() -> str:
    now = datetime.datetime.now()
    formatted_datetime = now.strftime('[%d.%m.%y %H:%M]')
    return formatted_datetime


async def listen_tcp_chat(
    host: str,
    port: int,
    messages_queue: asyncio.Queue,
    save_queue: asyncio.Queue,
    status_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue,
) -> None:
    async with get_asyncio_connection(
        host=host, port=port, status_queue=status_queue, client='read'
    ) as connection:
        reader, _ = connection
        watchdog_queue.put_nowait('Read connection is set')
        logger.debug(
            f'Client is on at {formatted_time()} on {host}, {port}'
        )
        while True:
            try:
                data = await reader.readline()
                message = data.decode()
                if message:
                    messages_queue.put_nowait(message.rstrip())
                    save_queue.put_nowait(message)
                    watchdog_queue.put_nowait('New message in chat')
            except KeyboardInterrupt:
                print('\nGoodbye!')
                logger.debug('Client was closed by KeyboardInterrupt')
                break


async def save_messages(history_file: str, save_queue: asyncio.Queue) -> None:
    async with aiofiles.open(history_file, mode='a') as log_file:
        while True:
            message = await save_queue.get()
            await log_file.write(f'{formatted_time()} {message}')
