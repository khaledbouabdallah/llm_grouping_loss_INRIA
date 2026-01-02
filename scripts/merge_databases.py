"""
Merge two SQLite databases
Copies all entities and related data from scripts/data/entities.db to data/entities.db
Handles duplicates gracefully using wikidata_id as the unique key
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# Paths
main_db_path = Path("../data/entities.db")
secondary_db_path = Path("data/entities.db")  # This script is in scripts/
backup_path = Path(
    f"../data/entities_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
)

print("=" * 70)
print("DATABASE MERGE SCRIPT")
print("=" * 70)

# Check if both databases exist
if not main_db_path.exists():
    print(f"ERROR: Main database not found: {main_db_path}")
    exit(1)

if not secondary_db_path.exists():
    print(f"ERROR: Secondary database not found: {secondary_db_path}")
    exit(1)

print(f"\n✓ Found main database: {main_db_path}")
print(f"  Size: {main_db_path.stat().st_size / 1024 / 1024:.2f} MB")

print(f"\n✓ Found secondary database: {secondary_db_path}")
print(f"  Size: {secondary_db_path.stat().st_size / 1024 / 1024:.2f} MB")

# Create backup
print(f"\nCreating backup: {backup_path}")
shutil.copy2(main_db_path, backup_path)
print(f"✓ Backup created: {backup_path.stat().st_size / 1024 / 1024:.2f} MB")

# Connect to main database
conn = sqlite3.connect(main_db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get initial counts
print("\n" + "=" * 70)
print("INITIAL STATE")
print("=" * 70)

cursor.execute("SELECT COUNT(*) as count FROM entities")
main_entities_before = cursor.fetchone()["count"]
print(f"Main DB entities: {main_entities_before}")

# Attach secondary database
print(f"\nAttaching secondary database...")
cursor.execute(f"ATTACH DATABASE '{secondary_db_path.absolute()}' AS secondary")

# Get secondary counts
cursor.execute("SELECT COUNT(*) as count FROM secondary.entities")
secondary_entities = cursor.fetchone()["count"]
print(f"Secondary DB entities: {secondary_entities}")

# Show overlap
cursor.execute(
    """
    SELECT COUNT(*) as count
    FROM secondary.entities se
    WHERE EXISTS (
        SELECT 1 FROM entities e WHERE e.wikidata_id = se.wikidata_id
    )
"""
)
overlap = cursor.fetchone()["count"]
print(f"Overlapping entities (by wikidata_id): {overlap}")
print(f"New entities to add: {secondary_entities - overlap}")

# Confirm before proceeding
print("\n" + "=" * 70)
response = input("Proceed with merge? (yes/no): ").strip().lower()
if response not in ["yes", "y"]:
    print("Merge cancelled")
    conn.close()
    exit(0)

print("\n" + "=" * 70)
print("MERGING DATA")
print("=" * 70)

# Start transaction
conn.execute("BEGIN TRANSACTION")

try:
    # Step 1: Create temporary mapping for entity IDs
    print("\n1. Creating entity ID mapping...")
    cursor.execute(
        """
        CREATE TEMPORARY TABLE id_mapping (
            old_id INTEGER,
            new_id INTEGER,
            wikidata_id TEXT
        )
    """
    )

    # Step 2: Insert entities and track ID mappings
    print("2. Merging entities...")
    cursor.execute(
        """
        SELECT * FROM secondary.entities
    """
    )

    new_count = 0
    updated_count = 0

    for row in cursor.fetchall():
        old_id = row["id"]
        wikidata_id = row["wikidata_id"]

        # Check if entity exists
        cursor.execute("SELECT id FROM entities WHERE wikidata_id = ?", (wikidata_id,))
        existing = cursor.fetchone()

        if existing:
            # Entity exists - use existing ID
            new_id = existing["id"]
            updated_count += 1

            # Update metadata if newer
            cursor.execute(
                """
                UPDATE entities
                SET culture = ?, country = ?
                WHERE id = ? AND (culture IS NULL OR country IS NULL)
            """,
                (row["culture"], row["country"], new_id),
            )
        else:
            # Insert new entity
            cursor.execute(
                """
                INSERT INTO entities (wikidata_id, type, culture, country)
                VALUES (?, ?, ?, ?)
            """,
                (row["wikidata_id"], row["type"], row["culture"], row["country"]),
            )
            new_id = cursor.lastrowid
            new_count += 1

        # Store mapping
        cursor.execute(
            """
            INSERT INTO id_mapping (old_id, new_id, wikidata_id)
            VALUES (?, ?, ?)
        """,
            (old_id, new_id, wikidata_id),
        )

    print(f"   New entities: {new_count}")
    print(f"   Existing entities: {updated_count}")

    # Step 3: Merge entity_labels
    print("3. Merging entity labels...")
    cursor.execute(
        """
        INSERT OR IGNORE INTO entity_labels (entity_id, language, label)
        SELECT m.new_id, sl.language, sl.label
        FROM secondary.entity_labels sl
        JOIN id_mapping m ON sl.entity_id = m.old_id
    """
    )
    print(f"   Added {cursor.rowcount} labels")

    # Step 4: Merge wikipedia_texts
    print("4. Merging Wikipedia texts...")
    cursor.execute(
        """
        INSERT OR REPLACE INTO wikipedia_texts
        (entity_id, language, title, summary, content, url)
        SELECT m.new_id, sw.language, sw.title, sw.summary, sw.content, sw.url
        FROM secondary.wikipedia_texts sw
        JOIN id_mapping m ON sw.entity_id = m.old_id
    """
    )
    print(f"   Added/updated {cursor.rowcount} Wikipedia texts")

    # Step 5: Merge facts
    print("5. Merging facts...")
    cursor.execute(
        """
        INSERT OR IGNORE INTO facts (entity_id, property, value)
        SELECT m.new_id, sf.property, sf.value
        FROM secondary.facts sf
        JOIN id_mapping m ON sf.entity_id = m.old_id
    """
    )
    facts_added = cursor.rowcount
    print(f"   Added {facts_added} facts")

    # Step 6: Merge fact_labels (need to map fact IDs)
    print("6. Merging fact labels...")

    # For each fact in secondary, find corresponding fact in main and copy labels
    cursor.execute(
        """
        SELECT sf.id as old_fact_id, m.new_id as new_entity_id, sf.property, sf.value
        FROM secondary.facts sf
        JOIN id_mapping m ON sf.entity_id = m.old_id
    """
    )

    fact_labels_added = 0
    for fact_row in cursor.fetchall():
        # Find the corresponding fact ID in main database
        cursor.execute(
            """
            SELECT id FROM facts
            WHERE entity_id = ? AND property = ? AND value = ?
        """,
            (fact_row["new_entity_id"], fact_row["property"], fact_row["value"]),
        )

        main_fact = cursor.fetchone()
        if main_fact:
            new_fact_id = main_fact["id"]
            old_fact_id = fact_row["old_fact_id"]

            # Copy fact labels
            cursor.execute(
                """
                INSERT OR IGNORE INTO fact_labels (fact_id, language, label)
                SELECT ?, sfl.language, sfl.label
                FROM secondary.fact_labels sfl
                WHERE sfl.fact_id = ?
            """,
                (new_fact_id, old_fact_id),
            )
            fact_labels_added += cursor.rowcount

    print(f"   Added {fact_labels_added} fact labels")

    # Step 7: Merge questions (if they exist)
    print("7. Merging questions...")
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO questions
            (entity_id, language, question_type, question_text, correct_answer,
             ground_truth, options, created_at)
            SELECT m.new_id, sq.language, sq.question_type, sq.question_text,
                   sq.correct_answer, sq.ground_truth, sq.options, sq.created_at
            FROM secondary.questions sq
            JOIN id_mapping m ON sq.entity_id = m.old_id
        """
        )
        print(f"   Added {cursor.rowcount} questions")
    except sqlite3.OperationalError:
        print("   No questions table (skipped)")

    # Step 8: Merge entity_metadata (if exists)
    print("8. Merging entity metadata...")
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO entity_metadata (entity_id, metadata_key, metadata_value)
            SELECT m.new_id, sem.metadata_key, sem.metadata_value
            FROM secondary.entity_metadata sem
            JOIN id_mapping m ON sem.entity_id = m.old_id
        """
        )
        print(f"   Added {cursor.rowcount} metadata entries")
    except sqlite3.OperationalError:
        print("   No metadata table (skipped)")

    # Commit transaction
    conn.commit()
    print("\n✓ Transaction committed successfully")

except Exception as e:
    conn.rollback()
    print(f"\n✗ ERROR: {e}")
    print("Transaction rolled back - no changes made")
    raise
finally:
    # Detach secondary database
    cursor.execute("DETACH DATABASE secondary")

# Final counts
print("\n" + "=" * 70)
print("FINAL STATE")
print("=" * 70)

cursor.execute("SELECT COUNT(*) as count FROM entities")
main_entities_after = cursor.fetchone()["count"]

cursor.execute("SELECT COUNT(*) as count FROM entity_labels")
total_labels = cursor.fetchone()["count"]

cursor.execute("SELECT COUNT(*) as count FROM wikipedia_texts")
total_wiki = cursor.fetchone()["count"]

cursor.execute("SELECT COUNT(*) as count FROM facts")
total_facts = cursor.fetchone()["count"]

print(
    f"Total entities: {main_entities_after} (added {main_entities_after - main_entities_before})"
)
print(f"Total labels: {total_labels}")
print(f"Total Wikipedia texts: {total_wiki}")
print(f"Total facts: {total_facts}")

conn.close()

print("\n" + "=" * 70)
print("MERGE COMPLETED SUCCESSFULLY!")
print("=" * 70)
print(f"\nBackup saved at: {backup_path}")
print(f"Main database: {main_db_path}")
print(f"\nYou can now delete: {secondary_db_path}")
print("=" * 70)
