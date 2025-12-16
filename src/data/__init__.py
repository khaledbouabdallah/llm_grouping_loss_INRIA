"""
Data collection and management module
"""

from .config import (
    WikidataProperties,
    WikidataEntities,
    WESTERN_COUNTRIES,
    ARABIC_COUNTRIES,
    ASIAN_COUNTRIES,
    EAST_ASIAN_COUNTRIES,
    SOUTH_ASIAN_COUNTRIES,
    SOUTHEAST_ASIAN_COUNTRIES,
    AFRICAN_COUNTRIES,
    LATIN_AMERICAN_COUNTRIES,
    COUNTRY_METADATA,
)
from .question_templates import (
    QUESTION_TEMPLATES,
    get_required_properties,
    generate_question,
)
from .database import EntityDatabase
from .wikidata_client import WikidataClient
from .wikipedia_client import WikipediaClient

__all__ = [
    "WikidataProperties",
    "WikidataEntities",
    "WESTERN_COUNTRIES",
    "ARABIC_COUNTRIES",
    "ASIAN_COUNTRIES",
    "EAST_ASIAN_COUNTRIES",
    "SOUTH_ASIAN_COUNTRIES",
    "SOUTHEAST_ASIAN_COUNTRIES",
    "AFRICAN_COUNTRIES",
    "LATIN_AMERICAN_COUNTRIES",
    "COUNTRY_METADATA",
    "QUESTION_TEMPLATES",
    "get_required_properties",
    "generate_question",
    "EntityDatabase",
    "WikidataClient",
    "WikipediaClient",
]
