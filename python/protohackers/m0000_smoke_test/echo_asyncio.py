import asyncio


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    data = await reader.read()
    writer.write(data)
    await writer.drain()
    writer.close()


async def serve():
    server = await asyncio.start_server(handle, "0.0.0.0", 10007)  # nosec
    async with server:
        await server.serve_forever()


def run():
    print("Running smoke test (asyncio)")
    asyncio.run(serve(), debug=True)


if __name__ == "__main__":
    run()
