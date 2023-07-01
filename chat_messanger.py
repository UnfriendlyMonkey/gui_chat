import asyncio
import json
# import configargparse
import logging
# import sys
# from os import environ
# from os.path import join, dirname
# from dotenv import load_dotenv
from asyncio import StreamReader, StreamWriter
# from argparse import Namespace

from utils import get_asyncio_connection

# from tkinter import messagebox


class InvalidToken(Exception):
    def __init__(self, title: str, message: str) -> None:
        self.title = title
        self.message = message
        super().__init__(title, message)


logger = logging.getLogger('messanger')
logging.basicConfig(
    filename='logging.log',
    level=logging.DEBUG,
    format='%(levelname)s:%(module)s:[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


async def authorise(
    reader: StreamReader,
    writer: StreamWriter,
    token: str,
    output_queue: asyncio.Queue
) -> None:
    hash_prompt = await reader.readline()
    if hash_prompt:
        ask_for_authorization = hash_prompt.decode()
        logger.debug(ask_for_authorization)
        # output_queue.put_nowait(ask_for_authorization)
    token = token[:-3]  # faking wrong token
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
    output_queue.put_nowait(f'Authorization complete. User {name}.')


# async def register(
#         reader: StreamReader,
#         writer: StreamWriter,
#         nickname: str
#         ) -> str:
#     if not nickname:
#         nickname = input('What nickname do you want to use?\t')
#     hash_prompt = await reader.readline()
#     if not hash_prompt:
#         message = 'Registration went wrong. Please try again'
#         print(message)
#         logger.debug(message)
#         sys.exit(1)
#     print(hash_prompt)
#     logger.debug(hash_prompt)
#     await submit_message(writer, '')
#     nickname_prompt = await reader.readline()
#     if not nickname_prompt:
#         message = 'Registration went wrong. Please try again'
#         print(message)
#         logger.debug(message)
#         sys.exit(1)
#     nickname_prompt = nickname_prompt.decode()
#     logger.debug(nickname_prompt)
#     print(nickname_prompt)
#     await submit_message(writer, nickname)
#     response = await reader.readline()
#     resp_data = json.loads(response)
#     logger.debug(resp_data)
#     new_token = resp_data.get('account_hash', None)
#     if new_token:
#         with open(join(dirname(__file__), '.env'), 'w') as envfile:
#             envfile.write(f'TOKEN={new_token}')
#     nickname = resp_data.get('nickname', None)
#     print(f'Your new nickname: {nickname} and token: {new_token}')
#     return new_token


async def submit_message(
    writer: StreamWriter,
    # input_queue: asyncio.Queue,
    message: str = None
) -> None:
    if not message:
        return
    message = message.replace("\\n", "")
    logger.debug(f'Sending: {message}')
    end_message = f'{message}\n\n'.encode()
    writer.write(end_message)
    await writer.drain()


# async def send_messages(
#     writer: StreamWriter, input_queue: asyncio.Queue, out_queue: asyncio.Queue
# ):
#     message = await input_queue.get()
#     out_queue.put_nowait(f'User send: {message}')
#     if message:
#         await submit_message(writer, message)


async def tcp_chat_messanger(
        # message: str,
        host: str,
        port: int,
        token: str,
        # name: str,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue
        ) -> None:
    logger.debug(f'The Messanger have started working on {host}, {port}')
    # if not token:
    #     token = environ.get('TOKEN')
    # if not token:
    #     async with get_asyncio_connection(host=host, port=port) as connection:
    #         reader, writer = connection
    #         token = await register(reader, writer, name)
    async with get_asyncio_connection(host=host, port=port) as connection:
        reader, writer = connection
        await authorise(reader, writer, token, output_queue)

        await reader.readline()
        # await submit_message(writer, message)
        while True:
            try:
                message = await input_queue.get()
                if message:
                    await submit_message(writer, message)
            except KeyboardInterrupt:
                print('\nGoodbye!')
                logger.debug('Program terminated by KeyboardInterrupt')
                break
