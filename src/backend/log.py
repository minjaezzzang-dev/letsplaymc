import logging
import sys
from pathlib import Path

from .config import settings

_LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(name: str = "letsplaymc") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    logger.handlers.clear()
    logger.addHandler(handler)

    log_dir = Path(settings.data_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger


logger = setup_logging()
