import asyncio
import logging
import logging.config
from asyncio.transports import DatagramTransport

# create logger
logging.config.fileConfig("../logging.conf")
logger = logging.getLogger("protohackers")


class KvServerProtocol:
    def __init__(self) -> None:
        self.kv = {
            "version": "Mez's Key-Value Store 0.1.0"
        }

    def connection_made(self, transport: DatagramTransport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr):
        message = data.decode()
        command = message.split("=", 1)
        if len(command) == 1:
            key = command[0]
            value = self.kv.get(key, "")
            response = f"{key}={value}"
            self.transport.sendto(response.encode(encoding="ascii"), addr)
        elif len(command) == 2:
            key, value = command[0], command[1]
            if key == "version":
                return
            self.kv[key] = value


async def main():
    ADDR = ("0.0.0.0", 10007)

    loop = asyncio.get_running_loop()

    await loop.create_datagram_endpoint(lambda: KvServerProtocol(), local_addr=ADDR)
    loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
