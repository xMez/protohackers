import sys
from protohackers.m0001_prime_time.is_prime import run


def main():
    try:
        run()
    except KeyboardInterrupt:
        print("Exited by user...")
        sys.exit(1)


if __name__ == "__main__":
    main()
