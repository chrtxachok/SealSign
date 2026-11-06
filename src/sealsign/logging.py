"""Настройка только логгера приложения; содержимое документов не логируется."""

import logging


def configure_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("sealsign")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.propagate = False
    return logger
