"""Text preprocessing utilities."""

import re
from typing import List
import pandas as pd


def clean_text(
    text: str, lowercase: bool = True, remove_special_chars: bool = True
) -> str:
    """Clean and normalize text.

    Args:
        text: Input text
        lowercase: Whether to convert to lowercase
        remove_special_chars: Whether to remove special characters

    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        return ""

    # Remove extra whitespace
    text = " ".join(text.split())

    # Lowercase
    if lowercase:
        text = text.lower()

    # Remove special characters (keep alphanumeric and basic punctuation)
    if remove_special_chars:
        text = re.sub(r"[^a-zA-Z0-9\s\.,!?;:\-]", "", text)

    return text.strip()


def preprocess_corpus(
    df: pd.DataFrame,
    text_column: str = "text",
    lowercase: bool = True,
    remove_special_chars: bool = False,
    min_length: int = 10,
) -> pd.DataFrame:
    """Preprocess corpus DataFrame.

    Args:
        df: Input DataFrame
        text_column: Name of text column
        lowercase: Whether to lowercase text
        remove_special_chars: Whether to remove special characters
        min_length: Minimum text length to keep

    Returns:
        Preprocessed DataFrame
    """
    df = df.copy()

    # Clean text
    df[text_column] = df[text_column].apply(
        lambda x: clean_text(x, lowercase, remove_special_chars)
    )

    # Filter by length
    df = df[df[text_column].str.len() >= min_length]

    return df.reset_index(drop=True)
