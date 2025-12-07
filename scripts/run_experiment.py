"""Run an experiment from configuration file."""

import sys
import argparse
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.logging_setup import setup_logging
from src.pipeline.phase1 import Phase1Pipeline


def main():
    """Main entry point for running experiments."""
    parser = argparse.ArgumentParser(
        description="Run LLM Grouping Loss experiment from config file"
    )
    parser.add_argument(
        "config", type=str, help="Path to experiment configuration YAML file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Setup logging
    log_file = Path(config["output"]["dir"]) / "experiment.log"
    logger = setup_logging(log_file=log_file, level=args.log_level)

    logger.info(f"=" * 80)
    logger.info(f"Starting experiment: {config['name']}")
    logger.info(f"Configuration: {args.config}")
    logger.info(f"=" * 80)

    # Determine pipeline phase
    phase = config.get("phase", 1)

    if phase == 1:
        pipeline = Phase1Pipeline(config)
    else:
        raise ValueError(f"Unknown phase: {phase}")

    # Run pipeline
    try:
        results = pipeline.run()
        pipeline.save_results(results)

        logger.info(f"=" * 80)
        logger.info(f"Experiment completed successfully!")
        logger.info(f"Results saved to: {config['output']['dir']}")
        logger.info(f"=" * 80)

    except Exception as e:
        logger.error(f"Experiment failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
