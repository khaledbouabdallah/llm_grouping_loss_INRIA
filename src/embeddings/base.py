"""Abstract base class for text embedders."""

from abc import ABC, abstractmethod
from typing import List
import numpy as np


class Embedder(ABC):
    """Abstract base class for text embedding models.

    All embedders should inherit from this class and implement
    fit(), transform(), and optionally fit_transform() methods.
    """

    @abstractmethod
    def fit(self, texts: List[str]) -> None:
        """Fit the embedder on a corpus of texts.

        Args:
            texts: List of text documents
        """
        pass

    @abstractmethod
    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform texts to embeddings.

        Args:
            texts: List of text documents

        Returns:
            Embedding matrix of shape (n_texts, embedding_dim)
        """
        pass

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """Fit embedder and transform texts in one step.

        Args:
            texts: List of text documents

        Returns:
            Embedding matrix of shape (n_texts, embedding_dim)
        """
        self.fit(texts)
        return self.transform(texts)

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Return the dimensionality of the embeddings."""
        pass
