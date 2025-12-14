# Project Structure

## Directory Layout

```
project/
├── src/
│   ├── __init__.py
│   ├── utils.py                      # Logging setup
│   └── data/
│       ├── __init__.py
│       ├── config.py                 # Wikidata codes, SPARQL templates
│       ├── question_templates.py     # Question definitions
│       ├── database.py               # SQLite operations
│       ├── wikidata_client.py        # Wikidata queries
│       └── wikipedia_client.py       # Wikipedia scraping
├── notebooks/
│   └── 01_data_collection.ipynb      # Use this to collect data
├── data/
│   └── entities.db                   # SQLite database (created automatically)
├── requirements.txt
└── README.md
```

## What Each Module Does

### `src/data/config.py`
- Wikidata property codes (P569 = birth date, etc.)
- Entity type codes (Q5 = human, etc.)
- Country codes (Q142 = France, etc.)
- SPARQL query templates

### `src/data/question_templates.py`
- Question templates for each entity type
- Maps questions to Wikidata properties
- Helper functions to generate questions

### `src/data/database.py`
- SQLite database with 3 tables:
  - `entities`: Main entity data
  - `facts`: Wikidata properties
  - `questions`: Generated Q&A pairs
- Automatic duplicate prevention
- Statistics and querying

### `src/data/wikidata_client.py`
- SPARQL query execution
- Rate limiting (1 sec between requests)
- Error handling and retries
- Methods: get_people(), get_discoveries(), get_places(), get_events()

### `src/data/wikipedia_client.py`
- Wikipedia article fetching
- Rate limiting (0.1 sec between requests)
- Handles disambiguation
- Returns full text + metadata

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. In your notebook

```python
# Import everything
from src.data import (
    EntityDatabase,
    WikidataClient,
    WikipediaClient,
    WESTERN_COUNTRIES,
    ARABIC_COUNTRIES,
    ASIAN_COUNTRIES,
    generate_question
)
from src.utils import setup_logging
import logging

# Setup logging
setup_logging(level=logging.INFO)

# Initialize clients
db = EntityDatabase("../data/entities.db")
wikidata = WikidataClient(rate_limit_delay=1.0)
wikipedia = WikipediaClient(language='en', rate_limit_delay=0.1)

# Collect Western people
people = wikidata.get_people(
    nationalities=WESTERN_COUNTRIES,
    limit=50
)

print(f"Got {len(people)} people")

# Add to database
for person in people:
    # Extract Wikidata ID
    wikidata_id = person['person'].split('/')[-1]
    name = person['person_label']

    # Add entity
    entity_id = db.add_entity(
        wikidata_id=wikidata_id,
        name=name,
        entity_type='person',
        culture='Western',
        country=person.get('nationality_label')
    )

    if entity_id:
        # Add facts
        db.add_fact(entity_id, 'P569', person['birthDate'])
        db.add_fact(entity_id, 'P19', person['birthPlace'], person.get('birthPlace_label'))

        # Generate questions
        q1 = generate_question('person', 'birth_date', name)
        db.add_question(entity_id, 'birth_date', q1, person['birthDate'], 'P569')

# Get statistics
print(db.get_statistics())
```

## Database Schema

### entities table
- id (PRIMARY KEY)
- wikidata_id (UNIQUE)
- name
- type (person|discovery|place|event)
- culture (Western|Arabic|Asian)
- country
- wikipedia_text
- created_at

### facts table
- id (PRIMARY KEY)
- entity_id (FOREIGN KEY)
- property (P569, P19, etc.)
- value
- value_label
- UNIQUE(entity_id, property, value)

### questions table
- id (PRIMARY KEY)
- entity_id (FOREIGN KEY)
- question_type (birth_date, birth_place, etc.)
- question_text
- ground_truth
- property
- UNIQUE(entity_id, question_type)

## Features

✅ **Automatic duplicate prevention** - Won't add same entity twice
✅ **Rate limiting** - Respects Wikidata and Wikipedia limits
✅ **Error handling** - Retries on failures
✅ **Logging** - Track progress and errors
✅ **Flexible queries** - Easy to customize SPARQL filters
✅ **Statistics** - Track collection progress

## Next Steps

1. Test with 50 entities in notebook
2. Time the full pipeline
3. Scale to 1000 entities
4. Add clustering code
5. Add LLM inference code