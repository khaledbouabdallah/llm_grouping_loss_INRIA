"""Confidence analysis and gap metrics (Phase 1)."""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ConfidenceAnalyzer:
    """Analyzer for confidence scores across clusters.

    This is for Phase 1 analysis where we measure confidence differences
    between clusters without ground truth.
    """

    @staticmethod
    def compute_cluster_statistics(
        confidences: np.ndarray, labels: np.ndarray
    ) -> pd.DataFrame:
        """Compute confidence statistics per cluster.

        Args:
            confidences: Array of confidence scores
            labels: Cluster labels

        Returns:
            DataFrame with statistics per cluster
        """
        stats_list = []

        for cluster_id in np.unique(labels):
            cluster_mask = labels == cluster_id
            cluster_confidences = confidences[cluster_mask]

            stats_list.append(
                {
                    "cluster_id": int(cluster_id),
                    "n_samples": int(cluster_mask.sum()),
                    "mean_confidence": float(cluster_confidences.mean()),
                    "std_confidence": float(cluster_confidences.std()),
                    "median_confidence": float(np.median(cluster_confidences)),
                    "min_confidence": float(cluster_confidences.min()),
                    "max_confidence": float(cluster_confidences.max()),
                    "q25_confidence": float(np.percentile(cluster_confidences, 25)),
                    "q75_confidence": float(np.percentile(cluster_confidences, 75)),
                }
            )

        return pd.DataFrame(stats_list)

    @staticmethod
    def confidence_gap(confidences: np.ndarray, labels: np.ndarray) -> float:
        """Compute confidence gap (variance of mean confidences across clusters).

        This measures how much confidence levels differ between clusters.
        Higher values indicate larger disparities.

        Args:
            confidences: Array of confidence scores
            labels: Cluster labels

        Returns:
            Confidence gap (variance of cluster means)
        """
        cluster_means = []

        for cluster_id in np.unique(labels):
            cluster_mask = labels == cluster_id
            cluster_mean = confidences[cluster_mask].mean()
            cluster_means.append(cluster_mean)

        return float(np.var(cluster_means))

    @staticmethod
    def pairwise_tests(
        confidences: np.ndarray, labels: np.ndarray, test: str = "t-test"
    ) -> List[Dict]:
        """Perform pairwise statistical tests between clusters.

        Args:
            confidences: Array of confidence scores
            labels: Cluster labels
            test: Statistical test to use ('t-test' or 'mann-whitney')

        Returns:
            List of test results for each pair
        """
        results = []
        unique_labels = np.unique(labels)

        for i, cluster_i in enumerate(unique_labels):
            for cluster_j in unique_labels[i + 1 :]:
                conf_i = confidences[labels == cluster_i]
                conf_j = confidences[labels == cluster_j]

                if test == "t-test":
                    statistic, p_value = stats.ttest_ind(conf_i, conf_j)
                elif test == "mann-whitney":
                    statistic, p_value = stats.mannwhitneyu(conf_i, conf_j)
                else:
                    raise ValueError(f"Unknown test: {test}")

                results.append(
                    {
                        "cluster_i": int(cluster_i),
                        "cluster_j": int(cluster_j),
                        "mean_i": float(conf_i.mean()),
                        "mean_j": float(conf_j.mean()),
                        "statistic": float(statistic),
                        "p_value": float(p_value),
                        "significant": p_value < 0.05,
                    }
                )

        return results

    @staticmethod
    def anova_test(confidences: np.ndarray, labels: np.ndarray) -> Tuple[float, float]:
        """Perform one-way ANOVA to test if cluster means differ.

        Args:
            confidences: Array of confidence scores
            labels: Cluster labels

        Returns:
            Tuple of (F-statistic, p-value)
        """
        groups = [confidences[labels == cluster_id] for cluster_id in np.unique(labels)]

        f_stat, p_value = stats.f_oneway(*groups)
        return float(f_stat), float(p_value)


def confidence_gap_analysis(
    confidences: np.ndarray, labels: np.ndarray, perform_tests: bool = True
) -> Dict:
    """Perform comprehensive confidence gap analysis.

    Args:
        confidences: Array of confidence scores
        labels: Cluster labels
        perform_tests: Whether to perform statistical tests

    Returns:
        Dictionary containing analysis results
    """
    analyzer = ConfidenceAnalyzer()

    # Compute statistics
    cluster_stats = analyzer.compute_cluster_statistics(confidences, labels)
    confidence_gap = analyzer.confidence_gap(confidences, labels)

    results = {
        "cluster_statistics": cluster_stats,
        "confidence_gap": confidence_gap,
        "overall_mean": float(confidences.mean()),
        "overall_std": float(confidences.std()),
    }

    if perform_tests:
        # ANOVA
        f_stat, p_value = analyzer.anova_test(confidences, labels)
        results["anova"] = {
            "f_statistic": f_stat,
            "p_value": p_value,
            "significant": p_value < 0.05,
        }

        # Pairwise tests (only if not too many clusters)
        n_clusters = len(np.unique(labels))
        if n_clusters <= 10:
            results["pairwise_tests"] = analyzer.pairwise_tests(confidences, labels)

    return results
