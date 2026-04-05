import logging
import sys
from pathlib import Path
from datetime import datetime


def configure_logging(level: int = logging.INFO) -> None:
    current_dir = Path(__file__).resolve().parents[1]
    current_logs_dir = current_dir / "logs"
    current_logs_dir.mkdir(parents=True, exist_ok=True)

    current_log_file = current_logs_dir / f"resume_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    current_file_handler = logging.FileHandler(current_log_file, encoding="utf-8")
    current_file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(current_file_handler)
