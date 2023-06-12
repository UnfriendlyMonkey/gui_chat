import asyncio
import socket
from contextlib import asynccontextmanager
from typing import Tuple


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
    port: str
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    try:
        for delay in increase_delay():
            try:
                reader, writer = await asyncio.open_connection(
                    host=host, port=port
                )
                yield reader, writer
            except (
                socket.gaierror,
                ConnectionRefusedError,
                ConnectionResetError
            ):
                await asyncio.sleep(delay)
    finally:
        writer.close()
        await writer.wait_closed()
