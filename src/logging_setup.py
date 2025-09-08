import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "app.log")

    logger = logging.getLogger()
    if logger.handlers:
        return  # already configured

    logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)

    fh = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    fh.setLevel(log_level)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
