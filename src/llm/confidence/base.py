"""Abstract base class for confidence extraction."""

from abc import ABC, abstractmethod
from typing import List, Any


class ConfidenceExtractor(ABC):
    """Abstract base class for confidence extraction methods."""

    @abstractmethod
    def extract(self, outputs: Any) -> List[float]:
        """Extract confidence scores from model outputs.

        Args:
            outputs: Model outputs (format depends on extraction method)

        Returns:
            List of confidence scores (0.0 to 1.0)
        """
        pass
