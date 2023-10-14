import asyncio
import socket
from contextlib import asynccontextmanager
from typing import Tuple
from async_timeout import timeout

import logging
from gui import ReadConnectionStateChanged, SendingConnectionStateChanged


watchdog_logger = logging.getLogger('watchdog')
formatter = logging.Formatter('[%(created)d]: %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
watchdog_logger.addHandler(ch)


states = {
    'read': ReadConnectionStateChanged,
    'send': SendingConnectionStateChanged
}


async def watch_for_connection(
    watchdog_queue: asyncio.Queue,
    tm: int = 1
) -> None:
    while True:
        try:
            async with timeout(tm) as _:
                message = await watchdog_queue.get()
                watchdog_logger.debug(f'Connection is alive. {message}')
        except asyncio.TimeoutError:
            watchdog_logger.debug(f'{tm}s timeout is elapsed.')


def increase_delay() -> int:
    increasing_delays = [0.01, 0.1, 0.3, 0.7, 1.2, 2.5]
    max_delay = 5
    for delay in increasing_delays:
        yield delay
    while True:
        yield max_delay


@asynccontextmanager
async def get_asyncio_connection(
    host: str,
    port: str,
    status_queue: asyncio.Queue,
    client: str
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    try:
        status_queue.put_nowait(states[client].INITIATED)
        await asyncio.sleep(3)
        for delay in increase_delay():
            try:
                reader, writer = await asyncio.open_connection(
                    host=host, port=port
                )
                status_queue.put_nowait(states[client].ESTABLISHED)
                yield reader, writer
            except (
                socket.gaierror,
                ConnectionRefusedError,
                ConnectionResetError
            ):
                await asyncio.sleep(delay)
    finally:
        status_queue.put_nowait(states[client].CLOSED)
        writer.close()
        await writer.wait_closed()
