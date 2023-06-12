import asyncio
import json
import configargparse
import logging
import sys
from os import environ
from os.path import join, dirname
from dotenv import load_dotenv
from asyncio import StreamReader, StreamWriter
from argparse import Namespace

from utils import get_asyncio_connection


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
        token: str
        ) -> None:
    hash_prompt = await reader.readline()
    if hash_prompt:
        ask_for_authorization = hash_prompt.decode()
        logger.debug(ask_for_authorization)
        print(ask_for_authorization, end='')
    await submit_message(writer, token)

    greeting = await reader.readline()
    if not greeting:
        message = 'Unknown token. Please check it or sign up again'
        print(message)
        logger.debug(message)
        sys.exit(1)

    greeting = json.loads(greeting)

    logger.debug(greeting)
    print(greeting)


async def register(
        reader: StreamReader,
        writer: StreamWriter,
        nickname: str
        ) -> str:
    if not nickname:
        nickname = input('What nickname do you want to use?\t')
    hash_prompt = await reader.readline()
    if not hash_prompt:
        message = 'Registration went wrong. Please try again'
        print(message)
        logger.debug(message)
        sys.exit(1)
    print(hash_prompt)
    logger.debug(hash_prompt)
    await submit_message(writer, '')
    nickname_prompt = await reader.readline()
    if not nickname_prompt:
        message = 'Registration went wrong. Please try again'
        print(message)
        logger.debug(message)
        sys.exit(1)
    nickname_prompt = nickname_prompt.decode()
    logger.debug(nickname_prompt)
    print(nickname_prompt)
    await submit_message(writer, nickname)
    response = await reader.readline()
    resp_data = json.loads(response)
    logger.debug(resp_data)
    new_token = resp_data.get('account_hash', None)
    if new_token:
        with open(join(dirname(__file__), '.env'), 'w') as envfile:
            envfile.write(f'TOKEN={new_token}')
    nickname = resp_data.get('nickname', None)
    print(f'Your new nickname: {nickname} and token: {new_token}')
    return new_token


async def submit_message(writer: StreamWriter, message: str = None) -> None:
    if message is None:
        message = input('>> ')
    message = message.replace("\\n", "")
    logger.debug(message)
    end_message = f'{message}\n\n'.encode()
    writer.write(end_message)
    await writer.drain()


async def tcp_chat_messanger(
        message: str,
        host: str,
        port: int,
        token: str,
        name: str
        ) -> None:
    logger.debug(f'The Messanger have started working on {host}, {port}')
    if not token:
        token = environ.get('TOKEN')
    if not token:
        async with get_asyncio_connection(host=host, port=port) as connection:
            reader, writer = connection
            token = await register(reader, writer, name)
    async with get_asyncio_connection(host=host, port=port) as connection:
        reader, writer = connection
        await authorise(reader, writer, token)

        await reader.readline()
        await submit_message(writer, message)
        while True:
            try:
                await submit_message(writer)
            except KeyboardInterrupt:
                print('\nGoodbye!')
                logger.debug('Program terminated by KeyboardInterrupt')
                break


def parse_arguments() -> Namespace:
    parser = configargparse.ArgParser(
        default_config_files=['config.txt'],
        description='''Local chat messanger. After beeing authorized
        you could input you messages for them to appear in local chat'''
    )
    parser.add(
        '-m',
        '--message',
        required=True,
        help='message to send'
    )
    parser.add(
        '-s',
        '--host',
        nargs='?',
        help='host site to be connected to'
    )
    parser.add(
        '-o',
        '--mport',
        type=int,
        nargs='?',
        help='host port to connect to send messages'
    )
    parser.add(
        '-t',
        '--token',
        nargs='?',
        help='enter your token to connect to chat'
    )
    parser.add(
        '-n',
        '--name',
        nargs='?',
        help='enter your preferred name'
    )
    args = parser.parse_known_args()

    return args


def main():
    args = parse_arguments()[0]
    message = args.message
    host, port = args.host, args.mport
    token, name = args.token, args.name
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    asyncio.run(tcp_chat_messanger(message, host, port, token, name))


if __name__ == '__main__':
    main()
