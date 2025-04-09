import logging
import sys
from pathlib import Path

LOG_FILE_NAME = "migration_run.log"


def setup_logging(log_dir: Path, level=logging.INFO):
    """Configures logging to file and console."""
    log_file = log_dir / LOG_FILE_NAME
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger()
    logger.setLevel(level)

    try:
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Error setting up file logging to {log_file}: {e}", file=sys.stderr)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {log_file}")
