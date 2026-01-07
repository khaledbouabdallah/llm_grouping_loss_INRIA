"""
Text embedding generation with caching
Thin wrapper around sentence-transformers for Wikipedia text embeddings
"""

import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class TextEmbedder:
    """Wrapper for sentence-transformers with simple interface"""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        Initialize embedder

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.model = None
        logger.info(f"TextEmbedder initialized with model: {model_name}")

    def load_model(self):
        """Load the sentence transformer model"""
        if self.model is None:
            logger.info(f"Loading SentenceTransformer: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")

    def embed_texts(
        self, texts: List[str], batch_size: int = 32, show_progress: bool = True
    ) -> np.ndarray:
        """
        Embed a list of texts

        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            Numpy array of embeddings [num_texts, embedding_dim]
        """
        if self.model is None:
            self.load_model()

        # E5 expects task prefixes
        texts = [f"query: {t}" for t in texts]

        logger.info(f"Encoding {len(texts)} texts...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        logger.info(f"Generated embeddings shape: {embeddings.shape}")
        return embeddings

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text"""
        if self.model is None:
            self.load_model()

        return self.model.encode([text], convert_to_numpy=True)[0]


def save_embeddings(
    embeddings: np.ndarray,
    entity_ids: List[int],
    language: str,
    model_name: str,
    save_dir: Path,
    text_type: str = "summary",
    metadata: Optional[Dict] = None,
):
    """
    Save embeddings to disk with metadata

    Args:
        embeddings: Numpy array of embeddings
        entity_ids: List of entity IDs corresponding to embeddings
        language: Language code
        model_name: Model name used for embeddings
        save_dir: Directory to save embeddings
        text_type: Type of text used ('summary' or 'content')
        metadata: Optional metadata dict
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with text_type
    model_slug = model_name.replace("/", "_")
    filename = f"embeddings_{language}_{text_type}_{model_slug}.pkl"
    filepath = save_dir / filename

    # Prepare data
    data = {
        "embeddings": embeddings,
        "entity_ids": entity_ids,
        "language": language,
        "model_name": model_name,
        "text_type": text_type,
        "shape": embeddings.shape,
        "metadata": metadata or {},
    }

    # Save
    with open(filepath, "wb") as f:
        pickle.dump(data, f)

    logger.info(f"Saved embeddings to {filepath}")
    logger.info(f"  Shape: {embeddings.shape}")
    logger.info(f"  Entities: {len(entity_ids)}")


def load_cached_embeddings(
    language: str, model_name: str, save_dir: Path, text_type: str = "summary"
) -> Optional[Dict]:
    """
    Load cached embeddings if they exist

    Args:
        language: Language code
        model_name: Model name
        save_dir: Directory where embeddings are saved
        text_type: Type of text used ('summary' or 'content')

    Returns:
        Dict with embeddings and metadata, or None if not found
    """
    save_dir = Path(save_dir)
    model_slug = model_name.replace("/", "_")
    filename = f"embeddings_{language}_{text_type}_{model_slug}.pkl"
    filepath = save_dir / filename

    if not filepath.exists():
        logger.info(f"No cached embeddings found at {filepath}")
        return None

    logger.info(f"Loading cached embeddings from {filepath}")
    with open(filepath, "rb") as f:
        data = pickle.load(f)

    logger.info(f"Loaded embeddings shape: {data['shape']}")
    logger.info(f"Number of entities: {len(data['entity_ids'])}")

    return data


def get_embedding_cache_info(save_dir: Path) -> List[Dict]:
    """
    Get information about all cached embeddings

    Args:
        save_dir: Directory where embeddings are saved

    Returns:
        List of dicts with cache info
    """
    save_dir = Path(save_dir)
    if not save_dir.exists():
        return []

    cache_info = []
    for filepath in save_dir.glob("embeddings_*.pkl"):
        try:
            with open(filepath, "rb") as f:
                data = pickle.load(f)

            info = {
                "filename": filepath.name,
                "language": data.get("language"),
                "model_name": data.get("model_name"),
                "text_type": data.get("text_type", "unknown"),
                "shape": data.get("shape"),
                "num_entities": len(data.get("entity_ids", [])),
                "size_mb": filepath.stat().st_size / (1024 * 1024),
            }
            cache_info.append(info)
        except Exception as e:
            logger.warning(f"Could not read {filepath}: {e}")

    return cache_info
