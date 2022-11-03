import asyncio
import logging
import logging.config
from typing import Dict

LENGTH = 9

# create logger
logging.config.fileConfig("../logging.conf")
logger = logging.getLogger("price")


class UndefinedBehaviour(Exception):
    def __init__(self, message: str) -> None:
        logger.error(message)
        super().__init__(message)


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    prices: Dict[int, int] = {}
    data = bytearray(9)
    try:
        while data := await reader.readexactly(LENGTH):
            logger.debug(f"Processing: {data}")
            match data[0]:
                case 73:  # I
                    prices = await insert(data[1:], prices)
                case 81:  # Q
                    price = await query(data[1:], prices)
                    logger.debug(f"Sending: {price}")
                    writer.write(price)
                    await writer.drain()
                case _:
                    raise UndefinedBehaviour(f"Invalid type, '{data[0]}'")
    except UndefinedBehaviour:
        writer.write(b"Undefined behaviour")
        await writer.drain()
    except asyncio.IncompleteReadError:
        writer.write(b"Incomplete message")
        await writer.drain()
    writer.close()
    await writer.wait_closed()


async def insert(data: bytearray, prices: Dict[int, int]) -> Dict[int, int]:
    time = int.from_bytes(data[:4], "big", signed=True)
    price = int.from_bytes(data[4:], "big", signed=True)
    logger.info(f"Inserting: '{time}: {price}'")
    if time in prices.keys():
        raise UndefinedBehaviour(f"Existing timestamp, '{time}', '{prices.keys()}'")
    prices[time] = price
    return prices


async def query(input: bytearray, prices: dict) -> bytes:
    min_time = int.from_bytes(input[:4], "big", signed=True)
    max_time = int.from_bytes(input[4:], "big", signed=True)

    if min_time > max_time:
        logger.debug(f"Min > Max: '{min_time}' < '{max_time}'")
        return bytes(4)
    logger.info(f"Querying: '{min_time}' to '{max_time}'")

    keys = list(filter(lambda x: x >= min_time and x <= max_time, prices.keys()))
    if not keys:
        logger.debug(f"No matching keys: '{min_time}' to '{max_time}'")
        return bytes(4)

    return int(sum([prices[key] for key in keys]) / len(keys)).to_bytes(
        4, "big", signed=True
    )


async def serve():
    server = await asyncio.start_server(handle, "0.0.0.0", 10007)  # nosec
    async with server:
        await server.serve_forever()


def run():
    print("Running means to an end")
    asyncio.run(serve(), debug=True)


if __name__ == "__main__":
    run()
