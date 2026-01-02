"""
Visualization utilities
Reusable plotting functions for calibration, clusters, embeddings
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
from matplotlib.patches import Patch


def plot_calibration_curve(
    calibration_info: Dict,
    title: str = "Calibration Curve",
    ax: Optional[plt.Axes] = None,
    show_ece: bool = True,
):
    """
    Plot calibration curve

    Args:
        calibration_info: Dict from calculate_binned_calibration()
        title: Plot title
        ax: Matplotlib axes (creates new if None)
        show_ece: Show ECE in title
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))

    bins = calibration_info["bin_info"]["bins"]

    # Extract bin data
    confidences = []
    accuracies = []
    sizes = []

    for bin_data in bins:
        if bin_data["size"] > 0:
            confidences.append(bin_data["avg_confidence"])
            accuracies.append(bin_data["accuracy"])
            sizes.append(bin_data["size"])

    # Plot perfect calibration line
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3, label="Perfect calibration")

    # Plot calibration curve with bin sizes
    sizes_normalized = np.array(sizes) / max(sizes) * 200  # Scale for visibility
    ax.scatter(
        confidences,
        accuracies,
        s=sizes_normalized,
        alpha=0.6,
        label="Model calibration",
    )

    ax.set_xlabel("Confidence")
    ax.set_ylabel("Accuracy")
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.grid(alpha=0.3)
    ax.legend()

    # Add ECE to title
    if show_ece:
        ece = calibration_info["ece"]
        title = f"{title} (ECE: {ece:.4f})"

    ax.set_title(title)

    return ax


def plot_calibration_comparison(
    calibrations: Dict[str, Dict], title: str = "Calibration Comparison"
):
    """
    Plot multiple calibration curves for comparison

    Args:
        calibrations: Dict mapping labels to calibration info
        title: Plot title
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Perfect calibration
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3, label="Perfect calibration")

    # Plot each calibration
    colors = plt.cm.tab10(np.linspace(0, 1, len(calibrations)))

    for (label, calib_info), color in zip(calibrations.items(), colors):
        bins = calib_info["bin_info"]["bins"]

        confidences = []
        accuracies = []

        for bin_data in bins:
            if bin_data["size"] > 0:
                confidences.append(bin_data["avg_confidence"])
                accuracies.append(bin_data["accuracy"])

        ece = calib_info["ece"]
        ax.plot(
            confidences,
            accuracies,
            marker="o",
            color=color,
            label=f"{label} (ECE: {ece:.4f})",
        )

    ax.set_xlabel("Confidence")
    ax.set_ylabel("Accuracy")
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.grid(alpha=0.3)
    ax.legend()
    ax.set_title(title)

    return fig, ax


def plot_confidence_distribution(
    results: List[Dict],
    group_by: Optional[str] = None,
    title: str = "Confidence Distribution",
):
    """
    Plot confidence distribution

    Args:
        results: List of evaluation results
        group_by: Optional attribute to group by
        title: Plot title
    """
    if group_by:
        # Group results
        groups = {}
        for r in results:
            key = r.get(group_by, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(r["confidence"])

        # Plot distributions
        fig, axes = plt.subplots(1, len(groups), figsize=(5 * len(groups), 4))
        if len(groups) == 1:
            axes = [axes]

        for ax, (label, confidences) in zip(axes, groups.items()):
            ax.hist(confidences, bins=20, alpha=0.7, edgecolor="black")
            ax.set_xlabel("Confidence")
            ax.set_ylabel("Count")
            ax.set_title(f"{label}\n(n={len(confidences)})")
            ax.axvline(
                np.mean(confidences),
                color="r",
                linestyle="--",
                label=f"Mean: {np.mean(confidences):.3f}",
            )
            ax.legend()

        fig.suptitle(title)
        plt.tight_layout()

    else:
        # Single distribution
        fig, ax = plt.subplots(figsize=(8, 5))
        confidences = [r["confidence"] for r in results]

        ax.hist(confidences, bins=20, alpha=0.7, edgecolor="black")
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Count")
        ax.axvline(
            np.mean(confidences),
            color="r",
            linestyle="--",
            label=f"Mean: {np.mean(confidences):.3f}",
        )
        ax.legend()
        ax.set_title(title)

    return fig


def plot_embedding_space(
    embeddings_2d: np.ndarray,
    labels: Optional[np.ndarray] = None,
    colors: Optional[List[str]] = None,
    title: str = "Embedding Space",
    legend_labels: Optional[List[str]] = None,
):
    """
    Plot 2D embedding space

    Args:
        embeddings_2d: 2D embeddings [N, 2]
        labels: Optional labels for coloring [N]
        colors: Optional colors for each point
        title: Plot title
        legend_labels: Optional legend labels
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    if labels is not None:
        unique_labels = np.unique(labels)
        palette = sns.color_palette("tab10", len(unique_labels))

        for i, label in enumerate(unique_labels):
            mask = labels == label
            label_name = legend_labels[i] if legend_labels else f"Group {label}"
            ax.scatter(
                embeddings_2d[mask, 0],
                embeddings_2d[mask, 1],
                c=[palette[i]],
                label=label_name,
                alpha=0.6,
                s=50,
            )

        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    else:
        ax.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], alpha=0.6, s=50)

    ax.set_xlabel("Dimension 1")
    ax.set_ylabel("Dimension 2")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    plt.tight_layout()

    return fig, ax


def plot_cluster_distribution(
    cluster_labels: np.ndarray,
    title: str = "Cluster Distribution",
    show_noise: bool = True,
):
    """
    Plot cluster size distribution

    Args:
        cluster_labels: Cluster labels [N]
        title: Plot title
        show_noise: Show noise points (-1) separately
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    unique_labels, counts = np.unique(cluster_labels, return_counts=True)

    # Separate noise if present
    if show_noise and -1 in unique_labels:
        noise_idx = np.where(unique_labels == -1)[0][0]
        noise_count = counts[noise_idx]

        # Remove noise from regular clusters
        regular_labels = np.delete(unique_labels, noise_idx)
        regular_counts = np.delete(counts, noise_idx)

        # Plot regular clusters
        bars = ax.bar(
            range(len(regular_labels)),
            regular_counts,
            color="steelblue",
            alpha=0.7,
            label="Clusters",
        )

        # Add noise bar
        ax.bar(
            len(regular_labels),
            noise_count,
            color="gray",
            alpha=0.7,
            label="Noise",
        )

        # Labels
        labels_list = [str(l) for l in regular_labels] + ["Noise"]
        ax.set_xticks(range(len(labels_list)))
        ax.set_xticklabels(labels_list)

    else:
        bars = ax.bar(
            range(len(unique_labels)),
            counts,
            color="steelblue",
            alpha=0.7,
        )
        ax.set_xticks(range(len(unique_labels)))
        ax.set_xticklabels([str(l) for l in unique_labels])

    ax.set_xlabel("Cluster")
    ax.set_ylabel("Number of Points")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)

    if show_noise and -1 in unique_labels:
        ax.legend()

    # Add count labels on bars
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
    return fig, ax


def plot_grouping_loss_comparison(
    grouping_losses: Dict[str, Dict],
    title: str = "Grouping Loss Comparison",
):
    """
    Plot grouping loss comparison across groups

    Args:
        grouping_losses: Dict mapping method names to grouping loss results
        title: Plot title
    """
    fig, axes = plt.subplots(
        1, len(grouping_losses), figsize=(6 * len(grouping_losses), 5)
    )
    if len(grouping_losses) == 1:
        axes = [axes]

    for ax, (method, loss_info) in zip(axes, grouping_losses.items()):
        if "group_accuracies" in loss_info:
            # Bar plot of group accuracies
            groups = list(loss_info["group_accuracies"].keys())
            values = list(loss_info["group_accuracies"].values())

            bars = ax.bar(range(len(groups)), values, alpha=0.7)
            ax.set_xticks(range(len(groups)))
            ax.set_xticklabels(groups, rotation=45, ha="right")
            ax.set_ylabel("Accuracy")
            ax.set_ylim([0, 1])
            ax.axhline(np.mean(values), color="r", linestyle="--", label="Mean")
            ax.set_title(f"{method}\nLoss: {loss_info['loss']:.4f}")
            ax.legend()
            ax.grid(axis="y", alpha=0.3)

        elif "group_eces" in loss_info:
            # Bar plot of group ECEs
            groups = list(loss_info["group_eces"].keys())
            values = list(loss_info["group_eces"].values())

            bars = ax.bar(range(len(groups)), values, alpha=0.7)
            ax.set_xticks(range(len(groups)))
            ax.set_xticklabels(groups, rotation=45, ha="right")
            ax.set_ylabel("ECE")
            ax.axhline(np.mean(values), color="r", linestyle="--", label="Mean")
            ax.set_title(f"{method}\nLoss: {loss_info['loss']:.4f}")
            ax.legend()
            ax.grid(axis="y", alpha=0.3)

    fig.suptitle(title, y=1.02)
    plt.tight_layout()
    return fig, axes
