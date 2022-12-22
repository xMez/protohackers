"""Package for solution to protohackers challenge 8 'Insecure Sockets Layer'."""


import sys
from protohackers.m0008_insecure_sockets_layer.server import run


def main():
    try:
        run()
    except KeyboardInterrupt:
        print("Exited by user...")
        sys.exit(1)


if __name__ == "__main__":
    main()
