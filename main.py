import asyncio

from os import environ
from os.path import join, dirname
from dotenv import load_dotenv
import gui
import configargparse
from argparse import Namespace
from chat_client import listen_tcp_chat, save_messages
from chat_messanger import tcp_chat_messanger, InvalidToken
from utils import watch_for_connection

from tkinter import messagebox


messages_queue = asyncio.Queue()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
save_queue = asyncio.Queue()
watchdog_queue = asyncio.Queue()


def parse_arguments() -> Namespace:
    parser = configargparse.ArgParser(
        default_config_files=['config.txt'],
        description='''Local chat client.
        Print messages to stdout and save them to file'''
    )
    parser.add(
        '-s',
        '--host',
        nargs='?',
        help='host site to be connected to'
    )
    parser.add(
        '-p',
        '--port',
        type=int,
        nargs='?',
        help='host port to be connected to'
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
        '-y',
        '--history',
        nargs='?',
        help='file to write chat history to'
    )
    args = parser.parse_known_args()

    return args


async def main():
    args = parse_arguments()[0]
    host, port, history_file = args.host, args.port, args.history
    mport, token = args.mport, args.token
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    if not token:
        token = environ.get('TOKEN')
    with open(history_file, 'r') as file:
        # load history to the GUI
        while line := file.readline():
            messages_queue.put_nowait(line.rstrip())
    await asyncio.gather(
        listen_tcp_chat(
            host,
            port,
            messages_queue,
            save_queue,
            status_updates_queue,
            watchdog_queue
        ),
        tcp_chat_messanger(
            host,
            mport,
            token,
            sending_queue,
            messages_queue,
            status_updates_queue,
            watchdog_queue
        ),
        save_messages(history_file, save_queue),
        watch_for_connection(watchdog_queue),
        gui.draw(
            messages_queue,
            sending_queue,
            status_updates_queue
        ),
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except InvalidToken as err:
        messagebox.showinfo(err.title, err.message)
    except Exception:
        pass
    finally:
        loop.close()
