import json
import math
import socket
import threading
import socketserver

BUFFER = 8192


class MalformedRequestError(Exception):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    request: socket.socket

    def handle(self) -> None:
        data, start = b"", 0
        while True:
            # Receive data from client
            recv = self.request.recv(BUFFER)
            if not recv:
                break
            data += recv

            start = self.split(data, start)
            if start == -1:
                break

    def split(self, data: bytes, start: int) -> int:
        end = data.find(b"\n", start)
        while end != -1:
            try:
                response = self.process(data[start:end])
                self.request.sendall(response)
            except MalformedRequestError:
                self.request.sendall(b"{}")
                return -1
            start = end + 1
            end = data.find(b"\n", start)
        return start

    def process(self, data: bytes) -> bytes:
        obj = self.get_json(data)
        if self.is_prime(self.get_number(obj)):
            return b'{"method":"isPrime","prime":true}\n'
        return b'{"method":"isPrime","prime":false}\n'

    @staticmethod
    def get_json(data: bytes) -> dict:
        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise MalformedRequestError from error

    @staticmethod
    def get_number(data: dict) -> int | float:
        if data.get("method") == "isPrime":
            print("correct method")
            number = data.get("number")
            if isinstance(number, (int, float)) and not isinstance(number, bool):
                return number
        raise MalformedRequestError

    @staticmethod
    def is_prime(num: int | float) -> bool:
        if isinstance(num, float):
            return False
        if num < 2:
            return False
        for i in range(2, int(math.sqrt(num)) + 1):
            if (num % i) == 0:
                return False
        return True


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def serve():
    server = ThreadedTCPServer(("0.0.0.0", 10008), ThreadedTCPRequestHandler)  # nosec
    with server:
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True  # noqa
        server_thread.start()

        print("server running in thread:", server_thread.name)

        server_thread.join()


def run():
    print("Running prime time")
    serve()


if __name__ == "__main__":
    run()
