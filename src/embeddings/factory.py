"""Factory for creating embedder instances."""

from typing import Dict, Any
from .base import Embedder
from .tfidf import TfidfEmbedder
from .sentence_bert import SBertEmbedder


class EmbedderFactory:
    """Factory for creating embedder instances.

    Allows easy swapping of embedding methods via configuration.

    Example:
        >>> embedder = EmbedderFactory.create('tfidf', max_features=500)
        >>> embedder = EmbedderFactory.create('sbert', model_name='all-MiniLM-L6-v2')
    """

    _registry: Dict[str, type] = {
        "tfidf": TfidfEmbedder,
        "sbert": SBertEmbedder,
        "sentence_bert": SBertEmbedder,
    }

    @classmethod
    def create(cls, method: str, **kwargs: Any) -> Embedder:
        """Create an embedder instance.

        Args:
            method: Name of embedding method ('tfidf', 'sbert', etc.)
            **kwargs: Arguments to pass to embedder constructor

        Returns:
            Embedder instance

        Raises:
            ValueError: If method is not registered
        """
        if method not in cls._registry:
            available_methods = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown embedding method: '{method}'. "
                f"Available methods: {available_methods}"
            )

        embedder_class = cls._registry[method]
        return embedder_class(**kwargs)

    @classmethod
    def register(cls, name: str, embedder_class: type) -> None:
        """Register a new embedder class.

        Args:
            name: Name to register embedder under
            embedder_class: Embedder class to register
        """
        cls._registry[name] = embedder_class
