"""Question template definitions."""

from typing import Dict, List

# Template sets for different languages and domains
TEMPLATE_SETS: Dict[str, List[str]] = {
    "english_biography": [
        "Who is {entity}?",
        "What is {entity} known for?",
        "When was {entity} born?",
        "Where was {entity} born?",
        "What is the nationality of {entity}?",
        "What are the main achievements of {entity}?",
        "In which field did {entity} work?",
    ],
    "french_biography": [
        "Qui est {entity} ?",
        "Pour quoi {entity} est-il/elle connu(e) ?",
        "Quand {entity} est-il/elle né(e) ?",
        "Où {entity} est-il/elle né(e) ?",
        "Quelle est la nationalité de {entity} ?",
        "Quelles sont les principales réalisations de {entity} ?",
        "Dans quel domaine {entity} a-t-il/elle travaillé ?",
    ],
    "french_profession": [
        "Quelles sont les compétences d'un(e) {entity} ?",
        "Quel est le salaire moyen d'un(e) {entity} ?",
        "Quel parcours pour devenir {entity} ?",
        "Quelles qualités pour exceller comme {entity} ?",
        "Quelles sont les missions d'un(e) {entity} ?",
    ],
    "english_general": [
        "Tell me about {entity}.",
        "What do you know about {entity}?",
        "Describe {entity}.",
        "What are the key facts about {entity}?",
    ],
    "factual_questions": [
        "What is the birth date of {entity}?",
        "What is the nationality of {entity}?",
        "Where did {entity} die?",
        "What is the occupation of {entity}?",
    ],
}


def get_template_set(name: str) -> List[str]:
    """Get a template set by name.

    Args:
        name: Name of template set

    Returns:
        List of template strings

    Raises:
        ValueError: If template set not found
    """
    if name not in TEMPLATE_SETS:
        available = ", ".join(TEMPLATE_SETS.keys())
        raise ValueError(
            f"Unknown template set: '{name}'. " f"Available sets: {available}"
        )

    return TEMPLATE_SETS[name]
