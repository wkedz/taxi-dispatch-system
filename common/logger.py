import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_configured = False
_logger_cache = {}

def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def _level_from_env(env_val: Optional[str], default: int = logging.INFO) -> int:
    if not env_val:
        return default
    return {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }.get(env_val.upper(), default)

def configure_root_logging(service_name: str) -> None:
    """
    Konfiguruje root logger JEDNORAZOWO, z rotacją plików.
    Parametry pobierane z ENV (z sensownymi defaultami).
    """
    global _configured
    if _configured:
        return

    log_dir = Path(os.getenv("LOG_DIR", "./logs"))
    log_file = os.getenv("LOG_FILE", "logs.txt")
    max_bytes = int(os.getenv("LOG_MAX_BYTES", "5242880"))   # 5 MB
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "3"))   # max 3 pliki: logs.txt, logs.txt.1, logs.txt.2
    level = _level_from_env(os.getenv("LOG_LEVEL"), logging.INFO)
    to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() in ("1", "true", "yes")

    _ensure_dir(log_dir)
    file_path = log_dir / log_file

    fmt = (
        "%(asctime)s %(levelname)s "
        f"[{service_name}] "
        "%(name)s %(module)s:%(lineno)d "
        "- %(message)s"
    )
    datefmt = "%Y-%m-%dT%H:%M:%S%z"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    handlers = []

    file_handler = RotatingFileHandler(
        filename=str(file_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    if to_console:
        console = logging.StreamHandler()  # przyda się w docker logs
        console.setFormatter(formatter)
        handlers.append(console)

    root = logging.getLogger()
    root.setLevel(level)
    for h in handlers:
        root.addHandler(h)

    # Uvicorn/fastapi integracja: wyrównaj poziomy i propagację
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).setLevel(level)
        logging.getLogger(name).propagate = True

    _configured = True


def get_logger(name: str) -> logging.Logger:
    logger = _logger_cache.get(name)
    if logger:
        return logger

    base = logging.getLogger(name)
    return base
