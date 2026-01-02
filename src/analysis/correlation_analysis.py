"""
Correlation analysis utilities
Analyze relationships between clusters and categorical variables (culture, country)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.stats import chi2_contingency
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
import logging

logger = logging.getLogger(__name__)


def calculate_contingency_table(
    labels: np.ndarray, df: pd.DataFrame, grouping_var: str
) -> pd.DataFrame:
    """
    Create contingency table between clusters and grouping variable

    Args:
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_var: Column name to analyze

    Returns:
        Contingency table as DataFrame
    """
    df_with_clusters = df.copy()
    df_with_clusters["cluster"] = labels

    # Remove noise points
    df_filtered = df_with_clusters[df_with_clusters["cluster"] != -1]

    contingency = pd.crosstab(
        df_filtered["cluster"],
        df_filtered[grouping_var],
        margins=True,
        margins_name="Total",
    )

    return contingency


def calculate_cramers_v(
    labels: np.ndarray, df: pd.DataFrame, grouping_var: str
) -> Dict:
    """
    Calculate Cramér's V statistic for association between clusters and grouping variable

    Args:
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_var: Column name to analyze

    Returns:
        Dict with Cramér's V and chi-square test results
    """
    df_with_clusters = df.copy()
    df_with_clusters["cluster"] = labels

    # Remove noise points
    df_filtered = df_with_clusters[df_with_clusters["cluster"] != -1]

    # Create contingency table
    contingency = pd.crosstab(df_filtered["cluster"], df_filtered[grouping_var])

    # Chi-square test
    chi2, p_value, dof, expected = chi2_contingency(contingency)

    # Cramér's V
    n = contingency.sum().sum()
    min_dim = min(contingency.shape[0] - 1, contingency.shape[1] - 1)
    cramers_v_value = np.sqrt(chi2 / (n * min_dim))

    logger.info(
        f"{grouping_var} - Cramér's V: {cramers_v_value:.3f}, p-value: {p_value:.4e}"
    )

    return {
        "cramers_v": float(cramers_v_value),
        "chi2": float(chi2),
        "p_value": float(p_value),
        "dof": int(dof),
        "n_samples": int(n),
        "significant": p_value < 0.05,
        "effect_size": (
            "small"
            if cramers_v_value < 0.1
            else "medium" if cramers_v_value < 0.3 else "large"
        ),
    }


def analyze_cluster_group_correlation(
    labels: np.ndarray, df: pd.DataFrame, grouping_vars: List[str]
) -> pd.DataFrame:
    """
    Comprehensive correlation analysis between clusters and multiple grouping variables

    Args:
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_vars: List of column names to analyze

    Returns:
        DataFrame with correlation statistics
    """
    logger.info(f"Analyzing correlations for {len(grouping_vars)} grouping variables")

    results = []

    for var in grouping_vars:
        # Cramér's V
        cramers_results = calculate_cramers_v(labels, df, var)

        # Adjusted Rand Index (if treating as categorical clustering)
        df_filtered = df[labels != -1].copy()
        labels_filtered = labels[labels != -1]

        # Convert categorical variable to numeric labels
        var_labels = pd.Categorical(df_filtered[var]).codes

        ari = adjusted_rand_score(labels_filtered, var_labels)
        nmi = normalized_mutual_info_score(labels_filtered, var_labels)

        results.append(
            {
                "grouping_variable": var,
                "cramers_v": cramers_results["cramers_v"],
                "chi2_p_value": cramers_results["p_value"],
                "significant": cramers_results["significant"],
                "effect_size": cramers_results["effect_size"],
                "adjusted_rand_index": float(ari),
                "normalized_mutual_info": float(nmi),
                "n_unique_values": df[var].nunique(),
            }
        )

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("cramers_v", ascending=False)

    logger.info(f"Correlation analysis complete for {len(results_df)} variables")

    return results_df


def analyze_cluster_purity(
    labels: np.ndarray, df: pd.DataFrame, grouping_var: str
) -> Dict:
    """
    Analyze purity of clusters with respect to a grouping variable

    Args:
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_var: Column name to analyze

    Returns:
        Dict with purity statistics per cluster
    """
    unique_clusters = sorted([l for l in set(labels) if l != -1])

    cluster_purities = {}
    overall_purities = []

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_values = df[mask][grouping_var].value_counts()

        if len(cluster_values) == 0:
            continue

        # Purity: fraction of most common value
        purity = cluster_values.iloc[0] / cluster_values.sum()

        # Entropy
        probs = cluster_values / cluster_values.sum()
        entropy = -np.sum(probs * np.log2(probs + 1e-10))

        # Gini impurity
        gini = 1 - np.sum(probs**2)

        cluster_purities[int(cluster_id)] = {
            "purity": float(purity),
            "entropy": float(entropy),
            "gini_impurity": float(gini),
            "dominant_value": cluster_values.index[0],
            "dominant_count": int(cluster_values.iloc[0]),
            "total_count": int(cluster_values.sum()),
            "n_unique_values": len(cluster_values),
        }

        overall_purities.append(purity)

    return {
        "per_cluster": cluster_purities,
        "overall_stats": {
            "mean_purity": float(np.mean(overall_purities)),
            "std_purity": float(np.std(overall_purities)),
            "min_purity": float(np.min(overall_purities)),
            "max_purity": float(np.max(overall_purities)),
            "median_purity": float(np.median(overall_purities)),
        },
    }


def compare_cluster_distributions(
    labels: np.ndarray,
    df: pd.DataFrame,
    grouping_var: str,
    cluster_pairs: Optional[List[Tuple[int, int]]] = None,
) -> pd.DataFrame:
    """
    Compare distributions of grouping variable between cluster pairs

    Args:
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_var: Column name to analyze
        cluster_pairs: Optional list of cluster ID pairs to compare
                      If None, compares all pairs

    Returns:
        DataFrame with comparison statistics
    """
    from scipy.stats import chi2_contingency, ks_2samp

    unique_clusters = sorted([l for l in set(labels) if l != -1])

    if cluster_pairs is None:
        # Generate all pairs
        cluster_pairs = [
            (c1, c2)
            for i, c1 in enumerate(unique_clusters)
            for c2 in unique_clusters[i + 1 :]
        ]

    results = []

    for c1, c2 in cluster_pairs:
        mask1 = labels == c1
        mask2 = labels == c2

        dist1 = df[mask1][grouping_var].value_counts()
        dist2 = df[mask2][grouping_var].value_counts()

        # Align distributions
        all_values = sorted(set(dist1.index) | set(dist2.index))
        counts1 = [dist1.get(v, 0) for v in all_values]
        counts2 = [dist2.get(v, 0) for v in all_values]

        # Chi-square test
        contingency = np.array([counts1, counts2])
        chi2, p_value, _, _ = chi2_contingency(contingency)

        # Total variation distance
        total1 = sum(counts1)
        total2 = sum(counts2)
        tv_distance = 0.5 * sum(
            abs(c1 / total1 - c2 / total2) for c1, c2 in zip(counts1, counts2)
        )

        results.append(
            {
                "cluster1": int(c1),
                "cluster2": int(c2),
                "chi2_statistic": float(chi2),
                "chi2_p_value": float(p_value),
                "significantly_different": p_value < 0.05,
                "total_variation_distance": float(tv_distance),
                "cluster1_size": int(total1),
                "cluster2_size": int(total2),
            }
        )

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("chi2_p_value")

    return results_df


def calculate_cluster_diversity_index(
    labels: np.ndarray, df: pd.DataFrame, grouping_var: str
) -> Dict:
    """
    Calculate diversity indices for each cluster

    Args:
        labels: Cluster labels
        df: DataFrame with entity data
        grouping_var: Column name to analyze

    Returns:
        Dict with diversity indices per cluster
    """
    unique_clusters = sorted([l for l in set(labels) if l != -1])

    diversity_results = {}

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_values = df[mask][grouping_var].value_counts()

        if len(cluster_values) == 0:
            continue

        # Simpson's diversity index
        probs = cluster_values / cluster_values.sum()
        simpsons = 1 - np.sum(probs**2)

        # Shannon diversity index
        shannon = -np.sum(probs * np.log(probs + 1e-10))

        # Effective number of species (exp of Shannon entropy)
        effective_n = np.exp(shannon)

        diversity_results[int(cluster_id)] = {
            "simpsons_index": float(simpsons),
            "shannon_index": float(shannon),
            "effective_number": float(effective_n),
            "richness": len(cluster_values),
            "total_count": int(cluster_values.sum()),
        }

    return diversity_results


def test_hierarchical_split_order(
    embeddings: np.ndarray,
    df: pd.DataFrame,
    grouping_vars: List[str],
    method: str = "ward",
    max_depth: int = 5,
) -> Dict:
    """
    Test whether hierarchical clustering splits by certain grouping variables first

    Args:
        embeddings: Input embeddings
        df: DataFrame with entity data
        grouping_vars: List of grouping variables to test (e.g., ['country', 'culture'])
        method: Hierarchical clustering method
        max_depth: Maximum depth to analyze

    Returns:
        Dict with split order analysis
    """
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import pdist

    logger.info(f"Analyzing hierarchical split order for {grouping_vars}")

    # Compute linkage
    if method == "ward":
        Z = linkage(embeddings, method=method)
    else:
        Z = linkage(pdist(embeddings), method=method)

    results = {}

    # For each depth (number of clusters)
    for n_clusters in range(2, min(max_depth + 1, len(embeddings))):
        depth_results = {}

        # Get clusters at this level
        labels = fcluster(Z, n_clusters, criterion="maxclust") - 1

        # For each grouping variable, calculate homogeneity
        for var in grouping_vars:
            purity_analysis = analyze_cluster_purity(labels, df, var)
            depth_results[var] = purity_analysis["overall_stats"]["mean_purity"]

        results[n_clusters] = depth_results

    # Determine which variable has higher purity at early splits
    early_splits = {
        var: np.mean(
            [results[k][var] for k in range(2, min(5, max_depth + 1)) if k in results]
        )
        for var in grouping_vars
    }

    sorted_vars = sorted(early_splits.items(), key=lambda x: x[1], reverse=True)

    return {
        "purity_by_depth": results,
        "early_split_ranking": sorted_vars,
        "interpretation": f"Hierarchical clustering tends to split by '{sorted_vars[0][0]}' first",
    }
