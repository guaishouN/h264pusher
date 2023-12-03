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


async def handle_stream(reader: StreamReader, writer: StreamWriter):
    global h264_sps_nal, h264_pps_nal
    print("new handle_stream")
    try:
        data = bytes()
        total_size = 0
        while True:
            if len(data) > 0:
                socketio.emit("video_nal", data)
            data = await reader.read(1024)
            total_size = total_size + len(data)
            print("\rread data total_size[", total_size, "]", end='', flush=True)
            if not data:
                break
            if len(h264_sps_nal) == 0:
                h264_sps_nal, h264_pps_nal, _ = find_sps_pps(data)
                print(h264_sps_nal, h264_pps_nal)

    except Exception as e:
        print(f"\nError in handle_stream: {e}")


async def stream_server():
    server = await asyncio.start_server(handle_stream, '127.0.0.1', 8888)
    server_addr = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {server_addr}')

    async with server:
        await server.serve_forever()


def start_stream_server():
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stream_server())
        pass

    worker = Thread(target=run, name=f"stream_server")
    worker.start()


start_stream_server()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
