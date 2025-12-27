# Data Collection Methodology

**Project:** LLM Grouping Loss Evaluation Across Cultures and Languages
**Author:** Khaled Bouabdallah
**Institution:** Université Paris-Saclay - M2 Data Science
**Date:** December 2024

---

## Table of Contents

1. [Overview](#1-overview)
2. [Data Sources](#2-data-sources)
3. [Entity Types Collected](#3-entity-types-collected)
4. [Multilingual Strategy](#4-multilingual-strategy)
5. [Data Collection Pipeline](#5-data-collection-pipeline)
6. [Metadata Collected](#6-metadata-collected)
7. [Data Quality Measures](#7-data-quality-measures)
8. [Database Schema](#8-database-schema)
9. [Dimensions for Analysis](#9-dimensions-for-analysis)
10. [Data Collection Statistics](#10-data-collection-statistics)
11. [Limitations and Biases](#11-limitations-and-biases)
12. [Reproducibility](#12-reproducibility)
13. [Usage Examples](#13-usage-examples)
14. [Appendix](#14-appendix)

---

## 1. Overview

### 1.1 Research Context

This document describes the data collection methodology for evaluating grouping loss in Large Language Models (LLMs) across different cultural groups and languages. Grouping loss measures the heterogeneity in confidence calibration across sub-groups, revealing whether LLMs exhibit systematic biases toward certain entities.

### 1.2 Research Questions

1. **Cultural Bias**: Do LLMs show different calibration quality for Western vs Arabic vs Asian entities?
2. **Language Effect**: Does the question language (English, French, Arabic) affect LLM performance on the same entity?
3. **Wikipedia Correlation**: Does Wikipedia article availability/quality predict LLM knowledge and confidence?
4. **Temporal Bias**: Are LLMs better calibrated on modern vs historical entities?

### 1.3 Data Collection Goals

- Collect entities with **complete multilingual labels** (English, French, Arabic)
- Include entities with **varying Wikipedia coverage** (0-3 languages) to test correlation
- Gather **rich metadata** for multidimensional analysis
- Support **two experimental designs**:
  - Experiment 1: Language-specific clustering (separate analyses per language)
  - Experiment 2: Cross-language comparison (same entities in all languages)

### 1.4 High-Level Pipeline

```
┌─────────────┐
│  Wikidata   │ ──> Query entities with multilingual labels
│   (SPARQL)  │     + metadata (gender, dates, Wikipedia count)
└─────────────┘
       │
       ▼
┌─────────────┐
│   Filter    │ ──> Keep only entities with complete labels
│  Complete   │     (English + French + Arabic)
│   Labels    │
└─────────────┘
       │
       ▼
┌─────────────┐
│  Wikipedia  │ ──> Fetch articles in en, fr, ar
│   Articles  │     + Extract metadata (length, backlinks)
└─────────────┘
       │
       ▼
┌─────────────┐
│   SQLite    │ ──> Store structured data
│  Database   │     (entities, labels, facts, Wikipedia texts)
└─────────────┘
```

---

## 2. Data Sources

### 2.1 Wikidata

**Source**: https://www.wikidata.org/
**Access Method**: SPARQL endpoint (https://query.wikidata.org/sparql)
**Rate Limiting**: 1 second between requests

**What We Extract:**
- Entity identifiers (Q-codes)
- Properties: birth date, birth place, nationality, occupation, gender, death date
- Multilingual labels in English (en), French (fr), Arabic (ar/arz)
- Sitelinks count (number of Wikipedia language versions)

**Why Wikidata:**
- Structured, machine-readable knowledge base
- Multilingual by design
- Authoritative source with community curation
- Provides ground truth for factual questions

**Limitations:**
- Completeness varies by entity
- Western entities better documented than non-Western
- Some properties may be missing or outdated

### 2.2 Wikipedia

**Source**: Wikipedia API (https://wikipedia.org/w/api.php)
**Access Method**: Python `wikipedia` library + direct API calls
**Rate Limiting**: 0.1 seconds between requests
**Languages**: English (en), French (fr), Arabic (ar)

**What We Extract:**
- Article title, content, summary, URL
- Text length (characters and words)
- Number of sections (approximate)

**Why Wikipedia:**
- Primary training data source for most LLMs
- Rich textual descriptions for clustering
- Multilingual coverage enables cross-language analysis
- Article metadata serves as proxy for entity importance

**Limitations:**
- Not all entities have articles in all languages
- Article quality and length vary significantly
- Modern/Western entities have better coverage
- Arabic Wikipedia smaller than English/French

---

## 3. Entity Types Collected

We collect four entity types to ensure diversity in domain and temporal coverage.

### 3.1 People (Person Entities)

**Wikidata Class**: Q5 (Human)
**Properties Collected**:
- P569: Birth date
- P19: Birth place
- P27: Nationality
- P106: Occupation
- P21: Gender
- P570: Death date (optional)

**Filtering Criteria**:
- Must have nationality in target countries (Western, Arabic, Asian)
- Birth year between 1850-2000 (for temporal analysis)
- Complete labels in en, fr, ar

**Research Value**:
- Core entity type for bias analysis
- Clear cultural groupings (nationality)
- Temporal dimension (birth year)
- Gender dimension for intersectional analysis

**Example SPARQL Query**:
```sparql
SELECT ?person ?personLabel_en ?personLabel_fr ?personLabel_ar
       ?birthDate ?birthPlace ?nationality ?occupation ?gender
WHERE {
  VALUES ?nationality { wd:Q142 wd:Q183 wd:Q30 wd:Q29 }  # France, Germany, USA, Spain
  ?person wdt:P31 wd:Q5 .                                # Instance of Human
  ?person wdt:P27 ?nationality .                         # Has nationality
  ?person wdt:P569 ?birthDate .                          # Has birth date
  FILTER(YEAR(?birthDate) > 1850)
  FILTER(YEAR(?birthDate) < 2000)
  # Multilingual labels...
}
```

### 3.2 Events (Historical Events)

**Wikidata Classes**: Q198 (War), Q18608583 (Revolution), Q27020041 (Sport Competition)
**Properties Collected**:
- P585: Point in time (event date)
- P276: Location
- P31: Instance of (event type)

**Filtering Criteria**:
- Event date between 1800-2000
- Complete labels in en, fr, ar

**Research Value**:
- Tests LLM knowledge of historical events
- Cultural perspective: same event described differently
- Temporal dimension: old vs recent events
- Event type provides domain clustering

**Example**: Battle of Waterloo, French Revolution, World Cup 1998

### 3.3 Discoveries (Scientific Discoveries & Inventions)

**Wikidata Classes**: Entities with P61 (Inventor/Discoverer)
**Properties Collected**:
- P61: Inventor/Discoverer
- P575: Discovery date
- P495: Country of origin

**Filtering Criteria**:
- Discovery date between 1800-2000
- Complete labels in en, fr, ar

**Research Value**:
- Science/technology domain
- Tests cultural attribution bias (who gets credit?)
- Historical vs modern discoveries

**Example**: Telephone (Alexander Graham Bell), Penicillin (Alexander Fleming)

### 3.4 Places (Cities)

**Wikidata Classes**: Q515 (City), Q5119 (Capital), Q1549591 (Big City)
**Properties Collected**:
- P17: Country
- P625: Coordinates
- P1082: Population

**Filtering Criteria**:
- Located in target countries (Western, Arabic, Asian)
- Complete labels in en, fr, ar

**Research Value**:
- Geographic knowledge testing
- Cultural familiarity bias
- Population serves as importance metric

**Example**: Paris, Cairo, Tokyo

---

## 4. Multilingual Strategy

### 4.1 Language Selection

**English (en)**: Global lingua franca, primary LLM training language
**French (fr)**: European language, colonial legacy in North Africa
**Arabic (ar)**: Major non-European language, underrepresented in LLM training

These three languages enable:
- Western vs Non-Western comparison
- European colonial language effect (French in Arab countries)
- Script diversity (Latin vs Arabic script)

### 4.2 Arabic Language Handling

**Challenge**: Wikidata contains both Modern Standard Arabic (ar) and Egyptian Arabic (arz) labels.

**Solution**: Hierarchical fallback strategy
1. **Try Modern Standard Arabic (ar)** first (preferred, formal)
2. **Fallback to Egyptian Arabic (arz)** if ar is missing
3. **Track which variant was used** in metadata

**Implementation**:
```python
def _apply_arabic_fallback(item):
    if item.get('personLabel_ar'):
        item['person_arabic_variant'] = 'ar'
    elif item.get('personLabel_arz'):
        item['personLabel_ar'] = item['personLabel_arz']
        item['person_arabic_variant'] = 'arz'
    else:
        item['person_arabic_variant'] = None
    return item
```

**Research Implication**:
- Tracking ar vs arz usage reveals **Arabic Wikipedia documentation bias**
- Entities requiring arz fallback may indicate sparse Arabic coverage
- This itself is a research finding about data availability

### 4.3 Label Completeness Requirements

**Strict Filtering**: An entity is included ONLY if:
- ✅ Has English label (personLabel_en)
- ✅ Has French label (personLabel_fr)
- ✅ Has Arabic label (personLabel_ar, after arz fallback)
- ✅ Has birth/event date
- ✅ Has birth place/event location labels in all 3 languages

**Rationale**:
- Ensures fair comparison across languages
- Avoids confounding effect of missing data
- Enables generation of equivalent questions in all languages

**Trade-off**:
- Reduces dataset size significantly (~30-50% of raw queries)
- Introduces selection bias toward better-documented entities
- This bias is **acknowledged and analyzed** in research

### 4.4 Wikipedia Article Availability

**Key Decision**: Unlike labels, **Wikipedia articles are NOT required in all languages**.

**Why Allow Missing Wikipedia:**
- Creates natural experimental condition: Wikipedia completeness as independent variable
- Tests hypothesis: "LLM performance correlates with Wikipedia availability"
- Reflects real-world data sparsity

**Wikipedia Completeness Groups**:
- **Complete (3 languages)**: Has en, fr, ar articles
- **Partial (2 languages)**: Has 2 of 3 articles
- **Sparse (1 language)**: Has only 1 article
- **None (0 languages)**: No Wikipedia (Wikidata only)

**Expected Distribution**:
- Western entities: Higher proportion with 3 languages
- Arabic entities: Higher proportion with 1-2 languages
- This distribution itself reveals **training data bias**

---

## 5. Data Collection Pipeline

### 5.1 Step-by-Step Process

#### **Step 1: Query Wikidata with Multilingual SPARQL**

For each entity type (people, events, discoveries, places):

```python
people = wikidata.get_people_multilingual(
    nationalities=WESTERN_COUNTRIES,  # [Q142, Q183, Q30, Q29]
    limit=50,
    min_year=1850,
    max_year=2000
)
```

**What Happens**:
- SPARQL query fetches entities matching criteria
- Retrieves labels in en, fr, ar, arz simultaneously
- Extracts metadata: gender, occupation, dates
- Counts Wikipedia sitelinks (num_wikipedia_languages)

**Output**: List of dicts with all properties and multilingual labels

#### **Step 2: Filter for Complete Labels**

```python
def has_complete_labels(entity, entity_type_key='person'):
    required = [
        f'{entity_type_key}Label_en',
        f'{entity_type_key}Label_fr',
        f'{entity_type_key}Label_ar',  # Already has arz fallback applied
    ]
    return all(entity.get(key) for key in required)

valid_entities = [e for e in people if has_complete_labels(e, 'person')]
```

**Filtering Impact**:
- Typical retention: 40-60% of raw results
- Higher retention for Western entities
- Lower retention for Arabic/Asian entities (data sparsity)

#### **Step 3: Store Entity in Database**

```python
# Add base entity (language-agnostic)
entity_id = db.add_entity(
    wikidata_id=person['person_id'],  # e.g., 'Q937'
    entity_type='person',
    culture='Western',  # Derived from nationality
    country=person.get('nationalityLabel_en')
)

# Add multilingual labels
db.add_entity_label(entity_id, 'en', person['personLabel_en'])
db.add_entity_label(entity_id, 'fr', person['personLabel_fr'])
db.add_entity_label(entity_id, 'ar', person['personLabel_ar'])
```

#### **Step 4: Store Entity-Level Metadata**

```python
# Demographic metadata
db.add_metadata(entity_id, 'gender', person.get('gender'))
db.add_metadata(entity_id, 'birth_year', person['birthDate'][:4])

# Fame metrics
db.add_metadata(entity_id, 'num_wikipedia_languages',
               str(person.get('num_wikipedia_languages')))

# Occupation (stored as JSON list)
db.add_metadata(entity_id, 'occupation',
               json.dumps([person['occupation']]))
```

#### **Step 5: Store Facts with Multilingual Labels**

Facts are stored as Wikidata URLs (language-agnostic), with separate multilingual labels:

```python
# Birth place fact
fact_id = db.add_fact(entity_id, 'P19', person['birthPlace'])  # URL

# Add labels for this fact in all languages
if fact_id:
    db.add_fact_label(fact_id, 'en', person['birthPlaceLabel_en'])
    db.add_fact_label(fact_id, 'fr', person['birthPlaceLabel_fr'])
    db.add_fact_label(fact_id, 'ar', person['birthPlaceLabel_ar'])
```

**Why Separate Facts from Labels**:
- Wikidata URLs are canonical and language-agnostic
- Labels change by language but reference same entity
- Enables efficient storage and querying

#### **Step 6: Fetch Wikipedia Articles (All Languages)**

```python
entity_names = {
    'en': person['personLabel_en'],
    'fr': person['personLabel_fr'],
    'ar': person['personLabel_ar']
}

wiki_pages = wikipedia.get_page_multilingual(entity_names)
```

**What Happens Per Language**:
1. Change Wikipedia API language setting
2. Search for article by entity name
3. Handle disambiguation (select first option)
4. Fetch full article: title, content, summary, URL
5. Extract metadata: length, sections, references
6. Query backlinks API for incoming link count
7. Return dict with article + metadata, or None if not found

#### **Step 7: Store Wikipedia Texts with Metadata**

```python
for lang, page_data in wiki_pages.items():
    if page_data:  # Article exists
        metadata = page_data['metadata']

        db.add_wikipedia_text(
            entity_id=entity_id,
            language=lang,
            title=page_data['title'],
            summary=page_data['summary'],
            content=page_data['content'],
            url=page_data['url'],
            # Metadata columns
            text_length_chars=metadata['text_length_chars'],
            text_length_words=metadata['text_length_words'],
            num_sections=metadata['num_sections'],
            num_references=metadata['num_references'],
            num_backlinks=metadata['num_backlinks']
        )
```

#### **Step 8: Track Wikipedia Availability**

```python
has_wikipedia = [lang for lang, page in wiki_pages.items() if page]

db.add_metadata(entity_id, 'wikipedia_completeness', str(len(has_wikipedia)))
db.add_metadata(entity_id, 'wikipedia_languages', json.dumps(has_wikipedia))
db.add_metadata(entity_id, 'has_all_wikipedia_languages',
               str(len(has_wikipedia) == 3))
```

**Purpose**: Enables filtering for Experiment 1 vs Experiment 2

### 5.2 Rate Limiting and Error Handling

**Wikidata**:
- Rate limit: 1 second between queries
- Max retries: 3 attempts with exponential backoff
- Timeout: 60 seconds per query

**Wikipedia**:
- Rate limit: 0.1 seconds between requests
- Max retries: 3 attempts
- Disambiguation: Automatically select first option
- Page not found: Log warning, return None (not an error)

**Error Recovery**:
- All database operations wrapped in try-except
- Duplicate entries ignored gracefully
- Partial failures logged but don't stop collection
- Transaction rollback on critical errors

---

## 6. Metadata Collected

### 6.1 Entity-Level Metadata

Stored in `entity_metadata` table as flexible key-value pairs.

| Metadata Key | Type | Description | Research Use |
|-------------|------|-------------|--------------|
| `gender` | Wikidata ID | Q6581097 (male), Q6581072 (female) | Gender bias analysis |
| `occupation` | JSON list | List of Wikidata occupation IDs | Domain clustering, not used in questions |
| `birth_year` | Integer | Year of birth (YYYY) | Temporal analysis, age calculation |
| `death_year` | Integer | Year of death (YYYY), NULL if alive | Temporal analysis |
| `is_alive` | Boolean string | 'True' or 'False' | Current vs historical entities |
| `event_type` | Wikidata ID | Type of event (war, revolution, etc.) | Event domain clustering |
| `event_year` | Integer | Year event occurred | Temporal analysis for events |
| `num_wikipedia_languages` | Integer | Count from Wikidata sitelinks | **Fame metric**: more languages = more famous |
| `wikipedia_completeness` | Integer (0-3) | How many of en/fr/ar have Wikipedia | **Key experimental variable** |
| `wikipedia_languages` | JSON list | Which languages have Wikipedia ['en', 'fr'] | Availability tracking |
| `has_wikipedia_en` | Boolean string | English Wikipedia exists | Language-specific filtering |
| `has_wikipedia_fr` | Boolean string | French Wikipedia exists | Language-specific filtering |
| `has_wikipedia_ar` | Boolean string | Arabic Wikipedia exists | Language-specific filtering |
| `has_all_wikipedia_languages` | Boolean string | All 3 exist | Experiment 2 filtering |

### 6.2 Wikipedia-Level Metadata

Stored as columns in `wikipedia_texts` table (per entity, per language).

| Field | Type | Description | Research Use |
|-------|------|-------------|--------------|
| `text_length_chars` | Integer | Character count of article | **Key hypothesis**: longer = more LLM knowledge |
| `text_length_words` | Integer | Word count of article | Article size metric |
| `num_sections` | Integer | Approximate section count | Article structure complexity |
| `num_references` | Integer | Citation count (approximate) | Article quality indicator |
| `num_backlinks` | Integer | **Incoming links from other articles** | **Fame metric**: highly linked = more important |

### 6.3 Metadata Extraction Process

**Text Length**:
```python
metadata['text_length_chars'] = len(content)
metadata['text_length_words'] = len(content.split())
```

**Sections**:
```python
# Count major section breaks (approximate)
metadata['num_sections'] = max(content.count('\n\n\n'), 1)
```

**References**:
```python
# Pattern matching for citation markers (approximate)
patterns = [r'\[\d+\]', r'Retrieved', r'Archived']
metadata['num_references'] = sum(len(re.findall(p, content)) for p in patterns)
```

**Backlinks** (Most Important):
```python
# Query Wikipedia API
url = f"https://{language}.wikipedia.org/w/api.php"
params = {
    'action': 'query',
    'list': 'backlinks',
    'bltitle': article_title,
    'bllimit': 'max',
    'format': 'json'
}
response = requests.get(url, params=params)
metadata['num_backlinks'] = len(response['query']['backlinks'])
```

**Why Backlinks Matter**:
- Direct measure of article importance in Wikipedia graph
- Strongly correlated with entity fame/significance
- More stable than page views (not affected by recent events)
- Available as historical data (not time-limited)

---

## 7. Data Quality Measures

### 7.1 Completeness Filtering

**Required for Inclusion**:
```python
# Entity must have:
✓ Wikidata ID (unique identifier)
✓ Entity label in English
✓ Entity label in French
✓ Entity label in Arabic (ar or arz fallback)
✓ Birth/event date
✓ Birth place/event location labels in all 3 languages
```

**Impact on Dataset**:
- **Retention rate**: ~40-60% of raw Wikidata results
- **Western entities**: ~60% retention (better documented)
- **Arabic entities**: ~35% retention (sparser coverage)
- **Asian entities**: ~45% retention (moderate coverage)

**Selection Bias Introduced**:
- Better-documented entities overrepresented
- Obscure entities underrepresented
- Modern entities overrepresented
- This bias is **acknowledged and quantified** in research

### 7.2 Wikipedia Availability Tracking

**Not Required, But Tracked**:
- Wikipedia articles in en, fr, ar are **optional**
- Entities with 0-3 Wikipedia languages all included
- Availability tracked as metadata for analysis

**Distribution** (Expected):
```
Wikipedia Completeness | Western | Arabic | Asian
----------------------|---------|---------|-------
3 languages (complete)| 60%     | 25%     | 40%
2 languages (partial) | 25%     | 35%     | 30%
1 language (sparse)   | 10%     | 30%     | 20%
0 languages (none)    | 5%      | 10%     | 10%
```

**Research Value**:
- Tests correlation between Wikipedia availability and LLM performance
- Reveals **training data bias** in LLMs
- Enables stratified analysis by completeness group

### 7.3 Validation Checks

**During Collection**:
- Duplicate Wikidata IDs rejected (entity uniqueness)
- Invalid dates filtered (year < 1800 or > 2000)
- Empty labels rejected
- Malformed URLs logged and skipped

**Post-Collection**:
```python
# Verify label completeness
stats = db.get_statistics()
assert stats['labels_by_language']['en'] == stats['total_entities']
assert stats['labels_by_language']['fr'] == stats['total_entities']
assert stats['labels_by_language']['ar'] == stats['total_entities']

# Verify Wikipedia tracking
complete_entities = db.get_entities_with_all_wikipedia()
assert len(complete_entities) <= stats['total_entities']
```

### 7.4 Error Handling and Logging

**All Operations Logged**:
```
INFO: Query successful: 50 results
WARNING: Disambiguation for 'John Smith': ['John Smith (politician)', ...]
WARNING: Page not found: 'Obscure Person'
ERROR: Wikipedia API timeout (attempt 2/3)
INFO: Added entity: Albert Einstein (Q937)
DEBUG: Using Egyptian Arabic (arz) fallback for birthPlace
```

**Error Recovery**:
- Transient errors: Retry with exponential backoff
- Permanent errors (page not found): Log and continue
- Database errors: Transaction rollback
- Network errors: Pause and retry

---

## 8. Database Schema

### 8.1 Entity-Relationship Diagram

```
┌──────────────┐
│   entities   │ (language-agnostic base)
├──────────────┤
│ id (PK)      │
│ wikidata_id  │──┐
│ type         │  │
│ culture      │  │
│ country      │  │
└──────────────┘  │
                  │
        ┌─────────┼──────────────────────────┐
        │         │                          │
        ▼         ▼                          ▼
┌─────────────┐ ┌───────────────┐  ┌──────────────────┐
│entity_labels│ │ wikipedia_texts│  │ entity_metadata  │
├─────────────┤ ├───────────────┤  ├──────────────────┤
│ entity_id(FK│ │ entity_id (FK)│  │ entity_id (FK)   │
│ language    │ │ language      │  │ metadata_key     │
│ label       │ │ title         │  │ metadata_value   │
└─────────────┘ │ content       │  └──────────────────┘
                │ summary       │
                │ url           │
                │ text_length_* │
                │ num_backlinks │
                └───────────────┘

        ┌─────────┘
        ▼
┌─────────────┐
│    facts    │ (Wikidata properties)
├─────────────┤
│ id (PK)     │──┐
│ entity_id(FK│  │
│ property    │  │
│ value (URL) │  │
└─────────────┘  │
                 │
                 ▼
        ┌──────────────┐
        │ fact_labels  │
        ├──────────────┤
        │ fact_id (FK) │
        │ language     │
        │ label        │
        └──────────────┘

        ┌─────────────┘
        ▼
┌─────────────┐
│  questions  │ (generated Q&A)
├─────────────┤
│ entity_id(FK│
│ language    │
│ question_type│
│ question_text│
│ ground_truth│
│ property    │
└─────────────┘
```

### 8.2 Table Descriptions

#### **entities**
Base entity information (language-agnostic).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| wikidata_id | TEXT UNIQUE | Wikidata Q-code (e.g., 'Q937') |
| type | TEXT | Entity type: person, event, discovery, place |
| culture | TEXT | Western, Arabic, Asian, Other |
| country | TEXT | Country name (English) |
| created_at | TIMESTAMP | Collection timestamp |

#### **entity_labels**
Multilingual names for entities.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| entity_id | INTEGER FK | References entities(id) |
| language | TEXT | 'en', 'fr', or 'ar' |
| label | TEXT | Entity name in this language |
| UNIQUE(entity_id, language) | | One label per language per entity |

#### **wikipedia_texts**
Wikipedia articles with metadata (per language).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| entity_id | INTEGER FK | References entities(id) |
| language | TEXT | 'en', 'fr', or 'ar' |
| title | TEXT | Wikipedia article title |
| summary | TEXT | First paragraph |
| content | TEXT | Full article text |
| url | TEXT | Wikipedia article URL |
| text_length_chars | INTEGER | Character count |
| text_length_words | INTEGER | Word count |
| num_sections | INTEGER | Section count (approx) |
| num_references | INTEGER | Citation count (approx) |
| num_backlinks | INTEGER | Incoming links count |
| fetched_at | TIMESTAMP | Collection timestamp |
| UNIQUE(entity_id, language) | | One article per language per entity |

#### **facts**
Wikidata properties (language-agnostic URLs).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| entity_id | INTEGER FK | References entities(id) |
| property | TEXT | Wikidata property code (e.g., 'P569') |
| value | TEXT | Wikidata URL (e.g., 'http://www.wikidata.org/entity/Q1489') |
| UNIQUE(entity_id, property, value) | | Avoid duplicates |

#### **fact_labels**
Multilingual labels for fact values.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| fact_id | INTEGER FK | References facts(id) |
| language | TEXT | 'en', 'fr', or 'ar' |
| label | TEXT | Human-readable label (e.g., 'Mexico City') |
| UNIQUE(fact_id, language) | | One label per language per fact |

#### **entity_metadata**
Flexible key-value metadata storage.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| entity_id | INTEGER FK | References entities(id) |
| metadata_key | TEXT | Key name (e.g., 'gender', 'birth_year') |
| metadata_value | TEXT | Value as string (convert as needed) |
| UNIQUE(entity_id, metadata_key) | | One value per key per entity |

#### **questions**
Generated questions for LLM testing (future use).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| entity_id | INTEGER FK | References entities(id) |
| language | TEXT | Question language ('en', 'fr', 'ar') |
| question_type | TEXT | Question category (birth_date, birth_place, etc.) |
| question_text | TEXT | Full question text |
| ground_truth | TEXT | Correct answer |
| property | TEXT | Wikidata property used (e.g., 'P569') |
| UNIQUE(entity_id, language, question_type) | | One question per type per language per entity |

### 8.3 Indexing Strategy

```sql
-- Entity lookups
CREATE INDEX idx_wikidata_id ON entities(wikidata_id);
CREATE INDEX idx_entity_type ON entities(type);
CREATE INDEX idx_culture ON entities(culture);

-- Language filtering
CREATE INDEX idx_entity_labels_lang ON entity_labels(language);
CREATE INDEX idx_wikipedia_texts_lang ON wikipedia_texts(language);
CREATE INDEX idx_fact_labels_lang ON fact_labels(language);

-- Metadata queries
CREATE INDEX idx_entity_metadata_key ON entity_metadata(metadata_key);
```

**Purpose**: Fast filtering by entity type, culture, and language for experiment queries.

---

## 9. Dimensions for Analysis

### 9.1 Cultural Dimension

**Groups**:
- **Western**: France, Germany, USA, Spain (Q142, Q183, Q30, Q29)
- **Arabic**: Egypt, Syria, Saudi Arabia, Lebanon (Q79, Q858, Q851, Q822)
- **Asian**: China, Japan, India, South Korea (Q148, Q17, Q668, Q884)

**Hypothesis**: LLMs exhibit Western-centric bias due to training data composition.

**Test**: Compare grouping loss across cultural groups.

### 9.2 Temporal Dimension

**Time Periods**:
- Ancient: 1800-1850
- Early Modern: 1850-1900
- Modern: 1900-1950
- Contemporary: 1950-2000

**Stored As**: `birth_year`, `event_year` in metadata

**Hypothesis**: LLMs better calibrated on contemporary entities (recency bias).

**Test**: Cluster by time period, measure grouping loss per period.

### 9.3 Fame/Importance Dimension

**Metrics**:
1. `num_wikipedia_languages` (Wikidata sitelinks count)
   - Einstein: 200+ languages
   - Obscure person: 3-5 languages

2. `num_backlinks` (Wikipedia incoming links)
   - Einstein: 10,000+ backlinks
   - Obscure person: 50-100 backlinks

3. `text_length_chars` (Wikipedia article size)
   - Famous: 50,000+ characters
   - Obscure: 5,000 characters

**Hypothesis**: LLM confidence/accuracy positively correlates with entity fame.

**Test**: Stratify entities by fame metrics, compare LLM performance.

### 9.4 Wikipedia Completeness Dimension

**Groups**:
- **Complete (3/3)**: Has en, fr, ar Wikipedia
- **Partial (2/3)**: Has 2 of 3
- **Sparse (1/3)**: Has only 1
- **None (0/3)**: No Wikipedia, Wikidata only

**Hypothesis**: LLM performance degrades with decreasing Wikipedia availability.

**Test**: Compare LLM confidence/accuracy across completeness groups.

### 9.5 Entity Type Dimension

**Types**: People, Events, Discoveries, Places

**Hypothesis**: LLM calibration quality varies by domain.

**Test**: Separate analysis per entity type, compare grouping loss.

### 9.6 Gender Dimension

**Groups**: Male (Q6581097), Female (Q6581072)

**Hypothesis**: Gender bias in LLM knowledge and confidence.

**Test**: Stratify people by gender, compare LLM performance.

---

## 10. Data Collection Statistics

### 10.1 Collection Summary Template

```
====================================================================
DATA COLLECTION SUMMARY
====================================================================
Collection Date: [YYYY-MM-DD]
Total Entities Collected: [N]

By Entity Type:
  - People:      [N] ([%])
  - Events:      [N] ([%])
  - Discoveries: [N] ([%])
  - Places:      [N] ([%])

By Culture:
  - Western: [N] ([%])
  - Arabic:  [N] ([%])
  - Asian:   [N] ([%])
  - Other:   [N] ([%])

Label Completeness:
  - English labels:  [N] (100%)
  - French labels:   [N] (100%)
  - Arabic labels:   [N] (100%)
    - Using ar:      [N] ([%])
    - Using arz:     [N] ([%])

Wikipedia Coverage:
  - Complete (3/3): [N] ([%])
  - Partial (2/3):  [N] ([%])
  - Sparse (1/3):   [N] ([%])
  - None (0/3):     [N] ([%])

Wikipedia by Language:
  - English:  [N] ([%])
  - French:   [N] ([%])
  - Arabic:   [N] ([%])

Metadata:
  - Entities with gender:      [N] ([%])
  - Entities with occupation:  [N] ([%])
  - Entities with birth_year:  [N] ([%])
  - Avg Wikipedia languages:   [X.X]
  - Avg text_length_chars:     [XXXX]
  - Avg num_backlinks:         [XXX]

Quality Metrics:
  - Duplicate-free:            [Y/N]
  - Complete label coverage:   [Y/N]
  - Wikipedia metadata complete: [Y/N]
====================================================================
```

### 10.2 Key Metrics to Report

1. **Total entities collected** (target: 500-1500)
2. **Retention rate after filtering** (expect 40-60%)
3. **Cultural balance** (aim for roughly equal groups)
4. **Wikipedia completeness distribution** (expect Western > Asian > Arabic)
5. **Arabic fallback usage rate** (indicates documentation sparsity)
6. **Average fame metrics** per cultural group
7. **Temporal distribution** (ensure coverage across time periods)

---

## 11. Limitations and Biases

### 11.1 Selection Bias

**Completeness Filtering**:
- Requiring labels in all 3 languages **oversamples well-documented entities**
- Better-documented → likely more famous → not representative of all entities
- Western entities disproportionately included

**Impact on Research**:
- Results generalize to "well-documented entities" not "all entities"
- This limitation is **acknowledged in research report**
- Bias direction is known and can be quantified

### 11.2 Wikipedia Coverage Bias

**Known Biases**:
- English Wikipedia largest (~6.7M articles)
- French Wikipedia medium (~2.5M articles)
- Arabic Wikipedia smallest (~1.2M articles)
- Western/modern/male entities overrepresented

**Impact on Research**:
- Naturally creates **unbalanced groups** by Wikipedia completeness
- This imbalance is **feature, not bug** for research question
- Reveals training data bias in LLMs

### 11.3 Wikidata Completeness Varies

**Known Issues**:
- Some properties missing for older entities
- Occupation field may list one of many occupations
- Death dates missing for recently deceased
- Coordinate precision varies for places

**Mitigation**:
- Focus on properties with high completion rates (birth date, birth place)
- Skip occupation questions (too ambiguous)
- Validate data during collection

### 11.4 Temporal Coverage Bias

**Modern Bias**:
- Entities born after 1950 better documented
- Pre-1900 entities sparse in Arabic Wikipedia
- Ancient discoveries poorly documented

**Impact on Research**:
- Temporal analysis may confound with documentation quality
- Older entities have fewer Wikipedia versions
- This confound is **acknowledged and analyzed**

### 11.5 Arabic Language Complexity

**Challenges**:
- Diglossia: Modern Standard Arabic (ar) vs dialects (arz, etc.)
- Egyptian Arabic most common variant in Wikipedia
- Fallback strategy may introduce inconsistency

**Mitigation**:
- Track which variant used (ar vs arz)
- Analyze separately if needed
- Report as research finding

### 11.6 Wikipedia Metadata Approximations

**Limitations**:
- `num_references` is approximate (plaintext parsing imperfect)
- `num_sections` is approximate (heuristic-based counting)
- `num_backlinks` accurate but expensive to fetch

**Impact on Research**:
- Metrics are **relative, not absolute**
- Suitable for correlation analysis
- Not suitable for precise quantification

---

## 12. Reproducibility

### 12.1 Configuration Parameters

```python
# Wikidata Query Parameters
NATIONALITIES_WESTERN = [Q142, Q183, Q30, Q29]  # France, Germany, USA, Spain
NATIONALITIES_ARABIC = [Q79, Q858, Q851, Q822]   # Egypt, Syria, Saudi Arabia, Lebanon
NATIONALITIES_ASIAN = [Q148, Q17, Q668, Q884]    # China, Japan, India, South Korea

MIN_BIRTH_YEAR = 1850
MAX_BIRTH_YEAR = 2000
MIN_EVENT_YEAR = 1800
MAX_EVENT_YEAR = 2000

ENTITIES_PER_CULTURE = 50  # Per nationality group
EVENT_LIMIT = 30
DISCOVERY_LIMIT = 30
PLACE_LIMIT = 30

# Rate Limiting
WIKIDATA_RATE_LIMIT = 1.0  # seconds
WIKIPEDIA_RATE_LIMIT = 0.1  # seconds

# Language Codes
LANGUAGES = ['en', 'fr', 'ar']
```

### 12.2 Software Versions

```
Python: 3.8+
Libraries:
  - requests: 2.31.0
  - wikipedia: 1.4.0
  - sqlite3: (built-in)

Data Sources:
  - Wikidata SPARQL: https://query.wikidata.org/sparql (accessed Dec 2024)
  - Wikipedia API: https://wikipedia.org/w/api.php (accessed Dec 2024)
```

### 12.3 Replication Steps

1. Install dependencies: `pip install requests wikipedia`
2. Initialize database: `python -c "from src.data import EntityDatabase; EntityDatabase('data/entities.db')"`
3. Run collection: `python collect_data_example.py`
4. Verify completeness: Check statistics output
5. Export data: Use query helpers in database module

### 12.4 Data Versioning

**Recommendations**:
- Record collection date (Wikidata/Wikipedia change over time)
- Store SPARQL query strings used
- Log software versions
- Archive raw API responses (optional)
- Export final database with timestamp

---

## 13. Usage Examples

### 13.1 Basic Collection

```python
from src.data import EntityDatabase, WikidataClient, WikipediaClient
from src.data import WESTERN_COUNTRIES

# Initialize
db = EntityDatabase("data/entities.db")
wikidata = WikidataClient(rate_limit_delay=1.0)
wikipedia = WikipediaClient(rate_limit_delay=0.1)

# Collect Western people
people = wikidata.get_people_multilingual(
    nationalities=WESTERN_COUNTRIES,
    limit=50,
    min_year=1850,
    max_year=2000
)

print(f"Fetched {len(people)} people from Wikidata")
```

### 13.2 Filtering for Complete Labels

```python
def has_complete_labels(entity):
    return all([
        entity.get('personLabel_en'),
        entity.get('personLabel_fr'),
        entity.get('personLabel_ar'),  # Fallback already applied
        entity.get('birthDate'),
        entity.get('birthPlaceLabel_en'),
        entity.get('birthPlaceLabel_fr'),
        entity.get('birthPlaceLabel_ar')
    ])

valid_people = [p for p in people if has_complete_labels(p)]
print(f"Filtered to {len(valid_people)} with complete labels")
```

### 13.3 Storing Entity with Metadata

```python
for person in valid_people:
    # Add base entity
    entity_id = db.add_entity(
        wikidata_id=person['person_id'],
        entity_type='person',
        culture='Western'
    )

    # Add labels
    db.add_entity_label(entity_id, 'en', person['personLabel_en'])
    db.add_entity_label(entity_id, 'fr', person['personLabel_fr'])
    db.add_entity_label(entity_id, 'ar', person['personLabel_ar'])

    # Add metadata
    db.add_metadata(entity_id, 'gender', person.get('gender'))
    db.add_metadata(entity_id, 'birth_year', person['birthDate'][:4])
    db.add_metadata(entity_id, 'num_wikipedia_languages',
                   str(person.get('num_wikipedia_languages', 0)))
```

### 13.4 Querying for Experiments

```python
# Experiment 1: Language-specific clustering
entities_with_english = db.get_entities_with_wikipedia('en', entity_type='person')
texts_en = db.export_wikipedia_texts('en', entity_type='person')
print(f"Entities with English Wikipedia: {len(entities_with_english)}")

# Experiment 2: Cross-language analysis
entities_complete = db.get_entities_with_all_wikipedia(['en', 'fr', 'ar'])
print(f"Entities with all 3 languages: {len(entities_complete)}")

# Filter by culture and completeness
western_complete = [e for e in entities_complete if e['culture'] == 'Western']
arabic_complete = [e for e in entities_complete if e['culture'] == 'Arabic']
```

### 13.5 Metadata Analysis

```python
# Get entity with all metadata
entity = db.get_entity('Q937')  # Albert Einstein
labels = db.get_entity_labels(entity['id'])
metadata = db.get_metadata(entity['id'])
wiki_texts = db.get_wikipedia_texts(entity['id'])

print(f"Entity: {labels['en']}")
print(f"Gender: {metadata.get('gender')}")
print(f"Birth year: {metadata.get('birth_year')}")
print(f"Wikipedia languages: {metadata.get('wikipedia_languages')}")
print(f"Wikipedia completeness: {metadata.get('wikipedia_completeness')}/3")

# Print Wikipedia stats per language
for lang, text in wiki_texts.items():
    print(f"{lang}: {text['text_length_chars']} chars, {text['num_backlinks']} backlinks")
```

---

## 14. Appendix

### 14.1 Wikidata Property Codes Reference

| Property | Code | Description |
|----------|------|-------------|
| Instance of | P31 | Entity type classification |
| Birth date | P569 | Date of birth |
| Birth place | P19 | Place of birth |
| Death date | P570 | Date of death |
| Death place | P20 | Place of death |
| Nationality | P27 | Country of citizenship |
| Occupation | P106 | Person's occupation |
| Gender | P21 | Gender identity |
| Inventor | P61 | Creator of invention |
| Discovery date | P575 | Date of discovery |
| Point in time | P585 | Date when event occurred |
| Location | P276 | Physical location |
| Country | P17 | Sovereign state |
| Coordinates | P625 | Geographic coordinates |
| Population | P1082 | Number of people |

### 14.2 Wikidata Entity Codes Reference

| Entity | Code | Description |
|--------|------|-------------|
| Human | Q5 | Individual person |
| City | Q515 | Large permanent settlement |
| Capital | Q5119 | Seat of government |
| Big city | Q1549591 | Major urban area |
| War | Q198 | Armed conflict |
| Revolution | Q18608583 | Political upheaval |
| Male | Q6581097 | Male gender |
| Female | Q6581072 | Female gender |

**Countries**:
- Q142: France
- Q183: Germany
- Q30: United States
- Q29: Spain
- Q79: Egypt
- Q858: Syria
- Q851: Saudi Arabia
- Q822: Lebanon
- Q148: China
- Q17: Japan
- Q668: India
- Q884: South Korea

### 14.3 Example SPARQL Query (Abbreviated)

```sparql
SELECT DISTINCT
    ?person
    ?personLabel_en ?personLabel_fr ?personLabel_ar
    ?birthDate ?birthPlace ?nationality ?occupation
    (COUNT(DISTINCT ?sitelink) as ?num_wikipedia_languages)
WHERE {
  VALUES ?nationality { wd:Q142 wd:Q183 wd:Q30 wd:Q29 }

  ?person wdt:P31 wd:Q5 .
  ?person wdt:P27 ?nationality .
  ?person wdt:P569 ?birthDate .
  ?person wdt:P19 ?birthPlace .
  ?person wdt:P106 ?occupation .

  OPTIONAL { ?person wdt:P21 ?gender . }

  OPTIONAL {
    ?sitelink schema:about ?person .
    FILTER(CONTAINS(STR(?sitelink), "wikipedia"))
  }

  FILTER(YEAR(?birthDate) > 1850)
  FILTER(YEAR(?birthDate) < 2000)

  # Labels in en, fr, ar, arz...
}
GROUP BY ?person ?birthDate ...
LIMIT 50
```

### 14.4 Database Size Estimates

For 1000 entities with full Wikipedia coverage:

| Table | Rows | Est. Size |
|-------|------|-----------|
| entities | 1,000 | 50 KB |
| entity_labels | 3,000 | 150 KB |
| entity_metadata | 10,000 | 500 KB |
| facts | 3,000 | 150 KB |
| fact_labels | 9,000 | 450 KB |
| wikipedia_texts | 2,500 | **500 MB** (bulk of data) |
| questions | 3,000 | 300 KB |
| **Total** | | **~500 MB** |

Most space consumed by Wikipedia article `content` field (text).

### 14.5 Collection Time Estimates

For 50 entities per cultural group (150 people total):

| Operation | Time per Entity | Total Time |
|-----------|----------------|-----------|
| Wikidata query | 1s (rate limit) | 50s per batch |
| Wikipedia fetch (3 languages) | 0.3s (0.1s × 3) | 45s |
| Backlinks fetch (3 languages) | 0.3s (0.1s × 3) | 45s |
| Database storage | 0.1s | 15s |
| **Per entity** | **~0.9s** | - |
| **150 entities** | - | **~2.25 minutes** |
| **1000 entities** | - | **~15 minutes** |

Actual time may vary due to:
- Network latency
- Wikipedia API response time
- Database write speed
- Error retries

---

## End of Documentation

This methodology ensures:
- ✅ **Rigorous data collection** with quality controls
- ✅ **Comprehensive metadata** for multidimensional analysis
- ✅ **Reproducible process** with clear documentation
- ✅ **Research-ready data** structured for clustering and LLM testing
- ✅ **Acknowledged biases** with transparent limitations

For questions or clarifications, refer to the source code in `src/data/` or contact the project maintainer.
