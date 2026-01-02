"""
Dimension reduction utilities for embeddings
UMAP and PCA wrappers for reducing embedding dimensions before clustering
"""

import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DimensionReducer:
    """Wrapper for dimension reduction methods"""

    def __init__(
        self, method: str = "umap", n_components: int = 50, random_state: int = 42
    ):
        """
        Initialize dimension reducer

        Args:
            method: 'umap' or 'pca'
            n_components: Number of dimensions to reduce to
            random_state: Random seed for reproducibility
        """
        self.method = method.lower()
        self.n_components = n_components
        self.random_state = random_state
        self.reducer = None

        logger.info(
            f"DimensionReducer initialized: method={method}, n_components={n_components}"
        )

    def fit_transform(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Fit reducer and transform embeddings

        Args:
            embeddings: Input embeddings [n_samples, n_features]

        Returns:
            Reduced embeddings [n_samples, n_components]
        """
        logger.info(
            f"Reducing {embeddings.shape} with {self.method} to {self.n_components} dimensions"
        )

        if self.method == "umap":
            from umap import UMAP

            self.reducer = UMAP(
                n_components=self.n_components,
                random_state=self.random_state,
                n_neighbors=15,
                min_dist=0.1,
                metric="cosine",
            )
        elif self.method == "pca":
            from sklearn.decomposition import PCA

            self.reducer = PCA(
                n_components=self.n_components, random_state=self.random_state
            )
        else:
            raise ValueError(f"Unknown method: {self.method}")

        reduced = self.reducer.fit_transform(embeddings)
        logger.info(f"Reduced to shape: {reduced.shape}")

        return reduced

    def transform(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Transform new embeddings using fitted reducer

        Args:
            embeddings: Input embeddings

        Returns:
            Reduced embeddings
        """
        if self.reducer is None:
            raise ValueError("Reducer not fitted yet. Call fit_transform first.")

        return self.reducer.transform(embeddings)

    def get_explained_variance(self) -> Optional[float]:
        """Get explained variance ratio (only for PCA)"""
        if self.method == "pca" and self.reducer is not None:
            return self.reducer.explained_variance_ratio_.sum()
        return None


def reduce_embeddings_umap(
    embeddings: np.ndarray,
    n_components: int = 50,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    random_state: int = 42,
) -> np.ndarray:
    """
    Reduce embeddings using UMAP

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        n_components: Number of dimensions to reduce to
        n_neighbors: UMAP n_neighbors parameter
        min_dist: UMAP min_dist parameter
        random_state: Random seed

    Returns:
        Reduced embeddings [n_samples, n_components]
    """
    from umap import UMAP

    logger.info(f"UMAP: {embeddings.shape} -> {n_components} dims")

    reducer = UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="cosine",
        random_state=random_state,
    )

    reduced = reducer.fit_transform(embeddings)
    logger.info(f"UMAP complete: {reduced.shape}")

    return reduced


def reduce_embeddings_pca(
    embeddings: np.ndarray, n_components: int = 50, random_state: int = 42
) -> Tuple[np.ndarray, float]:
    """
    Reduce embeddings using PCA

    Args:
        embeddings: Input embeddings [n_samples, n_features]
        n_components: Number of dimensions to reduce to
        random_state: Random seed

    Returns:
        Tuple of (reduced embeddings, explained variance ratio)
    """
    from sklearn.decomposition import PCA

    logger.info(f"PCA: {embeddings.shape} -> {n_components} dims")

    pca = PCA(n_components=n_components, random_state=random_state)
    reduced = pca.fit_transform(embeddings)

    explained_var = pca.explained_variance_ratio_.sum()
    logger.info(f"PCA complete: {reduced.shape}")
    logger.info(f"Explained variance: {explained_var:.2%}")

    return reduced, explained_var


def reduce_embeddings_for_visualization(
    embeddings: np.ndarray, method: str = "umap", random_state: int = 42
) -> np.ndarray:
    """
    Reduce embeddings to 2D for visualization

    Args:
        embeddings: Input embeddings
        method: 'umap' or 'pca'
        random_state: Random seed

    Returns:
        2D embeddings [n_samples, 2]
    """
    if method == "umap":
        from umap import UMAP

        reducer = UMAP(
            n_components=2,
            n_neighbors=15,
            min_dist=0.1,
            metric="cosine",
            random_state=random_state,
        )
    elif method == "pca":
        from sklearn.decomposition import PCA

        reducer = PCA(n_components=2, random_state=random_state)
    else:
        raise ValueError(f"Unknown method: {method}")

    logger.info(f"Reducing to 2D for visualization using {method}")
    reduced = reducer.fit_transform(embeddings)

    return reduced
