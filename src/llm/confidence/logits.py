"""Logits-based confidence extraction."""

from typing import List, Tuple
import torch
import numpy as np
from .base import ConfidenceExtractor


class LogitsConfidence(ConfidenceExtractor):
    """Extract confidence from token logits.

    This method computes confidence as the average probability
    of generated tokens using softmax over logits.

    Args:
        aggregation: How to aggregate token probabilities
                    ('mean', 'min', 'geometric_mean')
    """

    def __init__(self, aggregation: str = "mean"):
        self.aggregation = aggregation

        if aggregation not in ["mean", "min", "geometric_mean"]:
            raise ValueError(
                f"Unknown aggregation: {aggregation}. "
                "Choose from: 'mean', 'min', 'geometric_mean'"
            )

    def extract(self, scores: Tuple[torch.Tensor, ...]) -> List[float]:
        """Extract confidence from generation scores.

        Args:
            scores: Tuple of score tensors from model.generate()
                   Each tensor has shape (batch_size, vocab_size)

        Returns:
            List of confidence scores (one per sample in batch)
        """
        if not scores:
            raise ValueError("Empty scores tuple")

        # Stack scores: (seq_len, batch_size, vocab_size)
        scores_tensor = torch.stack(scores)

        # Apply softmax to get probabilities
        probs = torch.softmax(scores_tensor, dim=-1)

        # Get max probability for each position (greedy choice)
        max_probs = probs.max(dim=-1).values  # Shape: (seq_len, batch_size)

        # Transpose to (batch_size, seq_len)
        max_probs = max_probs.transpose(0, 1)

        # Aggregate per sequence
        confidences = []
        for seq_probs in max_probs:
            seq_probs_np = seq_probs.cpu().numpy()

            if self.aggregation == "mean":
                conf = float(np.mean(seq_probs_np))
            elif self.aggregation == "min":
                conf = float(np.min(seq_probs_np))
            elif self.aggregation == "geometric_mean":
                conf = float(np.exp(np.mean(np.log(seq_probs_np + 1e-10))))

            confidences.append(conf)

        return confidences
