"""Server for Insecure Sockets Layer."""
import asyncio
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass
import logging
from typing import Dict, Optional

from protohackers.m0008_insecure_sockets_layer.obfuscate import Cipher, CipherError

logging.basicConfig(level=logging.DEBUG)


@dataclass
class Io:
    """Asyncio reader and writer."""

    reader: StreamReader
    writer: StreamWriter


class Session:
    """Server session."""

    def __init__(self, io: Io, cipher: Optional[Cipher] = None) -> None:
        """Initialize a client/server session.

        Parameters
        ----------
        io : Io
            Client reader and writer
        cipher : Cipher, optional
            Cipher to use for encryption, by default None
        """
        self.cipher = cipher
        self.io = io
        self.read_pos = 0
        self.send_pos = 0

    async def handle(self) -> None:
        """Handle session."""
        logging.debug("Reading lines")
        if self.io.reader.at_eof():
            raise ConnectionError
        while line := await self.receive():
            toys = self.get_toys(line)
            max_toy = max(toys.keys())
            await self.send(f"{max_toy}x {toys[max_toy]}\n")

    async def receive(self) -> str:
        """Recieve and decrypt a line from the connected client.

        Returns
        -------
        str
            Decrypted line
        """
        line = ""
        while True:
            char = await self.io.reader.read(1)
            if char == b"":
                return ""
            if self.cipher:
                char = self.cipher.decrypt(char, self.read_pos)
            self.read_pos += 1
            if char == b"\n":
                break
            line += char.decode(encoding="ascii")
        logging.info("Received: %s", repr(line))
        return line

    async def send(self, line: str) -> None:
        """Encrypt and send a line to the connected client.

        Parameters
        ----------
        line : str
            Line to send
        """
        logging.info("Sending: %s", repr(line))
        encoded = line.encode(encoding="ascii")
        if self.cipher:
            encoded = self.cipher.encrypt(encoded, self.send_pos)
        self.io.writer.write(encoded)
        await self.io.writer.drain()
        self.send_pos += len(encoded)

    @staticmethod
    def get_toys(line: str) -> Dict[int, str]:
        if line[-1] == "\n":
            line = line[:-1]
        toys: Dict[int, str] = {}
        for entry in line.split(","):
            num, _, toy = entry.partition("x ")
            toys[int(num)] = toy
        return toys


async def get_cipher_spec(reader: StreamReader) -> bytearray:
    spec = bytearray(80)
    i = 0
    while True:
        chars = await reader.read(1)
        spec[i] = chars[0]
        if chars in (b"\x02", b"\x04"):
            i += 1
            chars = await reader.read(1)
            spec[i] = chars[0]
        elif chars == b"\x00":
            break
        i += 1
    return spec


async def handle(reader: StreamReader, writer: StreamWriter) -> None:
    """Handle incomming connection,
    initializing the cipher and starting a session.

    Parameters
    ----------
    reader : StreamReader
        Client reader
    writer : StreamWriter
        Client writer
    """
    logging.info("New connection %s", reader)
    try:
        cipher_spec = await get_cipher_spec(reader)
        cipher = Cipher(cipher_spec)
        io = Io(reader=reader, writer=writer)
        session = Session(io, cipher=cipher)
        await session.handle()
    except CipherError:
        writer.close()


async def serve() -> None:
    """Serve an async server."""
    server = await asyncio.start_server(handle, "0.0.0.0", 10000)  # nosec
    async with server:
        await server.serve_forever()


def run() -> None:
    """Run the server with a coroutine."""
    print("Running insecure socket layer")
    asyncio.run(serve(), debug=True)


if __name__ == "__main__":
    run()
