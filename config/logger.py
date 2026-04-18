import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import Settings


def setup_logging(settings: Settings) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    has_console_handler = any(isinstance(handler, logging.StreamHandler) for handler in root.handlers)
    has_file_handler = any(
        isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == log_file.resolve()
        for handler in root.handlers
    )

    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    if not has_file_handler:
        file_handler = RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
