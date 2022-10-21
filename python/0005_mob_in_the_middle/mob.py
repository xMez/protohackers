import asyncio
import re
from contextlib import closing
from typing import Tuple

StreamPair = Tuple[asyncio.StreamReader, asyncio.StreamWriter]

address = "7YWHMfk9JZe0LM0g1ZauHuiSxhI"
pattern = re.compile(r"(?:(?<=\s)|(?<=^))(7[a-zA-Z0-9]{25,36})(?:(?=\s)|(?=$))")


async def replace(data: bytes) -> bytes:
    message = data.decode(encoding="ascii")
    matches = re.findall(pattern, message)
    for match in matches:
        message = message.replace(match, address)
    return message.encode(encoding="ascii")


async def forward(stream: StreamPair, event: asyncio.Event, name: str):
    r, w = stream
    while not event.is_set():
        data = await r.readline()
        print(f"{name} [read]: {data}")
        if data == b"":
            w.close()
            event.set()
            break
        data = await replace(data)
        print(f"{name} [write]: {data}")
        w.write(data)
        await w.drain()


async def relay(local: StreamPair, remote: StreamPair):
    local_reader, local_writer = local
    remote_reader, remote_writer = remote

    close_event = asyncio.Event()
    print("relay")
    print(close_event.is_set())
    await asyncio.gather(
        forward((local_reader, remote_writer), close_event, "local"),
        forward((remote_reader, local_writer), close_event, "remote"),
    )


async def remote_handle(r: asyncio.StreamReader, w: asyncio.StreamWriter):
    remote_r, remote_w = await asyncio.open_connection("chat.protohackers.com", 16963)
    with closing(remote_w):
        print("remote")
        await relay((r, w), (remote_r, remote_w))


async def local_handle(r: asyncio.StreamReader, w: asyncio.StreamWriter):
    async def session():
        with closing(w):
            print("new connection")
            # data = await r.readline()
            # message = data.decode(encoding="utf-8")
            await remote_handle(r, w)
    asyncio.create_task(session())


async def main():
    server = await asyncio.start_server(local_handle, "0.0.0.0", 65535)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
