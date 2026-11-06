"""CLI без загрузки модели или зависимостей обучения при запуске справки."""

import argparse

from sealsign import __version__
from sealsign.logging import configure_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sealsign",
        description="SealSign — поиск печатей и подписей. Пока доступен каркас S01.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO"
    )
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    parser.print_help()
    return 0
