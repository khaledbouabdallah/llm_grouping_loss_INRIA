"""
Simple clustering method wrappers
K-Means, DBSCAN, HDBSCAN, Hierarchical clustering utilities
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple, List
import logging
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, HDBSCAN
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
    normalized_mutual_info_score,
)
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def cluster_kmeans(
    embeddings: np.ndarray, n_clusters: int = 8, random_state: int = 42
) -> np.ndarray:
    """
    K-Means clustering

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        n_clusters: Number of clusters
        random_state: Random seed

    Returns:
        Cluster labels [n_samples]
    """
    from sklearn.cluster import KMeans

    logger.info(f"K-Means clustering: {n_clusters} clusters")

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    logger.info(f"K-Means complete: {len(set(labels))} unique clusters")

    return labels


def cluster_dbscan(
    embeddings: np.ndarray, eps: float = 0.5, min_samples: int = 5
) -> np.ndarray:
    """
    DBSCAN clustering

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        eps: Maximum distance between samples
        min_samples: Minimum samples in neighborhood

    Returns:
        Cluster labels [n_samples] (-1 = noise)
    """

    logger.info(f"DBSCAN clustering: eps={eps}, min_samples={min_samples}")

    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
    labels = dbscan.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)

    logger.info(f"DBSCAN complete: {n_clusters} clusters, {n_noise} noise points")

    return labels


def cluster_hdbscan(
    embeddings: np.ndarray, min_cluster_size: int = 5, min_samples: int = 3
) -> np.ndarray:
    """
    HDBSCAN clustering

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        min_cluster_size: Minimum cluster size
        min_samples: Minimum samples parameter

    Returns:
        Cluster labels [n_samples] (-1 = noise)
    """

    logger.info(
        f"HDBSCAN clustering: min_cluster_size={min_cluster_size}, min_samples={min_samples}"
    )

    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)

    logger.info(f"HDBSCAN complete: {n_clusters} clusters, {n_noise} noise points")

    return labels


def cluster_hierarchical(
    embeddings: np.ndarray,
    n_clusters: int = 8,
    linkage: str = "ward",
    metric: str = "euclidean",
) -> np.ndarray:
    """
    Hierarchical clustering

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        n_clusters: Number of clusters
        linkage: Linkage method ('ward', 'complete', 'average', 'single')
        metric: Distance metric

    Returns:
        Cluster labels [n_samples]
    """
    from sklearn.cluster import AgglomerativeClustering

    logger.info(
        f"Hierarchical clustering: {n_clusters} clusters, linkage={linkage}, metric={metric}"
    )

    clusterer = AgglomerativeClustering(
        n_clusters=n_clusters, linkage=linkage, metric=metric
    )
    labels = clusterer.fit_predict(embeddings)

    logger.info(f"Hierarchical complete: {len(set(labels))} unique clusters")

    return labels


def get_cluster_labels(cluster_labels: np.ndarray) -> Dict:
    """
    Get summary statistics for cluster labels

    Args:
        cluster_labels: Array of cluster labels

    Returns:
        Dict with cluster statistics
    """
    unique_labels = set(cluster_labels)
    n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
    n_noise = list(cluster_labels).count(-1) if -1 in unique_labels else 0

    # Count per cluster
    cluster_counts = {}
    for label in unique_labels:
        if label != -1:
            cluster_counts[int(label)] = int(np.sum(cluster_labels == label))

    stats = {
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "cluster_counts": cluster_counts,
        "total_samples": len(cluster_labels),
    }

    return stats


def find_optimal_k_kmeans(
    embeddings: np.ndarray,
    k_range: range = range(2, 15),
    random_state: int = 42,
) -> Dict:
    """
    Find optimal number of clusters using silhouette score

    Args:
        embeddings: Input embeddings
        k_range: Range of k values to try
        random_state: Random seed

    Returns:
        Dict with scores for each k
    """
    logger.info(f"Finding optimal k in range {k_range}")

    results = {
        "k_values": [],
        "silhouette_scores": [],
        "davies_bouldin_scores": [],
        "calinski_harabasz_scores": [],
    }

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        # Silhouette score with cosine distance (higher is better, range [-1, 1])
        sil_score = silhouette_score(embeddings, labels, metric="cosine")

        # Davies-Bouldin score (lower is better, >= 0)
        db_score = davies_bouldin_score(embeddings, labels)

        # Calinski-Harabasz score (higher is better, >= 0)
        ch_score = calinski_harabasz_score(embeddings, labels)

        results["k_values"].append(k)
        results["silhouette_scores"].append(sil_score)
        results["davies_bouldin_scores"].append(db_score)
        results["calinski_harabasz_scores"].append(ch_score)

        logger.info(
            f"k={k}: silhouette={sil_score:.3f}, DB={db_score:.3f}, CH={ch_score:.1f}"
        )

    # Find optimal k
    best_k_sil = results["k_values"][np.argmax(results["silhouette_scores"])]
    best_k_db = results["k_values"][np.argmin(results["davies_bouldin_scores"])]
    best_k_ch = results["k_values"][np.argmax(results["calinski_harabasz_scores"])]

    results["optimal_k"] = {
        "silhouette": best_k_sil,
        "davies_bouldin": best_k_db,
        "calinski_harabasz": best_k_ch,
    }

    logger.info(f"Optimal k: silhouette={best_k_sil}, DB={best_k_db}, CH={best_k_ch}")

    return results


def compare_clustering_methods(
    embeddings: np.ndarray,
    labels_dict: Dict[str, np.ndarray],
    exclude_noise: bool = True,
) -> pd.DataFrame:
    """
    Compare multiple clustering methods using various metrics

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        labels_dict: Dict mapping method names to cluster labels
        exclude_noise: Whether to exclude noise points (-1) from metrics

    Returns:
        DataFrame with comparison metrics
    """
    logger.info(f"Comparing {len(labels_dict)} clustering methods")

    results = []

    for method_name, labels in labels_dict.items():
        # Handle noise points
        if exclude_noise and -1 in labels:
            mask = labels != -1
            eval_embeddings = embeddings[mask]
            eval_labels = labels[mask]
        else:
            eval_embeddings = embeddings
            eval_labels = labels

        # Skip if too few samples or clusters
        n_clusters = len(set(eval_labels)) - (1 if -1 in eval_labels else 0)
        if n_clusters < 2 or len(eval_embeddings) < 2:
            logger.warning(f"Skipping {method_name}: insufficient samples/clusters")
            continue

        # Calculate metrics with cosine distance
        sil_score = silhouette_score(eval_embeddings, eval_labels, metric="cosine")
        db_score = davies_bouldin_score(eval_embeddings, eval_labels)
        ch_score = calinski_harabasz_score(eval_embeddings, eval_labels)

        # Count noise points
        n_noise = int(np.sum(labels == -1)) if -1 in labels else 0
        n_total = len(labels)

        # Cluster size statistics
        cluster_sizes = [int(np.sum(labels == i)) for i in set(labels) if i != -1]

        results.append(
            {
                "method": method_name,
                "n_clusters": n_clusters,
                "n_noise": n_noise,
                "noise_pct": 100 * n_noise / n_total,
                "silhouette": sil_score,
                "davies_bouldin": db_score,
                "calinski_harabasz": ch_score,
                "min_cluster_size": min(cluster_sizes) if cluster_sizes else 0,
                "max_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
                "avg_cluster_size": np.mean(cluster_sizes) if cluster_sizes else 0,
                "std_cluster_size": np.std(cluster_sizes) if cluster_sizes else 0,
            }
        )

    df = pd.DataFrame(results)
    logger.info(f"Comparison complete for {len(df)} methods")

    return df


def analyze_hierarchical_dendrogram(
    embeddings: np.ndarray,
    method: str = "ward",
    metric: str = "euclidean",
    max_samples: int = 1000,
    figsize: Tuple[int, int] = (15, 7),
) -> Tuple[np.ndarray, plt.Figure]:
    """
    Create hierarchical clustering dendrogram

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        method: Linkage method ('ward', 'complete', 'average', 'single')
        metric: Distance metric
        max_samples: Maximum samples to include (for performance)
        figsize: Figure size

    Returns:
        linkage_matrix: Linkage matrix from scipy
        fig: Matplotlib figure
    """
    logger.info(f"Creating dendrogram: method={method}, metric={metric}")

    # Sample if too many points
    if len(embeddings) > max_samples:
        logger.info(f"Sampling {max_samples} points from {len(embeddings)}")
        indices = np.random.choice(len(embeddings), max_samples, replace=False)
        embeddings = embeddings[indices]

    # Compute linkage matrix
    if method == "ward":
        linkage_matrix = linkage(embeddings, method=method)
    else:
        linkage_matrix = linkage(pdist(embeddings, metric=metric), method=method)

    # Create dendrogram
    fig, ax = plt.subplots(figsize=figsize)
    dendrogram(linkage_matrix, ax=ax, no_labels=True)
    ax.set_title(
        f"Hierarchical Clustering Dendrogram ({method} linkage)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Distance")
    ax.grid(True, alpha=0.3)

    logger.info("Dendrogram created")

    return linkage_matrix, fig


def analyze_cluster_hierarchy(
    embeddings: np.ndarray,
    labels: np.ndarray,
    df: pd.DataFrame,
    grouping_vars: List[str],
    method: str = "ward",
) -> Dict:
    """
    Analyze how clusters split across grouping variables (e.g., culture, country)

    Args:
        embeddings: Input embeddings
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_vars: List of column names to analyze (e.g., ['culture', 'country'])
        method: Hierarchical clustering method

    Returns:
        Dict with hierarchy analysis results
    """
    logger.info(f"Analyzing cluster hierarchy for {grouping_vars}")

    results = {"cluster_compositions": {}, "purity_scores": {}, "entropy_scores": {}}

    # Analyze composition of each cluster
    for var in grouping_vars:
        cluster_compositions = {}
        purity_scores = []
        entropy_scores = []

        for cluster_id in sorted(set(labels)):
            if cluster_id == -1:  # Skip noise
                continue

            mask = labels == cluster_id
            cluster_values = df[mask][var].value_counts()

            # Store composition
            cluster_compositions[int(cluster_id)] = cluster_values.to_dict()

            # Calculate purity (percentage of most common value)
            purity = (
                cluster_values.iloc[0] / cluster_values.sum()
                if len(cluster_values) > 0
                else 0
            )
            purity_scores.append(purity)

            # Calculate entropy
            probs = cluster_values / cluster_values.sum()
            entropy = -np.sum(probs * np.log2(probs + 1e-10))
            entropy_scores.append(entropy)

        results["cluster_compositions"][var] = cluster_compositions
        results["purity_scores"][var] = {
            "mean": float(np.mean(purity_scores)),
            "std": float(np.std(purity_scores)),
            "min": float(np.min(purity_scores)),
            "max": float(np.max(purity_scores)),
        }
        results["entropy_scores"][var] = {
            "mean": float(np.mean(entropy_scores)),
            "std": float(np.std(entropy_scores)),
            "min": float(np.min(entropy_scores)),
            "max": float(np.max(entropy_scores)),
        }

        logger.info(
            f"{var} - Mean purity: {results['purity_scores'][var]['mean']:.3f}, "
            f"Mean entropy: {results['entropy_scores'][var]['mean']:.3f}"
        )

    return results


def extract_tfidf_keywords(
    texts: List[str],
    labels: np.ndarray,
    n_keywords: int = 10,
    ngram_range: Tuple[int, int] = (1, 3),
    min_df: int = 2,
    max_df: float = 0.7,
    custom_stopwords: Optional[List[str]] = None,
) -> Dict[int, List[str]]:
    """
    Extract TF-IDF keywords for each cluster

    Args:
        texts: List of text documents
        labels: Cluster labels
        n_keywords: Number of keywords per cluster
        ngram_range: N-gram range (e.g., (1, 3) for unigrams to trigrams)
        min_df: Minimum document frequency
        max_df: Maximum document frequency
        custom_stopwords: Optional list of custom stopwords

    Returns:
        Dict mapping cluster IDs to keyword lists
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    logger.info(f"Extracting TF-IDF keywords for {len(set(labels))} clusters")

    # Default multilingual stopwords
    default_stopwords = [
        "the",
        "and",
        "of",
        "to",
        "in",
        "a",
        "is",
        "that",
        "for",
        "on",
        "with",
        "as",
        "le",
        "la",
        "les",
        "de",
        "et",
        "un",
        "une",
        "dans",
        "pour",
        "est",
        "sur",
        "في",
        "من",
        "إلى",
        "على",
        "هو",
        "هي",
        "أن",
        "ما",
        "كان",
        "لا",
    ]

    if custom_stopwords:
        stopwords = list(set(default_stopwords + custom_stopwords))
    else:
        stopwords = default_stopwords

    keywords_by_cluster = {}
    unique_labels = sorted(set(labels))

    for label in unique_labels:
        if label == -1:  # Skip noise
            continue

        # Get texts for this cluster
        cluster_texts = [texts[i] for i in range(len(texts)) if labels[i] == label]

        if len(cluster_texts) < 2:
            keywords_by_cluster[int(label)] = ["insufficient_documents"]
            continue

        # Create vectorizer for this cluster
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=stopwords,
            ngram_range=ngram_range,
            min_df=min(min_df, len(cluster_texts) // 2),
            max_df=max_df,
            token_pattern=r"(?u)\b\w\w+\b",
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(cluster_texts)
            feature_names = vectorizer.get_feature_names_out()

            if len(feature_names) == 0:
                keywords_by_cluster[int(label)] = ["no_keywords_found"]
                continue

            # Get mean TF-IDF scores
            tfidf_scores = tfidf_matrix.mean(axis=0).A1
            top_indices = tfidf_scores.argsort()[-n_keywords:][::-1]
            top_keywords = [feature_names[i] for i in top_indices]

            keywords_by_cluster[int(label)] = top_keywords

        except Exception as e:
            logger.warning(f"Error extracting keywords for cluster {label}: {e}")
            keywords_by_cluster[int(label)] = [f"error: {str(e)[:30]}"]

    logger.info(f"Keyword extraction complete for {len(keywords_by_cluster)} clusters")

    return keywords_by_cluster
