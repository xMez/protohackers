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
        async def create(cls, r: asyncio.StreamReader, w: asyncio.StreamWriter, name: bytes):
            logger.debug(f"User session: {name}")
            self = Chat.Session()
            self.r = r
            self.w = w
            self.name = str(name, encoding="ascii").strip()
            return self
        
        def __eq__(self, value) -> str:
            return self.name == value

        def __hash__(self) -> int:
            return hash(self.name)

        def __str__(self) -> str:
            return self.name

        def __repr__(self) -> str:
            return self.name

    hello = b"Welcome to budgetchat! What shall I call you?\n"
    presence = "* The room contains: {}\n"
    announce = "* {} has entered the room\n"
    sessions: Set[Session]

    def __init__(self) -> None:
        self.sessions = set()
        self.name_pattern = re.compile(r"^[a-zA-Z0-9]+", re.ASCII)

    async def handle(self, r: asyncio.StreamReader, w: asyncio.StreamWriter):
        logger.debug("New connection!")
        w.write(self.hello)
        await w.drain()

        name = await r.readline()
        if not await self.validate_name(name):
            logger.error(f"Invalid name: {name}")
            return
        logger.info(f"Adding user: {name}")
        user_list: str = await self.get_users()
        presence = self.presence.format(user_list)
        logger.debug(presence)
        w.write(bytes(presence, encoding="ascii"))
        await w.drain()

        session = await self.Session.create(r, w, name)
        await self.announce_user(session.name)
        self.sessions.add(session)


    async def announce_user(self, name: str) -> None:
        announce = self.announce.format(name)
        for session in self.sessions:
            session.w.write(bytes(announce, encoding="ascii"))
            await session.w.drain()

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
    asyncio.run(main())
