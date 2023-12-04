import json
import logging
from asyncio import StreamReader, StreamWriter

from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, join_room, leave_room
from flask_cors import CORS, cross_origin
import asyncio
from threading import Thread

from find_sps_pps import find_sps_pps

async def stream_client():
    global h264_sps_nal, h264_pps_nal
    host = "127.0.0.1"
    port = 8888
    timeout = 20
    connect_count = 0
    while True:
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
            break
        except (Exception, asyncio.TimeoutError):
            connect_count = connect_count + 1
            print(f"\rConnection to {host}:{port} timed out, count[{connect_count}]", end='', flush=True)
    print(f"connected to {host}:{port} success")
    try:
        total_size = 0
        while True:
            data = await reader.read(1024)
            total_size = total_size + len(data)
            print(f'\rstream_client Received size: {total_size!r}', end='', flush=True)
            if data and len(h264_sps_nal) == 0:
                h264_sps_nal, h264_pps_nal, _ = find_sps_pps(data)
                print(h264_sps_nal, h264_pps_nal)
            if len(data) > 0:
                socketio.emit("video_nal", data)
            else:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"stream_client {e}")
    finally:
        writer.close()
        await writer.wait_closed()


def start_stream_client():
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stream_client())
        pass

    worker = Thread(target=run, name=f"stream_client")
    worker.start()


start_stream_client()
