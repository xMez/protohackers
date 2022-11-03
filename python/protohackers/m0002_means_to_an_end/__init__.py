import sys
from protohackers.m0002_means_to_an_end.price import run


def main():
    try:
        run()
    except KeyboardInterrupt:
        print("Exited by user...")
        sys.exit(1)


if __name__ == "__main__":
    main()
