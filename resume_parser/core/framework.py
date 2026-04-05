import logging

from .parser_factory import get_parser, FileParserError
from .resume_extractor import ResumeExtractor, ResumeParsingError

logger = logging.getLogger(__name__)


class ResumeParserFramework:
    """Orchestrates parser selection and resume field extraction."""

    def __init__(self, resume_extractor: ResumeExtractor):
        self.resume_extractor = resume_extractor

    def parse_resume(self, file_path: str):
        if not file_path or not isinstance(file_path, str):
            raise ResumeParsingError("A valid resume file path must be provided")

        try:
            parser = get_parser(file_path)          # PDFParser or WordParser based on file extension
        except FileParserError as exc:
            raise ResumeParsingError(str(exc)) from exc

        try:
            text = parser.load_text(file_path)
        except FileParserError as exc:
            raise ResumeParsingError(f"Could not parse resume file: {exc}") from exc

        if not text:
            logger.warning("Resume file parsed successfully but no text was extracted: %s", file_path)

        return self.resume_extractor.extract(text)
