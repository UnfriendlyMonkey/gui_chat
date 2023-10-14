import asyncio
import json
import logging
from asyncio import StreamReader, StreamWriter

from utils import get_asyncio_connection
from gui import NicknameReceived


class InvalidToken(Exception):
    def __init__(self, title: str, message: str) -> None:
        self.title = title
        self.message = message
        super().__init__(title, message)


logger = logging.getLogger('messanger')
logging.basicConfig(
    filename='logging.log',
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


async def authorise(
    reader: StreamReader,
    writer: StreamWriter,
    token: str,
    output_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue
) -> None:
    hash_prompt = await reader.readline()
    if hash_prompt:
        watchdog_queue.put_nowait('Prompt before auth')
        ask_for_authorization = hash_prompt.decode()
        logger.debug(ask_for_authorization)
        # output_queue.put_nowait(ask_for_authorization)
    # token = token[:-3]  # faking wrong token
    await submit_message(writer, token)

    greeting = await reader.readline()
    greeting = json.loads(greeting)
    logger.debug(f'Greeting: {greeting}')

    if not greeting:
        title, message = 'Unknown token', 'Check it or sign up again'
        output_queue.put_nowait(title)
        logger.debug(f'{title}. {message}')
        raise InvalidToken(title, message)

    name = greeting.get('nickname', 'WRONG!!!!!')
    watchdog_queue.put_nowait('Authorization done')
    return name


async def submit_message(
    writer: StreamWriter,
    message: str = None
) -> None:
    if not message:
        return
    message = message.replace("\\n", "")
    logger.debug(f'Sending: {message}')
    end_message = f'{message}\n\n'.encode()
    writer.write(end_message)
    await writer.drain()


async def tcp_chat_messanger(
        host: str,
        port: int,
        token: str,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
        status_queue: asyncio.Queue,
        watchdog_queue: asyncio.Queue
        ) -> None:
    logger.debug(f'The Messanger have started working on {host}, {port}')
    async with get_asyncio_connection(
        host=host, port=port, status_queue=status_queue, client='send'
    ) as connection:
        reader, writer = connection
        watchdog_queue.put_nowait('Messanger got connection')
        name = await authorise(
            reader, writer, token, output_queue, watchdog_queue)
        status_queue.put_nowait(NicknameReceived(name))

        await reader.readline()
        while True:
            try:
                message = await input_queue.get()
                if message:
                    await submit_message(writer, message)
                    watchdog_queue.put_nowait('Message send')
            except KeyboardInterrupt:
                print('\nGoodbye!')
                logger.debug('Program terminated by KeyboardInterrupt')
                break
