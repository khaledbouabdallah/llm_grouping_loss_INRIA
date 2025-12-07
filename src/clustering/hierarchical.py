"""Hierarchical clustering using scikit-learn."""

from typing import Optional, Literal
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from .base import Clusterer


class HierarchicalClusterer(Clusterer):
    """Agglomerative Hierarchical clustering using sklearn.

    Wrapper around sklearn's AgglomerativeClustering that conforms to
    our Clusterer interface.

    Args:
        n_clusters: Number of clusters to form
        linkage: Linkage criterion ('ward', 'complete', 'average', 'single')
        metric: Distance metric (only for linkage other than 'ward')
        **kwargs: Additional arguments passed to sklearn AgglomerativeClustering

    Example:
        >>> clusterer = HierarchicalClusterer(n_clusters=10, linkage='ward')
        >>> labels = clusterer.fit_predict(embeddings)
    """

    def __init__(
        self,
        n_clusters: int = 8,
        linkage: Literal["ward", "complete", "average", "single"] = "ward",
        metric: str = "euclidean",
        **kwargs,
    ):
        self._n_clusters = n_clusters

        # For 'ward' linkage, metric must be 'euclidean'
        if linkage == "ward":
            metric = "euclidean"

        # Initialize sklearn AgglomerativeClustering
        self.model = AgglomerativeClustering(
            n_clusters=n_clusters, linkage=linkage, metric=metric, **kwargs
        )

        self._is_fitted = False
        self._labels: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> None:
        """Fit hierarchical clustering on embeddings.

        Args:
            X: Embedding matrix of shape (n_samples, n_features)
        """
        self.model.fit(X)
        self._labels = self.model.labels_
        self._is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels.

        Note: Hierarchical clustering doesn't support prediction on new data.
        This returns the labels from the last fit() call.

        Args:
            X: Embedding matrix (ignored, but kept for interface consistency)

        Returns:
            Cluster labels from last fit
        """
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before predict. Call fit() first.")

        if self._labels is None:
            raise RuntimeError("No labels available. Call fit() first.")

        # Hierarchical clustering doesn't support prediction on new samples
        # Return cached labels from training
        return self._labels

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
    def n_leaves_(self) -> int:
        """Return the number of leaves in the hierarchical tree."""
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted first")

        return self.model.n_leaves_

    @property
    def n_connected_components_(self) -> int:
        """Return the number of connected components."""
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted first")

        return self.model.n_connected_components_
