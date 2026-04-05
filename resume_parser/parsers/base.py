import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class FileParserError(Exception):
    """Raised when a resume file cannot be parsed."""


class BaseParser(ABC):
    """Abstract parser for document content."""

    @abstractmethod
    def load_text(self, file_path: str) -> str:
        raise NotImplementedError

    def _validate_file(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.exists():
            logger.error("Input file does not exist: %s", file_path)
            raise FileParserError(f"File not found: {file_path}")
        if not path.is_file():
            logger.error("Input path is not a file: %s", file_path)
            raise FileParserError(f"Path is not a file: {file_path}")
        return path
