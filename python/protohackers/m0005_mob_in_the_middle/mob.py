import asyncio
import re
from contextlib import closing
from typing import Tuple

StreamPair = Tuple[asyncio.StreamReader, asyncio.StreamWriter]

ADDRESS = "7YWHMfk9JZe0LM0g1ZauHuiSxhI"
pattern = re.compile(r"(?:(?<=\s)|(?<=^))(7[a-zA-Z0-9]{25,36})(?:(?=\s)|(?=$))")


async def replace(data: bytes) -> bytes:
    message = data.decode(encoding="ascii")
    matches = re.findall(pattern, message)
    for match in matches:
        message = message.replace(match, ADDRESS)
    return message.encode(encoding="ascii")


async def forward(stream: StreamPair, event: asyncio.Event, name: str):
    reader, writer = stream
    while not event.is_set():
        data = await reader.readline()
        print(f"{name} [read]: {data!r}")
        if data == b"":
            writer.close()
            event.set()
            break
        data = await replace(data)
        print(f"{name} [write]: {data!r}")
        writer.write(data)
        await writer.drain()


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


async def remote_handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    remote_reader, remote_writer = await asyncio.open_connection(
        "chat.protohackers.com", 16963
    )
    with closing(remote_writer):
        print("remote")
        await relay((reader, writer), (remote_reader, remote_writer))


async def local_handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    async def session():
        with closing(writer):
            print("new connection")
            await remote_handle(reader, writer)

    asyncio.create_task(session())


async def serve():
    server = await asyncio.start_server(local_handle, "0.0.0.0", 65535)  # nosec

    async with server:
        await server.serve_forever()


def run():
    print("Running mob in the middle")
    asyncio.run(serve(), debug=True)


if __name__ == "__main__":
    run()
