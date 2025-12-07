"""Template-based question generator."""

from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from .base import QuestionGenerator
from .templates import get_template_set


class TemplateGenerator(QuestionGenerator):
    """Generate questions using predefined templates.

    This generator takes entity names/descriptions and fills them into
    question templates.

    Args:
        templates: List of template strings or name of template set
        entity_column: Column name containing entity names (default: 'id')
        questions_per_entity: Number of questions to generate per entity
        seed: Random seed for reproducibility

    Example:
        >>> generator = TemplateGenerator(
        ...     templates=["Who is {entity}?", "What is {entity} known for?"],
        ...     questions_per_entity=2
        ... )
        >>> questions_df = generator.generate(corpus_df, labels)
    """

    def __init__(
        self,
        templates: List[str] | str,
        entity_column: str = "id",
        questions_per_entity: int = 1,
        seed: Optional[int] = 42,
    ):
        # Load templates
        if isinstance(templates, str):
            self.templates = get_template_set(templates)
        else:
            self.templates = templates

        self.entity_column = entity_column
        self.questions_per_entity = questions_per_entity
        self.seed = seed

        if not self.templates:
            raise ValueError("At least one template must be provided")

        # Set random seed
        if seed is not None:
            np.random.seed(seed)

    def generate(self, corpus_df: pd.DataFrame, labels: List[int]) -> pd.DataFrame:
        """Generate questions from corpus using templates.

        Args:
            corpus_df: DataFrame with corpus (must have entity_column)
            labels: Cluster labels

        Returns:
            DataFrame with generated questions
        """
        if self.entity_column not in corpus_df.columns:
            raise ValueError(
                f"Entity column '{self.entity_column}' not found in corpus"
            )

        if len(corpus_df) != len(labels):
            raise ValueError("Corpus and labels must have same length")

        # Add labels to corpus
        corpus_with_labels = corpus_df.copy()
        corpus_with_labels["cluster_id"] = labels

        questions = []
        question_id = 0

        for idx, row in corpus_with_labels.iterrows():
            entity = row[self.entity_column]
            cluster_id = row["cluster_id"]
            entity_id = row.get("id", idx)

            # Select templates for this entity
            selected_templates = self._select_templates(self.questions_per_entity)

            for template in selected_templates:
                question_text = template.format(entity=entity)

                questions.append(
                    {
                        "id": question_id,
                        "entity_id": entity_id,
                        "cluster_id": int(cluster_id),
                        "question": question_text,
                        "template": template,
                        "entity": entity,
                    }
                )

                question_id += 1

        return pd.DataFrame(questions)

    def _select_templates(self, n: int) -> List[str]:
        """Select n templates randomly (with or without replacement).

        Args:
            n: Number of templates to select

        Returns:
            List of selected templates
        """
        if n <= len(self.templates):
            # Sample without replacement
            return list(np.random.choice(self.templates, size=n, replace=False))
        else:
            # Sample with replacement if we need more templates than available
            return list(np.random.choice(self.templates, size=n, replace=True))
