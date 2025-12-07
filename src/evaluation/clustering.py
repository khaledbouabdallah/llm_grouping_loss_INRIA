"""Clustering evaluation metrics using scikit-learn."""

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    silhouette_samples,
)


@dataclass
class ClusteringMetrics:
    """Container for clustering evaluation metrics.

    Attributes:
        silhouette: Silhouette coefficient (-1 to 1, higher is better)
        davies_bouldin: Davies-Bouldin index (lower is better)
        calinski_harabasz: Calinski-Harabasz index (higher is better)
        n_clusters: Number of clusters
        cluster_sizes: Dictionary mapping cluster_id to size
    """

    silhouette: float
    davies_bouldin: float
    calinski_harabasz: float
    n_clusters: int
    cluster_sizes: Dict[int, int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "silhouette_score": self.silhouette,
            "davies_bouldin_score": self.davies_bouldin,
            "calinski_harabasz_score": self.calinski_harabasz,
            "n_clusters": self.n_clusters,
            "cluster_sizes": self.cluster_sizes,
        }

    def __str__(self) -> str:
        """String representation of metrics."""
        return (
            f"Clustering Metrics (n_clusters={self.n_clusters}):\n"
            f"  Silhouette Score:        {self.silhouette:.4f} (higher is better)\n"
            f"  Davies-Bouldin Score:    {self.davies_bouldin:.4f} (lower is better)\n"
            f"  Calinski-Harabasz Score: {self.calinski_harabasz:.2f} (higher is better)"
        )


def evaluate_clustering(
    embeddings: np.ndarray, labels: np.ndarray, metric: str = "euclidean"
) -> ClusteringMetrics:
    """Evaluate clustering quality using sklearn metrics.

    Computes three standard clustering evaluation metrics:
    - Silhouette Score: Measures how similar objects are to their own cluster
                       compared to other clusters (-1 to 1, higher is better)
    - Davies-Bouldin Index: Average similarity ratio of each cluster with its
                            most similar cluster (lower is better)
    - Calinski-Harabasz Score: Ratio of between-cluster to within-cluster
                               dispersion (higher is better)

    Args:
        embeddings: Embedding matrix of shape (n_samples, n_features)
        labels: Cluster labels array of shape (n_samples,)
        metric: Distance metric to use (for silhouette score)

    Returns:
        ClusteringMetrics object containing all metrics

    Example:
        >>> metrics = evaluate_clustering(embeddings, labels)
        >>> print(metrics)
        >>> print(f"Silhouette: {metrics.silhouette:.3f}")
    """
    # Validate inputs
    if len(embeddings) != len(labels):
        raise ValueError("Embeddings and labels must have same length")

    n_clusters = len(np.unique(labels))

    # Compute cluster sizes
    unique_labels, counts = np.unique(labels, return_counts=True)
    cluster_sizes = dict(zip(unique_labels.tolist(), counts.tolist()))

    # Compute metrics using sklearn
    silhouette = silhouette_score(embeddings, labels, metric=metric)
    davies_bouldin = davies_bouldin_score(embeddings, labels)
    calinski_harabasz = calinski_harabasz_score(embeddings, labels)

    return ClusteringMetrics(
        silhouette=silhouette,
        davies_bouldin=davies_bouldin,
        calinski_harabasz=calinski_harabasz,
        n_clusters=n_clusters,
        cluster_sizes=cluster_sizes,
    )


def silhouette_per_cluster(
    embeddings: np.ndarray, labels: np.ndarray, metric: str = "euclidean"
) -> Dict[int, float]:
    """Compute average silhouette score per cluster.

    Args:
        embeddings: Embedding matrix
        labels: Cluster labels
        metric: Distance metric

    Returns:
        Dictionary mapping cluster_id to average silhouette score
    """
    # Compute silhouette for each sample (sklearn)
    sample_silhouette = silhouette_samples(embeddings, labels, metric=metric)

    # Average per cluster
    cluster_silhouette = {}
    for cluster_id in np.unique(labels):
        cluster_mask = labels == cluster_id
        cluster_silhouette[int(cluster_id)] = float(
            sample_silhouette[cluster_mask].mean()
        )

    return cluster_silhouette
