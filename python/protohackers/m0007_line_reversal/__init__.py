import sys
from protohackers.m0007_line_reversal.line_reversal import run


def main():
    try:
        run()
    except KeyboardInterrupt:
        print("Exited by user...")
        sys.exit(1)


if __name__ == "__main__":
    main()
