import logging
from typing import List, Optional

from .base import FieldExtractor
from .strategies import ExtractionStrategy

logger = logging.getLogger(__name__)


class SkillsExtractor(FieldExtractor):
    """Extracts technical skills from resume text using a configurable extraction strategy."""

    def __init__(self, strategy: Optional[ExtractionStrategy] = None):
        """Initialize with an extraction strategy.
        
        Args:
            strategy: ExtractionStrategy to use. Defaults to RegexExtractionStrategy.
        """
        super().__init__(strategy)

    def extract(self, text: str) -> List[str]:
        """Extract skills using the configured strategy.
        
        Args:
            text: Resume text to extract from.
            
        Returns:
            List of extracted skills sorted alphabetically.
        """
        logging.info("Extracting skills using strategy: %s", self.strategy.__class__.__name__)
        return self._extract_with_fallback("extract_skills", text)
