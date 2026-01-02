"""
Test script for multiple choice question generation
Tests generation for ONE entity to validate implementation
"""

import json
from src.data import EntityDatabase, MultipleChoiceQuestionGenerator


def test_question_generation():
    """Test question generation for a single entity"""

    print("=" * 80)
    print("TESTING MULTIPLE CHOICE QUESTION GENERATION")
    print("=" * 80 + "\n")

    # Initialize database
    db = EntityDatabase("../data/entities.db")

    # Get stats
    stats = db.get_statistics()
    print(f"Database stats:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  By culture: {stats.get('by_culture', {})}")
    print(f"  Entities with Wikipedia: {stats.get('wikipedia_by_language', {})}")
    print()

    # Get entities with all Wikipedia versions
    entities = db.get_entities_with_all_wikipedia(
        ["en", "fr", "ar"], entity_type="person"
    )

    if not entities:
        print("❌ No entities found with all Wikipedia versions!")
        print(
            "   You need entities with en, fr, and ar Wikipedia to generate questions."
        )
        return

    print(f"Found {len(entities)} entities with all Wikipedia versions\n")

    # Pick first entity
    entity = entities[0]
    entity_id = entity["id"]

    print(f"Testing with entity:")
    print(f"  ID: {entity_id}")
    print(f"  Wikidata: {entity['wikidata_id']}")
    print(f"  Culture: {entity['culture']}")
    print(f"  Country: {entity['country']}")

    # Get entity labels
    labels = db.get_entity_labels(entity_id)
    print(f"  Names:")
    for lang, label in labels.items():
        print(f"    {lang}: {label}")
    print()

    # Initialize generator
    generator = MultipleChoiceQuestionGenerator(db)

    # Generate questions
    print("Generating questions...")
    result_stats = generator.generate_all_questions(entity_id)

    print(f"\nGeneration results:")
    print(f"  ✅ Success: {result_stats['success']}")
    print(f"  ❌ Failed: {result_stats['failed']}")
    print(f"  ⏭️  Skipped: {result_stats['skipped']}")
    print()

    # Display generated questions
    print("=" * 80)
    print("GENERATED QUESTIONS")
    print("=" * 80 + "\n")

    for language in ["en", "fr", "ar"]:
        questions = db.get_entity_questions(entity_id, language=language)

        if not questions:
            print(f"No questions generated for {language}")
            continue

        print(f"\n{'─' * 80}")
        print(f"Language: {language.upper()}")
        print("─" * 80)

        for q in questions:
            print(f"\nQuestion Type: {q['question_type']}")
            print(f"Question: {q['question_text']}")
            print(f"Correct Answer: {q['correct_answer']}")
            print(f"Ground Truth: {q['ground_truth']}")

            if q["options"]:
                options = json.loads(q["options"])
                print("Options:")
                for opt in options:
                    marker = "✓" if opt["letter"] == q["correct_answer"] else " "
                    print(
                        f"  {marker} {opt['letter']}: {opt['text']} (entity_id: {opt['entity_id']})"
                    )
            print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    db.close()


if __name__ == "__main__":
    test_question_generation()
