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
        def __init__(self, r: asyncio.StreamReader, w: asyncio.StreamWriter, name: str) -> None:
            logger.debug(f"User session: {name}")
            self.r = r
            self.w = w
            self.name = name
        
        def __eq__(self, value) -> str:
            return self.name == value

    hello = b"Welcome to budgetchat! What shall I call you?\n"
    users = b"* The room contains: "
    sessions: Set[Session]

    def __init__(self) -> None:
        self.sessions = []
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
        await self.sessions.add(self.Session(r, w, name))

        logger.debug("Users: {self.sessions}")
        w.write(self.users + bytes(",".join(self.sessions), encoding="ascii") + b"\n")
        await w.drain()

        
    async def validate_name(self, name: str) -> bool:
        if len(name) > 32:
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
