import sys
from protohackers.m0003_budget_chat.chat import run


def main():
    try:
        run()
    except KeyboardInterrupt:
        print("Exited by user...")
        sys.exit(1)


if __name__ == "__main__":
    main()
