"""Abstract base class for corpus loaders."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd


class CorpusLoader(ABC):
    """Abstract base class for loading text corpora.

    All corpus loaders should inherit from this class and implement
    the load() method.
    """

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load corpus and return as DataFrame.

        Returns:
            DataFrame with at least 'id' and 'text' columns
            - id: Unique identifier for each document/entity
            - text: The text content to be clustered

        Additional columns may include metadata (e.g., 'entity_name', 'language')
        """
        pass

    def validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate that DataFrame has required columns.

        Args:
            df: DataFrame to validate

        Raises:
            ValueError: If required columns are missing
        """
        required_columns = ["id", "text"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(
                f"DataFrame missing required columns: {missing_columns}. "
                f"Required columns are: {required_columns}"
            )

        if df["text"].isna().any():
            raise ValueError("Text column contains NaN values")
