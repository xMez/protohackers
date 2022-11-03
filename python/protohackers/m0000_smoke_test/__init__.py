import argparse
import sys
from protohackers.m0000_smoke_test.echo_asyncio import run as run_asyncio
from protohackers.m0000_smoke_test.echo_socketserver import run as run_socketserver


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-m",
            "--method",
            type=str,
            choices=["asyncio", "socketserver"],
            default="asyncio",
            help="select which server to use (default asyncio)",
        )
        args = parser.parse_args()

        match args.method:
            case "asyncio":
                run_asyncio()
            case "socketserver":
                run_socketserver()
    except KeyboardInterrupt:
        print("Exited by user...")
        sys.exit(1)


if __name__ == "__main__":
    main()
