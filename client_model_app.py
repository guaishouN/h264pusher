import json
import logging
from asyncio import StreamReader, StreamWriter

from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, join_room, leave_room
from flask_cors import CORS, cross_origin
import asyncio
from threading import Thread

from find_sps_pps import find_sps_pps

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
cors = CORS(app)
room_device_dict = dict()
logging.basicConfig(format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
                    level=logging.INFO)
h264_sps_nal = bytes()
h264_pps_nal = bytes()


@app.route('/')
def index():  # put application's code here
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    sid = request.sid
    if len(h264_sps_nal) > 0:
        [socketio.emit("video_nal", key_nal) for key_nal in [h264_sps_nal, h264_pps_nal]]
    print(f'Client connected {sid}')


@socketio.on('message')
def handle_stream_in(message):
    print(f'handle_stream_in len {len(message)}')


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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
