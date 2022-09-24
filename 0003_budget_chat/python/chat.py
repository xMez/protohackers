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
            self.r = r
            self.w = w
            self.name = name
        
        def __eq__(self, value) -> str:
            return self.name == value

    hello = b"Welcome to budgetchat! What shall I call you?"
    users = b"* The room contains: "
    sessions: Set[Session]

    def __init__(self) -> None:
        self.sessions = []
        self.name_pattern = re.compile(r"^[a-zA-Z0-9]+", re.ASCII)

    async def handle(self, r: asyncio.StreamReader, w: asyncio.StreamWriter):
        w.write(self.hello)
        await w.drain()

        message = await r.readline()
        if name := await self.validate_name(message) == False:
            return
        self.sessions.add(self.Session(r, w, name))
        w.write(self.users + bytes(",".join(self.sessions), encoding="ascii"))

        
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
