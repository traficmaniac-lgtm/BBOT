import logging
from pathlib import Path
from typing import Optional


def setup_logger(log_path: Path = Path("logs/app.log"), level: str = "INFO") -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("bbot")
    logger.setLevel(level)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    return logger


def mask_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    return value[:3] + "***" + value[-2:]

