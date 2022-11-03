import argparse

from config.module import get_modules, get_name
from config.poetry import load_config, write_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="pyproject.toml",
    )
    parser.add_argument(
        "-m",
        "--module",
        type=str,
        required=True,
        help="python module",
    )
    args = parser.parse_args()

    config, poetry = load_config(args.file)
    modules = get_modules(args.module)

    for module in modules:
        poetry.add_script(get_name(module), f"{args.module}.{module}")

    write_config(args.file, (config, poetry))


if __name__ == "__main__":
    main()
