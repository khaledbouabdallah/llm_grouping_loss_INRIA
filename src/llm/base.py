"""Abstract base class for LLM interfaces."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd


class LLMInterface(ABC):
    """Abstract base class for LLM interaction.

    All LLM interfaces should inherit from this class.
    """

    @abstractmethod
    def generate(
        self, prompts: List[str], max_new_tokens: int = 50, **kwargs
    ) -> List[str]:
        """Generate responses for prompts.

        Args:
            prompts: List of input prompts
            max_new_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters

        Returns:
            List of generated responses
        """
        pass

    @abstractmethod
    def get_confidence(
        self, prompts: List[str], responses: List[str], **kwargs
    ) -> List[float]:
        """Extract confidence scores for responses.

        Args:
            prompts: List of input prompts
            responses: List of generated responses
            **kwargs: Additional parameters

        Returns:
            List of confidence scores (0.0 to 1.0)
        """
        pass

    def generate_with_confidence(
        self,
        questions_df: pd.DataFrame,
        question_column: str = "question",
        batch_size: int = 8,
        **kwargs,
    ) -> pd.DataFrame:
        """Generate responses and extract confidence scores.

        Args:
            questions_df: DataFrame with questions
            question_column: Name of question column
            batch_size: Batch size for processing
            **kwargs: Additional parameters

        Returns:
            DataFrame with responses and confidence scores
        """
        questions = questions_df[question_column].tolist()

        # Generate responses in batches
        all_responses = []
        all_confidences = []

        for i in range(0, len(questions), batch_size):
            batch_questions = questions[i : i + batch_size]

            # Generate
            batch_responses = self.generate(batch_questions, **kwargs)

            # Get confidence
            batch_confidences = self.get_confidence(
                batch_questions, batch_responses, **kwargs
            )

            all_responses.extend(batch_responses)
            all_confidences.extend(batch_confidences)

        # Add to dataframe
        result_df = questions_df.copy()
        result_df["response"] = all_responses
        result_df["confidence"] = all_confidences

        return result_df
