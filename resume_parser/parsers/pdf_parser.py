import logging

from PyPDF2 import PdfReader

from .base import BaseParser, FileParserError

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Parser for PDF resumes."""

    def load_text(self, file_path: str) -> str:
        path = self._validate_file(file_path)
        try:
            reader = PdfReader(str(path))
            text_chunks = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)

            if not text_chunks:
                logger.warning("No text extracted from PDF: %s", file_path)

            return "\n".join(text_chunks).strip()
        except Exception as exc:
            logger.exception("Failed to parse PDF file %s", file_path)
            raise FileParserError(f"Could not parse PDF {file_path}: {exc}") from exc
