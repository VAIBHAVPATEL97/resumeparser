import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from .strategies import ExtractionStrategy, RegexExtractionStrategy, LLMExtractionStrategy

logger = logging.getLogger(__name__)


class FieldExtractor(ABC):
    """Abstract base extractor for a single resume field.
    
    Uses a pluggable extraction strategy (regex, NER, LLM, etc.) to extract data.
    """

    def __init__(self, strategy: Optional[ExtractionStrategy] = None):
        """Initialize the field extractor with an extraction strategy.
        
        Args:
            strategy: ExtractionStrategy instance. Defaults to LLMExtractionStrategy with fallback to RegexExtractionStrategy.
        """
        if strategy is not None:
            self.strategy = strategy
        else:
            try:
                self.strategy = LLMExtractionStrategy()
            except Exception as exc:
                logger.warning(
                    "LLMExtractionStrategy unavailable, falling back to RegexExtractionStrategy: %s",
                    exc,
                )
                self.strategy = RegexExtractionStrategy()

    def _extract_with_fallback(self, method_name: str, text: str):
        """Attempt extraction and fallback to regex on strategy failure."""
        try:
            return getattr(self.strategy, method_name)(text)
        except Exception as exc:
            logger.warning(
                "Extraction with %s failed: %s. Falling back to RegexExtractionStrategy.",
                self.strategy.__class__.__name__,
                exc,
            )
            if isinstance(self.strategy, RegexExtractionStrategy):
                raise
            self.strategy = RegexExtractionStrategy()
            return getattr(self.strategy, method_name)(text)

    @abstractmethod
    def extract(self, text: str) -> Any:
        """Extract the field from the given text using the configured strategy.
        
        Args:
            text: The resume text to extract from.
            
        Returns:
            The extracted field value (type depends on the field).
        """
        raise NotImplementedError
