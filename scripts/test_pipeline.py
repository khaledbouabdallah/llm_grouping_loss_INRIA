"""Simple test to verify the pipeline works end-to-end."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.loaders.simple import SimpleTextLoader
from src.embeddings import TfidfEmbedder
from src.clustering import KMeansClusterer
from src.evaluation import evaluate_clustering
from src.qa import TemplateGenerator


def test_basic_pipeline():
    """Test basic pipeline components."""

    print("Testing LLM Grouping Loss Pipeline Components...")
    print("=" * 60)

    # Test 1: Data loading
    print("\n1. Testing data loader...")
    try:
        loader = SimpleTextLoader(
            file_path="data/raw/sample_entities.csv",
            id_column="id",
            text_column="description",
        )
        df = loader.load()
        print(f"   ✓ Loaded {len(df)} entities")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 2: Embeddings
    print("\n2. Testing TF-IDF embedder...")
    try:
        embedder = TfidfEmbedder(max_features=50, ngram_range=(1, 2))
        texts = df["text"].tolist()
        embeddings = embedder.fit_transform(texts)
        print(f"   ✓ Generated embeddings: {embeddings.shape}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 3: Clustering
    print("\n3. Testing K-Means clustering...")
    try:
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        labels = clusterer.fit_predict(embeddings)
        print(f"   ✓ Clustered into {len(set(labels))} clusters")
        print(
            f"   Cluster sizes: {dict(zip(*zip(*[(l, (labels == l).sum()) for l in set(labels)])))}"
        )
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 4: Clustering evaluation
    print("\n4. Testing clustering metrics...")
    try:
        metrics = evaluate_clustering(embeddings, labels)
        print(f"   ✓ Silhouette Score: {metrics.silhouette:.3f}")
        print(f"   ✓ Davies-Bouldin: {metrics.davies_bouldin:.3f}")
        print(f"   ✓ Calinski-Harabasz: {metrics.calinski_harabasz:.2f}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 5: Question generation
    print("\n5. Testing question generator...")
    try:
        generator = TemplateGenerator(
            templates=["Who is {entity}?", "What is {entity} known for?"],
            questions_per_entity=2,
        )
        questions_df = generator.generate(df, labels)
        print(f"   ✓ Generated {len(questions_df)} questions")
        print(f"   Sample: '{questions_df.iloc[0]['question']}'")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ All component tests passed!")
    print("\nYou can now run a full experiment with:")
    print("  python scripts/run_experiment.py configs/experiments/phase1_simple.yaml")

    return True


if __name__ == "__main__":
    success = test_basic_pipeline()
    sys.exit(0 if success else 1)
