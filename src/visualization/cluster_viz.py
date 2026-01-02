"""
Clustering visualization utilities
Functions for visualizing clusters, comparisons, and hierarchies
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from sklearn.manifold import TSNE
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_clustering_metrics_comparison(
    comparison_df: pd.DataFrame, figsize: Tuple[int, int] = (16, 10)
) -> plt.Figure:
    """
    Visualize comparison of clustering methods across multiple metrics

    Args:
        comparison_df: DataFrame from compare_clustering_methods()
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(2, 3, figsize=figsize)

    methods = comparison_df["method"].values

    # 1. Silhouette Score (higher is better)
    ax = axes[0, 0]
    bars = ax.barh(methods, comparison_df["silhouette"])
    ax.set_xlabel("Silhouette Score")
    ax.set_title("Silhouette Score (Higher is Better)", fontweight="bold")
    ax.axvline(0, color="k", linestyle="--", alpha=0.3)
    ax.grid(axis="x", alpha=0.3)
    # Color bars
    colors = plt.cm.RdYlGn(
        [
            (v - comparison_df["silhouette"].min())
            / (
                comparison_df["silhouette"].max()
                - comparison_df["silhouette"].min()
                + 1e-10
            )
            for v in comparison_df["silhouette"]
        ]
    )
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    # 2. Davies-Bouldin Score (lower is better)
    ax = axes[0, 1]
    bars = ax.barh(methods, comparison_df["davies_bouldin"])
    ax.set_xlabel("Davies-Bouldin Score")
    ax.set_title("Davies-Bouldin Score (Lower is Better)", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    # Color bars (reversed for "lower is better")
    colors = plt.cm.RdYlGn_r(
        [
            (v - comparison_df["davies_bouldin"].min())
            / (
                comparison_df["davies_bouldin"].max()
                - comparison_df["davies_bouldin"].min()
                + 1e-10
            )
            for v in comparison_df["davies_bouldin"]
        ]
    )
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    # 3. Calinski-Harabasz Score (higher is better)
    ax = axes[0, 2]
    bars = ax.barh(methods, comparison_df["calinski_harabasz"])
    ax.set_xlabel("Calinski-Harabasz Score")
    ax.set_title("Calinski-Harabasz Score (Higher is Better)", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    colors = plt.cm.RdYlGn(
        [
            (v - comparison_df["calinski_harabasz"].min())
            / (
                comparison_df["calinski_harabasz"].max()
                - comparison_df["calinski_harabasz"].min()
                + 1e-10
            )
            for v in comparison_df["calinski_harabasz"]
        ]
    )
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    # 4. Number of Clusters
    ax = axes[1, 0]
    bars = ax.barh(methods, comparison_df["n_clusters"])
    ax.set_xlabel("Number of Clusters")
    ax.set_title("Number of Clusters Found", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    for bar in bars:
        bar.set_color("steelblue")

    # 5. Noise Percentage
    ax = axes[1, 1]
    bars = ax.barh(methods, comparison_df["noise_pct"])
    ax.set_xlabel("Noise Percentage (%)")
    ax.set_title("Percentage of Noise Points", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    colors = plt.cm.YlOrRd(
        comparison_df["noise_pct"] / (comparison_df["noise_pct"].max() + 1e-10)
    )
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    # 6. Cluster Size Statistics
    ax = axes[1, 2]
    x = np.arange(len(methods))
    width = 0.25
    ax.bar(x - width, comparison_df["min_cluster_size"], width, label="Min", alpha=0.8)
    ax.bar(x, comparison_df["avg_cluster_size"], width, label="Avg", alpha=0.8)
    ax.bar(x + width, comparison_df["max_cluster_size"], width, label="Max", alpha=0.8)
    ax.set_ylabel("Cluster Size")
    ax.set_title("Cluster Size Distribution", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_optimal_k_analysis(
    results: Dict, figsize: Tuple[int, int] = (15, 5)
) -> plt.Figure:
    """
    Plot metrics for finding optimal k in K-Means

    Args:
        results: Dict from find_optimal_k_kmeans()
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    k_values = results["k_values"]

    # 1. Silhouette Score
    ax = axes[0]
    ax.plot(k_values, results["silhouette_scores"], "o-", linewidth=2, markersize=8)
    optimal_k = results["optimal_k"]["silhouette"]
    ax.axvline(
        optimal_k, color="r", linestyle="--", alpha=0.7, label=f"Optimal k={optimal_k}"
    )
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Silhouette Score (Higher is Better)", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Davies-Bouldin Score
    ax = axes[1]
    ax.plot(
        k_values,
        results["davies_bouldin_scores"],
        "o-",
        linewidth=2,
        markersize=8,
        color="orange",
    )
    optimal_k = results["optimal_k"]["davies_bouldin"]
    ax.axvline(
        optimal_k, color="r", linestyle="--", alpha=0.7, label=f"Optimal k={optimal_k}"
    )
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Davies-Bouldin Score")
    ax.set_title("Davies-Bouldin Score (Lower is Better)", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Calinski-Harabasz Score
    ax = axes[2]
    ax.plot(
        k_values,
        results["calinski_harabasz_scores"],
        "o-",
        linewidth=2,
        markersize=8,
        color="green",
    )
    optimal_k = results["optimal_k"]["calinski_harabasz"]
    ax.axvline(
        optimal_k, color="r", linestyle="--", alpha=0.7, label=f"Optimal k={optimal_k}"
    )
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Calinski-Harabasz Score")
    ax.set_title("Calinski-Harabasz Score (Higher is Better)", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_clusters_2d(
    embeddings_2d: np.ndarray,
    labels: np.ndarray,
    title: str = "Cluster Visualization",
    method_name: str = "t-SNE",
    color_map: Optional[Dict] = None,
    label_names: Optional[Dict] = None,
    figsize: Tuple[int, int] = (12, 8),
) -> plt.Figure:
    """
    Plot 2D cluster visualization

    Args:
        embeddings_2d: 2D embeddings [n_samples, 2]
        labels: Cluster labels
        title: Plot title
        method_name: Dimensionality reduction method name
        color_map: Optional dict mapping cluster IDs to colors
        label_names: Optional dict mapping cluster IDs to names
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    unique_labels = sorted(set(labels))

    # Generate colors if not provided
    if color_map is None:
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))
        color_map = {label: colors[i] for i, label in enumerate(unique_labels)}

    # Plot each cluster
    for label in unique_labels:
        mask = labels == label

        if label == -1:
            # Noise points
            ax.scatter(
                embeddings_2d[mask, 0],
                embeddings_2d[mask, 1],
                c="gray",
                s=20,
                alpha=0.3,
                label="Noise",
                marker="x",
            )
        else:
            label_name = (
                label_names.get(label, f"Cluster {label}")
                if label_names
                else f"Cluster {label}"
            )
            ax.scatter(
                embeddings_2d[mask, 0],
                embeddings_2d[mask, 1],
                c=[color_map[label]],
                s=50,
                alpha=0.6,
                label=label_name,
            )

    ax.set_xlabel(f"{method_name} Dimension 1")
    ax.set_ylabel(f"{method_name} Dimension 2")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_clusters_3d_interactive(
    embeddings_3d: np.ndarray,
    labels: np.ndarray,
    df: pd.DataFrame,
    title: str = "3D Cluster Visualization",
    color_by: Optional[str] = None,
    hover_cols: Optional[List[str]] = None,
) -> go.Figure:
    """
    Create interactive 3D scatter plot of clusters

    Args:
        embeddings_3d: 3D embeddings [n_samples, 3]
        labels: Cluster labels
        df: DataFrame with entity data
        title: Plot title
        color_by: Optional column name to color by (default: cluster labels)
        hover_cols: Optional list of columns to show in hover

    Returns:
        Plotly figure
    """
    if color_by is None:
        color_values = labels
        color_label = "Cluster"
    else:
        color_values = df[color_by].values
        color_label = color_by

    # Prepare hover text
    if hover_cols:
        hover_text = []
        for idx in range(len(df)):
            text = "<br>".join([f"{col}: {df.iloc[idx][col]}" for col in hover_cols])
            hover_text.append(text)
    else:
        hover_text = [f"Cluster: {label}" for label in labels]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=embeddings_3d[:, 0],
                y=embeddings_3d[:, 1],
                z=embeddings_3d[:, 2],
                mode="markers",
                marker=dict(
                    size=4,
                    color=color_values,
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title=color_label),
                    opacity=0.7,
                ),
                text=hover_text,
                hovertemplate="%{text}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="Dimension 1",
            yaxis_title="Dimension 2",
            zaxis_title="Dimension 3",
        ),
        height=700,
    )

    return fig


def plot_cluster_composition(
    labels: np.ndarray,
    df: pd.DataFrame,
    grouping_var: str,
    top_n: int = 10,
    figsize: Tuple[int, int] = (14, 8),
) -> plt.Figure:
    """
    Plot composition of clusters by a grouping variable (e.g., culture, country)

    Args:
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_var: Column name to group by
        top_n: Show top N values of grouping variable
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    # Get top N values of grouping variable
    top_values = df[grouping_var].value_counts().head(top_n).index

    # Create composition matrix
    unique_clusters = sorted([l for l in set(labels) if l != -1])
    composition_data = []

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_df = df[mask]

        row = []
        for value in top_values:
            count = (cluster_df[grouping_var] == value).sum()
            row.append(count)
        composition_data.append(row)

    composition_matrix = np.array(composition_data)

    # Normalize by row (cluster)
    composition_pct = (
        composition_matrix
        / (composition_matrix.sum(axis=1, keepdims=True) + 1e-10)
        * 100
    )

    # Create stacked bar plot
    fig, ax = plt.subplots(figsize=figsize)

    x = np.arange(len(unique_clusters))
    width = 0.8

    bottom = np.zeros(len(unique_clusters))
    colors = plt.cm.tab20(np.linspace(0, 1, len(top_values)))

    for i, value in enumerate(top_values):
        ax.bar(
            x, composition_pct[:, i], width, bottom=bottom, label=value, color=colors[i]
        )
        bottom += composition_pct[:, i]

    ax.set_ylabel("Percentage (%)")
    ax.set_xlabel("Cluster")
    ax.set_title(
        f"Cluster Composition by {grouping_var}", fontsize=14, fontweight="bold"
    )
    ax.set_xticks(x)
    ax.set_xticklabels([f"C{c}" for c in unique_clusters])
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title=grouping_var)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_hierarchy_purity_analysis(
    hierarchy_results: Dict, figsize: Tuple[int, int] = (14, 6)
) -> plt.Figure:
    """
    Plot purity and entropy analysis for hierarchical clustering

    Args:
        hierarchy_results: Dict from analyze_cluster_hierarchy()
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    grouping_vars = list(hierarchy_results["purity_scores"].keys())

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # 1. Purity scores
    ax = axes[0]
    purity_means = [
        hierarchy_results["purity_scores"][var]["mean"] for var in grouping_vars
    ]
    purity_stds = [
        hierarchy_results["purity_scores"][var]["std"] for var in grouping_vars
    ]

    x = np.arange(len(grouping_vars))
    bars = ax.bar(x, purity_means, yerr=purity_stds, capsize=5, alpha=0.7)
    ax.set_ylabel("Mean Purity Score")
    ax.set_title(
        "Cluster Purity by Grouping Variable\n(Higher = More Homogeneous)",
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(grouping_vars)
    ax.set_ylim([0, 1])
    ax.grid(axis="y", alpha=0.3)

    # Color bars
    colors = plt.cm.RdYlGn([v for v in purity_means])
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    # 2. Entropy scores
    ax = axes[1]
    entropy_means = [
        hierarchy_results["entropy_scores"][var]["mean"] for var in grouping_vars
    ]
    entropy_stds = [
        hierarchy_results["entropy_scores"][var]["std"] for var in grouping_vars
    ]

    bars = ax.bar(x, entropy_means, yerr=entropy_stds, capsize=5, alpha=0.7)
    ax.set_ylabel("Mean Entropy")
    ax.set_title(
        "Cluster Entropy by Grouping Variable\n(Lower = More Homogeneous)",
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(grouping_vars)
    ax.grid(axis="y", alpha=0.3)

    # Color bars (reversed for entropy)
    max_entropy = max(entropy_means) if entropy_means else 1
    colors = plt.cm.RdYlGn_r([v / (max_entropy + 1e-10) for v in entropy_means])
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    plt.tight_layout()
    return fig


def plot_keyword_wordcloud(
    keywords_by_cluster: Dict[int, List[str]],
    cluster_id: int,
    figsize: Tuple[int, int] = (10, 6),
) -> plt.Figure:
    """
    Create word cloud visualization for cluster keywords

    Args:
        keywords_by_cluster: Dict from extract_tfidf_keywords()
        cluster_id: Cluster ID to visualize
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    try:
        from wordcloud import WordCloud
    except ImportError:
        # Fallback: simple bar chart
        fig, ax = plt.subplots(figsize=figsize)
        keywords = keywords_by_cluster.get(cluster_id, [])
        if keywords:
            ax.barh(range(len(keywords)), [1] * len(keywords))
            ax.set_yticks(range(len(keywords)))
            ax.set_yticklabels(keywords)
            ax.set_xlabel("Keyword Rank")
            ax.set_title(f"Top Keywords for Cluster {cluster_id}", fontweight="bold")
        return fig

    keywords = keywords_by_cluster.get(cluster_id, [])

    if not keywords or keywords[0] in ["insufficient_documents", "no_keywords_found"]:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(
            0.5,
            0.5,
            f"No keywords available for Cluster {cluster_id}",
            ha="center",
            va="center",
            fontsize=14,
        )
        ax.axis("off")
        return fig

    # Create word frequency dict (decreasing weights)
    word_freq = {word: len(keywords) - i for i, word in enumerate(keywords)}

    # Generate word cloud
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        colormap="viridis",
        relative_scaling=0.5,
    ).generate_from_frequencies(word_freq)

    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(
        f"Top Keywords for Cluster {cluster_id}", fontsize=14, fontweight="bold"
    )

    return fig
