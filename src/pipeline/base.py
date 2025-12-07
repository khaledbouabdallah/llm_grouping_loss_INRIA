"""Abstract base class for experiment pipelines."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class Pipeline(ABC):
    """Abstract base class for experiment pipelines."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize pipeline with configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.output_dir = Path(config["output"]["dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Run the complete pipeline.

        Returns:
            Dictionary containing results
        """
        pass

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save pipeline results.

        Args:
            results: Results dictionary to save
        """
        from ..utils.io import save_results, save_config

        # Save configuration
        save_config(self.config, self.output_dir)

        # Save results
        save_results(results, self.output_dir)
