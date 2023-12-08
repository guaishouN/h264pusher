import logging
import asyncio
from asyncio import StreamWriter, StreamReader
from threading import Thread
from bitstring import BitStream

from find_sps_pps import find_sps_pps

logging.basicConfig(format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
                    level=logging.INFO)

writer_set: set[StreamWriter] = set()
sps_nal = bytes()
pps_nal = bytes()


async def handle_stream(reader: StreamReader, writer: StreamWriter):
    global sps_nal, pps_nal
    print("new handle_stream")
    writer_set.add(writer)
    try:
        data = bytes()
        [writer.write(key_nal) for key_nal in [sps_nal, pps_nal]]
        total_size = 0
        while True:
            for writer in writer_set:
                if len(data) > 0:
                    writer.write(data)
            data = await reader.read(1024)
            total_size = total_size + len(data)
            print("\rread data total_size[", total_size, "]", end='', flush=True)
            if not data:
                break
            if len(sps_nal) == 0:
                sps_nal, pps_nal, _ = find_sps_pps(data)
                print(sps_nal, pps_nal)

    except Exception as e:
        print(f"\nError in handle_stream: {e}")
    finally:
        writer_set.remove(writer)
        writer.close()


async def stream_dispatch_server():
    server = await asyncio.start_server(handle_stream, '127.0.0.1', 8989)
    server_addr = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'123 Serving on {server_addr}')

    async with server:
        await server.serve_forever()
    print(f'finish Serving on {server_addr}')


def start_stream_server():
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(stream_dispatch_server())
        pass

    worker = Thread(target=run, name=f"stream_server")
    worker.start()


start_stream_server()
