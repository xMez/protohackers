import asyncio
import logging
import logging.config
import re
from typing import Optional, Set
from uuid import uuid4

# create logger
logging.config.fileConfig("../../logging.conf")
logger = logging.getLogger("chat")


class UndefinedBehaviour(Exception):
    def __init__(self, message: str) -> None:
        logger.error(message)
        super().__init__(message)


class Chat:
    class Session:
        reader: asyncio.StreamReader
        writer: asyncio.StreamWriter
        name: str
        uuid: str

        @classmethod
        async def create(
            cls,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
        ):
            self = Chat.Session()
            self.reader = reader
            self.writer = writer
            self.uuid = await uuid4().hex
            return self

        async def send(self, message: bytes | str, name: Optional[str] = None) -> None:
            if name == self.name:
                return
            if isinstance(message, str):
                message = bytes(message, encoding="ascii")
            self.writer.write(message)
            logger.info(f"{self.uuid} --> {self.name}: {message!r}")
            await self.writer.drain()

        async def recv(self) -> str:
            message = await self.reader.readline()
            logger.info(f"{self.uuid} <-- {self.name}: {message!r}")
            return message.decode(encoding="ascii")

        def __eq__(self, value) -> bool:
            return self.name == value

        def __hash__(self) -> int:
            return hash(self.name)

        def __str__(self) -> str:
            return self.name

        def __repr__(self) -> str:
            return self.name

    hello = b"Welcome to budgetchat! What shall I call you?\n"
    presence = "* The room contains: {}\n"
    user_join = "* {} has entered the room\n"
    user_leave = "* {} has left the room\n"
    message = "[{}] {}\n"
    sessions: Set[Session]

    def __init__(self) -> None:
        self.sessions = set()
        self.name_pattern = re.compile(r"^[a-zA-Z0-9]+", re.ASCII)

    async def join(self, session: Session) -> str:
        await session.send(self.hello)
        name = await session.recv()
        if await self.validate_name(name):
            logger.debug(f"Valid user: {name}")
            users: str = await self.get_users()
            await session.send(self.presence.format(users))
            return name.rstrip("\r\n")
        raise UndefinedBehaviour("User failed to join")

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            session = await self.Session.create(reader, writer, "")
            session.name = await self.join(session)
            await self.send(self.user_join, session.name)
            self.sessions.add(session)

            while message := await session.recv():
                await self.send(self.message, session.name, message, name=session.name)

            self.sessions.remove(session)
            await self.send(self.user_leave, session.name)

        except UndefinedBehaviour:
            writer.write(b"Undefined behaviour")
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def send(self, template: str, *args, name: Optional[str] = None):
        message = template.format(*args)
        for session in self.sessions:
            await session.send(message, name)

    async def get_users(self) -> str:
        users = [f"{session}" for session in self.sessions]
        return ",".join(users)

    async def validate_name(self, name: str) -> bool:
        if len(name) >= 32:
            return False
        if name in self.sessions:
            return False
        if not self.name_pattern.match(name):
            return False
        return True


async def main():
    HOST, PORT = "0.0.0.0", 10007

    chat = Chat()
    server = await asyncio.start_server(chat.handle, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
