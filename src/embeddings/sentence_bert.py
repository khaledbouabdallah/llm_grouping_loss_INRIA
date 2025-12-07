"""Sentence-BERT embedder for semantic embeddings."""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from .base import Embedder


class SBertEmbedder(Embedder):
    """Sentence-BERT embedder for semantic text embeddings.

    Uses pre-trained sentence transformers models to generate
    dense semantic embeddings.

    Args:
        model_name: Name of sentence-transformers model
                   (e.g., 'all-MiniLM-L6-v2', 'paraphrase-multilingual-MiniLM-L12-v2')
        device: Device to use ('cuda' or 'cpu')
        batch_size: Batch size for encoding

    Example:
        >>> embedder = SBertEmbedder(model_name='all-MiniLM-L6-v2')
        >>> embeddings = embedder.fit_transform(texts)
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size

        # Load model
        self.model = SentenceTransformer(model_name, device=device)
        self._is_fitted = True  # Pre-trained model is already "fitted"

    def fit(self, texts: List[str]) -> None:
        """No-op for pre-trained model.

        Sentence transformers are pre-trained and don't need fitting,
        but we implement this method to comply with the interface.

        Args:
            texts: List of text documents (unused)
        """
        # Pre-trained model doesn't need fitting
        pass

    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform texts to sentence embeddings.

        Args:
            texts: List of text documents

        Returns:
            Embedding matrix of shape (n_texts, embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings

    @property
    def embedding_dim(self) -> int:
        """Return embedding dimensionality."""
        return self.model.get_sentence_embedding_dimension()
