import logging
from typing import Any, Dict

from ..extractors.base import FieldExtractor
from ..models.resume_data import ResumeData

logger = logging.getLogger(__name__)


class ResumeParsingError(Exception):
    """Raised when extraction fails."""


class ResumeExtractor:
    """Runs configured FieldExtractor instances and returns structured resume data."""

    def __init__(self, extractors: Dict[str, FieldExtractor]):
        self.extractors = extractors

    def extract(self, text: str) -> ResumeData:
        if not isinstance(text, str):
            raise ResumeParsingError("Extracted resume content must be a string")

        logger.info("Starting resume extraction with extractors: %s", {
            field_name: type(extractor).__name__
            for field_name, extractor in self.extractors.items()
        })

        extracted: Dict[str, Any] = {}
        for field_name, extractor in self.extractors.items():
            try:
                logger.info(
                    "Extracting field %s using extractor %s",
                    field_name,
                    type(extractor).__name__,
                )
                extracted[field_name] = extractor.extract(text)
            except Exception as exc:
                logger.exception("Extractor for field %s failed", field_name)
                raise ResumeParsingError(
                    f"Field extraction for '{field_name}' failed: {exc}"
                ) from exc

        return ResumeData(
            name=extracted.get("name") or "",
            email=extracted.get("email") or "",
            skills=extracted.get("skills") or [],
        )
