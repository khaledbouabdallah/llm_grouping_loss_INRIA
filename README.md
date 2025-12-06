# LLM Grouping Loss Analysis

**Student:** Khaled Bouabdallah
**Supervisor:** Laure Bourgois (INRIA Saclay)
**Institution:** Université Paris-Saclay - M2 Data Science
**Reference Paper:** "Reconfidencing LLMs from the Grouping Loss Perspective" (Chen et al., EMNLP 2024)

## Overview

This project implements a modular pipeline for measuring **grouping loss** in Large Language Models (LLMs) - the phenomenon where models show different confidence calibration across entity clusters, leading to algorithmic bias.

### Project Goal

Identify and measure confidence bias in LLMs by:
1. Clustering a text corpus to discover entity groups
2. Generating questions from clusters
3. Querying LLMs and extracting confidence scores
4. Analyzing confidence differences across clusters

## Features

- ✅ **Modular Architecture**: Plug-and-play components with abstract base classes
- ✅ **sklearn-Focused**: Extensive use of scikit-learn for clustering and metrics
- ✅ **Config-Driven**: All experiments via YAML configuration
- ✅ **Multiple Clustering Methods**: K-Means, Hierarchical (Agglomerative), and more
- ✅ **Flexible Embeddings**: TF-IDF (sklearn), Sentence-BERT
- ✅ **LLM-Agnostic**: Support for any HuggingFace decoder model (GPT-2, Mistral, LLaMA)
- ✅ **Confidence Extraction**: Logits-based method for white-box models
- ✅ **Comprehensive Evaluation**: Silhouette, Davies-Bouldin, Calinski-Harabasz scores
- ✅ **Statistical Analysis**: ANOVA, t-tests for confidence gap significance
- ✅ **Rich Visualizations**: Cluster plots, confidence distributions

## Project Structure

```
llm_grouping_loss_INRIA/
├── src/
│   ├── data/              # Corpus loading and preprocessing
│   ├── embeddings/        # Text embedding (TF-IDF, SBERT)
│   ├── clustering/        # Clustering algorithms (sklearn)
│   ├── qa/                # Question generation
│   ├── llm/               # LLM interface and confidence extraction
│   ├── evaluation/        # Metrics (clustering quality, confidence gap)
│   ├── visualization/     # Plotting functions
│   ├── pipeline/          # End-to-end pipelines
│   └── utils/             # Configuration, logging, I/O
├── configs/
│   ├── experiments/       # Experiment configurations
│   └── defaults/          # Default component configs
├── scripts/
│   └── run_experiment.py  # Main entry point
├── data/
│   ├── raw/               # Original datasets
│   └── processed/         # Generated questions, results
├── experiments/           # Experiment outputs
└── notebooks/             # Jupyter notebooks for exploration
```

## Installation

### 1. Clone Repository

```bash
cd llm_grouping_loss_INRIA
```

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv pip install -e .
```

Or using `pip`:
```bash
pip install -e .
```

For development tools:
```bash
uv pip install -e ".[dev]"
```

## Quick Start

### 1. Prepare Your Data

Create a CSV file with entity descriptions:

```csv
id,description
Albert Einstein,German-born theoretical physicist who developed the theory of relativity
Marie Curie,Polish-French physicist and chemist who conducted pioneering research on radioactivity
...
```

Place it in `data/raw/sample_entities.csv`.

### 2. Run Simple Test Experiment

```bash
python scripts/run_experiment.py configs/experiments/phase1_simple.yaml
```

This will:
- Load your corpus
- Generate TF-IDF embeddings
- Cluster using K-Means and Hierarchical clustering
- Generate questions from templates
- Query GPT-2 and extract confidence scores
- Analyze confidence gaps across clusters
- Create visualizations

### 3. View Results

Results are saved to `experiments/phase1_simple_test/`:
- `config.yaml` - Configuration used
- `experiment.log` - Detailed logs
- `cluster_statistics.csv` - Statistics per cluster
- `confidence_analysis.json` - Confidence gap analysis
- `visualizations/` - Plots (clusters, confidence distributions)

## Configuration

### Example Configuration

```yaml
name: "my_experiment"
phase: 1

corpus:
  loader: "simple"
  params:
    file_path: "data/raw/entities.csv"
    id_column: "name"
    text_column: "description"

embeddings:
  method: "tfidf"  # or "sbert"
  params:
    max_features: 500
    ngram_range: [1, 2]

clustering:
  methods:
    - name: "kmeans"
      params:
        n_clusters: 10
        random_state: 42
    - name: "hierarchical"
      params:
        n_clusters: 10
        linkage: "ward"

question_generation:
  generator: "template_based"
  params:
    templates: "english_biography"
    questions_per_entity: 3

llm:
  model_name: "gpt2"  # or "mistralai/Mistral-7B-Instruct-v0.3"
  params:
    device: "auto"
    load_in_4bit: false

output:
  dir: "experiments/my_experiment"
```

### Swapping Components

**Change embedding method:**
```yaml
embeddings:
  method: "sbert"
  params:
    model_name: "all-MiniLM-L6-v2"
```

**Use larger model:**
```yaml
llm:
  model_name: "mistralai/Mistral-7B-Instruct-v0.3"
  params:
    load_in_4bit: true  # Quantization for memory efficiency
```

**Try different clustering:**
```yaml
clustering:
  methods:
    - name: "hierarchical"
      params:
        n_clusters: 15
        linkage: "average"
```

## Key Components

### Embeddings

**TF-IDF (sklearn):**
```python
from src.embeddings import TfidfEmbedder

embedder = TfidfEmbedder(max_features=500, ngram_range=(1, 2))
embeddings = embedder.fit_transform(texts)
```

**Sentence-BERT:**
```python
from src.embeddings import SBertEmbedder

embedder = SBertEmbedder(model_name='all-MiniLM-L6-v2')
embeddings = embedder.fit_transform(texts)
```

### Clustering (sklearn)

**K-Means:**
```python
from src.clustering import KMeansClusterer

clusterer = KMeansClusterer(n_clusters=10, random_state=42)
labels = clusterer.fit_predict(embeddings)
```

**Hierarchical:**
```python
from src.clustering import HierarchicalClusterer

clusterer = HierarchicalClusterer(n_clusters=10, linkage='ward')
labels = clusterer.fit_predict(embeddings)
```

### Evaluation (sklearn)

```python
from src.evaluation import evaluate_clustering

metrics = evaluate_clustering(embeddings, labels)
print(f"Silhouette Score: {metrics.silhouette:.3f}")
print(f"Davies-Bouldin Index: {metrics.davies_bouldin:.3f}")
print(f"Calinski-Harabasz Score: {metrics.calinski_harabasz:.2f}")
```

### Confidence Analysis

```python
from src.evaluation import confidence_gap_analysis

results = confidence_gap_analysis(confidences, labels, perform_tests=True)
print(f"Confidence Gap: {results['confidence_gap']:.4f}")
print(f"ANOVA p-value: {results['anova']['p_value']:.4f}")
```

## Available Template Sets

- `english_biography` - Biographical questions in English
- `french_biography` - Biographical questions in French
- `french_profession` - Professional questions in French
- `english_general` - General questions
- `factual_questions` - Factual queries (nationality, birthdate, etc.)

## Metrics

### Clustering Quality (sklearn)

- **Silhouette Score**: -1 to 1 (higher is better)
- **Davies-Bouldin Index**: Lower is better
- **Calinski-Harabasz Score**: Higher is better

### Confidence Gap (Phase 1)

- **Confidence Gap**: Variance of mean confidences across clusters
- **ANOVA Test**: Statistical significance of differences
- **Pairwise t-tests**: Which clusters differ significantly

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ scripts/
ruff check src/ scripts/
```

### Type Checking

```bash
mypy src/
```

## Roadmap

### Phase 1: Confidence Gap Analysis ✅
- [x] Modular architecture
- [x] sklearn-based clustering
- [x] Confidence extraction
- [x] Statistical analysis

### Phase 2: Grouping Loss (Future)
- [ ] Ground truth integration
- [ ] Calibration error calculation
- [ ] Full grouping loss metric

### Extensions (Optional)
- [ ] Additional clustering methods (DBSCAN, Spectral)
- [ ] Cross-lingual analysis
- [ ] Interactive dashboard (Streamlit/Gradio)
- [ ] Model comparison framework

## References

- **Paper**: Chen et al. (2024). "Reconfidencing LLMs from the Grouping Loss Perspective". EMNLP 2024.
- **arXiv**: https://arxiv.org/abs/2402.04957
- **Code**: https://github.com/tigerchen52/reconfidencing_llms

## License

This project is for academic research purposes at Université Paris-Saclay.

## Contact

- **Student**: Khaled Bouabdallah
- **Supervisor**: Laure Bourgois (laure.bourgois@inria.fr)
- **Institution**: INRIA Saclay, Université Paris-Saclay
