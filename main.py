import asyncio
import gui
import configargparse
from argparse import Namespace
from chat_client import listen_tcp_chat, save_messages
from chat_messanger import send_messages


messages_queue = asyncio.Queue()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
save_queue = asyncio.Queue()


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
    with open(history_file, 'r') as file:
        # load history to the GUI
        while line := file.readline():
            messages_queue.put_nowait(line.rstrip())
    await asyncio.gather(
        listen_tcp_chat(host, port, messages_queue, save_queue),
        save_messages(history_file, save_queue),
        send_messages('test', 5555, sending_queue, messages_queue),
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
    except Exception:
        pass
    finally:
        loop.close()
