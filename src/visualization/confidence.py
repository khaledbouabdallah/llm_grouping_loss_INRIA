"""Confidence visualization functions."""

from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plot_confidence_distribution(
    confidences: np.ndarray,
    figsize: tuple = (10, 6),
    title: str = "Confidence Score Distribution",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot overall confidence distribution.

    Args:
        confidences: Array of confidence scores
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Histogram
    axes[0].hist(confidences, bins=30, color="steelblue", alpha=0.7, edgecolor="black")
    axes[0].axvline(
        confidences.mean(),
        color="red",
        linestyle="--",
        label=f"Mean: {confidences.mean():.3f}",
    )
    axes[0].axvline(
        np.median(confidences),
        color="green",
        linestyle="--",
        label=f"Median: {np.median(confidences):.3f}",
    )
    axes[0].set_xlabel("Confidence Score")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Histogram")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Box plot
    axes[1].boxplot(confidences, vert=True)
    axes[1].set_ylabel("Confidence Score")
    axes[1].set_title("Box Plot")
    axes[1].grid(True, alpha=0.3, axis="y")

    fig.suptitle(title, fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_confidence_by_cluster(
    confidences: np.ndarray,
    labels: np.ndarray,
    figsize: tuple = (12, 6),
    title: str = "Confidence Scores by Cluster",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot confidence distribution per cluster.

    Args:
        confidences: Array of confidence scores
        labels: Cluster labels
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    # Prepare data
    df = pd.DataFrame({"confidence": confidences, "cluster": labels})

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Box plot
    sns.boxplot(data=df, x="cluster", y="confidence", ax=axes[0])
    axes[0].set_xlabel("Cluster ID")
    axes[0].set_ylabel("Confidence Score")
    axes[0].set_title("Box Plot by Cluster")
    axes[0].grid(True, alpha=0.3, axis="y")

    # Violin plot
    sns.violinplot(data=df, x="cluster", y="confidence", ax=axes[1])
    axes[1].set_xlabel("Cluster ID")
    axes[1].set_ylabel("Confidence Score")
    axes[1].set_title("Violin Plot by Cluster")
    axes[1].grid(True, alpha=0.3, axis="y")

    fig.suptitle(title, fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig
