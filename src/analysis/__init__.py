"""Analysis utilities for calculating metrics"""

from .metrics import (
    calculate_ece,
    calculate_grouping_loss,
    calculate_binned_calibration,
    group_by_attribute,
)

from .correlation_analysis import (
    calculate_contingency_table,
    calculate_cramers_v,
    analyze_cluster_group_correlation,
    analyze_cluster_purity,
    compare_cluster_distributions,
    calculate_cluster_diversity_index,
    test_hierarchical_split_order,
)

__all__ = [
    "calculate_ece",
    "calculate_grouping_loss",
    "calculate_binned_calibration",
    "group_by_attribute",
]
