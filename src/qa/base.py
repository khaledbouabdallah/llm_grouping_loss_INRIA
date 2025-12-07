"""Abstract base class for question generators."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd


class QuestionGenerator(ABC):
    """Abstract base class for question generation.

    All question generators should inherit from this class.
    """

    @abstractmethod
    def generate(self, corpus_df: pd.DataFrame, labels: List[int]) -> pd.DataFrame:
        """Generate questions from corpus.

        Args:
            corpus_df: DataFrame with corpus data (must include 'id' and 'text')
            labels: Cluster labels for each item in corpus

        Returns:
            DataFrame with columns:
                - id: Unique question ID
                - entity_id: ID of entity from corpus
                - cluster_id: Cluster label
                - question: Generated question text
                - template: Template used (optional)
                - metadata: Additional metadata (optional)
        """
        pass
