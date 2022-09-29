import socket
import threading
import socketserver

BUFFER = 1024


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    request: socket.socket

    def handle(self) -> None:
        while True:
            data = self.request.recv(BUFFER)
            if not data:
                break
            self.request.sendall(data)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 10007

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        print("server running in thread:", server_thread.name)

        server_thread.join()
