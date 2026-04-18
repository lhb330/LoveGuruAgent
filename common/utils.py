from datetime import datetime
from pathlib import Path


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
