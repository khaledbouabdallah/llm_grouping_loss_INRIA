"""Input/output utilities for saving and loading results."""

import json
import pickle
from pathlib import Path
from typing import Any, Dict
from dataclasses import is_dataclass, asdict
import pandas as pd
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types and dataclasses."""

    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def _convert_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {k: _convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_for_json(item) for item in obj]
    return obj


def save_results(results: Dict[str, Any], output_dir: Path, prefix: str = "") -> None:
    """Save experiment results to disk.

    Args:
        results: Dictionary containing results to save
        output_dir: Directory to save results
        prefix: Optional prefix for filenames
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for key, value in results.items():
        filename = f"{prefix}{key}" if prefix else key
        filepath = output_dir / filename

        # Save based on data type
        if isinstance(value, pd.DataFrame):
            value.to_csv(f"{filepath}.csv", index=False)
        elif isinstance(value, np.ndarray):
            np.save(f"{filepath}.npy", value)
        elif isinstance(value, dict):
            # Handle nested dictionaries with DataFrames
            converted = _convert_for_json(value)
            with open(f"{filepath}.json", "w") as f:
                json.dump(converted, f, indent=2, cls=NumpyEncoder)
        elif isinstance(value, list):
            converted = _convert_for_json(value)
            with open(f"{filepath}.json", "w") as f:
                json.dump(converted, f, indent=2, cls=NumpyEncoder)
        else:
            # Fallback to pickle for other types
            with open(f"{filepath}.pkl", "wb") as f:
                pickle.dump(value, f)


def load_results(results_dir: Path, filename: str) -> Any:
    """Load results from disk.

    Args:
        results_dir: Directory containing results
        filename: Name of file to load (without extension)

    Returns:
        Loaded data

    Raises:
        FileNotFoundError: If no file with given name exists
    """
    results_dir = Path(results_dir)

    # Try different extensions
    for ext, loader in [
        (".csv", lambda p: pd.read_csv(p)),
        (".npy", lambda p: np.load(p, allow_pickle=True)),
        (".json", lambda p: json.load(open(p))),
        (".pkl", lambda p: pickle.load(open(p, "rb"))),
    ]:
        filepath = results_dir / f"{filename}{ext}"
        if filepath.exists():
            return loader(filepath)

    raise FileNotFoundError(f"No results file found for '{filename}' in {results_dir}")


def save_config(config: Dict[str, Any], output_dir: Path) -> None:
    """Save configuration to output directory.

    Args:
        config: Configuration dictionary
        output_dir: Output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    import yaml

    with open(output_dir / "config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
