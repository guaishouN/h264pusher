import json
import logging
from asyncio import StreamReader, StreamWriter

from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, join_room, leave_room
from flask_cors import CORS, cross_origin
import asyncio
from threading import Thread
from find_sps_pps import find_sps_pps
h264_sps_nal = bytes()
h264_pps_nal = bytes()


async def stream_client(to_play_writer: StreamWriter):
    global h264_sps_nal, h264_pps_nal
    host = "127.0.0.1"
    port = 8888
    timeout = 20
    connect_count = 0
    while True:
        try:
            get_from_reader, get_from_writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
            break
        except (Exception, asyncio.TimeoutError):
            connect_count = connect_count + 1
            print(f"\rConnection to {host}:{port} timed out, count[{connect_count}]", end='', flush=True)
    print(f"connected to {host}:{port} success")
    try:
        total_size = 0
        while True:
            data = await get_from_reader.read(1024)
            total_size = total_size + len(data)
            print(f'\rstream_client Received size: {total_size!r}', end='', flush=True)
            if data and len(h264_sps_nal) == 0:
                h264_sps_nal, h264_pps_nal, _ = find_sps_pps(data)
                print(h264_sps_nal, h264_pps_nal)
            if len(data) > 0:
                to_play_writer.write(data)
                await to_play_writer.drain()
            else:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"stream_client {e}")
    finally:
        get_from_writer.close()
        await get_from_writer.wait_closed()


async def stream_dispatch_server():
    async def handle_stream(to_play_reader: StreamReader, to_play_writer: StreamWriter):
        await stream_client(to_play_writer)

    server = await asyncio.start_server(handle_stream, '127.0.0.1', 8989)
    server_addr = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {server_addr}')

    async with server:
        await server.serve_forever()
    print(f'finish Serving on {server_addr}')


def start_stream():
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stream_dispatch_server())
        pass

    worker = Thread(target=run, name=f"stream_server")
    worker.start()
    worker.join()


start_stream()
