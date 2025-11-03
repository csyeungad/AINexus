import logging
import logging.config
import os
from datetime import datetime


def setup_logging(log_dir: str = None, base_file_name: str = "app.log", level: str = "INFO"):
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
    os.makedirs(log_dir, exist_ok=True)

    # Format date as YYYYMMDD
    date_str = datetime.now().strftime("%Y%m%d")

    # Generate log filename like "20250512_app.log"
    log_file_name = f"{date_str}_{base_file_name}"
    log_file_path = os.path.join(log_dir, log_file_name)

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",  # simple FileHandler, no rotation
                "level": level,
                "formatter": "standard",
                "filename": log_file_path,
                "encoding": "utf-8",
                "mode": "a",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": level,
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)


def add_module_file_handler(logger_name: str, log_dir: str = "log", level=logging.INFO):
    os.makedirs(log_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{date_str}_{logger_name.replace('.', '_')}.log")

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file:
            return logger

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    return logger
