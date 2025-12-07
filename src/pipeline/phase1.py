"""Phase 1 Pipeline: Confidence gap analysis without ground truth."""

from typing import Dict, Any
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm

from .base import Pipeline
from ..data.loaders.simple import SimpleTextLoader
from ..data.preprocessing import preprocess_corpus
from ..embeddings.factory import EmbedderFactory
from ..clustering.factory import ClustererFactory
from ..qa.template_based import TemplateGenerator
from ..llm.decoder import DecoderLLM
from ..evaluation.clustering import evaluate_clustering
from ..evaluation.confidence import confidence_gap_analysis
from ..visualization.clusters import plot_clusters, plot_cluster_sizes
from ..visualization.confidence import (
    plot_confidence_distribution,
    plot_confidence_by_cluster,
)


class Phase1Pipeline(Pipeline):
    """Phase 1: Confidence gap analysis pipeline.

    This pipeline measures confidence differences across clusters
    without requiring ground truth answers.

    Steps:
        1. Load corpus
        2. Preprocess text
        3. Generate embeddings
        4. Cluster embeddings
        5. Evaluate clustering
        6. Generate questions
        7. Query LLM and extract confidence
        8. Analyze confidence gaps
        9. Visualize results
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger("llm_grouping_loss.phase1")

    def run(self) -> Dict[str, Any]:
        """Run Phase 1 pipeline.

        Returns:
            Dictionary containing all results
        """
        self.logger.info("Starting Phase 1 Pipeline: Confidence Gap Analysis")

        results = {}

        # Step 1: Load corpus
        self.logger.info("Step 1: Loading corpus...")
        corpus_df = self._load_corpus()
        results["corpus_size"] = len(corpus_df)
        self.logger.info(f"Loaded {len(corpus_df)} items")

        # Step 2: Preprocess
        self.logger.info("Step 2: Preprocessing...")
        corpus_df = self._preprocess_corpus(corpus_df)
        results["corpus_size_after_preprocessing"] = len(corpus_df)

        # Step 3: Generate embeddings
        self.logger.info("Step 3: Generating embeddings...")
        embeddings, embedder = self._generate_embeddings(corpus_df)
        results["embedding_dim"] = embeddings.shape[1]
        results["embeddings"] = embeddings

        # Step 4: Cluster
        self.logger.info("Step 4: Clustering...")
        clustering_results = self._cluster_embeddings(embeddings)
        results.update(clustering_results)

        # Step 5: Evaluate clustering
        self.logger.info("Step 5: Evaluating clustering...")
        for method_name, method_results in clustering_results["methods"].items():
            labels = method_results["labels"]
            metrics = evaluate_clustering(embeddings, labels)
            method_results["metrics"] = metrics
            self.logger.info(f"{method_name}:\n{metrics}")

        # Step 6: Generate questions (use first clustering method)
        self.logger.info("Step 6: Generating questions...")
        first_method = list(clustering_results["methods"].keys())[0]
        labels = clustering_results["methods"][first_method]["labels"]
        questions_df = self._generate_questions(corpus_df, labels)
        results["n_questions"] = len(questions_df)
        results["questions"] = questions_df
        self.logger.info(f"Generated {len(questions_df)} questions")

        # Step 7: Query LLM
        self.logger.info("Step 7: Querying LLM and extracting confidence...")
        responses_df = self._query_llm(questions_df)
        results["responses"] = responses_df

        # Step 8: Analyze confidence gaps
        self.logger.info("Step 8: Analyzing confidence gaps...")
        confidence_results = self._analyze_confidence(responses_df)
        results["confidence_analysis"] = confidence_results

        # Step 9: Visualizations
        self.logger.info("Step 9: Creating visualizations...")
        self._create_visualizations(embeddings, labels, responses_df)

        self.logger.info("Phase 1 Pipeline completed successfully!")

        return results

    def _load_corpus(self) -> pd.DataFrame:
        """Load corpus from configuration."""
        loader_config = self.config["corpus"]
        loader_type = loader_config.get("loader", "simple")

        if loader_type == "simple":
            loader = SimpleTextLoader(**loader_config.get("params", {}))
        else:
            raise ValueError(f"Unknown loader type: {loader_type}")

        return loader.load()

    def _preprocess_corpus(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess corpus text."""
        preprocessing_config = self.config.get("preprocessing", {})
        return preprocess_corpus(df, **preprocessing_config)

    def _generate_embeddings(self, df: pd.DataFrame):
        """Generate embeddings from text."""
        embedding_config = self.config["embeddings"]
        method = embedding_config["method"]
        params = embedding_config.get("params", {})

        embedder = EmbedderFactory.create(method, **params)
        texts = df["text"].tolist()
        embeddings = embedder.fit_transform(texts)

        return embeddings, embedder

    def _cluster_embeddings(self, embeddings: np.ndarray) -> Dict[str, Any]:
        """Cluster embeddings using configured methods."""
        clustering_config = self.config["clustering"]
        methods_config = clustering_config.get("methods", [])

        results = {"methods": {}}

        for method_config in methods_config:
            method_name = method_config["name"]
            params = method_config.get("params", {})

            self.logger.info(f"  Clustering with {method_name}...")
            clusterer = ClustererFactory.create(method_name, **params)
            labels = clusterer.fit_predict(embeddings)

            results["methods"][method_name] = {
                "labels": labels,
                "n_clusters": len(np.unique(labels)),
            }

        return results

    def _generate_questions(
        self, corpus_df: pd.DataFrame, labels: np.ndarray
    ) -> pd.DataFrame:
        """Generate questions from corpus."""
        qa_config = self.config["question_generation"]
        params = qa_config.get("params", {})

        generator = TemplateGenerator(**params)
        return generator.generate(corpus_df, labels)

    def _query_llm(self, questions_df: pd.DataFrame) -> pd.DataFrame:
        """Query LLM and extract confidence scores."""
        llm_config = self.config["llm"]
        model_name = llm_config.get("model_name", "gpt2")
        params = llm_config.get("params", {})

        self.logger.info(f"  Loading model: {model_name}")
        llm = DecoderLLM(model_name=model_name, **params)

        # Generate with confidence
        batch_size = llm_config.get("batch_size", 8)
        max_new_tokens = llm_config.get("max_new_tokens", 50)

        return llm.generate_with_confidence(
            questions_df, batch_size=batch_size, max_new_tokens=max_new_tokens
        )

    def _analyze_confidence(self, responses_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze confidence gaps across clusters."""
        confidences = responses_df["confidence"].values
        labels = responses_df["cluster_id"].values

        return confidence_gap_analysis(confidences, labels, perform_tests=True)

    def _create_visualizations(
        self, embeddings: np.ndarray, labels: np.ndarray, responses_df: pd.DataFrame
    ) -> None:
        """Create and save visualizations."""
        viz_dir = self.output_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)

        # Cluster visualization
        plot_clusters(
            embeddings, labels, method="pca", save_path=viz_dir / "clusters_pca.png"
        )

        plot_cluster_sizes(labels, save_path=viz_dir / "cluster_sizes.png")

        # Confidence visualizations
        confidences = responses_df["confidence"].values
        cluster_labels = responses_df["cluster_id"].values

        plot_confidence_distribution(
            confidences, save_path=viz_dir / "confidence_distribution.png"
        )

        plot_confidence_by_cluster(
            confidences, cluster_labels, save_path=viz_dir / "confidence_by_cluster.png"
        )

        self.logger.info(f"Visualizations saved to {viz_dir}")
