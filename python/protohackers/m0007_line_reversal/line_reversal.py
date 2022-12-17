import asyncio
from asyncio.transports import DatagramTransport
from bisect import bisect
from dataclasses import dataclass
from time import asctime

from typing import Dict, List, Tuple, TypeAlias

Address: TypeAlias = tuple[str, int]  # (host, port)


def send(transport: DatagramTransport, address: Address, message: str) -> None:
    transport.sendto(message.encode(), address)
    print(asctime(), "sending", repr(str(message))[:30], "to", address)


class InvalidMessage(Exception):
    pass


@dataclass
class Session:
    session: str
    address: Address
    transport: DatagramTransport
    message: str
    read: int
    sent: int
    ack: int
    ttl: int

    async def send_task(self) -> None:
        reverse = ""
        while self.ttl > 0 and not self.transport.is_closing():
            if self.ttl % 3:
                send(self.transport, self.address, f"/ack/{self.session}/{self.read}/")
                if len(reverse) != len(self.message):
                    reverse = self.reverse_lines(self.message)
                self.send_message(reverse)
            await asyncio.sleep(1)
            self.ttl -= 1

    def send_message(self, reverse: str) -> None:
        limit = 900
        message, sep, _ = reverse.rpartition("\n")
        message = (message + sep)[self.ack :]
        messages = [message[i : i + limit] for i in range(0, len(message), limit)]
        for i, message in enumerate(messages):
            escaped = message.replace("\\", "\\\\").replace("/", "\\/")
            send(
                self.transport,
                self.address,
                f"/data/{self.session}/{self.ack + i * limit}/{escaped}/",
            )
            self.sent = self.ack + len(message) + i * limit
            if i == 5:
                break

    @staticmethod
    def reverse_lines(lines: str) -> str:
        reverse: List[str] = []
        for line in lines.splitlines(keepends=True):
            new_line = line[-1] if line[-1] == "\n" else ""
            if new_line:
                line = line[:-1]
            reverse.append(line[::-1] + new_line)
        return "".join(reverse)

    def __repr__(self) -> str:
        return repr(self.message)[:30]


SESSIONS: Dict[str, Session] = {}


class LineReversalProtocol:
    TTL = 60
    NUM_MAX = 2**31 - 1

    def __init__(self) -> None:
        self.addr: Address
        self.transport: DatagramTransport

    def connection_made(self, transport: DatagramTransport) -> None:
        self.transport = transport

    def get_type_and_session(self, message: str) -> Tuple[str, ...]:
        split_message = message.split("/", maxsplit=3)
        if len(split_message) < 2:
            raise InvalidMessage
        message_type, session = split_message[0], split_message[1]
        if (
            message_type not in ("connect", "data", "ack", "close")
            or not session.isdigit()
            or int(session) > self.NUM_MAX
            or int(session) < 0
        ):
            raise InvalidMessage
        message = split_message[2:] if len(split_message) > 2 else ""
        return message_type, session, message

    def handle(self, message: str):
        if len(message) > 10000 or message[0] != "/" or message[-1] != "/":
            raise InvalidMessage
        message_type, session, message = self.get_type_and_session(message[1:-1])
        match message_type:
            case "connect":
                self.handle_connect(session)
            case "data":
                self.handle_data(session, *message)
            case "ack":
                self.handle_ack(session, *message)
            case "close":
                self.handle_close(session)
            case _:
                raise InvalidMessage

    def handle_connect(self, session: str) -> None:
        if session not in SESSIONS:
            SESSIONS[session] = Session(
                session=session,
                address=self.addr,
                transport=self.transport,
                message="",
                ack=0,
                read=0,
                sent=0,
                ttl=self.TTL,
            )
        asyncio.create_task(SESSIONS[session].send_task())

    def handle_data(self, session_id: str, str_pos: str, message: str) -> None:
        # If the session is not open: send `/close/SESSION/` and stop.
        if session_id not in SESSIONS:
            send(self.transport, self.addr, f"/close/{session_id}/")
            return
        session = SESSIONS[session_id]
        pos = int(str_pos)
        escaped_slash = message.count("\\/")
        unescaped = message.replace("\\\\", "\\").replace("\\/", "/")
        unescaped_slash = unescaped.count("/")
        if escaped_slash != unescaped_slash:
            raise InvalidMessage
        # If you've already received everything up to POS: unescape "\\" and "\/",
        # find the total LENGTH of unscaped data that you've already recevied
        # (including the data in this message, if any), send `/ack/SESSION/LENGTH/`,
        # and pass on the new data (if any) to the application layer.
        if session.read >= pos and len(unescaped) > 0:
            read = pos + len(unescaped)
            if read > session.read:
                session.message = session.message[:pos] + unescaped
                session.read = read
            send(self.transport, self.addr, f"/ack/{session_id}/{session.read}/")
        # If you have not received everything up to POS: send a duplicate of your
        # previous ack (or /ack/SESSION/0/ if none), saying how much you have recevied,
        # to provoke the other side to retransmit whatever you're missing.
        elif session.read < pos:
            send(self.transport, self.addr, f"/ack/{session_id}/{session.read}/")

    def handle_ack(self, session: str, length: str) -> None:
        # If the SESSION is not open: send `/close/SESSION` and stop.
        if session not in SESSIONS:
            self.handle_close(session)
            return
        print("ACK", session, length)
        ack = int(length)
        current = SESSIONS[session].ack
        sent = SESSIONS[session].sent

        # If the LENGTH value is not larger than the largest LENGTH value in any
        # ack message you've received on this session so far:
        # do nothing and stop (assume it's a duplicate ack that got delayed).
        if current > ack:
            return
        # If the LENGTH value is larger than the total amount of payload you've
        # sent: the peer is misbehaving, close the session.
        if SESSIONS[session].read < ack:
            self.handle_close(session)
            return
        # If the LENGTH value is smaller than the total amount of payload you've sent:
        # retransmit all payload data after the first LENGTH bytes.
        if sent > ack:
            SESSIONS[session].sent = ack
            SESSIONS[session].ack = ack
            return
        # If the LENGTH value is equal to the total amount of payload you've sent:
        # don'd send any reply.

        SESSIONS[session].ttl = self.TTL
        if sent == ack:
            SESSIONS[session].ack = ack
            return

    def handle_close(self, session: str) -> None:
        send(self.transport, self.addr, f"/close/{session}/")
        if SESSIONS.get(session):
            SESSIONS[session].ttl = 0
            del SESSIONS[session]

    def datagram_received(self, data: bytes, address: Address) -> None:
        self.addr = address
        message = data.decode()
        try:
            self.handle(message)
        except InvalidMessage:
            pass


async def serve():
    loop = asyncio.get_running_loop()
    print("Starting UDP server")

    transport, _ = await loop.create_datagram_endpoint(
        lambda: LineReversalProtocol(), local_addr=("0.0.0.0", 10000)  # nosec
    )

    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()


def run():
    print("Running line reversal")
    asyncio.run(serve(), debug=True)


if __name__ == "__main__":
    run()
