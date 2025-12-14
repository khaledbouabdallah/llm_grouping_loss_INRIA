"""
Question templates for each entity type
"""

from .config import WikidataProperties as P


# ============================================================================
# QUESTION TEMPLATES
# ============================================================================

PEOPLE_QUESTIONS = {
    "birth_date": {
        "template": "When was {name} born?",
        "property": P.BIRTH_DATE,
        "required": True,
    },
    "birth_place": {
        "template": "Where was {name} born?",
        "property": P.BIRTH_PLACE,
        "required": True,
    },
    "death_date": {
        "template": "When did {name} die?",
        "property": P.DEATH_DATE,
        "required": False,  # Not everyone is dead
    },
    "nationality": {
        "template": "What is {name}'s nationality?",
        "property": P.NATIONALITY,
        "required": True,
    },
    "occupation": {
        "template": "What is {name}'s occupation?",
        "property": P.OCCUPATION,
        "required": True,
    },
}

DISCOVERY_QUESTIONS = {
    "inventor": {
        "template": "Who invented {name}?",
        "property": P.INVENTOR,
        "required": True,
    },
    "discovery_date": {
        "template": "When was {name} invented?",
        "property": P.DISCOVERY_DATE,
        "required": True,
    },
    "country": {
        "template": "What country was {name} invented in?",
        "property": P.COUNTRY_OF_ORIGIN,
        "required": False,
    },
}

PLACE_QUESTIONS = {
    "country": {
        "template": "What country is {name} in?",
        "property": P.COUNTRY,
        "required": True,
    },
    "population": {
        "template": "What is the population of {name}?",
        "property": P.POPULATION,
        "required": False,
    },
    "coordinates": {
        "template": "What are the coordinates of {name}?",
        "property": P.COORDINATES,
        "required": True,
    },
}

EVENT_QUESTIONS = {
    "event_date": {
        "template": "When did {name} occur?",
        "property": P.POINT_IN_TIME,
        "required": True,
    },
    "event_location": {
        "template": "Where did {name} take place?",
        "property": P.LOCATION,
        "required": True,
    },
    "participants": {
        "template": "Who participated in {name}?",
        "property": P.PARTICIPANT,
        "required": False,
    },
}


# ============================================================================
# TEMPLATE MAPPING
# ============================================================================

QUESTION_TEMPLATES = {
    "person": PEOPLE_QUESTIONS,
    "discovery": DISCOVERY_QUESTIONS,
    "place": PLACE_QUESTIONS,
    "event": EVENT_QUESTIONS,
}


def get_required_properties(entity_type: str) -> list:
    """Get list of required Wikidata properties for entity type"""
    templates = QUESTION_TEMPLATES.get(entity_type, {})
    return [q["property"] for q in templates.values() if q["required"]]


def generate_question(entity_type: str, question_type: str, entity_name: str) -> str:
    """Generate question from template"""
    templates = QUESTION_TEMPLATES.get(entity_type, {})
    question_config = templates.get(question_type)

    if not question_config:
        raise ValueError(
            f"Unknown question type: {question_type} for entity type: {entity_type}"
        )

    return question_config["template"].format(name=entity_name)
