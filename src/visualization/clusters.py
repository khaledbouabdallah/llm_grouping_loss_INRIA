"""Cluster visualization functions."""

from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


def plot_clusters(
    embeddings: np.ndarray,
    labels: np.ndarray,
    method: str = "pca",
    figsize: tuple = (10, 8),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Visualize clusters in 2D using dimensionality reduction.

    Args:
        embeddings: Embedding matrix
        labels: Cluster labels
        method: Reduction method ('pca' or 'tsne')
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    # Reduce to 2D
    if method == "pca":
        reducer = PCA(n_components=2, random_state=42)
        coords = reducer.fit_transform(embeddings)
        subtitle = (
            f"(PCA, explained variance: {reducer.explained_variance_ratio_.sum():.2%})"
        )
    elif method == "tsne":
        reducer = TSNE(n_components=2, random_state=42)
        coords = reducer.fit_transform(embeddings)
        subtitle = "(t-SNE)"
    else:
        raise ValueError(f"Unknown method: {method}")

    # Create plot
    fig, ax = plt.subplots(figsize=figsize)

    # Plot each cluster
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)
    colors = sns.color_palette("husl", n_clusters)

    for i, label in enumerate(unique_labels):
        mask = labels == label
        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            c=[colors[i]],
            label=f"Cluster {label} (n={mask.sum()})",
            alpha=0.6,
            s=50,
        )

    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")

    if title:
        ax.set_title(f"{title}\n{subtitle}")
    else:
        ax.set_title(f"Cluster Visualization {subtitle}")

    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_cluster_sizes(
    labels: np.ndarray,
    figsize: tuple = (10, 6),
    title: str = "Cluster Sizes",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot cluster size distribution.

    Args:
        labels: Cluster labels
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    unique_labels, counts = np.unique(labels, return_counts=True)

    fig, ax = plt.subplots(figsize=figsize)

    bars = ax.bar(
        unique_labels, counts, color=sns.color_palette("husl", len(unique_labels))
    )

    ax.set_xlabel("Cluster ID")
    ax.set_ylabel("Number of Samples")
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis="y")

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig
