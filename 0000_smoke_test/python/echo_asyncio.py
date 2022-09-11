import asyncio


async def handle(r: asyncio.StreamReader, w: asyncio.StreamWriter):
    data = await r.read()
    w.write(data)
    await w.drain()
    w.close()


async def main():
    HOST, PORT = "0.0.0.0", 10007

    server = await asyncio.start_server(handle, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
