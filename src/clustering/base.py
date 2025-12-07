"""Abstract base class for clustering algorithms."""

from abc import ABC, abstractmethod
import numpy as np


class Clusterer(ABC):
    """Abstract base class for clustering algorithms.

    All clusterers should inherit from this class and implement
    fit(), predict(), and optionally fit_predict() methods.
    """

    @abstractmethod
    def fit(self, X: np.ndarray) -> None:
        """Fit the clustering model on embeddings.

        Args:
            X: Embedding matrix of shape (n_samples, n_features)
        """
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels for embeddings.

        Args:
            X: Embedding matrix of shape (n_samples, n_features)

        Returns:
            Cluster labels array of shape (n_samples,)
        """
        pass

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit clustering model and predict labels in one step.

        Args:
            X: Embedding matrix of shape (n_samples, n_features)

        Returns:
            Cluster labels array of shape (n_samples,)
        """
        self.fit(X)
        return self.predict(X)

    @property
    @abstractmethod
    def n_clusters(self) -> int:
        """Return the number of clusters."""
        pass

    @property
    def labels_(self) -> np.ndarray:
        """Return cluster labels from last fit_predict call."""
        if not hasattr(self, "_labels"):
            raise RuntimeError(
                "Model must be fitted first. Call fit() or fit_predict()."
            )
        return self._labels
