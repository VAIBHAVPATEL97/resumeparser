import logging

import docx

from .base import BaseParser, FileParserError

logger = logging.getLogger(__name__)


class WordParser(BaseParser):
    """Parser for Word (.docx/.doc) resumes."""

    def load_text(self, file_path: str) -> str:
        path = self._validate_file(file_path)
        try:
            document = docx.Document(str(path))
            paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]

            if not paragraphs:
                logger.warning("No text extracted from Word file: %s", file_path)

            return "\n".join(paragraphs).strip()
        except Exception as exc:
            logger.exception("Failed to parse Word file %s", file_path)
            raise FileParserError(f"Could not parse Word document {file_path}: {exc}") from exc
