import asyncio
from asyncio.transports import DatagramTransport


class LineReversalProtocol:
    def __init__(self) -> None:
        self.transport: DatagramTransport

    def connection_made(self, transport: DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr) -> None:
        message = data.decode()


async def serve():
    loop = asyncio.get_running_loop()
    print("Starting UDP server")

    transport, _ = await loop.create_datagram_endpoint(
        lambda: LineReversalProtocol(), local_addr=("0.0.0.0", 10007)  # nosec
    )

    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()


def run():
    print("Running line reversal")
    asyncio.run(serve(), debug=True)


if __name__ == "__main__":
    run()
