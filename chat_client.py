import asyncio
import aiofiles
import datetime
# import configargparse
import logging
# from argparse import Namespace

from utils import get_asyncio_connection


logger = logging.getLogger('client')
logging.basicConfig(filename='logging.log', level=logging.DEBUG)


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
) -> None:
    async with get_asyncio_connection(
        host=host, port=port, status_queue=status_queue, client='read'
    ) as connection:
        reader, _ = connection
        save_queue.put_nowait('Connection is set\n')
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
            except KeyboardInterrupt:
                print('\nGoodbye!')
                logger.debug('Client was closed by KeyboardInterrupt')
                break


async def save_messages(history_file: str, save_queue: asyncio.Queue) -> None:
    async with aiofiles.open(history_file, mode='a') as log_file:
        while True:
            message = await save_queue.get()
            await log_file.write(f'{formatted_time()} {message}')


# def parse_arguments() -> Namespace:
#     parser = configargparse.ArgParser(
#         default_config_files=['config.txt'],
#         description='''Local chat client.
#         Print messages to stdout and save them to file'''
#     )
#     parser.add(
#         '-s',
#         '--host',
#         nargs='?',
#         help='host site to be connected to'
#     )
#     parser.add(
#         '-p',
#         '--port',
#         type=int,
#         nargs='?',
#         help='host port to be connected to'
#     )
#     parser.add(
#         '-y',
#         '--history',
#         nargs='?',
#         help='file to write chat history to'
#     )
#     args = parser.parse_known_args()

#     return args


# def main():
#     args = parse_arguments()[0]
#     host, port, history_file = args.host, args.port, args.history
#     asyncio.run(listen_tcp_chat(host, port, history_file))


# if __name__ == '__main__':
#     main()
