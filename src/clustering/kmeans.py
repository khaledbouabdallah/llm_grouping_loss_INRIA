"""K-Means clustering using scikit-learn."""

from typing import Optional
import numpy as np
from sklearn.cluster import KMeans
from .base import Clusterer


class KMeansClusterer(Clusterer):
    """K-Means clustering using sklearn.

    Wrapper around sklearn's KMeans that conforms to our Clusterer interface.

    Args:
        n_clusters: Number of clusters to form
        random_state: Random state for reproducibility
        n_init: Number of times to run with different centroid seeds
        max_iter: Maximum number of iterations
        **kwargs: Additional arguments passed to sklearn KMeans

    Example:
        >>> clusterer = KMeansClusterer(n_clusters=10, random_state=42)
        >>> labels = clusterer.fit_predict(embeddings)
    """

    def __init__(
        self,
        n_clusters: int = 8,
        random_state: Optional[int] = 42,
        n_init: int = 10,
        max_iter: int = 300,
        **kwargs,
    ):
        self._n_clusters = n_clusters

        # Initialize sklearn KMeans
        self.model = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=n_init,
            max_iter=max_iter,
            **kwargs,
        )

        self._is_fitted = False
        self._labels: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> None:
        """Fit K-Means on embeddings.

        Args:
            X: Embedding matrix of shape (n_samples, n_features)
        """
        self.model.fit(X)
        self._labels = self.model.labels_
        self._is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels for embeddings.

        Args:
            X: Embedding matrix of shape (n_samples, n_features)

        Returns:
            Cluster labels array of shape (n_samples,)
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before predict. Call fit() first.")

        return self.model.predict(X)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and predict in one step.

        Args:
            X: Embedding matrix of shape (n_samples, n_features)

        Returns:
            Cluster labels array of shape (n_samples,)
        """
        labels = self.model.fit_predict(X)
        self._labels = labels
        self._is_fitted = True
        return labels

    @property
    def n_clusters(self) -> int:
        """Return the number of clusters."""
        return self._n_clusters

    @property
    def cluster_centers_(self) -> np.ndarray:
        """Return cluster centroids.

        Returns:
            Cluster centers array of shape (n_clusters, n_features)
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted first")

        return self.model.cluster_centers_

    @property
    def inertia_(self) -> float:
        """Return sum of squared distances to closest cluster center."""
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted first")

        return self.model.inertia_
