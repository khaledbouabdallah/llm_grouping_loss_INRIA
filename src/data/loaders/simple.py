"""Simple text file loader for CSV, JSON, and other formats."""

from pathlib import Path
from typing import Optional, List
import pandas as pd
from ..base import CorpusLoader


class SimpleTextLoader(CorpusLoader):
    """Load corpus from CSV, JSON, or other tabular formats.

    This loader can read data from various file formats and expects
    columns that can be mapped to 'id' and 'text'.

    Args:
        file_path: Path to data file (CSV, JSON, Excel, etc.)
        id_column: Name of column to use as 'id' (default: 'id')
        text_column: Name of column to use as 'text' (default: 'text')
        additional_columns: Optional list of additional columns to keep

    Example:
        >>> loader = SimpleTextLoader(
        ...     file_path="data/entities.csv",
        ...     id_column="entity_id",
        ...     text_column="description"
        ... )
        >>> df = loader.load()
    """

    def __init__(
        self,
        file_path: str | Path,
        id_column: str = "id",
        text_column: str = "text",
        additional_columns: Optional[List[str]] = None,
    ):
        self.file_path = Path(file_path)
        self.id_column = id_column
        self.text_column = text_column
        self.additional_columns = additional_columns or []

        if not self.file_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.file_path}")

    def load(self) -> pd.DataFrame:
        """Load data from file and standardize column names.

        Returns:
            DataFrame with 'id', 'text', and any additional columns
        """
        # Read file based on extension
        suffix = self.file_path.suffix.lower()

        if suffix == ".csv":
            df = pd.read_csv(self.file_path)
        elif suffix == ".json":
            df = pd.read_json(self.file_path)
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(self.file_path)
        elif suffix == ".parquet":
            df = pd.read_parquet(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        # Check that required columns exist
        if self.id_column not in df.columns:
            raise ValueError(f"ID column '{self.id_column}' not found in file")
        if self.text_column not in df.columns:
            raise ValueError(f"Text column '{self.text_column}' not found in file")

        # Select and rename columns
        columns_to_keep = [self.id_column, self.text_column] + self.additional_columns
        columns_to_keep = [col for col in columns_to_keep if col in df.columns]

        df = df[columns_to_keep].copy()

        # Rename to standard names
        df = df.rename(columns={self.id_column: "id", self.text_column: "text"})

        # Remove rows with missing text
        df = df.dropna(subset=["text"])

        # Reset index
        df = df.reset_index(drop=True)

        # Validate
        self.validate_dataframe(df)

        return df
