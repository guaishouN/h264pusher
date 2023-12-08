import logging
import struct
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

"""
adb push scrcpy-server /data/local/tmp/scrcpy-server-manual.jar
adb forward tcp:10037 localabstract:scrcpy
adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / com.genymobile.scrcpy.Server 2.1.1 tunnel_forward=true audio=false control=false video_codec=h264 cleanup=false send_device_meta=false send_frame_meta=true send_dummy_byte=false send_codec_meta=false max_size=720 video_codec_options=profile=1,level=2 power_on=true
"""


@app.route('/')
def index():
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
    port = 10038
    timeout = 10
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
            frame_meta = await reader.readexactly(12)
            print(f'frame_meta={frame_meta.hex()}')
            if len(frame_meta) == 12:
                data_len = struct.unpack('>L', frame_meta[8:])[0]
            else:
                continue

            data = await reader.readexactly(data_len)
            total_size = total_size + len(data)
            print(f'\rstream_client data_len=[{data_len}], Received size: {total_size!r}', end='', flush=True)

            if data and len(h264_sps_nal) == 0:
                h264_sps_nal, h264_pps_nal, _ = find_sps_pps(data)
                print(h264_sps_nal, h264_pps_nal)
                socketio.emit("video_nal", h264_sps_nal)
                socketio.emit("video_nal", h264_pps_nal)
                continue

            if len(data) > 0:
                socketio.emit("video_nal", data)
            else:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"stream_client error!!!!!!!!!!!!!!! {e}")
    finally:
        writer.close()
        reader.close()
        await writer.wait_closed()
        await reader.wait_closed()
        await stream_client()


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
