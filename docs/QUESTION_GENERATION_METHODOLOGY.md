# Question Generation Methodology

## Overview

This document describes the methodology for generating **multiple-choice questions** with **consistent distractors across languages** for the LLM Grouping Loss evaluation project. The goal is to create questions that can be used to measure calibration bias across different cultural/linguistic groups.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Question Types](#question-types)
3. [Distractor Selection Strategy](#distractor-selection-strategy)
4. [Language-Agnostic Generation](#language-agnostic-generation)
5. [Database Schema](#database-schema)
6. [Implementation Details](#implementation-details)
7. [Quality Control](#quality-control)
8. [Examples](#examples)

---

## Design Principles

### Core Requirements

1. **Cross-Language Consistency**: Same entity must have the **exact same distractor entities** across all languages (English, French, Arabic)
2. **Deterministic Randomization**: Use entity ID as seed to ensure reproducible option ordering
3. **Diverse Distractors**: Avoid repetitive or trivial wrong answers
4. **Cultural Balance**: Select distractors from entities across all cultural groups (Western, Arabic, Asian, African, Latin American)

### Why Consistency Matters

For grouping loss evaluation, we need to isolate **language/cultural bias** from **question difficulty**:

```python
# BAD: Different distractors per language
EN: "Where was X born?" Options: [Paris, London, Berlin, Madrid]
FR: "Où est né X?"     Options: [Paris, Tokyo, Cairo, Sydney]
# ❌ Can't compare - different difficulty levels!

# GOOD: Same distractors, different labels
EN: "Where was X born?" Options: [Paris, London, Berlin, Madrid]
FR: "Où est né X?"     Options: [Paris, Londres, Berlin, Madrid]
# ✅ Can compare - same entities, just translated
```

---

## Question Types

### 1. Birth Place Questions

**Template**: `"Where was {entity_name} born?"` (translated to en/fr/ar)

**Properties Used**:
- Property: `P19` (birth place) from Wikidata
- Stored as: URL (`http://www.wikidata.org/entity/Q12345`)
- Labels in: English, French, Arabic

**Distractor Selection**:
- Find 3 other people with **different** birth places
- Use `ORDER BY RANDOM()` for diversity
- Exclude the correct entity's birth place
- Prefer major cities for recognizability

**Example**:
```
Question: "Where was Yunjin Kim born?"
Correct: B) Seoul (entity_id=1)
Distractors:
  A) Sanxing Township (entity_id=5234)
  C) Zhongli District (entity_id=3421)
  D) Tainan County (entity_id=8765)
```

---

### 2. Nationality Questions

**Template**: `"What is the nationality of {entity_name}?"` (translated to en/fr/ar)

**Properties Used**:
- Property: `P27` (nationality) from Wikidata
- Stored as: URL (`http://www.wikidata.org/entity/Q30`)
- Labels in: English, French, Arabic

**Distractor Selection**:
- Find 3 other people with **different nationalities**
- **Explicitly exclude** the entity's own nationality
- Aim for cultural diversity (Western, Arabic, Asian, etc.)
- Use `ORDER BY RANDOM()` for variety

**Example**:
```
Question: "What is the nationality of Yunjin Kim?"
Correct: D) South Korea (entity_id=1)
Distractors:
  A) United States (entity_id=2453)
  B) France (entity_id=8721)
  C) Egypt (entity_id=5342)
```

---

### 3. Birth Date Questions

**Template**: `"When was {entity_name} born?"` (translated to en/fr/ar)

**Properties Used**:
- Property: `P569` (birth date) from Wikidata
- Stored as: ISO date string (`"1973-11-07"`)
- Displayed as: Year only (`"1973"`)

**Distractor Selection**:
- Find 3 other people with **different birth years**
- Prefer nearby years for plausibility (±50 years)
- Randomize selection for diversity

**Example**:
```
Question: "When was Yunjin Kim born?"
Correct: B) 1973 (entity_id=1)
Distractors:
  A) 1971 (entity_id=2341)
  C) 1980 (entity_id=4567)
  D) 1965 (entity_id=7890)
```

---

## Distractor Selection Strategy

### Algorithm Overview

```python
def generate_question(entity_id, languages):
    # 1. Get distractor ENTITY IDs (language-agnostic)
    distractor_ids = get_distractor_entities(
        entity_id,
        limit=3,
        exclude_entity=entity_id,
        exclude_value=entity.correct_value  # e.g., exclude entity's nationality
    )

    # 2. Shuffle deterministically (same order for all languages)
    random.Random(entity_id + question_offset).shuffle(distractor_ids)

    # 3. Assign letters A/B/C/D
    all_entity_ids = [entity_id] + distractor_ids
    random.Random(entity_id + question_offset).shuffle(all_entity_ids)

    # 4. FOR EACH LANGUAGE: Get labels in that language
    for lang in languages:
        options = []
        for letter, eid in zip(['A', 'B', 'C', 'D'], all_entity_ids):
            label = get_label(eid, lang)  # e.g., "Seoul" / "Séoul" / "سيول"
            options.append({"letter": letter, "text": label, "entity_id": eid})

        save_question(entity_id, lang, question_type, options)
```

### Key Implementation Details

#### 1. **Deterministic Randomization**

```python
# Use entity_id as seed for reproducible shuffling
seed = entity_id + question_type_offset
rng = random.Random(seed)

# Offset prevents same order for different question types
offsets = {
    "birth_place": 1000,
    "nationality": 2000,
    "birth_date": 3000
}
```

#### 2. **Diverse Distractor Query**

```python
# Without ORDER BY RANDOM() - BAD
SELECT DISTINCT e.id FROM entities e
WHERE e.id != ? AND EXISTS (
    SELECT 1 FROM facts f
    WHERE f.entity_id = e.id AND f.property = 'birthPlace'
)
LIMIT 100
# Returns: [1, 2, 3, 4, 5, ...] - always same entities!

# With ORDER BY RANDOM() - GOOD
SELECT DISTINCT e.id FROM entities e
WHERE e.id != ? AND EXISTS (
    SELECT 1 FROM facts f
    WHERE f.entity_id = e.id AND f.property = 'birthPlace'
)
ORDER BY RANDOM()  # ← Critical for diversity
LIMIT 100
# Returns: [342, 87, 1523, 45, ...] - diverse selection!
```

#### 3. **Exclusion Logic**

For nationality questions, we must **exclude the entity's own nationality**:

```python
def _get_nationality_distractors(
    self,
    culture: str,
    exclude_entity_id: int,
    exclude_nationality_url: str,  # ← NEW: Exclude entity's nationality
    limit: int = 100
) -> List[int]:
    """Get entities with DIFFERENT nationality"""

    cursor.execute("""
        SELECT DISTINCT e.id FROM entities e
        WHERE e.id != ?
        AND e.culture = ?
        AND EXISTS (
            SELECT 1 FROM facts f
            WHERE f.entity_id = e.id
            AND f.property = 'nationality'
            AND f.value != ?  # ← Exclude entity's nationality
        )
        ORDER BY RANDOM()
        LIMIT ?
    """, (exclude_entity_id, culture, exclude_nationality_url, limit))
```

---

## Language-Agnostic Generation

### Problem: Why Not Generate Per Language?

**Naive Approach** (generates 3 times):
```python
# BAD: Generate separately for each language
for lang in ['en', 'fr', 'ar']:
    distractors = get_random_distractors(limit=3)  # Different each time!
    generate_question(entity, lang, distractors)
```

**Result**: Inconsistent distractors across languages
- EN might get Paris, London, Berlin
- FR might get Tokyo, Cairo, Sydney
- AR might get Madrid, Rome, Athens

### Solution: Generate Once, Label Per Language

**Correct Approach**:
```python
# GOOD: Generate distractors once
distractor_entity_ids = get_random_distractors(limit=3)  # [123, 456, 789]

# Then get labels for each language
for lang in ['en', 'fr', 'ar']:
    options = []
    for entity_id in distractor_entity_ids:
        label = get_label(entity_id, lang)
        options.append(label)
    generate_question(entity, lang, options)
```

**Result**: Consistent distractors with multilingual labels
- EN: Paris, London, Berlin (entities 123, 456, 789)
- FR: Paris, Londres, Berlin (entities 123, 456, 789)
- AR: باريس, لندن, برلين (entities 123, 456, 789)

---

## Database Schema

### Questions Table

```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,           -- Which person this question is about
    language TEXT NOT NULL,                -- 'en', 'fr', or 'ar'
    question_type TEXT NOT NULL,           -- 'birth_place', 'nationality', 'birth_date'
    question_text TEXT NOT NULL,           -- Full question in this language
    ground_truth TEXT NOT NULL,            -- Correct answer text (e.g., "Seoul")
    property TEXT NOT NULL,                -- Wikidata property code (e.g., "P19")
    options TEXT,                          -- JSON array of option objects
    correct_answer TEXT,                   -- Letter of correct answer ('A', 'B', 'C', or 'D')
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    UNIQUE(entity_id, language, question_type)
)
```

### Options Format

Stored as JSON array:

```json
[
  {"letter": "A", "text": "Sanxing Township", "entity_id": 5234},
  {"letter": "B", "text": "Seoul", "entity_id": 1},
  {"letter": "C", "text": "Zhongli District", "entity_id": 3421},
  {"letter": "D", "text": "Tainan County", "entity_id": 8765}
]
```

**Why include `entity_id`?**
- Enables tracking which entities were used as distractors
- Allows analysis of distractor patterns
- Helps debug consistency issues

---

## Implementation Details

### Full Generation Workflow

```python
class MultipleChoiceQuestionGenerator:
    def generate_all_questions(self, entity_id: int):
        """Generate 9 questions: 3 types × 3 languages"""

        question_types = ["birth_place", "nationality", "birth_date"]
        languages = ["en", "fr", "ar"]

        # Generate by TYPE first (not by language!)
        for qtype in question_types:
            if qtype == "birth_place":
                self._generate_birth_place_questions(entity_id, languages)
            elif qtype == "nationality":
                self._generate_nationality_questions(entity_id, languages)
            elif qtype == "birth_date":
                self._generate_birth_date_questions(entity_id, languages)
```

### Birth Place Generation

```python
def _generate_birth_place_questions(self, entity_id: int, languages: List[str]):
    """Generate birth place questions for all languages at once"""

    # 1. Get entity's birth place
    birth_place_url = get_birth_place(entity_id)

    # 2. Get distractor entity IDs (language-agnostic)
    distractor_ids = self._get_birth_place_distractors(
        culture=entity['culture'],
        exclude_entity_id=entity_id,
        limit=100
    )

    if len(distractor_ids) < 3:
        logger.warning("Not enough distractors")
        return

    # 3. Select 3 distractors deterministically
    rng = random.Random(entity_id + 1000)
    selected_distractors = rng.sample(distractor_ids, 3)

    # 4. Shuffle all entities (correct + distractors)
    all_entities = [entity_id] + selected_distractors
    rng.shuffle(all_entities)

    # 5. Assign letters
    option_letters = ['A', 'B', 'C', 'D']

    # 6. FOR EACH LANGUAGE: Get labels and save
    for lang in languages:
        options = []
        correct_answer = None

        for letter, eid in zip(option_letters, all_entities):
            # Get birth place label for this entity in this language
            label = get_birth_place_label(eid, lang)

            options.append({
                "letter": letter,
                "text": label,
                "entity_id": eid
            })

            if eid == entity_id:
                correct_answer = letter
                ground_truth = label

        # Save to database
        save_question(
            entity_id=entity_id,
            language=lang,
            question_type="birth_place",
            question_text=get_question_template(lang, "birth_place", entity_name),
            ground_truth=ground_truth,
            options=json.dumps(options),
            correct_answer=correct_answer
        )
```

---

## Quality Control

### Validation Checks

1. **Uniqueness**: Ensure no duplicate distractors in same question
2. **Diversity**: Verify distractors come from different entities
3. **Consistency**: Check that option ordering is same across languages for same entity
4. **Correctness**: Validate that correct_answer letter matches ground truth

### Example Validation Query

```python
def validate_consistency(entity_id):
    """Check that all 3 languages have same entity_ids in same positions"""

    questions = db.execute("""
        SELECT language, options, correct_answer
        FROM questions
        WHERE entity_id = ? AND question_type = 'birth_place'
    """, (entity_id,))

    entity_id_sequences = []
    correct_letters = []

    for q in questions:
        options = json.loads(q['options'])
        entity_ids = [opt['entity_id'] for opt in options]
        entity_id_sequences.append(entity_ids)
        correct_letters.append(q['correct_answer'])

    # Check all languages have same entity_id order
    assert all(seq == entity_id_sequences[0] for seq in entity_id_sequences)

    # Check all languages have same correct letter
    assert all(letter == correct_letters[0] for letter in correct_letters)
```

---

## Examples

### Complete Example: Yunjin Kim (Q229389)

**Entity Info**:
- Birth Place: Seoul (Q8684)
- Nationality: South Korea (Q884)
- Birth Date: 1973-11-07

**Generated Questions** (all 9):

#### English Questions

```
1. Birth Place (en):
   Q: "Where was Yunjin Kim born?"
   A) Sanxing Township  [entity_id=5234]
   B) Seoul ✓           [entity_id=1]
   C) Zhongli District  [entity_id=3421]
   D) Tainan County     [entity_id=8765]
   Correct: B

2. Nationality (en):
   Q: "What is the nationality of Yunjin Kim?"
   A) United States     [entity_id=2453]
   B) France            [entity_id=8721]
   C) Egypt             [entity_id=5342]
   D) South Korea ✓     [entity_id=1]
   Correct: D

3. Birth Date (en):
   Q: "When was Yunjin Kim born?"
   A) 1971              [entity_id=7273]
   B) 1973 ✓            [entity_id=1]
   C) 1935              [entity_id=3578]
   D) 1980              [entity_id=6623]
   Correct: B
```

#### French Questions (Same entity_ids, French labels)

```
1. Birth Place (fr):
   Q: "Où est né Yunjin Kim?"
   A) Sanxing Township  [entity_id=5234] ← Same!
   B) Séoul ✓           [entity_id=1]    ← Same!
   C) Zhongli District  [entity_id=3421] ← Same!
   D) Tainan County     [entity_id=8765] ← Same!
   Correct: B ← Same letter!
```

#### Arabic Questions (Same entity_ids, Arabic labels)

```
1. Birth Place (ar):
   Q: "أين ولد يونجين كيم؟"
   A) Sanxing Township  [entity_id=5234] ← Same!
   B) سيول ✓            [entity_id=1]    ← Same!
   C) Zhongli District  [entity_id=3421] ← Same!
   D) Tainan County     [entity_id=8765] ← Same!
   Correct: B ← Same letter!
```

---

## Summary

### Key Takeaways

1. ✅ **Consistency First**: Generate distractor entity IDs once, then get labels per language
2. ✅ **Deterministic**: Use entity_id as random seed for reproducible results
3. ✅ **Diverse**: Use `ORDER BY RANDOM()` to avoid repetitive distractors
4. ✅ **Validated**: Check that entity_ids and correct letters match across languages
5. ✅ **Traceable**: Store entity_id in options JSON for debugging and analysis

### Benefits for Grouping Loss Evaluation

- **Fair Comparison**: Same question difficulty across languages
- **Isolates Bias**: Any performance difference is due to language/cultural bias, not question variation
- **Reproducible**: Deterministic generation enables consistent experimental results
- **Analyzable**: Entity_id tracking enables detailed distractor analysis

---

## References

- Wikidata Property Codes: https://www.wikidata.org/wiki/Wikidata:List_of_properties
- Project Summary: `notes/LLM_Grouping_Loss_Project_Summary.md`
- Database Schema: `docs/db_schema.md`
- Implementation: `src/data/question_generator.py`
