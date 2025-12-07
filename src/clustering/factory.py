"""Factory for creating clusterer instances."""

from typing import Dict, Any
from .base import Clusterer
from .kmeans import KMeansClusterer
from .hierarchical import HierarchicalClusterer


class ClustererFactory:
    """Factory for creating clusterer instances.

    Allows easy swapping of clustering methods via configuration.

    Example:
        >>> clusterer = ClustererFactory.create('kmeans', n_clusters=10)
        >>> clusterer = ClustererFactory.create('hierarchical', linkage='ward')
    """

    _registry: Dict[str, type] = {
        "kmeans": KMeansClusterer,
        "k-means": KMeansClusterer,
        "hierarchical": HierarchicalClusterer,
        "agglomerative": HierarchicalClusterer,
    }

    @classmethod
    def create(cls, method: str, **kwargs: Any) -> Clusterer:
        """Create a clusterer instance.

        Args:
            method: Name of clustering method ('kmeans', 'hierarchical', etc.)
            **kwargs: Arguments to pass to clusterer constructor

        Returns:
            Clusterer instance

        Raises:
            ValueError: If method is not registered
        """
        method_lower = method.lower()

        if method_lower not in cls._registry:
            available_methods = ", ".join(set(cls._registry.keys()))
            raise ValueError(
                f"Unknown clustering method: '{method}'. "
                f"Available methods: {available_methods}"
            )

        clusterer_class = cls._registry[method_lower]
        return clusterer_class(**kwargs)

    @classmethod
    def register(cls, name: str, clusterer_class: type) -> None:
        """Register a new clusterer class.

        Args:
            name: Name to register clusterer under
            clusterer_class: Clusterer class to register
        """
        cls._registry[name.lower()] = clusterer_class
