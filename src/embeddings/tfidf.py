"""TF-IDF embedder using scikit-learn."""

from typing import List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from .base import Embedder


class TfidfEmbedder(Embedder):
    """TF-IDF text embedder using sklearn.

    This embedder uses TfidfVectorizer from scikit-learn to convert
    texts to TF-IDF representations, optionally reducing dimensionality
    with TruncatedSVD (LSA).

    Args:
        max_features: Maximum number of features (vocabulary size)
        ngram_range: Range of n-grams to extract (e.g., (1, 2) for unigrams and bigrams)
        min_df: Minimum document frequency (int or float)
        max_df: Maximum document frequency (int or float)
        use_svd: Whether to apply dimensionality reduction with SVD
        n_components: Number of SVD components (only if use_svd=True)
        **kwargs: Additional arguments passed to TfidfVectorizer

    Example:
        >>> embedder = TfidfEmbedder(max_features=500, ngram_range=(1, 2))
        >>> embeddings = embedder.fit_transform(texts)
    """

    def __init__(
        self,
        max_features: int = 1000,
        ngram_range: Tuple[int, int] = (1, 1),
        min_df: int | float = 1,
        max_df: int | float = 1.0,
        use_svd: bool = False,
        n_components: int = 100,
        **kwargs,
    ):
        self.max_features = max_features
        # Convert list to tuple if needed (YAML parsing compatibility)
        self.ngram_range = (
            tuple(ngram_range) if isinstance(ngram_range, list) else ngram_range
        )
        self.min_df = min_df
        self.max_df = max_df
        self.use_svd = use_svd
        self.n_components = n_components

        # Initialize TF-IDF vectorizer (sklearn)
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=self.ngram_range,
            min_df=min_df,
            max_df=max_df,
            **kwargs,
        )

        # Optional SVD for dimensionality reduction (sklearn)
        self.svd: Optional[TruncatedSVD] = None
        if use_svd:
            self.svd = TruncatedSVD(n_components=n_components, random_state=42)

        self._is_fitted = False

    def fit(self, texts: List[str]) -> None:
        """Fit TF-IDF vectorizer on texts.

        Args:
            texts: List of text documents
        """
        # Fit TF-IDF
        self.vectorizer.fit(texts)

        # Fit SVD if enabled
        if self.use_svd and self.svd is not None:
            tfidf_matrix = self.vectorizer.transform(texts)
            n_features = tfidf_matrix.shape[1]

            # Adjust n_components if it exceeds n_features
            if self.n_components >= n_features:
                actual_components = n_features - 1
                self.svd = TruncatedSVD(n_components=actual_components, random_state=42)
                self.n_components = actual_components

            self.svd.fit(tfidf_matrix)

        self._is_fitted = True

    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform texts to TF-IDF embeddings.

        Args:
            texts: List of text documents

        Returns:
            Embedding matrix of shape (n_texts, embedding_dim)
        """
        if not self._is_fitted:
            raise RuntimeError(
                "Embedder must be fitted before transform. Call fit() first."
            )

        # Transform to TF-IDF
        tfidf_matrix = self.vectorizer.transform(texts)

        # Apply SVD if enabled
        if self.use_svd and self.svd is not None:
            embeddings = self.svd.transform(tfidf_matrix)
        else:
            embeddings = tfidf_matrix.toarray()

        return embeddings

    @property
    def embedding_dim(self) -> int:
        """Return embedding dimensionality."""
        if not self._is_fitted:
            raise RuntimeError("Embedder must be fitted first")

        if self.use_svd and self.svd is not None:
            return self.n_components
        else:
            return len(self.vectorizer.vocabulary_)

    def get_feature_names(self) -> List[str]:
        """Get feature names (vocabulary terms).

        Returns:
            List of feature names
        """
        if not self._is_fitted:
            raise RuntimeError("Embedder must be fitted first")

        return self.vectorizer.get_feature_names_out().tolist()
