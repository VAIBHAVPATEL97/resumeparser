import logging
from typing import Optional

from .base import FieldExtractor
from .strategies import ExtractionStrategy

logger = logging.getLogger(__name__)


class NameExtractor(FieldExtractor):
    """Extracts a candidate name from resume text using a configurable extraction strategy."""

    def __init__(self, strategy: Optional[ExtractionStrategy] = None):
        """Initialize with an extraction strategy.
        
        Args:
            strategy: ExtractionStrategy to use. Defaults to RegexExtractionStrategy.
        """
        super().__init__(strategy)

    def extract(self, text: str) -> Optional[str]:
        """Extract candidate name using the configured strategy.
        
        Args:
            text: Resume text to extract from.
            
        Returns:
            Extracted name or None if not found.
        """
        logging.info("Extracting name using strategy: %s", self.strategy.__class__.__name__)
        return self._extract_with_fallback("extract_name", text)
