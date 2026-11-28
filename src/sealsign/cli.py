"""CLI без загрузки модели или зависимостей обучения при запуске справки."""

import argparse
import json
import zipfile
from pathlib import Path

from sealsign import __version__
from sealsign.logging import configure_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sealsign",
        description="SealSign — поиск печатей и подписей; исследовательский импорт данных.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO"
    )
    commands = parser.add_subparsers(dest="command")
    data = commands.add_parser("data", help="Исследовательская подготовка данных")
    actions = data.add_subparsers(dest="action", required=True)
    importer = actions.add_parser("import", help="ZIP → канонический bundle (unreviewed)")
    importer.add_argument("archive", type=Path)
    importer.add_argument("--config", required=True, type=Path)
    importer.add_argument("--output", required=True, type=Path)
    importer.add_argument("--preview-limit", default=12, type=int)
    validator = actions.add_parser("validate", help="Проверить структуру и геометрию bundle")
    validator.add_argument("bundle", type=Path)
    demo = commands.add_parser("demo", help="Открыть локальную проверку изображения")
    demo.add_argument("--bundle", type=Path)
    demo.add_argument("--port", type=int, default=8765)
    demo.add_argument("--open", action="store_true", help="Открыть страницу в браузере")
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    if args.command == "demo":
        from sealsign.demo import serve
        from sealsign.paths import RuntimePaths

        bundle = args.bundle or RuntimePaths.from_env().artifacts / "s05-runs" / "bundle-v1"
        try:
            serve(bundle, args.port, args.open)
        except ModuleNotFoundError as exc:
            parser.error(f"Установите зависимости из requirements-s05.txt ({exc.name}).")
        except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
            parser.error(str(exc))
        return 0
    if args.command == "data":
        try:
            if args.action == "import":
                from sealsign.data.importer import import_zip

                result = import_zip(
                    args.archive,
                    json.loads(args.config.read_text()),
                    args.output,
                    args.preview_limit,
                )
            else:
                from sealsign.data.validator import validate_bundle

                result = validate_bundle(args.bundle)
        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
            parser.error(str(exc))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    parser.print_help()
    return 0
