import asyncio
import logging
import logging.config

LENGTH = 9

# create logger
logging.config.fileConfig("../../logging.conf")
logger = logging.getLogger('price')


class UndefinedBehaviour(Exception):
    def __init__(self, message: str) -> None:
        logger.error(message)
        super().__init__(message)


async def handle(r: asyncio.StreamReader, w: asyncio.StreamWriter):
    prices = {}
    data = bytearray(9)
    try:
        while data := await r.readexactly(LENGTH):
            logger.debug(f"Processing: {data}")
            match data[0]:
                case 73:  # I
                    prices = await insert(data[1:], prices)
                case 81:  # Q
                    price = await query(data[1:], prices)
                    logger.debug(f"Sending: {price}")
                    w.write(price)
                    await w.drain()
                case _:
                    raise UndefinedBehaviour(f"Invalid type, '{data[0]}'")
    except UndefinedBehaviour:
        w.write(b"Undefined behaviour")
        await w.drain()
    except asyncio.IncompleteReadError:
        w.write(b"Incomplete message")
        await w.drain()
    w.close()
    await w.wait_closed()
    

async def insert(input: bytearray, prices: dict) -> dict:
    time = int.from_bytes(input[:4], "big", signed=True)
    price = int.from_bytes(input[4:], "big", signed=True)
    logger.info(f"Inserting: '{time}: {price}'")
    if time in prices.keys():
        raise UndefinedBehaviour(f"Existing timestamp, '{time}', '{prices.keys()}'")
    prices[time] = price
    return prices


async def query(input: bytearray, prices: dict) -> bytes:
    min_time = int.from_bytes(input[:4], "big", signed=True)
    max_time = int.from_bytes(input[4:], "big", signed=True)
    logger.info(f"Querying: '{min_time}' to '{max_time}'")
    keys = list(filter(lambda x: x >= min_time and x <= max_time, prices.keys()))
    logger.debug(f"Matching keys: '{keys}'")

    return int(sum([prices[key] for key in keys]) / len(keys)).to_bytes(4, "big", signed=True)


async def main():
    HOST, PORT = "0.0.0.0", 10007

    server = await asyncio.start_server(handle, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
