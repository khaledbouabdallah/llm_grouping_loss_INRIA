# LLM Grouping Loss Project

This repository contains all code, data, and notebooks for the LLM Grouping Loss project. The goal is to analyze how large language models (LLMs) group, cluster, and answer questions about real-world entities (e.g., people, jobs) and to evaluate the impact of clustering and prompting strategies on model confidence and calibration.

---

## Project Directory Structure

```
llm_grouping_loss_INRIA/
├── src/                # Main Python source code (modularized)
│   ├── analysis/       # Metrics, correlation, and evaluation code
│   ├── clustering/     # Clustering algorithms (KMeans, DBSCAN, etc.)
│   ├── data/           # Data loading, config, question generation
│   ├── embeddings/     # Embedding and dimensionality reduction
│   ├── evaluation/     # LLM evaluation and scoring
│   ├── visualization/  # Plotting and cluster visualization
│   └── utils.py        # Shared utilities
├── notebooks/          # Jupyter/VSCode notebooks for experiments
│   ├── 00_01_resumes_example_modifed.ipynb
│   ├── 00_01_resumes_example_experiement.ipynb
│   └── ...
├── data/               # Raw and processed data, embeddings, results
│   ├── resumes.csv
│   ├── llm_generation_results.csv
│   └── experiment/
├── docs/               # Project documentation and methodology
│   ├── QUESTION_GENERATION_METHODOLOGY.md
│   ├── GROUPING_LOSS_CALCULATION.md
│   └── ...
├── scripts/            # Data collection, merging, and utility scripts
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project metadata
└── README.md           # This file
```

---

## Main Components

- **src/**: All core code for clustering, analysis, embeddings, evaluation, and visualization
- **notebooks/**: Interactive notebooks for data exploration, clustering experiments, LLM prompting, and evaluation
- **data/**: Input data (resumes, embeddings), experiment outputs, and results
- **docs/**: Methodology, schema, and project documentation
- **scripts/**: Helper scripts for data collection and processing

---

## Typical Workflow

1. **Data Preparation**: Load and preprocess resumes or entity data (see `data/` and `notebooks/`)
2. **Embedding Generation**: Compute or load text embeddings for entities
3. **Clustering**: Apply KMeans, DBSCAN, or other clustering methods (see `src/clustering/` and notebooks)
4. **Prompt Engineering**: Experiment with different LLM prompts to generate answers for each entity/cluster
5. **LLM Inference**: Run LLMs (e.g., Mistral, Phi-2, TinyLlama) to generate answers and extract token-level confidence
6. **Evaluation**: Analyze model confidence, grouping loss, and calibration across clusters and prompts
7. **Visualization**: Plot results, cluster assignments, and confidence distributions

---

## Key Files & Folders

- `src/` - Modular code for all major steps (clustering, embeddings, evaluation, etc.)
- `notebooks/` - Main entry point for experiments and analysis
- `data/` - All input data, intermediate results, and experiment outputs
- `docs/` - Methodology and documentation for reproducibility

---

## Getting Started

1. **Install dependencies**
   ```bash
   uv sync
   ```

2. **Open a notebook** in `notebooks/` and follow the instructions in the markdown cells
3. **Modify configuration cells** to change clustering method, prompt style, or LLM model

---

## Notes
- GPU recommended for LLM inference (CPU is supported but much slower)
- See `docs/` for detailed methodology and schema
- data is uploaded seperatly and it will be made availbale