import asyncio
import logging
import logging.config
import re
from typing import Set

# create logger
logging.config.fileConfig("../../logging.conf")
logger = logging.getLogger('chat')


class UndefinedBehaviour(Exception):
    def __init__(self, message: str) -> None:
        logger.error(message)
        super().__init__(message)


class Chat:
    class Session:
        r: asyncio.StreamReader
        w: asyncio.StreamWriter
        name: str

        @classmethod
        async def create(cls, r: asyncio.StreamReader, w: asyncio.StreamWriter, name: bytes | str):
            logger.debug(f"User session: {name}")
            self = Chat.Session()
            self.r = r
            self.w = w
            if isinstance(name, bytes):
                name = str(name, encoding="ascii").strip()
            self.name = name
            return self

        async def send(self, message: bytes | str) -> None:
            if isinstance(message, str):
                message = bytes(message, encoding="ascii")
            self.w.write(message)
            logger.info(f"--> {self.name}: {message}")
            await self.w.drain()

        async def recv(self) -> str:
            message = await self.r.readline()
            logger.info(f"<-- {self.name}: {message}")
            return message.decode(encoding="ascii")
        
        def __eq__(self, value) -> str: return self.name == value
        def __hash__(self) -> int: return hash(self.name)
        def __str__(self) -> str: return self.name
        def __repr__(self) -> str: return self.name

    hello = b"Welcome to budgetchat! What shall I call you?\n"
    presence = "* The room contains: {}\n"
    join = "* {} has entered the room\n"
    leave = "* {} has left the room\n"
    message = "[{}] {}\n"
    sessions: Set[Session]

    def __init__(self) -> None:
        self.sessions = set()
        self.name_pattern = re.compile(r"^[a-zA-Z0-9]+", re.ASCII)

    async def join(self, session: Session) -> str:
        await session.send(self.hello)
        name = await session.recv()
        if await self.validate_name(name):
            users: str = await self.get_users()
            await session.send(self.presence.format(users))
            return name
        raise UndefinedBehaviour


    async def handle(self, r: asyncio.StreamReader, w: asyncio.StreamWriter):
        try:
            session = await self.Session.create(r, w, "")
            session.name = await self.join(session)
            self.announce_join(session.name)
            self.sessions.add(session)

            while message := await session.recv():
                self.send_message(session.name, message)
            
            self.sessions.remove(session)
            self.announce_leave(session.name)

        except UndefinedBehaviour:
            w.write(b"Undefined behaviour")
            await w.drain()
        w.close()
        await w.wait_closed()

    async def send_message(self, name: str, message: str):
        message = self.message.format(name, message)
        sessions = set(name) ^ self.sessions
        for session in sessions:
            await session.send(message)

    async def announce_join(self, name: str) -> None:
        announce = self.join.format(name)
        for session in self.sessions:
            await session.send(announce)

    async def announce_leave(self, name: str)  -> None:
        announce = self.leave.format(name)
        for session in self.sessions:
            await session.send(announce)

    async def get_users(self) -> str:
        users = [f"{session}" for session in self.sessions]
        user_list = ",".join(users)
        return user_list
        
    async def validate_name(self, name: str) -> bool:
        if len(name) >= 32:
            return False
        elif name in self.sessions:
            return False
        elif not self.name_pattern.match(str(name, encoding="ascii")):
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
