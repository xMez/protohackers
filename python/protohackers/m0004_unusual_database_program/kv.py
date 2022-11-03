import asyncio
from asyncio.transports import DatagramTransport


class KvServerProtocol:
    def __init__(self) -> None:
        self.store = {"version": "Mez's Key-Value Store 0.1.0"}
        self.transport: DatagramTransport

    def connection_made(self, transport: DatagramTransport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr):
        message = data.decode()
        command = message.split("=", 1)
        if len(command) == 1:
            key = command[0]
            value = self.store.get(key, "")
            response = f"{key}={value}"
            self.transport.sendto(response.encode(encoding="ascii"), addr)
        elif len(command) == 2:
            key, value = command[0], command[1]
            if key == "version":
                return
            self.store[key] = value


async def serve():
    loop = asyncio.get_running_loop()
    print("Starting UDP server")

    transport, _ = await loop.create_datagram_endpoint(
        lambda: KvServerProtocol(), local_addr=("0.0.0.0", 10007)  # nosec
    )

    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()


def run():
    print("Running unusual database program")
    asyncio.run(serve(), debug=True)


if __name__ == "__main__":
    run()
