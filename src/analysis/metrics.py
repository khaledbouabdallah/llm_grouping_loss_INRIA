"""
Metrics calculation utilities
ECE, grouping loss, calibration error
"""

import numpy as np
from typing import Dict, List, Tuple


def calculate_ece(
    confidences: np.ndarray, correctness: np.ndarray, n_bins: int = 10
) -> Tuple[float, Dict]:
    """
    Calculate Expected Calibration Error

    Args:
        confidences: Array of confidence scores [N]
        correctness: Array of binary correctness [N] (1 = correct, 0 = incorrect)
        n_bins: Number of bins

    Returns:
        ece: Expected calibration error
        bin_info: Dict with bin information
    """
    confidences = np.array(confidences)
    correctness = np.array(correctness)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(confidences, bin_edges[:-1]) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    ece = 0.0
    bin_info = []

    for i in range(n_bins):
        mask = bin_indices == i
        bin_size = mask.sum()

        if bin_size > 0:
            bin_confidences = confidences[mask]
            bin_correctness = correctness[mask]

            avg_confidence = bin_confidences.mean()
            accuracy = bin_correctness.mean()
            calibration_error = abs(avg_confidence - accuracy)

            ece += (bin_size / len(confidences)) * calibration_error

            bin_info.append(
                {
                    "bin_idx": i,
                    "bin_range": (bin_edges[i], bin_edges[i + 1]),
                    "size": int(bin_size),
                    "avg_confidence": float(avg_confidence),
                    "accuracy": float(accuracy),
                    "calibration_error": float(calibration_error),
                }
            )
        else:
            bin_info.append(
                {
                    "bin_idx": i,
                    "bin_range": (bin_edges[i], bin_edges[i + 1]),
                    "size": 0,
                    "avg_confidence": None,
                    "accuracy": None,
                    "calibration_error": None,
                }
            )

    return float(ece), {"bins": bin_info, "n_bins": n_bins}


def calculate_binned_calibration(
    results: List[Dict], n_bins: int = 10, attribute: str = None
) -> Dict:
    """
    Calculate binned calibration metrics

    Args:
        results: List of evaluation results
        n_bins: Number of bins
        attribute: Optional attribute to group by (e.g., 'language', 'culture')

    Returns:
        Dict with calibration metrics
    """
    if attribute:
        # Group by attribute
        groups = {}
        for r in results:
            key = r.get(attribute, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(r)

        # Calculate ECE for each group
        calibration = {}
        for key, group in groups.items():
            confidences = [r["confidence"] for r in group]
            correctness = [int(r["is_correct"]) for r in group]

            ece, bin_info = calculate_ece(confidences, correctness, n_bins)
            calibration[key] = {
                "ece": ece,
                "bin_info": bin_info,
                "n_samples": len(group),
            }

    else:
        # Overall calibration
        confidences = [r["confidence"] for r in results]
        correctness = [int(r["is_correct"]) for r in results]

        ece, bin_info = calculate_ece(confidences, correctness, n_bins)
        calibration = {"ece": ece, "bin_info": bin_info, "n_samples": len(results)}

    return calibration


def calculate_grouping_loss(
    results: List[Dict], group_attribute: str, method: str = "variance"
) -> Dict:
    """
    Calculate grouping loss

    Args:
        results: List of evaluation results
        group_attribute: Attribute to group by (e.g., 'language', 'culture', 'cluster_id')
        method: Method to calculate loss ('variance', 'maxgap', 'ece_variance')

    Returns:
        Dict with grouping loss metrics
    """
    # Group results by attribute
    groups = {}
    for r in results:
        key = r.get(group_attribute, "unknown")
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    if method == "variance":
        # Variance in accuracy across groups
        accuracies = [
            np.mean([int(r["is_correct"]) for r in group]) for group in groups.values()
        ]
        loss = float(np.var(accuracies))

        return {
            "method": "variance",
            "loss": loss,
            "group_accuracies": {
                key: float(np.mean([int(r["is_correct"]) for r in group]))
                for key, group in groups.items()
            },
            "n_groups": len(groups),
        }

    elif method == "maxgap":
        # Maximum gap between group accuracies
        accuracies = [
            np.mean([int(r["is_correct"]) for r in group]) for group in groups.values()
        ]
        loss = float(max(accuracies) - min(accuracies))

        return {
            "method": "maxgap",
            "loss": loss,
            "group_accuracies": {
                key: float(np.mean([int(r["is_correct"]) for r in group]))
                for key, group in groups.items()
            },
            "n_groups": len(groups),
        }

    elif method == "ece_variance":
        # Variance in ECE across groups
        group_eces = {}
        for key, group in groups.items():
            confidences = [r["confidence"] for r in group]
            correctness = [int(r["is_correct"]) for r in group]
            ece, _ = calculate_ece(confidences, correctness)
            group_eces[key] = ece

        loss = float(np.var(list(group_eces.values())))

        return {
            "method": "ece_variance",
            "loss": loss,
            "group_eces": {key: float(ece) for key, ece in group_eces.items()},
            "n_groups": len(groups),
        }

    else:
        raise ValueError(f"Unknown method: {method}")


def group_by_attribute(results: List[Dict], attribute: str) -> Dict[str, List[Dict]]:
    """
    Group results by an attribute

    Args:
        results: List of evaluation results
        attribute: Attribute to group by

    Returns:
        Dict mapping attribute values to result lists
    """
    groups = {}
    for r in results:
        key = r.get(attribute, "unknown")
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    return groups


def calculate_group_statistics(results: List[Dict], group_attribute: str) -> Dict:
    """
    Calculate statistics for each group

    Args:
        results: List of evaluation results
        group_attribute: Attribute to group by

    Returns:
        Dict with group statistics
    """
    groups = group_by_attribute(results, group_attribute)

    stats = {}
    for key, group in groups.items():
        confidences = [r["confidence"] for r in group]
        correctness = [int(r["is_correct"]) for r in group]
        calibration_errors = [r["calibration_error"] for r in group]

        stats[key] = {
            "n_samples": len(group),
            "accuracy": float(np.mean(correctness)),
            "avg_confidence": float(np.mean(confidences)),
            "avg_calibration_error": float(np.mean(calibration_errors)),
            "ece": float(calculate_ece(confidences, correctness)[0]),
        }

    return stats
