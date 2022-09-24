import asyncio
import logging

LENGTH = 9


class UndefinedBehaviour(Exception):
    def __init__(self, message: str) -> None:
        logging.error(message)
        super().__init__(message)


async def handle(r: asyncio.StreamReader, w: asyncio.StreamWriter):
    prices = {}
    data = bytearray(9)
    data = await r.read(LENGTH)
    while data:
        try:
            match data[0]:
                case 73:  # I
                    prices = await insert(data[1:], prices)
                case 81:  # Q
                    price = await query(data[1:], prices)
                    w.write(bytes(price))
                    await w.drain()
                case _:
                    raise UndefinedBehaviour(f"Invalid type, '{data[0]}'")
        except UndefinedBehaviour:
            w.write(b"Undefined behaviour")
            break
        data = await r.read(LENGTH)
    await w.drain()
    w.close()
    

async def insert(input: bytearray, prices: dict) -> dict:
    time = int.from_bytes(input[:4], "big", signed=True)
    price = int.from_bytes(input[4:], "big", signed=True)
    logging.error(f"Inserting, {time}: {price}")
    if time in prices.keys():
        raise UndefinedBehaviour(f"Existing timestamp, '{time}', '{prices.keys()}'")
    prices[time] = price
    return prices


async def query(input: bytearray, prices: dict) -> int:
    min_time = int.from_bytes(input[:4], "big", signed=True)
    max_time = int.from_bytes(input[4:], "big", signed=True)
    keys = filter(lambda x: x >= min_time and x <= max_time, prices.keys())
    return int(sum([prices[key] for key in keys]) / len(keys))


async def main():
    HOST, PORT = "0.0.0.0", 10007

    server = await asyncio.start_server(handle, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
