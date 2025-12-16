"""
Database operations for entity storage with multilingual support
SQLite database with duplicate prevention
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EntityDatabase:
    """SQLite database for storing entities with multilingual labels and Wikipedia texts"""

    def __init__(self, db_path: str = "data/entities.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._setup_database()

    def _setup_database(self):
        """Create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows

        cursor = self.conn.cursor()

        # Entities table - language-agnostic base info
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wikidata_id TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                culture TEXT,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Entity labels - multilingual names
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entity_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                label TEXT NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE(entity_id, language)
            )
        """
        )

        # Wikipedia texts - multilingual articles
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS wikipedia_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                title TEXT,
                summary TEXT,
                content TEXT,
                url TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE(entity_id, language)
            )
        """
        )

        # Facts table - stores Wikidata property values (URLs are language-agnostic)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                property TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE(entity_id, property, value)
            )
        """
        )

        # Fact labels - multilingual labels for fact values
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fact_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                label TEXT NOT NULL,
                FOREIGN KEY (fact_id) REFERENCES facts(id) ON DELETE CASCADE,
                UNIQUE(fact_id, language)
            )
        """
        )

        # Questions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                question_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                ground_truth TEXT NOT NULL,
                property TEXT NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE(entity_id, language, question_type)
            )
        """
        )

        # Entity metadata table - flexible key-value storage
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entity_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                metadata_key TEXT NOT NULL,
                metadata_value TEXT NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE(entity_id, metadata_key)
            )
        """
        )

        # Check if wikipedia_texts needs metadata columns (for existing databases)
        cursor.execute("PRAGMA table_info(wikipedia_texts)")
        columns = [row[1] for row in cursor.fetchall()]

        if "text_length_chars" not in columns:
            cursor.execute(
                "ALTER TABLE wikipedia_texts ADD COLUMN text_length_chars INTEGER"
            )
        if "text_length_words" not in columns:
            cursor.execute(
                "ALTER TABLE wikipedia_texts ADD COLUMN text_length_words INTEGER"
            )
        if "num_sections" not in columns:
            cursor.execute(
                "ALTER TABLE wikipedia_texts ADD COLUMN num_sections INTEGER"
            )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_wikidata_id ON entities(wikidata_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_culture ON entities(culture)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_labels_lang ON entity_labels(language)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_wikipedia_texts_lang ON wikipedia_texts(language)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_fact_labels_lang ON fact_labels(language)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_metadata_key ON entity_metadata(metadata_key)"
        )

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def entity_exists(self, wikidata_id: str) -> bool:
        """Check if entity already exists"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM entities WHERE wikidata_id = ?", (wikidata_id,))
        return cursor.fetchone() is not None

    def add_entity(
        self,
        wikidata_id: str,
        entity_type: str,
        culture: str = None,
        country: str = None,
    ) -> Optional[int]:
        """
        Add entity to database (language-agnostic base)
        Returns entity_id if added, or existing entity_id if already exists
        """
        if self.entity_exists(wikidata_id):
            logger.warning(
                f"Entity {wikidata_id} already exists, returning existing ID"
            )
            # Return existing entity_id
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id FROM entities WHERE wikidata_id = ?", (wikidata_id,)
            )
            return cursor.fetchone()["id"]

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO entities (wikidata_id, type, culture, country)
            VALUES (?, ?, ?, ?)
        """,
            (wikidata_id, entity_type, culture, country),
        )

        self.conn.commit()
        entity_id = cursor.lastrowid
        logger.info(f"Added entity: {wikidata_id}")
        return entity_id

    def add_entity_label(self, entity_id: int, language: str, label: str) -> bool:
        """Add entity label for a specific language"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO entity_labels (entity_id, language, label)
                VALUES (?, ?, ?)
            """,
                (entity_id, language, label),
            )
            self.conn.commit()
            logger.debug(f"Added label for entity {entity_id} in {language}: {label}")
            return True
        except sqlite3.IntegrityError:
            logger.debug(
                f"Duplicate label for entity {entity_id} in {language}, skipping"
            )
            return False

    def add_wikipedia_text(
        self,
        entity_id: int,
        language: str,
        title: str = None,
        summary: str = None,
        content: str = None,
        url: str = None,
        text_length_chars: int = None,
        text_length_words: int = None,
        num_sections: int = None,
    ) -> bool:
        """Add Wikipedia text for a specific language with metadata"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO wikipedia_texts (
                    entity_id, language, title, summary, content, url,
                    text_length_chars, text_length_words, num_sections
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entity_id,
                    language,
                    title,
                    summary,
                    content,
                    url,
                    text_length_chars,
                    text_length_words,
                    num_sections,
                ),
            )
            self.conn.commit()
            logger.info(
                f"Added Wikipedia text for entity {entity_id} in {language}: {title}"
            )
            return True
        except sqlite3.IntegrityError:
            logger.debug(
                f"Duplicate Wikipedia text for entity {entity_id} in {language}, skipping"
            )
            return False

    def add_fact(self, entity_id: int, property_code: str, value: str) -> Optional[int]:
        """Add fact to database, returns fact_id or None if duplicate"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO facts (entity_id, property, value)
                VALUES (?, ?, ?)
            """,
                (entity_id, property_code, value),
            )
            self.conn.commit()
            fact_id = cursor.lastrowid
            logger.debug(f"Added fact for entity {entity_id}, property {property_code}")
            return fact_id
        except sqlite3.IntegrityError:
            # Get existing fact_id
            cursor.execute(
                """
                SELECT id FROM facts
                WHERE entity_id = ? AND property = ? AND value = ?
            """,
                (entity_id, property_code, value),
            )
            result = cursor.fetchone()
            return result["id"] if result else None

    def add_fact_label(self, fact_id: int, language: str, label: str) -> bool:
        """Add label for a fact in a specific language"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO fact_labels (fact_id, language, label)
                VALUES (?, ?, ?)
            """,
                (fact_id, language, label),
            )
            self.conn.commit()
            logger.debug(f"Added label for fact {fact_id} in {language}: {label}")
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"Duplicate label for fact {fact_id} in {language}, skipping")
            return False

    def add_question(
        self,
        entity_id: int,
        language: str,
        question_type: str,
        question_text: str,
        ground_truth: str,
        property_code: str,
    ) -> bool:
        """Add question to database, returns False if duplicate"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO questions (entity_id, language, question_type, question_text, ground_truth, property)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    entity_id,
                    language,
                    question_type,
                    question_text,
                    ground_truth,
                    property_code,
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.debug(
                f"Duplicate question for entity {entity_id}, type {question_type}, language {language}"
            )
            return False

    def add_metadata(self, entity_id: int, key: str, value: str) -> bool:
        """Add metadata for an entity (stores as string, convert as needed)"""
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO entity_metadata (entity_id, metadata_key, metadata_value)
                VALUES (?, ?, ?)
            """,
                (entity_id, key, value),
            )
            self.conn.commit()
            logger.debug(f"Added metadata for entity {entity_id}: {key}={value}")
            return True
        except sqlite3.IntegrityError:
            # Update existing value
            cursor.execute(
                """
                UPDATE entity_metadata
                SET metadata_value = ?
                WHERE entity_id = ? AND metadata_key = ?
            """,
                (value, entity_id, key),
            )
            self.conn.commit()
            logger.debug(f"Updated metadata for entity {entity_id}: {key}={value}")
            return True

    def get_metadata(self, entity_id: int, key: str = None) -> Dict[str, str]:
        """
        Get metadata for an entity
        If key is specified, returns single value as dict {key: value}
        If key is None, returns all metadata as dict {key: value, ...}
        """
        cursor = self.conn.cursor()

        if key:
            cursor.execute(
                "SELECT metadata_value FROM entity_metadata WHERE entity_id = ? AND metadata_key = ?",
                (entity_id, key),
            )
            row = cursor.fetchone()
            return {key: row["metadata_value"]} if row else {}
        else:
            cursor.execute(
                "SELECT metadata_key, metadata_value FROM entity_metadata WHERE entity_id = ?",
                (entity_id,),
            )
            return {
                row["metadata_key"]: row["metadata_value"] for row in cursor.fetchall()
            }

    def get_entity(self, wikidata_id: str) -> Optional[Dict]:
        """Get entity by Wikidata ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE wikidata_id = ?", (wikidata_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_entity_labels(self, entity_id: int) -> Dict[str, str]:
        """Get all labels for an entity (returns dict: {language: label})"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT language, label FROM entity_labels WHERE entity_id = ?",
            (entity_id,),
        )
        return {row["language"]: row["label"] for row in cursor.fetchall()}

    def get_wikipedia_texts(self, entity_id: int) -> Dict[str, Dict]:
        """Get all Wikipedia texts for an entity (returns dict: {language: {title, summary, content, url}})"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT language, title, summary, content, url FROM wikipedia_texts WHERE entity_id = ?",
            (entity_id,),
        )
        return {
            row["language"]: {
                "title": row["title"],
                "summary": row["summary"],
                "content": row["content"],
                "url": row["url"],
            }
            for row in cursor.fetchall()
        }

    def get_entity_facts(self, entity_id: int) -> List[Dict]:
        """Get all facts for an entity with multilingual labels"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT f.id, f.property, f.value
            FROM facts f
            WHERE f.entity_id = ?
        """,
            (entity_id,),
        )

        facts = []
        for row in cursor.fetchall():
            fact = dict(row)

            # Get labels for this fact
            cursor.execute(
                "SELECT language, label FROM fact_labels WHERE fact_id = ?",
                (fact["id"],),
            )
            fact["labels"] = {r["language"]: r["label"] for r in cursor.fetchall()}

            facts.append(fact)

        return facts

    def get_entity_questions(self, entity_id: int, language: str = None) -> List[Dict]:
        """Get all questions for an entity, optionally filtered by language"""
        cursor = self.conn.cursor()

        if language:
            cursor.execute(
                "SELECT * FROM questions WHERE entity_id = ? AND language = ?",
                (entity_id, language),
            )
        else:
            cursor.execute("SELECT * FROM questions WHERE entity_id = ?", (entity_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_all_entities(
        self, entity_type: str = None, culture: str = None
    ) -> List[Dict]:
        """Get all entities with optional filters"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM entities WHERE 1=1"
        params = []

        if entity_type:
            query += " AND type = ?"
            params.append(entity_type)

        if culture:
            query += " AND culture = ?"
            params.append(culture)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Total entities
        cursor.execute("SELECT COUNT(*) as count FROM entities")
        stats["total_entities"] = cursor.fetchone()["count"]

        # By type
        cursor.execute("SELECT type, COUNT(*) as count FROM entities GROUP BY type")
        stats["by_type"] = {row["type"]: row["count"] for row in cursor.fetchall()}

        # By culture
        cursor.execute(
            "SELECT culture, COUNT(*) as count FROM entities GROUP BY culture"
        )
        stats["by_culture"] = {
            row["culture"]: row["count"] for row in cursor.fetchall()
        }

        # Total labels per language
        cursor.execute(
            "SELECT language, COUNT(*) as count FROM entity_labels GROUP BY language"
        )
        stats["labels_by_language"] = {
            row["language"]: row["count"] for row in cursor.fetchall()
        }

        # Total Wikipedia texts per language
        cursor.execute(
            "SELECT language, COUNT(*) as count FROM wikipedia_texts GROUP BY language"
        )
        stats["wikipedia_by_language"] = {
            row["language"]: row["count"] for row in cursor.fetchall()
        }

        # Total questions
        cursor.execute("SELECT COUNT(*) as count FROM questions")
        stats["total_questions"] = cursor.fetchone()["count"]

        # Total facts
        cursor.execute("SELECT COUNT(*) as count FROM facts")
        stats["total_facts"] = cursor.fetchone()["count"]

        return stats

    def get_entities_with_wikipedia(
        self, language: str, entity_type: str = None
    ) -> List[Dict]:
        """
        Get all entities that have Wikipedia text in specified language

        Args:
            language: Language code ('en', 'fr', 'ar')
            entity_type: Optional filter by entity type

        Returns:
            List of entity dicts
        """
        cursor = self.conn.cursor()

        query = """
            SELECT DISTINCT e.*
            FROM entities e
            INNER JOIN wikipedia_texts w ON e.id = w.entity_id
            WHERE w.language = ?
        """
        params = [language]

        if entity_type:
            query += " AND e.type = ?"
            params.append(entity_type)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_entities_with_all_wikipedia(
        self, languages: List[str] = ["en", "fr", "ar"], entity_type: str = None
    ) -> List[Dict]:
        """
        Get all entities that have Wikipedia text in ALL specified languages

        Args:
            languages: List of language codes (default: ['en', 'fr', 'ar'])
            entity_type: Optional filter by entity type

        Returns:
            List of entity dicts with complete Wikipedia coverage
        """
        cursor = self.conn.cursor()

        # Build query to find entities with Wikipedia in all languages
        query = f"""
            SELECT e.*
            FROM entities e
            WHERE (
                SELECT COUNT(DISTINCT w.language)
                FROM wikipedia_texts w
                WHERE w.entity_id = e.id
                AND w.language IN ({','.join(['?'] * len(languages))})
            ) = ?
        """
        params = languages + [len(languages)]

        if entity_type:
            query += " AND e.type = ?"
            params.append(entity_type)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def export_wikipedia_texts(
        self, language: str, entity_type: str = None
    ) -> List[Tuple[int, str]]:
        """
        Export Wikipedia texts for clustering

        Args:
            language: Language code
            entity_type: Optional filter by entity type

        Returns:
            List of tuples: [(entity_id, text), ...]
        """
        cursor = self.conn.cursor()

        query = """
            SELECT e.id, w.content
            FROM entities e
            INNER JOIN wikipedia_texts w ON e.id = w.entity_id
            WHERE w.language = ? AND w.content IS NOT NULL
        """
        params = [language]

        if entity_type:
            query += " AND e.type = ?"
            params.append(entity_type)

        cursor.execute(query, params)
        return [(row["id"], row["content"]) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
